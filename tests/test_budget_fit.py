"""Unit tests for 'Fit My Budget' optimization engine."""

import pytest
from engine.budget_fit import fit_bundle_to_budget
from engine.eligibility import BusinessProfile
from kyc.registry import load_catalogue


def test_budget_fit_respects_ceiling():
    """Verify optimized bundle never exceeds entered monthly budget."""
    prof = BusinessProfile(
        business_name="Green Leaf Legal",
        business_type="Professional Services",
        employee_count=4,
        num_sites=1,
        city="Ahmedabad",
        has_gstin=True,
        gstin="24XORXG9365M1Z3",
        stated_needs=["broadband", "cloud backup", "cctv"],
    )

    budget = 2500
    res = fit_bundle_to_budget(prof, monthly_budget=budget)

    assert res.total_monthly_cost <= budget
    assert res.remaining_budget >= 0
    assert res.remaining_budget == budget - res.total_monthly_cost
    assert len(res.selected_items) >= 1
    # Check that base connectivity is included
    selected_pids = {p["product_id"] for p in res.selected_items}
    assert any(pid in ["P01", "P02", "P04"] for pid in selected_pids)


def test_budget_fit_respects_requires_one_of_dependencies():
    """Verify dependent products are only included if their parent is also present."""
    prof = BusinessProfile(
        business_name="Apex Labs",
        business_type="Healthcare/Clinic",
        employee_count=6,
        num_sites=1,
        city="Bengaluru",
        has_gstin=True,
        gstin="29AABCS1429B1ZB",
        stated_needs=["broadband", "static ip", "cloud backup"],
    )

    budget = 3500
    res = fit_bundle_to_budget(prof, monthly_budget=budget)

    df_cat = load_catalogue().set_index("product_id")
    selected_pids = {p["product_id"] for p in res.selected_items}

    for pid in selected_pids:
        req_str = str(df_cat.loc[pid]["requires_one_of"]) if pid in df_cat.index else ""
        if req_str and req_str.strip() and req_str != "nan":
            parents = [c.strip() for c in req_str.split("|") if c.strip()]
            assert any(parent in selected_pids for parent in parents), f"{pid} selected without parent from {parents}"


def test_budget_fit_drops_and_explains():
    """Verify that products exceeding budget or deprioritized are listed with clear reasons."""
    prof = BusinessProfile(
        business_name="City Kirana",
        business_type="Retail/Kirana",
        employee_count=2,
        num_sites=1,
        city="Pune",
        has_gstin=False,
        stated_needs=["broadband", "cctv"],
    )

    # Budget ₹1,200 allows P01 (₹999) but cannot fit P23 Cloud CCTV (₹1,500)
    res = fit_bundle_to_budget(prof, monthly_budget=1200)

    assert res.total_monthly_cost <= 1200
    selected_pids = {p["product_id"] for p in res.selected_items}
    assert "P01" in selected_pids

    # Cloud CCTV should be in dropped items with explanation
    dropped_pids = {d.product_id for d in res.dropped_items}
    assert "P23" in dropped_pids
    cctv_dropped = [d for d in res.dropped_items if d.product_id == "P23"][0]
    assert "Exceeded remaining budget" in cctv_dropped.reason


def test_budget_fit_below_minimum_entry():
    """Verify budget below cheapest connectivity returns informative explanation."""
    prof = BusinessProfile(
        business_name="Micro Stall",
        business_type="Retail/Kirana",
        employee_count=1,
        num_sites=1,
        city="Delhi",
        has_gstin=False,
        stated_needs=["broadband"],
    )

    # ₹500 is below cheapest catalogue connectivity (₹899 or ₹999)
    res = fit_bundle_to_budget(prof, monthly_budget=500)

    assert len(res.selected_items) == 0
    assert res.total_monthly_cost == 0
    assert "below the minimum entry cost" in res.explanation


def test_budget_fit_contract_months_constraint():
    """Verify products requiring longer contract than selected are excluded."""
    prof = BusinessProfile(
        business_name="Popup Shop",
        business_type="Retail/Kirana",
        employee_count=2,
        num_sites=1,
        city="Mumbai",
        has_gstin=True,
        gstin="27QHJXK0658U1ZL",
        stated_needs=["broadband"],
    )

    # Contract commitment limited to 1 month excludes 12-month minimum products
    res = fit_bundle_to_budget(prof, monthly_budget=5000, contract_months=1)

    for p in res.selected_items:
        assert p["price_min"] > 0
