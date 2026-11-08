"""
Boundary condition validation and fuzz tests for Accel Business Udyam Digital.
Verifies that:
1. Extreme, negative, zero, and out-of-range user inputs do not crash Streamlit widgets.
2. Values are strictly clamped within [min_value, max_value] and written back to session state.
3. User-friendly notices appear when values are rejected or clamped.
4. Fuzz profiles with random extreme inputs render cleanly across all journey steps without exception.
"""

import pathlib
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(pathlib.Path("app.py").resolve())


@pytest.mark.parametrize(
    "msg, expected_emp, expected_sites, expected_note_part",
    [
        (
            "Dental clinic in Kochi with 600 employees, 1 location, GSTIN available",
            600,
            1,
            None,
        ),
        (
            "Large tech campus in Bengaluru with 12,000 employees across 1 location",
            10000,
            1,
            "Employees capped at 10,000",
        ),
        (
            "Automated data center in Mumbai with 0 employees and 1 site",
            1,
            1,
            "Employee count must be at least 1 (received 0)",
        ),
        (
            "Retail store in Chennai with -5 staff and 1 branch",
            1,
            1,
            "Employee count must be at least 1 (received -5)",
        ),
        (
            "Logistics warehouse enterprise with 100 staff across 1,000 sites in Delhi",
            100,
            500,
            "Operational sites capped at 500",
        ),
        (
            "Startup clinic in Bengaluru with 5 staff, 1 location, a budget of 0",
            5,
            1,
            None,
        ),
        (
            "Automotive plant in Pune with 50 staff across 1 site, a budget of 5 crore",
            50,
            1,
            "Monthly budget ceiling capped at ₹10,00,000",
        ),
    ],
)
def test_advisor_boundary_messages(msg, expected_emp, expected_sites, expected_note_part):
    """
    Asserts no exception, the page renders, values are clamped,
    and a clear note appears when clamping happens.
    """
    at = AppTest.from_file(APP_PATH)
    at.run()
    at.session_state.current_step = 1
    at.session_state.nav_view_selector = "Customer Journey"
    at.run()

    at.text_area[0].set_value(msg)
    buttons = [b for b in at.button if "Analyze with AI" in b.label]
    assert len(buttons) > 0
    buttons[0].click()
    at.run()

    assert len(at.exception) == 0, f"App threw exception on message: {msg}"
    assert at.session_state.advisor_input["employees"] == expected_emp
    assert at.session_state.advisor_input["sites"] == expected_sites

    num_inputs = [n.value for n in at.number_input]
    assert expected_emp in num_inputs
    assert expected_sites in num_inputs

    info_messages = [i.value for i in at.info]
    if expected_note_part:
        found = any(expected_note_part in m for m in info_messages)
        assert found, f"Expected note '{expected_note_part}' not found in info messages: {info_messages}"


def test_fuzz_extreme_profiles_all_steps():
    """
    Fuzz test that feeds extreme, corrupted, and out-of-range profile data
    through each journey step (Advisor, Quote, KYC, Checkout, Track) and asserts zero exceptions.
    """
    fuzz_cases = [
        {"employees": -100, "sites": -5, "budget": -50000, "btype": "UnknownCorp", "bb": "Satellite123"},
        {"employees": 0, "sites": 0, "budget": 0, "btype": None, "bb": None},
        {"employees": 999999, "sites": 50000, "budget": 999999999, "btype": "AlienIndustry", "bb": "QuantumWire"},
        {"employees": 600, "sites": 1, "budget": 1000000, "btype": "Healthcare/Clinic", "bb": "Fiber"},
    ]

    for case in fuzz_cases:
        at = AppTest.from_file(APP_PATH)
        at.run()
        at.session_state.nav_view_selector = "Customer Journey"

        # Step 1: Advisor with extreme profile
        at.session_state.current_step = 1
        at.session_state.advisor_input.update({
            "employees": case["employees"],
            "sites": case["sites"],
            "business_type": case["btype"],
            "current_broadband": case["bb"],
            "budget": case["budget"],
        })
        at.run()
        assert len(at.exception) == 0, f"Step 1 crashed on fuzz case {case}"

        # Step 2: Quote with extreme budget & extreme quantities
        at.session_state.current_step = 2
        at.session_state["input_budget_ceiling"] = case["budget"]
        at.session_state["last_budget_entered"] = case["budget"]
        if at.session_state.get("selected_items"):
            for item in at.session_state.selected_items:
                pid = item["product_id"]
                at.session_state[f"qty_{pid}"] = 99999
        at.run()
        assert len(at.exception) == 0, f"Step 2 crashed on fuzz case {case}"

        # Step 3: KYC with invalid applicant selection
        at.session_state.current_step = 3
        at.session_state["sb_demo_applicant"] = "INVALID_SPECIMEN_99"
        at.run()
        assert len(at.exception) == 0, f"Step 3 crashed on fuzz case {case}"

        # Step 4: Checkout with invalid payment method
        at.session_state.current_step = 4
        at.session_state["checkout_pay_method"] = "CryptoBitcoin"
        at.run()
        assert len(at.exception) == 0, f"Step 4 crashed on fuzz case {case}"

        # Step 5: Track with non-existent order ID
        at.session_state.current_step = 5
        at.session_state["last_order_id"] = "ORD-NONEXISTENT-9999"
        at.run()
        assert len(at.exception) == 0, f"Step 5 crashed on fuzz case {case}"
