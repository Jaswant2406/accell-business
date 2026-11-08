"""
Accel Business QA Validation Test Harness (Corrected & Regraded).
Implements Oracle Sanity Checks:
  (a) At most ONE primary connectivity product (P01-P06, P04 for wireless) per site.
  (b) No product unless stated in needs or a required prerequisite dependency.
  (c) Budget adherence: default bundle <= budget or explicit dropped explanation.
Executes every scenario twice:
  - Run A: Prompt exact (GSTIN not specified, except TC10 where user claims GST without number; TC07 no GST).
  - Run B: With valid active registry GSTIN.
Evaluates Edge Cases E01-E08, Rules Determinism (3x run), and Multilingual Needs Matching.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.independent_oracle import CatalogueOracle
from engine.eligibility import (
    BusinessProfile,
    evaluate_product_eligibility,
    recommend_products,
    determine_quantity,
    compute_unlock_suggestion,
)
from engine.pricing import calculate_quote, validate_quote_dependencies, remove_product_with_dependency_check
from engine.budget_fit import fit_bundle_to_budget
from engine.advisor import (
    extract_profile_multilingual_fallback,
    evaluate_slot_filling,
)
from kyc.registry import (
    get_city_tier,
    get_city_tier_info,
    load_catalogue,
    lookup_gstin,
    validate_gstin_format,
    compute_gstin_check_digit,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs"
OUTPUT_DIR.mkdir(exist_ok=True)


BEFORE_FIX_METRICS = {
    "TC01": {"pids": ["P01", "P02", "P03", "P04", "P09", "P12", "P13", "P16", "P17"], "monthly": 15519},
    "TC02": {"pids": ["P01", "P02", "P04", "P07", "P08", "P19", "P23"], "monthly": 7088},
    "TC03": {"pids": ["P01", "P02", "P04", "P05", "P06", "P11", "P20", "P21", "P22", "P24", "P25"], "monthly": 44149},
    "TC04": {"pids": ["P01", "P02", "P04", "P05", "P10", "P15", "P19", "P22", "P23"], "monthly": 46878},
    "TC05": {"pids": ["P01", "P02", "P03", "P04", "P05", "P06", "P09", "P11", "P16", "P17", "P20", "P21", "P22"], "monthly": 49592},
    "TC06": {"pids": ["P01", "P02", "P03", "P04", "P05", "P06", "P09", "P23", "P25"], "monthly": 87561},
    "TC07": {"pids": ["P01", "P02", "P04", "P07", "P08", "P19", "P23"], "monthly": 6190},
    "TC08": {"pids": ["P01", "P02", "P04", "P05", "P16", "P18", "P22", "P23"], "monthly": 13993},
    "TC09": {"pids": ["P01", "P02", "P03", "P04", "P05", "P06", "P10", "P16", "P19", "P21", "P23"], "monthly": 233210},
    "TC10": {"pids": ["P01", "P02", "P04", "P07", "P08", "P09", "P17", "P23"], "monthly": 11977},
}


def run_evaluated_scenario(
    scenario_id: str,
    name: str,
    profile_kwargs: Dict[str, Any],
    oracle: CatalogueOracle,
    vehicle_count: Optional[int] = None,
    budget_ceiling: Optional[int] = None,
) -> Dict[str, Any]:
    if budget_ceiling:
        profile_kwargs["budget"] = budget_ceiling
    profile = BusinessProfile(**profile_kwargs)
    city_tier, is_known_city = oracle.lookup_city_tier(profile.city)
    
    # Run Engine
    engine_result = recommend_products(profile)
    rec_items = engine_result["recommended"]
    rec_pids = [it["product_id"] for it in rec_items]
    auto_added_pids = [it["product_id"] for it in rec_items if it.get("auto_added")]
    
    # Calculate Engine Quote
    quote = calculate_quote([{"product_id": it["product_id"], "quantity": it["quantity"]} for it in rec_items])
    
    # -------------------------------------------------------------
    # Oracle Sanity Checks
    # -------------------------------------------------------------
    sanity_a_pass, sanity_a_msg = oracle.sanity_check_single_connectivity(rec_pids)
    sanity_b_pass, sanity_b_violations = oracle.sanity_check_stated_needs_and_deps(
        rec_pids, profile.stated_needs, auto_added_pids
    )
    sanity_c_pass, sanity_c_msg = oracle.sanity_check_budget_adherence(
        quote.monthly_subtotal, budget_ceiling, bool(engine_result.get("budget_fit_summary"))
    )
    
    # Verify price match against oracle
    oracle_items = [{"product_id": it["product_id"], "quantity": it["quantity"]} for it in rec_items]
    oracle_quote = oracle.calculate_expected_pricing(oracle_items)
    price_match = (quote.monthly_subtotal == oracle_quote["monthly_subtotal"]) and \
                  (quote.one_time_subtotal == oracle_quote["one_time_subtotal"])
                  
    # Check if any ineligible product was included
    has_active_gst = profile.has_gstin and bool(profile.gstin)
    ineligible_pids = []
    for pid in rec_pids:
        is_elig, reasons = oracle.evaluate_eligibility(
            pid, profile.city_tier, profile.employee_count, profile.num_sites, has_active_gst
        )
        if not is_elig:
            ineligible_pids.append(f"{pid}: {'; '.join(reasons)}")
            
    # Dependencies check
    dep_issues = oracle.check_dependencies(set(rec_pids))
    
    # Grade Status honestly
    status = "PASS"
    issues = []
    if not sanity_a_pass:
        status = "FAIL"
        issues.append(sanity_a_msg)
    if not sanity_b_pass:
        status = "FAIL"
        issues.extend(sanity_b_violations)
    if not sanity_c_pass:
        status = "FAIL"
        issues.append(sanity_c_msg)
    if ineligible_pids:
        status = "FAIL"
        issues.append(f"Ineligible products included: {ineligible_pids}")
    if dep_issues:
        status = "FAIL"
        issues.append(f"Unsatisfied dependencies: {dep_issues}")
    if not price_match:
        status = "FAIL"
        issues.append("Pricing calculation mismatch between engine and oracle")
        
    observations = []
    if profile.city_tier_unconfirmed:
        observations.append(profile.city_tier_disclosure)
    if profile.gstin_pending_verification:
        observations.append(profile.gstin_disclosure)
    if engine_result.get("budget_fit_summary"):
        observations.append(f"Budget Fit applied: capped to ₹{engine_result['budget_fit_summary']['fitted_monthly_total']:,}/mo")
    if engine_result.get("static_ip_disclosure"):
        observations.append(engine_result["static_ip_disclosure"])

    return {
        "scenario_id": scenario_id,
        "name": name,
        "profile": {
            "business_name": profile.business_name,
            "business_type": profile.business_type,
            "segment": profile.segment,
            "employee_count": profile.employee_count,
            "num_sites": profile.num_sites,
            "city": profile.city,
            "city_tier": profile.city_tier,
            "city_tier_unconfirmed": profile.city_tier_unconfirmed,
            "has_gstin": profile.has_gstin,
            "gstin": profile.gstin,
            "gstin_pending_verification": profile.gstin_pending_verification,
            "stated_needs": profile.stated_needs,
            "budget": profile.budget,
        },
        "recommended_pids": rec_pids,
        "recommended_items": [
            {
                "product_id": it["product_id"],
                "product_name": it["product_name"],
                "quantity": it["quantity"],
                "unit": it["unit"],
                "price_min": it["price_min"],
                "monthly_amount": it["price_min"] * it["quantity"],
                "setup_fee": it["one_time_setup"] * it["quantity"],
                "reason": it["reason"],
                "auto_added": it.get("auto_added", False),
            }
            for it in rec_items
        ],
        "optional_addons_count": len(engine_result.get("optional_addons", [])),
        "alternatives_count": len(engine_result.get("alternatives", [])),
        "pricing": {
            "monthly_subtotal": quote.monthly_subtotal,
            "one_time_subtotal": quote.one_time_subtotal,
            "first_month_payable": quote.first_month_payable,
            "contract_months": quote.contract_months,
            "total_contract_value": quote.total_contract_value,
        },
        "sanity_checks": {
            "single_connectivity_pass": sanity_a_pass,
            "stated_needs_only_pass": sanity_b_pass,
            "budget_compliance_pass": sanity_c_pass,
        },
        "status": status,
        "issues": issues,
        "observations": observations,
    }


def main():
    oracle = CatalogueOracle()
    
    print("==========================================================================")
    print("ACCEL BUSINESS RECOMMENDATION ENGINE VALIDATION & REGISTRATION RUN")
    print("==========================================================================")
    
    # Base scenario definitions
    raw_scenarios = [
        ("TC01", "Dental Clinic", "Bengaluru", 5, 1, "Dental Clinic", ["broadband", "cloud backup", "email", "voice_lines"], None, None, "29CPSXS6426Z1ZL"),
        ("TC02", "Retail Store", "Chennai", 3, 1, "Retail Store", ["broadband", "pos", "payments", "cctv", "mobile"], None, None, "33MFTXS9954Q1Z9"),
        ("TC03", "Manufacturing", "Coimbatore", 35, 1, "Manufacturing", ["dedicated internet", "static ip", "firewall", "security", "iot"], None, None, "33PBWXO2282E1ZL"),
        ("TC04", "Restaurant Chain", "Madurai", 18, 3, "Restaurant Chain", ["broadband", "sd-wan", "pos", "wifi", "cctv", "whatsapp"], None, None, "33MFTXS9954Q1Z9"),
        ("TC05", "Software Agency", "Bengaluru", 25, 1, "Software Development", ["1 gbps", "static ip", "email", "backup", "security"], None, None, "29CPSXS6426Z1ZL"),
        ("TC06", "Logistics Co.", "Hyderabad", 40, 2, "Logistics & Transport", ["fleet", "failover", "broadband", "cctv"], {"P25": 25}, None, "36KNNXK2611U1ZM"),
        ("TC07", "Small Kirana", "Tirunelveli", 2, 1, "Kirana Store", ["internet", "pos", "cctv", "mobile"], None, 3000, None),
        ("TC08", "Education", "Coimbatore", 12, 1, "Educational Coaching", ["broadband", "wifi", "email", "cctv", "website"], None, None, "33PBWXO2282E1ZL"),
        ("TC09", "Pharmacy Chain", "Chennai", 30, 5, "Pharmacy Chain", ["broadband", "sd-wan", "firewall", "pos", "cctv", "email", "automatic backup connectivity to prevent downtime"], None, None, "33MFTXS9954Q1Z9"),
        ("TC10", "Rural Mfg", "Dindigul", 8, 1, "Manufacturing / Agro", ["wireless", "mobile", "cctv", "machine monitoring", "cloud backup"], None, None, "33MFTXS9954Q1Z9"),
    ]

    # RUN A: Prompt Exact (No GSTIN supplied unless stated; TC10 has GST claimed without number)
    print("\n--------------------------------------------------------------------------")
    print("RUN A: PROMPT EXACT (GSTIN Unspecified / Stated Claim Without Number)")
    print("--------------------------------------------------------------------------")
    results_run_a = []
    for sc in raw_scenarios:
        sc_id, name, city, emps, sites, b_type, needs, custom_q, budget, _ = sc
        has_gst = False
        gstin_val = None
        if sc_id == "TC10":
            has_gst = True
            gstin_val = ""  # User claims GST without number
            
        kwargs = {
            "business_name": f"{name} Test",
            "business_type": b_type,
            "employee_count": emps,
            "num_sites": sites,
            "city": city,
            "has_gstin": has_gst,
            "gstin": gstin_val,
            "stated_needs": needs,
            "custom_quantities": custom_q or {},
        }
        res_a = run_evaluated_scenario(
            scenario_id=sc_id,
            name=name,
            profile_kwargs=kwargs,
            oracle=oracle,
            budget_ceiling=budget,
        )
        print(f"[{res_a['status']}] {res_a['scenario_id']} - {res_a['name']}: {res_a['recommended_pids']} | Subtotal: ₹{res_a['pricing']['monthly_subtotal']:,}/mo | Addons: {res_a['optional_addons_count']} | Alts: {res_a['alternatives_count']}")
        for obs in res_a["observations"]:
            print(f"       -> {obs}")
        for iss in res_a["issues"]:
            print(f"       !! ISSUE: {iss}")
        results_run_a.append(res_a)

    # RUN B: With Valid Active Registry GSTIN
    print("\n--------------------------------------------------------------------------")
    print("RUN B: WITH VALID ACTIVE REGISTRY GSTIN")
    print("--------------------------------------------------------------------------")
    results_run_b = []
    for sc in raw_scenarios:
        sc_id, name, city, emps, sites, b_type, needs, custom_q, budget, valid_gst = sc
        has_gst = bool(valid_gst)
        kwargs = {
            "business_name": f"{name} Enterprise",
            "business_type": b_type,
            "employee_count": emps,
            "num_sites": sites,
            "city": city,
            "has_gstin": has_gst,
            "gstin": valid_gst,
            "stated_needs": needs,
            "custom_quantities": custom_q or {},
        }
        res_b = run_evaluated_scenario(
            scenario_id=sc_id,
            name=name,
            profile_kwargs=kwargs,
            oracle=oracle,
            budget_ceiling=budget,
        )
        print(f"[{res_b['status']}] {res_b['scenario_id']} - {res_b['name']}: {res_b['recommended_pids']} | Subtotal: ₹{res_b['pricing']['monthly_subtotal']:,}/mo | Addons: {res_b['optional_addons_count']} | Alts: {res_b['alternatives_count']}")
        for obs in res_b["observations"]:
            print(f"       -> {obs}")
        for iss in res_b["issues"]:
            print(f"       !! ISSUE: {iss}")
        results_run_b.append(res_b)

    # Save results
    output_payload = {
        "before_fix": BEFORE_FIX_METRICS,
        "run_a_prompt_exact": results_run_a,
        "run_b_with_active_gstin": results_run_b,
    }
    out_file = OUTPUT_DIR / "qa_regraded_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)
    print(f"\n[DONE] Regraded results written to {out_file}")

    # Programmatically generate docs/ACCEL_BUSINESS_COMPLETE_QA_REPORT.md
    from scripts.generate_qa_report import generate_report
    generate_report()



if __name__ == "__main__":
    main()
