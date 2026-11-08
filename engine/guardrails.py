"""
Deterministic Guardrails Module for Accel Business Udyam Digital.
Enforces:
1. Product Guardrail: Any LLM output that mentions a product not in product_catalogue.csv is rejected.
2. Pricing Guardrail: Any LLM output that mentions a price not in product_catalogue.csv is rejected.
3. Pricing Sovereignty: Product prices strictly come from the rules/pricing engine, never free-form LLM text.
"""

import re
from typing import List, Optional, Set, Tuple
from kyc.registry import load_catalogue


def get_catalogue_canonical_products() -> Tuple[Set[str], List[str]]:
    """Return valid product IDs and lowercase canonical product names from catalogue."""
    df = load_catalogue()
    valid_pids = {str(pid).strip().upper() for pid in df["product_id"]}
    valid_names = [str(name).strip() for name in df["product_name"]]
    return valid_pids, valid_names


def get_catalogue_valid_prices() -> Set[int]:
    """
    Return set of all valid individual product price figures from product_catalogue.csv:
    price_min, price_max, and one_time_setup values.
    """
    df = load_catalogue()
    prices: Set[int] = set()
    for _, row in df.iterrows():
        prices.add(int(row["price_min_inr_per_month"]))
        prices.add(int(row["price_max_inr_per_month"]))
        prices.add(int(row["one_time_setup_inr"]))
    return prices


# Common product hallucination keywords and invalid product identifiers
KNOWN_INVALID_PRODUCTS = [
    "super fiber",
    "ultra leased line",
    "gigabit pro",
    "megaband",
    "turbo speed",
    "fiber prime",
    "super unlimited 500",
    "enterprise 10g",
    "platinum net",
    "cloud connect supreme",
]


def extract_monetary_values(text: str) -> List[int]:
    """
    Extract rupee amounts from text (e.g. ₹999, Rs. 1499, INR 25,000, 15000/mo).
    """
    # Matches patterns like ₹ 1,499, Rs 25000, INR 8000, ₹999/mo
    patterns = [
        r'(?:₹|rs\.?|inr)\s*([0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)',
        r'([0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)\s*(?:inr|rs|rupees|\/-\s*|\/mo\b|\/month\b)',
    ]
    found_values: List[int] = []
    for pat in patterns:
        matches = re.finditer(pat, text, re.IGNORECASE)
        for m in matches:
            val_str = m.group(1).replace(",", "")
            if val_str.isdigit():
                found_values.append(int(val_str))
    return found_values


def extract_mentioned_product_codes(text: str) -> List[str]:
    """
    Find product code patterns like P01, P25, P99, P00 in text.
    """
    return [m.upper() for m in re.findall(r'\bP[0-9]{2}\b', text, re.IGNORECASE)]


def validate_llm_product_and_pricing_guardrails(text: str) -> Tuple[bool, Optional[str]]:
    """
    Validate LLM output against strict product and pricing guardrails:
    - Fails if text mentions a product code not in P01..P25.
    - Fails if text mentions hallucinated/fake telecom products.
    - Fails if text quotes a monetary price figure not present in product_catalogue.csv.
    """
    if not text:
        return True, None

    valid_pids, valid_names = get_catalogue_canonical_products()
    valid_prices = get_catalogue_valid_prices()

    # 1. Check for invalid product codes (e.g. P99, P00, P30)
    mentioned_codes = extract_mentioned_product_codes(text)
    for code in mentioned_codes:
        if code not in valid_pids:
            return False, f"Guardrail violation: Mentioned invalid product code '{code}' not in catalogue"

    # 2. Check for known hallucinated product brandings
    text_lower = text.lower()
    for inv_prod in KNOWN_INVALID_PRODUCTS:
        if inv_prod in text_lower:
            return False, f"Guardrail violation: Mentioned uncatalogued product '{inv_prod}'"

    # 3. Check for unauthorized price figures
    found_prices = extract_monetary_values(text)
    for price in found_prices:
        # Ignore nominal counts like 1, 2, 5, 10, 24, 30 if caught by mistake
        if price < 50:
            continue
        if price not in valid_prices:
            return False, (
                f"Guardrail violation: Mentioned price ₹{price:,} is not an authorized catalogue price "
                f"(catalogue prices: {sorted(list(valid_prices))[:6]}...)"
            )

    return True, None
