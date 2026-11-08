"""
Smoke test suite using streamlit.testing.v1.AppTest.
Verifies that app.py and all journey steps render with zero exceptions,
and tests complete end-to-end flows for K12 (Approved) and K06 (Manual Review).
"""

from pathlib import Path
import cv2
import pytest
from streamlit.testing.v1 import AppTest

from engine.advisor import build_business_profile_from_advisor, deterministic_advisor_fallback
from engine.eligibility import recommend_products
from engine.orders import advance_order_status, create_new_order_record, get_order
from engine.pricing import calculate_quote
from kyc.ocr import (
    extract_address_proof_fields,
    extract_gst_certificate_fields,
    extract_signatory_id_fields,
    extract_udyam_certificate_fields,
)
from kyc.validators import validate_applicant_kyc

DOCS_DIR = Path("data/kyc_documents")
APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_initial_render():
    """Verify app.py loads cleanly with zero exceptions on cold start."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert len(at.exception) == 0


def test_app_all_journey_steps():
    """Verify that each of the 5 journey steps renders cleanly."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert len(at.exception) == 0

    # Step 1: Advisor
    at.session_state["current_step"] = 1
    at.run()
    assert len(at.exception) == 0

    # Step 2: Quote
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
            "reason": "Base connectivity",
            "assumption": "1 site",
        }
    ]
    at.run()
    assert len(at.exception) == 0

    # Step 3: KYC
    at.session_state["current_step"] = 3
    at.session_state["dpdp_consent_granted"] = True
    at.run()
    assert len(at.exception) == 0

    # Step 4: Checkout
    at.session_state["current_step"] = 4
    at.session_state["current_quote"] = {
        "monthly_subtotal": 999,
        "one_time_subtotal": 1500,
        "first_month_payable": 2499,
        "contract_months": 12,
        "max_install_days": 3,
        "items": [{"product_name": "Biz Fibre 100 Mbps", "monthly_amount": 999}],
    }
    at.run()
    assert len(at.exception) == 0

    # Step 5: Track
    at.session_state["current_step"] = 5
    at.run()
    assert len(at.exception) == 0


def test_app_views_kyc_and_analytics():
    """Verify Operational KYC Desk and Sales Analytics render with zero exceptions."""
    at = AppTest.from_file(APP_PATH)
    at.run()
    assert len(at.exception) == 0

    # Test KYC Desk
    at.session_state["nav_view_selector"] = "KYC Verification Desk"
    at.run(timeout=30)
    assert len(at.exception) == 0

    # Test Sales Analytics
    at.session_state["nav_view_selector"] = "Sales Analytics"
    at.run(timeout=30)
    assert len(at.exception) == 0


def test_k12_flow_through_track():
    """
    End-to-end customer flow for Applicant K12 (Star Electronics):
    Advisor -> Quote -> Approved KYC (8/8) -> Order Creation -> Track & Successful Simulation.
    """
    at = AppTest.from_file(APP_PATH)
    at.run()

    # Step 1: Advisor setup
    prof_dict = deterministic_advisor_fallback(
        business_type="Retail/Kirana",
        employees=3,
        sites=1,
        city="Visakhapatnam",
        has_gstin=True,
        gstin="37NBLXS1145E1ZU",
        current_broadband="None",
        digital_needs=["cloud_storage"],
    )
    prof = build_business_profile_from_advisor(prof_dict)
    rec_res = recommend_products(prof)
    recommended = rec_res["recommended"]
    assert len(recommended) >= 1

    # Step 2: Quote
    quote = calculate_quote(recommended, contract_months=12)
    assert quote.monthly_subtotal > 0

    # Step 3: Smart KYC with K12 documents
    gst_f = extract_gst_certificate_fields(cv2.imread(str(DOCS_DIR / "K12_gst_certificate.png")))
    u_f = extract_udyam_certificate_fields(cv2.imread(str(DOCS_DIR / "K12_udyam_certificate.png")))
    sig_f = extract_signatory_id_fields(cv2.imread(str(DOCS_DIR / "K12_signatory_id.png")))
    addr_f = extract_address_proof_fields(cv2.imread(str(DOCS_DIR / "K12_address_proof.png")))

    kyc_res = validate_applicant_kyc(
        "K12",
        {
            "gst_certificate": gst_f,
            "udyam_certificate": u_f,
            "signatory_id": sig_f,
            "address_proof": addr_f,
        },
    )
    assert kyc_res.decision == "APPROVED"
    assert sum(1 for c in kyc_res.checks if c.passed) == 8

    # Step 4: Checkout & Order Creation
    order = create_new_order_record(
        company_name="Star Electronics",
        contact_person="Ravi Teja",
        phone="+91 98480 12345",
        email="orders@starelectronics.in",
        city="Visakhapatnam",
        quote_data=quote.to_dict(),
        kyc_result_data={"decision": kyc_res.decision, "reasons": kyc_res.summary_reasons},
    )
    order_id = order["order_id"]
    assert order_id.startswith("AB-2026-")

    # Step 5: Render Track step in AppTest
    at.session_state["current_step"] = 5
    at.session_state["last_order_id"] = order_id
    at.run()
    assert len(at.exception) == 0

    # Milestone simulation succeeds for Approved applicant
    ok, msg, updated_order = advance_order_status(order_id)
    assert ok is True
    assert updated_order["status"] == "SURVEY_SCHEDULED"


def test_k06_flow_through_track():
    """
    End-to-end customer flow for Applicant K06 (Saffron Unisex Salon):
    Advisor -> Quote -> Manual Review KYC (7/8) -> Provisional Order -> Track (Installation Blocked).
    """
    at = AppTest.from_file(APP_PATH)
    at.run()

    # Step 1: Advisor setup
    prof_dict = deterministic_advisor_fallback(
        business_type="Salon/Beauty",
        employees=4,
        sites=1,
        city="Jaipur",
        has_gstin=True,
        gstin="O8YKZXS8189L1Z0",
        current_broadband="None",
        digital_needs=[],
    )
    prof = build_business_profile_from_advisor(prof_dict)
    rec_res = recommend_products(prof)
    recommended = rec_res["recommended"]

    # Step 2: Quote
    quote = calculate_quote(recommended, contract_months=12)

    # Step 3: Smart KYC with K06 documents
    gst_f = extract_gst_certificate_fields(cv2.imread(str(DOCS_DIR / "K06_gst_certificate.png")))
    u_f = extract_udyam_certificate_fields(cv2.imread(str(DOCS_DIR / "K06_udyam_certificate.png")))
    sig_f = extract_signatory_id_fields(cv2.imread(str(DOCS_DIR / "K06_signatory_id.png")))
    addr_f = extract_address_proof_fields(cv2.imread(str(DOCS_DIR / "K06_address_proof.png")))

    kyc_res = validate_applicant_kyc(
        "K06",
        {
            "gst_certificate": gst_f,
            "udyam_certificate": u_f,
            "signatory_id": sig_f,
            "address_proof": addr_f,
        },
    )
    assert kyc_res.decision == "MANUAL REVIEW"
    assert sum(1 for c in kyc_res.checks if c.passed) == 7

    # Step 4: Checkout & Order Creation in Manual Review status
    order = create_new_order_record(
        company_name="Saffron Unisex Salon",
        contact_person="Anita Sharma",
        phone="+91 94140 56789",
        email="contact@saffronsalon.in",
        city="Jaipur",
        quote_data=quote.to_dict(),
        kyc_result_data={"decision": kyc_res.decision, "reasons": kyc_res.summary_reasons},
    )
    order_id = order["order_id"]

    # Step 5: Render Track step in AppTest
    at.session_state["current_step"] = 5
    at.session_state["last_order_id"] = order_id
    at.run()
    assert len(at.exception) == 0

    # Milestone simulation MUST be blocked for Manual Review applicant
    ok, msg, updated_order = advance_order_status(order_id)
    assert ok is False
    assert "MANUAL REVIEW" in msg
    assert updated_order["status"] == "PLACED"
