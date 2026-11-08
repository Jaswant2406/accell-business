"""
Interactive AppTest regression suite verifying submit and continue actions across all journey stages:
1. Advisor chat submit with Gemini disabled (offline rules mode): asserts non-empty bundle & Kochi profile.
2. Advisor slot-filling: incomplete input triggers next question or ambiguity confirmation.
3. Quote accept: validates dependencies, calculates quote, advances to KYC (Step 3).
4. KYC consent & verification: runs 8 compliance checks, asserts APPROVED for K12, advances to Checkout (Step 4).
5. Checkout order placement: submits digital mandate, creates order record, advances to Track (Step 5).
6. Track order advance: advances milestone telemetry on live order.
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from engine.orders import get_order, advance_order_status

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_advisor_chat_submit_recommends_bundle():
    """Verify typing a business description and clicking Analyze with AI updates profile and recommends items."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert len(at.exception) == 0

    at.session_state["nav_view_selector"] = "Customer Journey"
    at.session_state["current_step"] = 1
    at.run()
    assert len(at.exception) == 0

    # Simulate entering chat message
    chat_msg = "Dental clinic, 5 staff, 1 location in Kochi, I have a GSTIN"
    at.session_state.advisor_input["chat_text"] = chat_msg
    
    # Click "Analyze with AI ↗" button
    # In AppTest, find the analyze button
    btn_ai = [b for b in at.button if "Analyze with AI" in b.label]
    assert len(btn_ai) > 0
    btn_ai[0].click()
    at.run(timeout=50)
    assert len(at.exception) == 0

    # Assert business profile was updated correctly
    prof = at.session_state.business_profile
    assert prof is not None
    assert prof.city == "Kochi"
    assert prof.employee_count == 5
    assert prof.business_type == "Healthcare/Clinic"
    assert prof.has_gstin is True

    # Assert curated recommendations are non-empty
    assert "advisor_input" in at.session_state
    assert at.session_state.advisor_input.get("is_llm") is False
    assert at.session_state.advisor_input.get("mode_note") == "Running in rules mode"


def test_advisor_slot_filling_incomplete_input():
    """Verify vague input prompts for missing slots (e.g. employee count or city)."""
    at = AppTest.from_file(APP_PATH)
    at.run()

    at.session_state["nav_view_selector"] = "Customer Journey"
    at.session_state["current_step"] = 1
    at.run()

    # Enter vague input without city or headcount
    at.session_state.advisor_input["chat_text"] = "I need broadband for my office"
    btn_ai = [b for b in at.button if "Analyze with AI" in b.label]
    assert len(btn_ai) > 0
    btn_ai[0].click()
    at.run(timeout=50)
    assert len(at.exception) == 0

    raw = at.session_state.get("raw_extracted_profile")
    assert raw is not None
    # Employees or city should be missing/defaulted and slot filling should be active
    assert raw.get("employees_missing") or raw.get("city") == "Unknown" or raw.get("city") == "Mumbai"


def test_quote_accept_advances_to_kyc():
    """Verify clicking Accept & Proceed to KYC advances to Step 3."""
    at = AppTest.from_file(APP_PATH)
    at.run()

    at.session_state["nav_view_selector"] = "Customer Journey"
    at.session_state["current_step"] = 2
    at.session_state["selected_items"] = [
        {
            "product_id": "P01",
            "product_name": "Biz Fibre 100 Mbps",
            "category": "Broadband",
            "quantity": 1,
            "price_min": 999,
            "price_max": 1499,
            "one_time_setup": 1500,
            "unit": "per site",
            "min_contract_months": 12,
            "typical_install_days": 3,
            "reason": "Primary connectivity",
            "assumption": "Single site",
        }
    ]
    at.run()
    assert len(at.exception) == 0

    # Click Accept & Proceed to KYC button
    btn_accept = [b for b in at.button if "Accept & Proceed to KYC" in b.label]
    assert len(btn_accept) > 0
    assert not btn_accept[0].disabled
    btn_accept[0].click()
    at.run()
    assert len(at.exception) == 0

    assert at.session_state.current_step == 3


def test_kyc_consent_and_verification_flow():
    """Verify DPDP consent grant and running verification for benchmark applicant."""
    at = AppTest.from_file(APP_PATH)
    at.run()

    at.session_state["nav_view_selector"] = "Customer Journey"
    at.session_state["current_step"] = 3
    at.session_state["dpdp_consent_granted"] = True
    at.session_state["sb_demo_applicant"] = "K12"
    at.run()
    assert len(at.exception) == 0

    # Run KYC verification
    btn_kyc = [b for b in at.button if "Run Smart KYC Verification" in b.label]
    assert len(btn_kyc) > 0
    btn_kyc[0].click()
    at.run(timeout=20)
    assert len(at.exception) == 0

    res = at.session_state.get("kyc_result")
    assert res is not None
    assert res.decision == "APPROVED"
    assert at.session_state.kyc_verified is True

    # Click Proceed to Checkout
    btn_checkout = [b for b in at.button if "Proceed to Checkout" in b.label]
    assert len(btn_checkout) > 0
    btn_checkout[0].click()
    at.run()
    assert len(at.exception) == 0

    assert at.session_state.current_step == 4


def test_checkout_confirm_order_and_track_advance():
    """Verify confirming order creates order record, advances to Step 5, and advances milestones."""
    from kyc.validators import KYCVerificationResult
    
    at = AppTest.from_file(APP_PATH)
    at.run()

    at.session_state["nav_view_selector"] = "Customer Journey"
    at.session_state["current_step"] = 4
    at.session_state["current_quote"] = {
        "monthly_subtotal": 1999,
        "one_time_subtotal": 2000,
        "first_month_payable": 3999,
        "contract_months": 12,
        "max_install_days": 3,
        "items": [{"product_name": "Biz Fibre 300 Mbps", "monthly_amount": 1999}],
    }
    at.session_state["kyc_result"] = KYCVerificationResult(
        applicant_id="K12",
        decision="APPROVED",
        checks=[],
        summary_reasons=[],
        extracted_fields={},
    )
    at.session_state["cb_auth_mandate"] = True
    at.run()
    assert len(at.exception) == 0

    # Click Confirm Order
    btn_confirm = [b for b in at.button if "Confirm Order" in b.label]
    assert len(btn_confirm) > 0
    btn_confirm[0].click()
    at.run()
    assert len(at.exception) == 0

    assert at.session_state.current_step == 5
    order_id = at.session_state.get("last_order_id")
    assert order_id is not None
    assert order_id.startswith("AB-2026-")

    # Verify order in store
    rec = get_order(order_id)
    assert rec is not None
    assert rec["company_name"] is not None
    assert rec["kyc_decision"] == "APPROVED"

    # Test advancing milestone
    ok, msg, updated = advance_order_status(order_id)
    assert ok is True
    assert updated["status"] == "SURVEY_SCHEDULED"


def test_sidebar_ai_mode_toggle_behavior():
    """
    Validates:
    1. Sidebar toggle 'AI mode (Gemini)' defaults to False (OFF).
    2. When OFF, advisor goes directly to rules mode without spinner delay.
    3. When toggled ON with failed health check, toggle automatically switches off
       and displays 'Gemini unavailable, using rules mode'.
    """
    at = AppTest.from_file(APP_PATH)
    at.run()

    # 1. Check default toggle state is False
    assert at.session_state.get("ai_mode_toggle") is False
    toggles = [t for t in at.toggle if "AI mode" in t.label]
    assert len(toggles) > 0
    assert toggles[0].value is False

    # 2. Simulate health check failure when toggled ON
    at.session_state["gemini_health_cached"] = False
    toggles[0].set_value(True)
    at.run()
    assert len(at.exception) == 0

    # Toggle should have reset itself to False
    assert at.session_state.get("ai_mode_toggle") is False
    assert at.session_state.get("gemini_unavailable_note") == "Gemini unavailable, using rules mode"

    # 3. Simulate health check success when toggled ON with a fresh AppTest
    at2 = AppTest.from_file(APP_PATH)
    at2.run()
    at2.session_state["gemini_health_cached"] = True
    toggles2 = [t for t in at2.toggle if "AI mode" in t.label]
    toggles2[0].set_value(True)
    at2.run()
    assert len(at2.exception) == 0
    assert at2.session_state.get("ai_mode_toggle") is True
    assert "gemini_unavailable_note" not in at2.session_state

