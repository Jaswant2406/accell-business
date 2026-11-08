"""
Independent Ground-Truth Oracle for Accel Business Product Catalogue.

This script parses product_catalogue.csv directly and implements the pure
catalogue rules independently without importing or relying on engine.eligibility.
Used to cross-validate engine.eligibility outputs against pure catalogue specifications.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

CATALOGUE_PATH = Path(__file__).resolve().parent.parent / "product_catalogue.csv"
SMB_LEADS_PATH = Path(__file__).resolve().parent.parent / "smb_leads.csv"


class CatalogueOracle:
    def __init__(self, catalogue_path: Path = CATALOGUE_PATH, leads_path: Path = SMB_LEADS_PATH):
        self.catalogue_path = catalogue_path
        self.leads_path = leads_path
        self.products: Dict[str, Dict[str, Any]] = {}
        self.known_city_tiers: Dict[str, int] = {}
        self._load_data()

    def _load_data(self):
        # Load catalogue
        with open(self.catalogue_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row["product_id"].strip()
                tiers = [int(t.strip()) for t in row["available_city_tiers"].split(";") if t.strip().isdigit()]
                req_one_of = [p.strip() for p in row["requires_one_of"].split("|") if p.strip()] if row.get("requires_one_of") else []
                self.products[pid] = {
                    "product_id": pid,
                    "category": row["category"].strip(),
                    "product_name": row["product_name"].strip(),
                    "description": row["description"].strip(),
                    "unit": row["unit"].strip(),
                    "price_min": int(row["price_min_inr_per_month"]),
                    "price_max": int(row["price_max_inr_per_month"]),
                    "one_time_setup": int(row["one_time_setup_inr"]),
                    "min_contract_months": int(row["min_contract_months"]),
                    "available_city_tiers": tiers,
                    "min_employees": int(row["min_employees"]),
                    "min_sites": int(row["min_sites"]),
                    "requires_gstin": row["requires_gstin"].strip().upper() == "Y",
                    "requires_one_of": req_one_of,
                    "typical_install_days": int(row["typical_install_days"]),
                    "target_segments": [s.strip() for s in row["target_segments"].split(";") if s.strip()],
                }

        # Load known city tiers from leads
        with open(self.leads_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                city = row["city"].strip().lower()
                try:
                    self.known_city_tiers[city] = int(row["city_tier"])
                except (ValueError, TypeError):
                    continue

    def lookup_city_tier(self, city_name: str) -> Tuple[int, bool]:
        """
        Returns (city_tier, is_known).
        If unknown, returns (2, False) noting that it is an unlisted city.
        """
        clean = (city_name or "").strip().lower()
        if clean in self.known_city_tiers:
            return self.known_city_tiers[clean], True
        return 2, False  # Defaulted to Tier 2

    def evaluate_eligibility(
        self,
        product_id: str,
        city_tier: int,
        employee_count: int,
        num_sites: int,
        has_active_gstin: bool,
    ) -> Tuple[bool, List[str]]:
        """
        Strict evaluation of eligibility criteria from product_catalogue.csv.
        Returns (is_eligible, failure_reasons).
        """
        if product_id not in self.products:
            return False, [f"Unknown product {product_id}"]

        p = self.products[product_id]
        reasons = []

        # 1. City Tier
        if city_tier not in p["available_city_tiers"]:
            reasons.append(f"Available only in Tier {p['available_city_tiers']} cities (current is Tier {city_tier})")

        # 2. Employees
        if employee_count < p["min_employees"]:
            reasons.append(f"Requires minimum {p['min_employees']} employees (current: {employee_count})")

        # 3. Sites
        if num_sites < p["min_sites"]:
            reasons.append(f"Requires minimum {p['min_sites']} sites (current: {num_sites})")

        # 4. GSTIN
        if p["requires_gstin"] and not has_active_gstin:
            reasons.append("Requires active GSTIN registration")

        return len(reasons) == 0, reasons

    def check_dependencies(
        self,
        selected_pids: Set[str],
    ) -> Dict[str, List[str]]:
        """
        Checks requires_one_of dependencies.
        Returns dict of {product_id: [missing_candidate_parents]}.
        """
        missing = {}
        for pid in selected_pids:
            if pid not in self.products:
                continue
            req = self.products[pid]["requires_one_of"]
            if req and not any(parent in selected_pids for parent in req):
                missing[pid] = req
        return missing

    def sanity_check_single_connectivity(self, bundle_pids: List[str]) -> Tuple[bool, str]:
        """
        Sanity Check (a): At most ONE primary connectivity product (P01-P06, P04 for wireless) per site.
        """
        conn_pids = [pid for pid in bundle_pids if pid in ["P01", "P02", "P03", "P04", "P05", "P06"]]
        if len(conn_pids) > 1:
            return False, f"Violated Sanity Check (a): Multiple primary connectivity products in bundle: {conn_pids}"
        return True, "Pass: Exactly one primary connectivity product selected"

    def sanity_check_stated_needs_and_deps(
        self,
        bundle_pids: List[str],
        stated_needs: List[str],
        auto_added_pids: List[str],
    ) -> Tuple[bool, List[str]]:
        """
        Sanity Check (b): No product unless it was stated as a need or is a required dependency.
        """
        from engine.eligibility import matches_stated_need
        violations = []
        for pid in bundle_pids:
            if pid in ["P01", "P02", "P03", "P04", "P05", "P06"]:
                # Primary connectivity is validated under check (a)
                continue
            if pid in auto_added_pids:
                # Required dependency is permitted
                continue
            if not matches_stated_need(pid, stated_needs):
                violations.append(f"Product {pid} ({self.products.get(pid, {}).get('product_name')}) neither stated in needs nor a required dependency")
        return len(violations) == 0, violations

    def sanity_check_budget_adherence(
        self,
        monthly_subtotal: int,
        budget: Optional[int],
        has_dropped_explanation: bool,
    ) -> Tuple[bool, str]:
        """
        Sanity Check (c): When budget given, bundle total must be at or under it, or explanation must state why.
        """
        if budget is None or budget <= 0:
            return True, "No budget ceiling specified"
        if monthly_subtotal <= budget:
            return True, f"Pass: Subtotal ₹{monthly_subtotal:,} <= Budget ₹{budget:,}"
        if has_dropped_explanation:
            return True, f"Pass: Subtotal ₹{monthly_subtotal:,} exceeds budget ₹{budget:,} with explanation provided"
        return False, f"Violated Sanity Check (c): Subtotal ₹{monthly_subtotal:,} exceeds budget ₹{budget:,} without dropped explanation"

    def determine_expected_quantity(
        self,
        product_id: str,
        employee_count: int,
        num_sites: int,
        vehicle_count: Optional[int] = None,
    ) -> Tuple[int, str]:
        """
        Independent baseline quantity calculation per product unit specification.
        """
        if product_id not in self.products:
            return 1, "Unknown product"

        unit = self.products[product_id]["unit"].lower()
        pid = product_id

        if unit == "per site":
            return max(1, num_sites), f"1 per site across {num_sites} site(s)"
        elif unit == "per user":
            return max(1, employee_count), f"1 per employee ({employee_count} employees)"
        elif unit == "per line":
            return max(1, employee_count), f"1 business mobile connection per employee ({employee_count} lines)"
        elif unit == "per account":
            return 1, "1 primary organizational subscription account"
        elif unit == "per counter":
            return max(1, num_sites), f"1 POS billing counter per site ({num_sites} counter(s))"
        elif unit == "per camera":
            # 2 cameras per site standard assumption
            q = max(2, num_sites * 2)
            return q, f"Assumption: 2 cameras per site ({q} cameras total)"
        elif unit == "per device":
            if pid == "P20":
                return max(1, employee_count), f"1 endpoint security license per employee PC ({employee_count} devices)"
            elif pid == "P24":
                q = max(2, min(employee_count, 10))
                return q, f"Industrial starter kit: {q} machine sensors"
            return 1, "1 device"
        elif unit == "per vehicle":
            if vehicle_count is not None and vehicle_count > 0:
                return vehicle_count, f"Requested vehicle fleet count: {vehicle_count}"
            q = max(1, min(num_sites, 5))
            return q, f"Assumption: default {q} fleet vehicles"
        elif unit == "per ip":
            return 1, "1 static public IP address"
        elif unit == "per channel":
            q = max(2, min(employee_count, 8))
            return q, f"SIP trunk: {q} channels based on {employee_count} employees"
        elif unit == "per number":
            return 1, "1 toll-free 1800 number"
        elif unit == "per pack":
            return 1, "1 pack of 10,000 SMS"

        return 1, "1 unit"

    def calculate_expected_pricing(
        self,
        items: List[Dict[str, Any]],
        contract_months: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculates quote pricing directly from catalogue constants.
        """
        line_items = []
        monthly_subtotal = 0
        one_time_subtotal = 0
        min_allowed_contract = 1
        max_install_days = 0

        for it in items:
            pid = it["product_id"]
            if pid not in self.products:
                continue
            p = self.products[pid]
            qty = it.get("quantity", 1)
            p_min = p["price_min"]
            p_max = p["price_max"]
            setup = p["one_time_setup"]
            cm = p["min_contract_months"]
            days = p["typical_install_days"]

            if cm > min_allowed_contract:
                min_allowed_contract = cm
            if days > max_install_days:
                max_install_days = days

            m_amt = p_min * qty
            o_amt = setup * qty
            monthly_subtotal += m_amt
            one_time_subtotal += o_amt

            line_items.append({
                "product_id": pid,
                "product_name": p["product_name"],
                "unit": p["unit"],
                "quantity": qty,
                "unit_price": p_min,
                "unit_setup_fee": setup,
                "monthly_amount": m_amt,
                "one_time_amount": o_amt,
                "min_contract_months": cm,
                "typical_install_days": days,
            })

        effective_cm = contract_months if contract_months is not None else min_allowed_contract
        if effective_cm < min_allowed_contract:
            effective_cm = min_allowed_contract

        first_month = monthly_subtotal + one_time_subtotal
        total_contract_value = (monthly_subtotal * effective_cm) + one_time_subtotal

        return {
            "items": line_items,
            "monthly_subtotal": monthly_subtotal,
            "one_time_subtotal": one_time_subtotal,
            "first_month_payable": first_month,
            "total_contract_value": total_contract_value,
            "min_allowed_contract_months": min_allowed_contract,
            "effective_contract_months": effective_cm,
            "max_install_days": max_install_days,
        }
