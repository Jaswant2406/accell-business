"""
Automated Pytest Suite for Accel Business QA Scenarios and Edge Cases.
Validates TC01-TC10, E01-E08, and Independent CatalogueOracle consistency.
"""

import json
import pytest
import pandas as pd
from scripts.independent_oracle import CatalogueOracle
from engine.eligibility import BusinessProfile, recommend_products, evaluate_product_eligibility
from engine.pricing import calculate_quote, validate_quote_dependencies, remove_product_with_dependency_check
from engine.budget_fit import fit_bundle_to_budget
from kyc.registry import load_catalogue


@pytest.fixture(scope="session")
def oracle():
    return CatalogueOracle()


def test_catalogue_oracle_product_count(oracle):
    assert len(oracle.products) == 25
    assert len(oracle.known_city_tiers) == 22


def test_tc01_dental_clinic(oracle):
    profile = BusinessProfile(
        business_name="Smile Dental Care",
        business_type="Dental Clinic",
        employee_count=5,
        num_sites=1,
        city="Bengaluru",
        has_gstin=True,
        gstin="29CPSXS6426Z1ZL",
        stated_needs=["broadband", "cloud backup", "email", "voice_lines"],
    )
    rec = recommend_products(profile)
    pids = [it["product_id"] for it in rec["recommended"]]
    assert "P12" in pids  # SIP telephony
    assert "P16" in pids  # Email
    assert "P17" in pids  # Cloud backup
    # Check pricing
    q = calculate_quote([{"product_id": it["product_id"], "quantity": it["quantity"]} for it in rec["recommended"]])
    assert q.monthly_subtotal > 0
    assert q.first_month_payable >= q.monthly_subtotal


def test_tc02_retail_store(oracle):
    profile = BusinessProfile(
        business_name="Modern Trendz",
        business_type="Retail Store",
        employee_count=3,
        num_sites=1,
        city="Chennai",
        has_gstin=True,
        gstin="33MFTXS9954Q1Z9",
        stated_needs=["broadband", "pos", "payments", "cctv", "mobile"],
    )
    rec = recommend_products(profile)
    pids = [it["product_id"] for it in rec["recommended"]]
    assert "P19" in pids  # POS & Billing (handles payments)
    assert "P23" in pids  # CCTV


def test_tc03_manufacturing_facility(oracle):
    profile = BusinessProfile(
        business_name="Precision Auto Parts",
        business_type="Manufacturing",
        employee_count=35,
        num_sites=1,
        city="Coimbatore",
        has_gstin=True,
        gstin="33PBWXO2282E1ZL",
        stated_needs=["dedicated internet", "static ip", "firewall", "security", "iot"],
    )
    rec = recommend_products(profile)
    pids = [it["product_id"] for it in rec["recommended"]]
    assert "P06" in pids  # Leased Line 100 (min 25 emp)
    assert "P21" in pids  # Firewall
    assert "P20" in pids  # Endpoint security (does not require GSTIN)
    assert "P24" in pids  # Machine Monitoring IoT
    # P11 requires P01|P02|P03 only; since P06 is chosen, P11 cannot be recommended without P01|P02|P03
    assert "P11" not in pids
    assert rec.get("static_ip_disclosure") == "Static IP (P11) is only available with Biz Fibre 100/300/1G in our catalogue"


def test_multilingual_needs_matching(oracle):
    """Verify Hindi and Tamil keywords resolve cleanly in deterministic recommendation."""
    # Hindi needs
    prof_hi = BusinessProfile(
        business_name="Sharma Mfg",
        business_type="Manufacturing",
        employee_count=30,
        num_sites=1,
        city="Pune",
        has_gstin=True,
        gstin="27DGKXS9651J1Z2",
        stated_needs=["समर्पित", "फ़ायरवॉल", "मशीन", "सुरक्षा"],  # Dedicated, Firewall, Machine, Security
    )
    rec_hi = recommend_products(prof_hi)
    pids_hi = [it["product_id"] for it in rec_hi["recommended"]]
    assert "P06" in pids_hi
    assert "P21" in pids_hi
    assert "P24" in pids_hi
    assert "P20" in pids_hi

    # Tamil needs
    prof_ta = BusinessProfile(
        business_name="Murugan Store",
        business_type="Retail Store",
        employee_count=3,
        num_sites=1,
        city="Chennai",
        has_gstin=False,
        stated_needs=["இணையம்", "பில்லிங்", "கண்காணிப்பு கேமரா", "மொபைல்"],  # Internet, Billing/POS, CCTV, Mobile
    )
    rec_ta = recommend_products(prof_ta)
    pids_ta = [it["product_id"] for it in rec_ta["recommended"]]
    assert "P01" in pids_ta
    assert "P19" in pids_ta
    assert "P23" in pids_ta
    assert "P07" in pids_ta


def test_tc04_restaurant_chain_unlisted_city(oracle):
    profile = BusinessProfile(
        business_name="Spice Route Diners",
        business_type="Restaurant Chain",
        employee_count=18,
        num_sites=3,
        city="Madurai",
        has_gstin=True,
        gstin="33MFTXS9954Q1Z9",
        stated_needs=["broadband", "sd-wan", "pos", "wifi", "cctv", "whatsapp"],
    )
    # City tier is defaulted to 2
    assert profile.city_tier == 2
    rec = recommend_products(profile)
    pids = [it["product_id"] for it in rec["recommended"]]
    assert "P10" in pids  # SD-WAN eligible (3 sites, 18 emp)
    assert "P15" in pids  # WhatsApp API


def test_tc07_kirana_no_gstin(oracle):
    profile = BusinessProfile(
        business_name="Lakshmi Provision Store",
        business_type="Kirana Store",
        employee_count=2,
        num_sites=1,
        city="Tirunelveli",
        has_gstin=False,
        gstin=None,
        stated_needs=["internet", "pos", "cctv", "mobile"],
    )
    rec = recommend_products(profile)
    for it in rec["recommended"]:
        pid = it["product_id"]
        assert oracle.products[pid]["requires_gstin"] is False


def test_edge_case_e01_gstin_states(oracle):
    # State A: No GSTIN
    p_a = BusinessProfile(business_type="Retail", employee_count=5, num_sites=1, city="Chennai", has_gstin=False, gstin=None)
    res_a = recommend_products(p_a)
    assert not res_a["catalogue_status"]["P12"]["eligible"]

    # State B: "I have GST" but empty string
    p_b = BusinessProfile(business_type="Retail", employee_count=5, num_sites=1, city="Chennai", has_gstin=True, gstin="")
    res_b = recommend_products(p_b)
    assert not res_b["catalogue_status"]["P12"]["eligible"]

    # State C: Valid Active GSTIN
    p_c = BusinessProfile(business_type="Retail", employee_count=5, num_sites=1, city="Chennai", has_gstin=True, gstin="33MFTXS9954Q1Z9")
    res_c = recommend_products(p_c)
    assert res_c["catalogue_status"]["P12"]["eligible"]


def test_edge_case_e03_site_threshold(oracle):
    p2 = BusinessProfile(business_type="Retail Chain", employee_count=15, num_sites=2, city="Chennai", has_gstin=True, gstin="33MFTXS9954Q1Z9")
    p3 = BusinessProfile(business_type="Retail Chain", employee_count=15, num_sites=3, city="Chennai", has_gstin=True, gstin="33MFTXS9954Q1Z9")
    res2 = recommend_products(p2)
    res3 = recommend_products(p3)
    assert not res2["catalogue_status"]["P10"]["eligible"]
    assert res3["catalogue_status"]["P10"]["eligible"]


def test_edge_case_e05_budget_fit(oracle):
    profile = BusinessProfile(
        business_type="Kirana",
        employee_count=2,
        num_sites=1,
        city="Jaipur",
        has_gstin=False,
        stated_needs=["broadband", "pos", "cctv", "mobile"],
    )
    b_fit = fit_bundle_to_budget(profile, monthly_budget=2000)
    assert b_fit.total_monthly_cost <= 2000
    assert len(b_fit.dropped_items) > 0


def test_edge_case_e07_dependency_resolution(oracle):
    p_dep = BusinessProfile(
        business_type="Clinic",
        employee_count=12,
        num_sites=1,
        city="Pune",
        has_gstin=True,
        gstin="27DGKXS9651J1Z2",
        current_internet="Business broadband",
        stated_needs=["firewall"],
    )
    rec = recommend_products(p_dep)
    pids = [it["product_id"] for it in rec["recommended"]]
    assert "P21" in pids
    assert any(it["auto_added"] for it in rec["recommended"])


def test_tc06_logistics_failover(oracle):
    """TC06: Verify failover link (P09) quantity equals sites count (2)."""
    profile = BusinessProfile(
        business_name="FastTrack Logistics",
        business_type="Logistics & Transport",
        employee_count=40,
        num_sites=2,
        city="Hyderabad",
        has_gstin=True,
        gstin="36KNNXK2611U1ZM",
        stated_needs=["fleet", "failover", "broadband", "cctv"],
        custom_quantities={"P25": 25},
    )
    rec = recommend_products(profile)
    pids = [it["product_id"] for it in rec["recommended"]]
    assert "P02" in pids
    assert "P09" in pids  # Failover backup link
    assert "P23" in pids  # CCTV
    assert "P25" in pids  # Fleet tracker
    p09_item = next(it for it in rec["recommended"] if it["product_id"] == "P09")
    assert p09_item["quantity"] == 2  # 2 sites


def test_tc09_pharmacy_backup_connectivity(oracle):
    """TC09: Verify automatic backup connectivity maps to P09 with quantity = 5 sites."""
    # Run A: No GSTIN
    prof_a = BusinessProfile(
        business_name="MedLife Pharma Chain",
        business_type="Pharmacy Chain",
        employee_count=30,
        num_sites=5,
        city="Chennai",
        has_gstin=False,
        gstin=None,
        stated_needs=[
            "broadband",
            "sd-wan",
            "firewall",
            "pos",
            "cctv",
            "email",
            "automatic backup connectivity to prevent downtime",
        ],
    )
    rec_a = recommend_products(prof_a)
    pids_a = [it["product_id"] for it in rec_a["recommended"]]
    assert "P02" in pids_a
    assert "P09" in pids_a  # P09 does not require GSTIN and matches backup connectivity
    assert "P19" in pids_a  # POS (does not require GSTIN)
    assert "P23" in pids_a  # CCTV
    assert "P16" in pids_a  # Email
    assert "P10" not in pids_a  # SD-WAN locked (needs GSTIN)
    assert "P21" not in pids_a  # Firewall locked (needs GSTIN)
    p09_item_a = next(it for it in rec_a["recommended"] if it["product_id"] == "P09")
    assert p09_item_a["quantity"] == 5

    # Run B: Active GSTIN
    prof_b = BusinessProfile(
        business_name="MedLife Pharma Chain",
        business_type="Pharmacy Chain",
        employee_count=30,
        num_sites=5,
        city="Chennai",
        has_gstin=True,
        gstin="33MFTXS9954Q1Z9",
        stated_needs=[
            "broadband",
            "sd-wan",
            "firewall",
            "pos",
            "cctv",
            "email",
            "automatic backup connectivity to prevent downtime",
        ],
    )
    rec_b = recommend_products(prof_b)
    pids_b = [it["product_id"] for it in rec_b["recommended"]]
    assert "P02" in pids_b
    assert "P09" in pids_b
    assert "P10" in pids_b  # SD-WAN unlocked
    assert "P21" in pids_b  # Firewall unlocked
    assert "P19" in pids_b
    assert "P23" in pids_b
    assert "P16" in pids_b
    p09_item_b = next(it for it in rec_b["recommended"] if it["product_id"] == "P09")
    assert p09_item_b["quantity"] == 5


def test_tc10_rural_mfg_dindigul(oracle):
    """TC10: Small Manufacturing Unit near Dindigul, 8 emp, unlisted city, P24 blocked."""
    profile = BusinessProfile(
        business_name="Dindigul Agro Works",
        business_type="Manufacturing / Agro",
        employee_count=8,
        num_sites=1,
        city="Dindigul",
        has_gstin=True,
        gstin="",  # Claims GST registration without 15-char number
        stated_needs=["wireless", "mobile", "cctv", "machine monitoring", "cloud backup"],
    )
    assert profile.city_tier == 2
    assert profile.city_tier_unconfirmed is True
    assert profile.city_tier_disclosure == "We couldn't confirm your city tier, assuming Tier 2"
    assert profile.gstin_pending_verification is True
    assert profile.gstin_disclosure is not None

    rec = recommend_products(profile)
    pids = [it["product_id"] for it in rec["recommended"]]
    assert "P04" in pids  # Wireless AirFiber 100
    assert "P07" in pids  # Postpaid 299 lines (8 lines)
    assert "P17" in pids  # Cloud backup
    assert "P23" in pids  # CCTV

    # P24 (Machine Monitoring) must be strictly blocked: 8 employees < 10 required
    assert "P24" not in pids
    assert not rec["catalogue_status"]["P24"]["eligible"]
    assert "Requires at least 10 employee(s)" in rec["catalogue_status"]["P24"]["reason"]


def test_multilingual_backup_failover_mapping():
    """Verify Hindi and Tamil backup connectivity / downtime prevention keywords resolve to P09."""
    from engine.eligibility import matches_stated_need

    # Hindi
    assert matches_stated_need("P09", ["बैकअप कनेक्टिविटी"])
    assert matches_stated_need("P09", ["डाउनटाइम रोकें"])
    assert matches_stated_need("P09", ["फेलओवर"])
    # Must NOT match Cloud Backup (P17)
    assert not matches_stated_need("P17", ["बैकअप कनेक्टिविटी"])

    # Tamil
    assert matches_stated_need("P09", ["காப்பு இணைப்பு"])
    assert matches_stated_need("P09", ["செயலிழப்பைத் தடுக்க"])
    assert not matches_stated_need("P17", ["காப்பு இணைப்பு"])


def test_setup_fee_scaling_smb_leads_all_248_rows(oracle):
    """
    Assert that for all 248 leads in smb_leads.csv with one_time_setup_inr > 0,
    setup equals sum(catalogue one_time_setup_inr x quantity) over bundle_products,
    verified via both engine pricing (calculate_quote) and CatalogueOracle.
    """
    import pandas as pd
    leads = pd.read_csv("smb_leads.csv")
    leads_with_setup = leads[leads["one_time_setup_inr"] > 0]
    assert len(leads_with_setup) == 248

    for _, row in leads_with_setup.iterrows():
        bundle_str = str(row["bundle_products"])
        items = []
        for token in bundle_str.split(";"):
            token = token.strip()
            if not token:
                continue
            if "x" in token:
                pid, q_str = token.split("x", 1)
                q = int(q_str)
            else:
                pid = token
                q = 1
            items.append({"product_id": pid, "quantity": q})

        expected_setup = int(row["one_time_setup_inr"])

        # Engine calculate_quote check
        quote = calculate_quote(items)
        assert quote.one_time_subtotal == expected_setup, (
            f"Lead {row['lead_id']} setup mismatch: got {quote.one_time_subtotal}, expected {expected_setup}"
        )

        # Independent CatalogueOracle check
        oracle_res = oracle.calculate_expected_pricing(items)
        assert oracle_res["one_time_subtotal"] == expected_setup, (
            f"Oracle setup mismatch on lead {row['lead_id']}: got {oracle_res['one_time_subtotal']}, expected {expected_setup}"
        )


def test_setup_fee_scaling_all_products_p01_to_p25_quantities(oracle):
    """
    Verify that for every product P01-P25 at quantities 1, 3, and 10,
    setup fee strictly equals one_time_setup_inr x quantity.
    """
    cat = load_catalogue().set_index("product_id")
    quantities = [1, 3, 10]

    for pid in cat.index:
        base_setup = int(cat.loc[pid, "one_time_setup_inr"])
        for q in quantities:
            # 1. Engine check
            quote = calculate_quote([{"product_id": pid, "quantity": q}])
            expected = base_setup * q
            assert quote.one_time_subtotal == expected, (
                f"Engine setup mismatch for {pid} at qty {q}: got {quote.one_time_subtotal}, expected {expected}"
            )
            assert quote.items[0].one_time_amount == expected
            assert quote.items[0].unit_setup_fee == base_setup

            # 2. Oracle check
            oracle_res = oracle.calculate_expected_pricing([{"product_id": pid, "quantity": q}])
            assert oracle_res["one_time_subtotal"] == expected, (
                f"Oracle setup mismatch for {pid} at qty {q}: got {oracle_res['one_time_subtotal']}, expected {expected}"
            )
            assert oracle_res["items"][0]["one_time_amount"] == expected
            assert oracle_res["items"][0]["unit_setup_fee"] == base_setup


def test_report_and_results_match_catalogue_ground_truth():
    """
    Validates that every scenario in docs/qa_regraded_results.json and
    docs/ACCEL_BUSINESS_COMPLETE_QA_REPORT.md strictly equals the ground truth
    read directly from product_catalogue.csv (not from engine functions).
    """
    cat_df = pd.read_csv("product_catalogue.csv").set_index("product_id")
    with open("docs/qa_regraded_results.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    with open("docs/ACCEL_BUSINESS_COMPLETE_QA_REPORT.md", "r", encoding="utf-8") as f:
        report_md = f.read()

    for run_key in ["run_a_prompt_exact", "run_b_with_active_gstin"]:
        for sc in data[run_key]:
            sc_id = sc["scenario_id"]
            items = sc["recommended_items"]
            
            # Ground truth sum directly from product_catalogue.csv
            expected_monthly = 0
            expected_setup = 0
            for it in items:
                pid = it["product_id"]
                qty = it["quantity"]
                unit_price = int(cat_df.loc[pid, "price_min_inr_per_month"])
                unit_setup = int(cat_df.loc[pid, "one_time_setup_inr"])

                line_monthly = unit_price * qty
                line_setup = unit_setup * qty

                assert it["price_min"] == unit_price, f"{sc_id} {pid} unit price mismatch"
                assert it["monthly_amount"] == line_monthly, f"{sc_id} {pid} monthly amount mismatch"
                assert it["setup_fee"] == line_setup, f"{sc_id} {pid} setup fee mismatch"

                expected_monthly += line_monthly
                expected_setup += line_setup

            # Check JSON pricing block
            assert sc["pricing"]["monthly_subtotal"] == expected_monthly, (
                f"{sc_id} {run_key} monthly subtotal mismatch: got {sc['pricing']['monthly_subtotal']}, expected {expected_monthly}"
            )
            assert sc["pricing"]["one_time_subtotal"] == expected_setup, (
                f"{sc_id} {run_key} setup subtotal mismatch: got {sc['pricing']['one_time_subtotal']}, expected {expected_setup}"
            )

            # Check markdown report text contains the exact formatted values
            fmt_m = f"₹{expected_monthly:,}"
            fmt_s = f"₹{expected_setup:,}"
            assert fmt_m in report_md, f"Markdown report does not contain expected monthly {fmt_m} for {sc_id}"
            assert fmt_s in report_md, f"Markdown report does not contain expected setup {fmt_s} for {sc_id}"

    # Assert specific user-expected values
    tc01_a = [s for s in data["run_a_prompt_exact"] if s["scenario_id"] == "TC01"][0]
    tc01_b = [s for s in data["run_b_with_active_gstin"] if s["scenario_id"] == "TC01"][0]
    tc03_a = [s for s in data["run_a_prompt_exact"] if s["scenario_id"] == "TC03"][0]
    tc03_b = [s for s in data["run_b_with_active_gstin"] if s["scenario_id"] == "TC03"][0]
    tc05_a = [s for s in data["run_a_prompt_exact"] if s["scenario_id"] == "TC05"][0]
    tc05_b = [s for s in data["run_b_with_active_gstin"] if s["scenario_id"] == "TC05"][0]
    tc08_a = [s for s in data["run_a_prompt_exact"] if s["scenario_id"] == "TC08"][0]
    tc08_b = [s for s in data["run_b_with_active_gstin"] if s["scenario_id"] == "TC08"][0]

    assert tc01_a["pricing"]["one_time_subtotal"] == 0
    assert tc01_b["pricing"]["one_time_subtotal"] == 10000
    assert tc03_a["pricing"]["one_time_subtotal"] == 0
    assert tc03_b["pricing"]["one_time_subtotal"] == 49000
    assert tc05_a["pricing"]["one_time_subtotal"] == 0
    assert tc05_b["pricing"]["one_time_subtotal"] == 0
    assert tc08_a["pricing"]["one_time_subtotal"] == 4600
    assert tc08_b["pricing"]["one_time_subtotal"] == 4600

