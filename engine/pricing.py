"""Pricing and quote calculation engine for Accel Business Udyam Digital."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd

from kyc.registry import load_catalogue


@dataclass
class QuoteLineItem:
    """Individual line item in a customer quote."""
    product_id: str
    product_name: str
    category: str
    unit: str
    quantity: int
    price_min: int              # Catalogue min monthly price
    price_max: int              # Catalogue max monthly price
    unit_price: int             # Starting price (price_min)
    unit_setup_fee: int         # Catalogue one-time setup fee
    min_contract_months: int
    typical_install_days: int
    monthly_amount: int         # unit_price * quantity
    one_time_amount: int        # unit_setup_fee * quantity
    assumption: str = ""
    reason: str = ""


@dataclass
class Quote:
    """Full customer quote summary."""
    items: List[QuoteLineItem]
    contract_months: int
    min_allowed_contract_months: int
    monthly_subtotal: int
    one_time_subtotal: int
    first_month_payable: int
    total_contract_value: int
    max_install_days: int
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert quote to dictionary for UI and persistence."""
        return {
            "items": [
                {
                    "product_id": it.product_id,
                    "product_name": it.product_name,
                    "category": it.category,
                    "unit": it.unit,
                    "quantity": it.quantity,
                    "price_min": it.price_min,
                    "price_max": it.price_max,
                    "unit_price": it.unit_price,
                    "unit_setup_fee": it.unit_setup_fee,
                    "min_contract_months": it.min_contract_months,
                    "typical_install_days": it.typical_install_days,
                    "monthly_amount": it.monthly_amount,
                    "one_time_amount": it.one_time_amount,
                    "assumption": it.assumption,
                    "reason": it.reason,
                }
                for it in self.items
            ],
            "contract_months": self.contract_months,
            "min_allowed_contract_months": self.min_allowed_contract_months,
            "monthly_subtotal": self.monthly_subtotal,
            "one_time_subtotal": self.one_time_subtotal,
            "first_month_payable": self.first_month_payable,
            "total_contract_value": self.total_contract_value,
            "max_install_days": self.max_install_days,
            "warnings": self.warnings,
        }


def calculate_quote(
    selected_items: List[Dict[str, Any]],
    contract_months: Optional[int] = None,
) -> Quote:
    """
    Compute official quote strictly using product_catalogue.csv.
    selected_items: list of dicts with 'product_id' and optional 'quantity', 'assumption', 'reason'.
    """
    df = load_catalogue().set_index("product_id")
    line_items: List[QuoteLineItem] = []
    
    warnings: List[str] = []
    min_contract_req = 1
    max_days = 0
    
    for item in selected_items:
        pid = str(item["product_id"]).strip()
        if pid not in df.index:
            warnings.append(f"Product {pid} not found in official catalogue - ignored")
            continue
            
        row = df.loc[pid]
        qty = max(1, int(item.get("quantity", 1)))
        
        p_min = int(row["price_min_inr_per_month"])
        p_max = int(row["price_max_inr_per_month"])
        setup = int(row["one_time_setup_inr"])
        min_cm = int(row["min_contract_months"])
        install_days = int(row["typical_install_days"])
        
        if min_cm > min_contract_req:
            min_contract_req = min_cm
        if install_days > max_days:
            max_days = install_days
            
        line_items.append(
            QuoteLineItem(
                product_id=pid,
                product_name=str(row["product_name"]),
                category=str(row["category"]),
                unit=str(row["unit"]),
                quantity=qty,
                price_min=p_min,
                price_max=p_max,
                unit_price=p_min,  # Quoted starting price strictly from catalogue
                unit_setup_fee=setup,
                min_contract_months=min_cm,
                typical_install_days=install_days,
                monthly_amount=p_min * qty,
                one_time_amount=setup * qty,
                assumption=str(item.get("assumption", "")),
                reason=str(item.get("reason", "")),
            )
        )
    
    # Contract months must be at least the highest min_contract_months
    effective_cm = contract_months if contract_months is not None else min_contract_req
    if effective_cm < min_contract_req:
        warnings.append(
            f"Contract duration adjusted to {min_contract_req} months to satisfy product minimum requirements."
        )
        effective_cm = min_contract_req
        
    monthly_subtotal = sum(it.monthly_amount for it in line_items)
    one_time_subtotal = sum(it.one_time_amount for it in line_items)
    first_month_payable = monthly_subtotal + one_time_subtotal
    total_contract_value = (monthly_subtotal * effective_cm) + one_time_subtotal
    
    return Quote(
        items=line_items,
        contract_months=effective_cm,
        min_allowed_contract_months=min_contract_req,
        monthly_subtotal=monthly_subtotal,
        one_time_subtotal=one_time_subtotal,
        first_month_payable=first_month_payable,
        total_contract_value=total_contract_value,
        max_install_days=max_days,
        warnings=warnings,
    )


def validate_quote_dependencies(product_ids: List[str]) -> Tuple[bool, List[str]]:
    """
    Given the current list of product IDs in the quote, check if any product is missing
    its required parent dependency (requires_one_of).
    Returns:
      - is_valid: True if all dependencies are satisfied, False otherwise
      - issues: List of human-readable warnings explaining which products are missing a parent
    """
    df = load_catalogue().set_index("product_id")
    pids_set = set(product_ids)
    issues: List[str] = []
    
    for pid in product_ids:
        if pid not in df.index:
            continue
        req_str = str(df.loc[pid]["requires_one_of"]) if pd.notna(df.loc[pid]["requires_one_of"]) else ""
        if not req_str:
            continue
        candidates = [c.strip() for c in req_str.split("|") if c.strip()]
        if not any(c in pids_set for c in candidates):
            prod_name = df.loc[pid]["product_name"]
            issues.append(
                f"{prod_name} ({pid}) requires at least one base connectivity service ({' / '.join(candidates)})"
            )
            
    return len(issues) == 0, issues


def remove_product_with_dependency_check(
    selected_items: List[Dict[str, Any]],
    product_id_to_remove: str,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Remove product from bundle and warn/remove about broken dependent products.
    Returns:
      - updated_items: list of remaining items (with broken dependents pruned)
      - warnings: explanations of what was removed
    """
    df = load_catalogue().set_index("product_id")
    remaining_items = [it for it in selected_items if it["product_id"] != product_id_to_remove]
    remaining_pids = {it["product_id"] for it in remaining_items}
    
    warnings: List[str] = []
    removed_name = df.loc[product_id_to_remove]["product_name"] if product_id_to_remove in df.index else product_id_to_remove
    warnings.append(f"Removed {removed_name} ({product_id_to_remove}) from quote.")
    
    # Check if any remaining item now has an unsatisfied dependency
    cascade_removals = []
    for it in remaining_items:
        pid = it["product_id"]
        if pid not in df.index:
            continue
        req_str = str(df.loc[pid]["requires_one_of"]) if pd.notna(df.loc[pid]["requires_one_of"]) else ""
        if not req_str:
            continue
        candidates = [c.strip() for c in req_str.split("|") if c.strip()]
        if not any(c in remaining_pids for c in candidates):
            # Broken dependency
            dep_name = df.loc[pid]["product_name"]
            warnings.append(
                f"Also removed {dep_name} ({pid}) because it requires a broadband link ({' / '.join(candidates)})"
            )
            cascade_removals.append(pid)
            
    if cascade_removals:
        remaining_items = [it for it in remaining_items if it["product_id"] not in cascade_removals]
        
    return remaining_items, warnings
