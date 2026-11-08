"""
Budget Optimization Module: "Fit My Budget".
Selects the product bundle that maximizes coverage of customer stated needs
under a monthly budget ceiling while strictly respecting:
- Eligibility rules (City Tier, GSTIN, Employees, Sites)
- Catalogue pricing (price_min) and unit quantities
- Contract duration constraints (min_contract_months)
- requires_one_of parent/child dependency DAGs
Transparently explains what products were included, what was dropped, and why.
"""

from dataclasses import dataclass, field
import itertools
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd

from engine.eligibility import (
    BusinessProfile,
    determine_quantity,
    evaluate_product_eligibility,
    matches_stated_need,
)
from kyc.registry import load_catalogue, lookup_gstin


@dataclass
class DroppedProductExplanation:
    product_id: str
    product_name: str
    monthly_cost: int
    reason: str


@dataclass
class BudgetFitResult:
    selected_items: List[Dict[str, Any]]
    total_monthly_cost: int
    monthly_budget: int
    remaining_budget: int
    dropped_items: List[DroppedProductExplanation]
    covered_needs: List[str]
    uncovered_needs: List[str]
    explanation: str
    total_setup_cost: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_items": self.selected_items,
            "total_monthly_cost": self.total_monthly_cost,
            "total_setup_cost": self.total_setup_cost,
            "monthly_budget": self.monthly_budget,
            "remaining_budget": self.remaining_budget,
            "dropped_items": [
                {
                    "product_id": d.product_id,
                    "product_name": d.product_name,
                    "monthly_cost": d.monthly_cost,
                    "reason": d.reason,
                }
                for d in self.dropped_items
            ],
            "covered_needs": self.covered_needs,
            "uncovered_needs": self.uncovered_needs,
            "explanation": self.explanation,
        }


def fit_bundle_to_budget(
    profile: BusinessProfile,
    monthly_budget: int,
    contract_months: Optional[int] = None,
) -> BudgetFitResult:
    """
    Optimize bundle selection to maximize utility within monthly_budget.
    """
    df = load_catalogue()
    gstin_record = lookup_gstin(profile.gstin) if profile.gstin else None

    # 1. Determine candidate eligible products
    eligible_products: Dict[str, Dict[str, Any]] = {}
    ineligible_explanations: List[DroppedProductExplanation] = []

    for _, row in df.iterrows():
        pid = str(row["product_id"])
        pname = str(row["product_name"])
        p_min = int(row["price_min_inr_per_month"])
        p_max = int(row["price_max_inr_per_month"])
        setup = int(row["one_time_setup_inr"])
        min_cm = int(row["min_contract_months"])
        install_days = int(row["typical_install_days"])
        req_one_of = str(row["requires_one_of"]) if pd.notna(row["requires_one_of"]) else ""
        unit = str(row["unit"])

        is_elig, inelig_reason = evaluate_product_eligibility(row, profile, gstin_record)
        if not is_elig:
            ineligible_explanations.append(
                DroppedProductExplanation(
                    product_id=pid,
                    product_name=pname,
                    monthly_cost=p_min,
                    reason=f"Ineligible: {inelig_reason}",
                )
            )
            continue

        if contract_months is not None and min_cm > contract_months:
            ineligible_explanations.append(
                DroppedProductExplanation(
                    product_id=pid,
                    product_name=pname,
                    monthly_cost=p_min,
                    reason=f"Requires {min_cm} months contract (selected: {contract_months} mo)",
                )
            )
            continue

        qty, assumption = determine_quantity(row, profile)
        monthly_cost = p_min * qty

        # Calculate utility score
        # Base connectivity has highest foundational value
        is_wired_fibre = pid in ["P01", "P02", "P03", "P05", "P06"]
        is_airfiber = pid == "P04"
        is_base = is_wired_fibre or is_airfiber
        matches_need = matches_stated_need(pid, profile.stated_needs)
        
        utility = 0
        if is_wired_fibre:
            utility += 150
        elif is_airfiber:
            utility += 120

        if matches_need:
            utility += 1000

        # Segment affinity only when stated needs are general/empty
        if not profile.stated_needs:
            segments_str = str(row["target_segments"]).lower()
            if profile.segment and profile.segment.lower() in segments_str:
                utility += 25

        eligible_products[pid] = {
            "product_id": pid,
            "product_name": pname,
            "category": str(row["category"]),
            "unit": unit,
            "quantity": qty,
            "price_min": p_min,
            "price_max": p_max,
            "one_time_setup": setup,
            "min_contract_months": min_cm,
            "typical_install_days": install_days,
            "requires_one_of": req_one_of,
            "monthly_cost": monthly_cost,
            "utility": utility,
            "assumption": assumption,
            "matches_need": matches_need,
            "is_base": is_base,
        }

    # Determine relevant products (matching stated needs or foundational connectivity)
    relevant_candidates = [
        p for p in eligible_products.values()
        if p["matches_need"] or p["is_base"]
    ]
    if not relevant_candidates:
        relevant_candidates = list(eligible_products.values())

    # If budget cannot afford even the cheapest relevant product
    cheapest_cost = min((p["monthly_cost"] for p in relevant_candidates), default=999)
    if monthly_budget < cheapest_cost:
        dropped = [
            DroppedProductExplanation(
                product_id=p["product_id"],
                product_name=p["product_name"],
                monthly_cost=p["monthly_cost"],
                reason=f"Monthly cost ₹{p['monthly_cost']:,} exceeds total budget of ₹{monthly_budget:,}",
            )
            for p in relevant_candidates
        ]
        return BudgetFitResult(
            selected_items=[],
            total_monthly_cost=0,
            monthly_budget=monthly_budget,
            remaining_budget=monthly_budget,
            dropped_items=dropped,
            covered_needs=[],
            uncovered_needs=profile.stated_needs,
            explanation=f"Budget of ₹{monthly_budget:,}/mo is below the minimum entry cost (₹{cheapest_cost:,}/mo) for enterprise connectivity.",
        )

    # 2. Optimization Search: Maximize utility subject to budget & requires_one_of
    pids = list(eligible_products.keys())
    # Sort candidate products by utility desc, then cost asc
    pids.sort(key=lambda x: (eligible_products[x]["utility"], -eligible_products[x]["monthly_cost"]), reverse=True)

    best_combo: Set[str] = set()
    best_utility = 0
    best_cost = 0

    # Branch and bound / combo search prioritizing high-utility combinations
    # Only consider products with positive utility or prerequisite parents
    search_pids = [p for p in pids if eligible_products[p]["utility"] > 0]
    # Also include any parent products required by candidates
    for p in list(search_pids):
        req_str = eligible_products[p]["requires_one_of"]
        if req_str:
            for parent in req_str.split("|"):
                parent = parent.strip()
                if parent in eligible_products and parent not in search_pids:
                    search_pids.append(parent)

    def is_valid_dependency_subset(subset: Set[str]) -> bool:
        # At most ONE primary connectivity product (P01-P06) permitted per bundle
        base_conns = [p for p in subset if p in ["P01", "P02", "P03", "P04", "P05", "P06"]]
        if len(base_conns) > 1:
            return False
        for p in subset:
            req_str = eligible_products[p]["requires_one_of"]
            if req_str:
                parents = [c.strip() for c in req_str.split("|") if c.strip()]
                if not any(parent in subset for parent in parents):
                    return False
        return True

    # Check baseline greedy first
    def evaluate_set(s: Set[str]) -> Tuple[int, int]:
        total_u = sum(eligible_products[p]["utility"] for p in s)
        total_c = sum(eligible_products[p]["monthly_cost"] for p in s)
        return total_u, total_c

    # Systematic exploration of combinations up to size 7
    # (Typical bundles have 2-5 products)
    from itertools import combinations
    primary_base_pids = {"P01", "P02", "P03", "P05", "P06"}

    for k in range(1, min(len(search_pids) + 1, 7)):
        for combo in combinations(search_pids, k):
            c_set = set(combo)
            # If single site, at most 1 primary fixed broadband line
            if profile.num_sites == 1 and len(c_set.intersection(primary_base_pids)) > 1:
                continue

            cost = sum(eligible_products[p]["monthly_cost"] for p in c_set)
            if cost <= monthly_budget:
                if is_valid_dependency_subset(c_set):
                    # Prefer having a base connectivity product if available
                    has_base = any(eligible_products[p]["is_base"] for p in c_set)
                    util = sum(eligible_products[p]["utility"] for p in c_set)
                    if has_base:
                        util += 50
                    if util > best_utility or (util == best_utility and cost < best_cost):
                        best_utility = util
                        best_cost = cost
                        best_combo = c_set

    # 3. Compile selected products
    selected_items: List[Dict[str, Any]] = []
    covered_needs: Set[str] = set()

    for pid in sorted(best_combo):
        p_info = eligible_products[pid]
        selected_items.append({
            "product_id": pid,
            "product_name": p_info["product_name"],
            "category": p_info["category"],
            "quantity": p_info["quantity"],
            "price_min": p_info["price_min"],
            "price_max": p_info["price_max"],
            "one_time_setup": p_info["one_time_setup"],
            "unit": p_info["unit"],
            "reason": f"Optimized within ₹{monthly_budget:,}/mo budget",
            "assumption": p_info["assumption"],
        })
        for need in profile.stated_needs:
            if matches_stated_need(pid, [need]):
                covered_needs.add(need)

    uncovered_needs = [n for n in profile.stated_needs if n not in covered_needs]

    # 4. Compile dropped products with clear explanations
    dropped_explanations: List[DroppedProductExplanation] = []
    for pid, p_info in eligible_products.items():
        if pid not in best_combo and (p_info["matches_need"] or p_info["is_base"]):
            m_cost = p_info["monthly_cost"]
            if best_cost + m_cost > monthly_budget:
                reason = f"Exceeded remaining budget of ₹{monthly_budget - best_cost:,}/mo (product requires ₹{m_cost:,}/mo)"
            elif p_info["requires_one_of"]:
                req_parents = p_info["requires_one_of"]
                reason = f"Required broadband dependency ({req_parents}) not accommodated within budget"
            else:
                reason = "Lower priority than selected core connectivity and higher-ranked needs"

            dropped_explanations.append(
                DroppedProductExplanation(
                    product_id=pid,
                    product_name=p_info["product_name"],
                    monthly_cost=m_cost,
                    reason=reason,
                )
            )

    # 5. Build summary explanation
    prod_names = ", ".join([it["product_name"] for it in selected_items])
    if selected_items:
        summary = (
            f"Optimized bundle for ₹{monthly_budget:,}/mo budget: Selected {len(selected_items)} products "
            f"({prod_names}) totaling ₹{best_cost:,}/mo (₹{monthly_budget - best_cost:,} surplus). "
        )
        if uncovered_needs:
            summary += f"Could not accommodate: {', '.join(uncovered_needs)} within this budget tier."
    else:
        summary = f"No complete valid bundle could fit within ₹{monthly_budget:,}/mo."

    total_setup = sum(it.get("one_time_setup", 0) * it.get("quantity", 1) for it in selected_items)
    return BudgetFitResult(
        selected_items=selected_items,
        total_monthly_cost=best_cost,
        total_setup_cost=total_setup,
        monthly_budget=monthly_budget,
        remaining_budget=monthly_budget - best_cost,
        dropped_items=dropped_explanations,
        covered_needs=list(covered_needs),
        uncovered_needs=uncovered_needs,
        explanation=summary,
    )
