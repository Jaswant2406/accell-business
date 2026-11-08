"""Comprehensive pytest test suite for Accel Business Udyam Digital rules & pricing engine."""

import pytest
import pandas as pd
from engine.eligibility import (
    BusinessProfile,
    evaluate_product_eligibility,
    infer_segment,
    recommend_products,
    validate_bundle_selection,
    determine_quantity,
)
from engine.pricing import (
    calculate_quote,
    remove_product_with_dependency_check,
)
from kyc.registry import (
    get_city_tier,
    load_catalogue,
    lookup_gstin,
    validate_gstin_format,
    compute_gstin_check_digit,
)


@pytest.fixture(scope="session")
def catalogue_df():
    return load_catalogue().set_index("product_id")


# ---------------------------------------------------------------------------
# Test 1: 5-employee clinic
# ---------------------------------------------------------------------------
def test_five_employee_clinic(catalogue_df):
    """
    Test scenario: 5-employee physiotherapy/dental clinic in Kochi (Tier 2).
    Has active GSTIN.
    Expected:
      - Inferred segment is 'prof'
      - Ineligible for P05 (ILL 20: needs 10 emp), P06 (ILL 100: needs 25 emp),
        P10 (SD-WAN: needs 10 emp, 3 sites), P21 (Firewall: needs 10 emp),
        P24 (Machine IoT: needs 10 emp)
      - Eligible for Biz Fibre (P01/P02), Postpaid lines, Telephony (P12), Cloud CCTV (P23)
      - Quantities: 1 per site, 5 per user/line
    """
    # Active GSTIN from registry in Kochi
    valid_gstin = "32TTNXB7384T1ZW"
    profile = BusinessProfile(
        business_name="Balaji Dental Care LLP",
        business_type="Dental clinic",
        employee_count=5,
        num_sites=1,
        city="Kochi",
        has_gstin=True,
        gstin=valid_gstin,
        stated_needs=["broadband", "telephony", "cctv"],
    )

    assert profile.segment == "prof"
    assert profile.city_tier == 2

    rec = recommend_products(profile)
    cat_status = rec["catalogue_status"]

    # Size-gated products must be ineligible with clear reasons
    assert not cat_status["P05"]["eligible"]
    assert "at least 10 employee" in cat_status["P05"]["reason"]

    assert not cat_status["P06"]["eligible"]
    assert "at least 25 employee" in cat_status["P06"]["reason"]

    assert not cat_status["P10"]["eligible"]
    assert "site" in cat_status["P10"]["reason"] or "employee" in cat_status["P10"]["reason"]

    assert not cat_status["P21"]["eligible"]
    assert "at least 10 employee" in cat_status["P21"]["reason"]

    # Recommended bundle should include broadband, telephony, and CCTV
    rec_pids = [item["product_id"] for item in rec["recommended"]]
    assert any(pid in rec_pids for pid in ["P01", "P02"])  # Broadband parent
    assert "P12" in rec_pids  # Cloud Telephony
    assert "P23" in rec_pids  # Cloud CCTV

    # Check quantities and assumptions
    cctv_item = next(it for it in rec["recommended"] if it["product_id"] == "P23")
    assert cctv_item["quantity"] >= 2
    assert "CCTV" in cctv_item["assumption"] or "camera" in cctv_item["assumption"]


# ---------------------------------------------------------------------------
# Test 2: Kirana store with no GSTIN
# ---------------------------------------------------------------------------
def test_kirana_no_gstin(catalogue_df):
    """
    Test scenario: Kirana store, 3 employees, 1 site, no GSTIN.
    Expected:
      - Inferred segment is 'micro'
      - Every product with requires_gstin = 'Y' MUST be ineligible
      - Non-GSTIN products like P01, P04, P07, P19, P22, P23 remain eligible
    """
    profile = BusinessProfile(
        business_name="Lakshmi Grocery Store",
        business_type="Kirana store",
        employee_count=3,
        num_sites=1,
        city="Delhi",
        has_gstin=False,
        gstin=None,
        stated_needs=["broadband", "pos", "cctv"],
    )

    assert profile.segment == "micro"

    rec = recommend_products(profile)
    cat_status = rec["catalogue_status"]

    gst_required_pids = [
        pid for pid, row in catalogue_df.iterrows() if str(row["requires_gstin"]).upper() == "Y"
    ]
    assert len(gst_required_pids) > 0

    for pid in gst_required_pids:
        assert not cat_status[pid]["eligible"], f"{pid} requires GSTIN but was marked eligible!"
        assert "GSTIN" in cat_status[pid]["reason"]

    # P01 and P19 should be eligible
    assert cat_status["P01"]["eligible"]
    assert cat_status["P19"]["eligible"]  # Cloud POS does not require GSTIN

    rec_pids = [item["product_id"] for item in rec["recommended"]]
    assert "P01" in rec_pids or "P04" in rec_pids
    assert "P19" in rec_pids


# ---------------------------------------------------------------------------
# Test 3: 3-site restaurant chain
# ---------------------------------------------------------------------------
def test_three_site_restaurant_chain(catalogue_df):
    """
    Test scenario: 3-site restaurant chain, 18 employees.
    Has active GSTIN.
    Expected:
      - Inferred segment is 'multi'
      - Eligible for P10 (Managed SD-WAN, min_sites=3, min_emp=10)
      - Per-site quantities scale to 3
    """
    valid_gstin = "33MFTXS9954Q1Z9"  # Active in registry
    profile = BusinessProfile(
        business_name="Spice Garden Chain",
        business_type="Restaurant chain",
        employee_count=18,
        num_sites=3,
        city="Chennai",
        has_gstin=True,
        gstin=valid_gstin,
        stated_needs=["broadband", "sdwan", "cctv", "pos"],
    )

    assert profile.segment == "multi"
    assert profile.num_sites == 3

    rec = recommend_products(profile)
    cat_status = rec["catalogue_status"]

    assert cat_status["P10"]["eligible"], "P10 SD-WAN should be eligible for 3 sites & 18 employees"

    rec_pids = [item["product_id"] for item in rec["recommended"]]
    assert "P10" in rec_pids

    # Check scaling of per-site items (e.g. broadband or SD-WAN)
    for it in rec["recommended"]:
        if it["unit"] == "per site":
            assert it["quantity"] == 3, f"Unit 'per site' for {it['product_id']} should be 3"


# ---------------------------------------------------------------------------
# Test 4: 30-employee manufacturer
# ---------------------------------------------------------------------------
def test_thirty_employee_manufacturer(catalogue_df):
    """
    Test scenario: 30-employee auto-parts manufacturer in Ludhiana (Tier 2).
    Has active GSTIN.
    Expected:
      - Inferred segment is 'mfg'
      - Eligible for high-tier enterprise products:
        P05 (ILL 20), P06 (ILL 100, min_emp=25), P21 (Firewall, min_emp=10),
        P24 (Machine Monitoring IoT, min_emp=10)
    """
    valid_gstin = "03JEUXR9399M1ZI"  # Active in registry (Ludhiana)
    profile = BusinessProfile(
        business_name="Royal Auto Components",
        business_type="Auto parts manufacturing",
        employee_count=30,
        num_sites=1,
        city="Ludhiana",
        has_gstin=True,
        gstin=valid_gstin,
        stated_needs=["internet", "firewall", "machine", "security"],
    )

    assert profile.segment == "mfg"

    rec = recommend_products(profile)
    cat_status = rec["catalogue_status"]

    assert cat_status["P05"]["eligible"]
    assert cat_status["P06"]["eligible"]
    assert cat_status["P21"]["eligible"]
    assert cat_status["P24"]["eligible"]

    rec_pids = [item["product_id"] for item in rec["recommended"]]
    # Should recommend leased line (P06 or P05), firewall (P21), machine monitoring (P24)
    assert any(pid in rec_pids for pid in ["P05", "P06"])
    assert "P21" in rec_pids
    assert "P24" in rec_pids


# ---------------------------------------------------------------------------
# Test 5: Dependency auto-add case
# ---------------------------------------------------------------------------
def test_dependency_auto_add(catalogue_df):
    """
    Test scenario: Customer needs Cloud CCTV (P23) or Backup Failover (P09).
    P23 has requires_one_of = 'P01|P02|P03|P04|P05|P06'.
    Neither broadband is in current selection.
    Expected:
      - Rules engine auto-adds the cheapest valid parent (P01 or P04)
      - Marks auto_added = True with plain-language explanation
      - If user removes parent, removal warns and removes dependents
    """
    profile = BusinessProfile(
        business_name="Apex Legal Advisors",
        business_type="Law office",
        employee_count=4,
        num_sites=1,
        city="Delhi",
        has_gstin=False,
        gstin=None,
        current_internet="Competitor broadband",  # Already has internet, did not ask for broadband
        stated_needs=["cctv"],  # Only asked for CCTV
    )

    rec = recommend_products(profile)
    rec_items = rec["recommended"]
    rec_pids = [item["product_id"] for item in rec_items]

    # CCTV is in bundle
    assert "P23" in rec_pids

    # Parent broadband must be auto-added
    parent_pids = ["P01", "P02", "P03", "P04", "P05", "P06"]
    added_parents = [pid for pid in parent_pids if pid in rec_pids]
    assert len(added_parents) > 0, "A broadband parent should be auto-added to satisfy P23 prerequisite"

    parent_item = next(it for it in rec_items if it["product_id"] in added_parents)
    assert parent_item["auto_added"] is True
    assert "prerequisite" in parent_item["reason"].lower() or "auto-added" in parent_item["reason"].lower()

    # Now test removal cascade in pricing engine
    bundle_to_prune = [
        {"product_id": parent_item["product_id"], "quantity": 1},
        {"product_id": "P23", "quantity": 2},
    ]
    updated_bundle, warnings = remove_product_with_dependency_check(bundle_to_prune, parent_item["product_id"])
    assert len(updated_bundle) == 0, "Removing broadband parent should cascade-remove dependent CCTV"
    assert any("requires a broadband link" in w for w in warnings)


# ---------------------------------------------------------------------------
# Test 6: Tier-2 city case
# ---------------------------------------------------------------------------
def test_tier_two_city_eligibility(catalogue_df):
    """
    Test scenario: Business located in Jaipur (Tier 2).
    P03 (Biz Fibre 1G) has available_city_tiers = '1'.
    Expected:
      - City tier derived as 2 from smb_leads
      - P03 is INELIGIBLE with reason mentioning Tier 1
      - Products with available_city_tiers = '1;2' remain eligible
    """
    tier = get_city_tier("Jaipur")
    assert tier == 2, f"Jaipur should be Tier 2 (got {tier})"

    valid_gstin = "08JVKXA4705I1Z0"  # Active in registry (Jaipur)
    profile = BusinessProfile(
        business_name="Jaipur Textiles",
        business_type="Textile showroom",
        employee_count=12,
        num_sites=1,
        city="Jaipur",
        has_gstin=True,
        gstin=valid_gstin,
    )

    rec = recommend_products(profile)
    cat_status = rec["catalogue_status"]

    # P03 is only Tier 1
    assert not cat_status["P03"]["eligible"]
    assert "Tier 1" in cat_status["P03"]["reason"]
    assert "Tier 2" in cat_status["P03"]["reason"]

    # P01, P02 are 1;2
    assert cat_status["P01"]["eligible"]
    assert cat_status["P02"]["eligible"]


# ---------------------------------------------------------------------------
# Test 7: Pricing engine calculations and contract enforcement
# ---------------------------------------------------------------------------
def test_quote_calculations(catalogue_df):
    """
    Test quote calculation against product_catalogue.csv.
    Verify:
      - Quoted at price_min starting price
      - Monthly total = sum(unit_price * qty)
      - One time total = sum(setup * qty)
      - First month payable = monthly total + one time total
      - Contract duration cannot be below product min_contract_months
    """
    items = [
        {"product_id": "P01", "quantity": 2},   # P01: min 999, setup 0, min_cm 12, install 5
        {"product_id": "P09", "quantity": 2},   # P09: min 499, setup 1500, min_cm 12, install 3
        {"product_id": "P10", "quantity": 1},   # P10: min 2500, setup 5000, min_cm 24, install 14
    ]

    # Test automatic adjustment if user requested 12 months, but P10 requires 24
    quote = calculate_quote(items, contract_months=12)
    assert quote.contract_months == 24
    assert quote.min_allowed_contract_months == 24
    assert any("adjusted to 24 months" in w for w in quote.warnings)

    expected_monthly = (999 * 2) + (499 * 2) + (2500 * 1)
    expected_setup = (0 * 2) + (1500 * 2) + (5000 * 1)
    expected_first_month = expected_monthly + expected_setup
    expected_contract_val = (expected_monthly * 24) + expected_setup

    assert quote.monthly_subtotal == expected_monthly
    assert quote.one_time_subtotal == expected_setup
    assert quote.first_month_payable == expected_first_month
    assert quote.total_contract_value == expected_contract_val
    assert quote.max_install_days == 14  # Max of 5, 3, 14


# ---------------------------------------------------------------------------
# Test 8: GSTIN checksum & registry integrity
# ---------------------------------------------------------------------------
def test_gstin_checksum_and_validation():
    """Verify GSTIN checksum calculation and validation logic."""
    # Valid active GSTIN
    valid_gstin = "32TTNXB7384T1ZW"
    ok, msg = validate_gstin_format(valid_gstin)
    assert ok, f"Expected {valid_gstin} to be valid: {msg}"

    # Invalid checksum
    bad_check_gstin = "32TTNXB7384T1ZA"
    ok, msg = validate_gstin_format(bad_check_gstin)
    assert not ok
    assert "checksum mismatch" in msg

    # Invalid length
    ok, msg = validate_gstin_format("12345")
    assert not ok
    assert "15 characters" in msg
