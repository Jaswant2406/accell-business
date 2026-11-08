"""Test suite for Smart KYC OCR pipeline, validators, and DPDP masking."""

import datetime
from pathlib import Path
import cv2
import pytest

from kyc.ocr import (
    correct_gstin_via_substitutions,
    correct_udyam_via_substitutions,
    deskew_image,
    extract_address_proof_fields,
    extract_gst_certificate_fields,
    extract_signatory_id_fields,
    extract_udyam_certificate_fields,
    mask_identifier,
)
from kyc.validators import (
    TODAY,
    validate_applicant_kyc,
)

DOCS_DIR = Path("data/kyc_documents")


def test_dpdp_masking():
    """Verify DPDP identifier masking for privacy compliance."""
    assert mask_identifier("37IHKXV5167L1ZS") == "37XXXXXXXXXX1ZS"
    assert mask_identifier("UDYAM-WB-00-5053330") == "UDYAM-**-00-****330"
    assert mask_identifier("") == "N/A"
    assert mask_identifier(None) == "N/A"


def test_ocr_confusion_substitutions():
    """Verify single-character substitutions map OCR misreads to unique registry records."""
    # K03: 'O' instead of '0' at index 8
    corr, rec, note, is_corr = correct_gstin_via_substitutions("27XUIXGO767D1ZP")
    assert corr == "27XUIXG0767D1ZP"
    assert rec is not None
    assert is_corr is True
    assert "Substituted 'O' -> '0'" in note

    # K08: '0' instead of 'O' at index 3
    corr, rec, note, is_corr = correct_gstin_via_substitutions("24X0RXG9365M1Z3")
    assert corr == "24XORXG9365M1Z3"
    assert rec is not None
    assert is_corr is True
    assert "Substituted '0' -> 'O'" in note


def test_applicant_k06_multi_substitution_manual_review():
    """K06 requires >1 substitution (O->0, 8->5, 0->O); must NOT auto-approve and routes to MANUAL REVIEW."""
    gst_path = DOCS_DIR / "K06_gst_certificate.png"
    u_path = DOCS_DIR / "K06_udyam_certificate.png"
    sig_path = DOCS_DIR / "K06_signatory_id.png"
    addr_path = DOCS_DIR / "K06_address_proof.png"

    docs_data = {
        "gst_certificate": extract_gst_certificate_fields(cv2.imread(str(gst_path))),
        "udyam_certificate": extract_udyam_certificate_fields(cv2.imread(str(u_path))),
        "signatory_id": extract_signatory_id_fields(cv2.imread(str(sig_path))),
        "address_proof": extract_address_proof_fields(cv2.imread(str(addr_path))),
    }
    res = validate_applicant_kyc("K06", docs_data)
    assert res.decision == "MANUAL REVIEW"
    assert any("GSTIN on document does not match registry" in r for r in res.summary_reasons)


def test_applicant_k10_checksum_interpretation_approved():
    """K10 (Kaveri Stays LLP) resolves via checksum-level resolution and all 8 checks pass -> APPROVED."""
    gst_path = DOCS_DIR / "K10_gst_certificate.png"
    u_path = DOCS_DIR / "K10_udyam_certificate.png"
    sig_path = DOCS_DIR / "K10_signatory_id.png"
    addr_path = DOCS_DIR / "K10_address_proof.png"

    docs_data = {
        "gst_certificate": extract_gst_certificate_fields(cv2.imread(str(gst_path))),
        "udyam_certificate": extract_udyam_certificate_fields(cv2.imread(str(u_path))),
        "signatory_id": extract_signatory_id_fields(cv2.imread(str(sig_path))),
        "address_proof": extract_address_proof_fields(cv2.imread(str(addr_path))),
    }
    res = validate_applicant_kyc("K10", docs_data)
    assert res.decision == "APPROVED"
    assert sum(1 for c in res.checks if c.passed) == 8
    assert docs_data["gst_certificate"]["corrected_gstin"] == "27QHJXK0658U1ZL"
    assert docs_data["gst_certificate"]["registry_record"]["trade_name"] == "Kaveri Stays LLP"


def test_applicant_k01_cancelled_gstin_rejected():
    """K01 has Cancelled GSTIN status in registry; must be REJECTED."""
    gst_path = DOCS_DIR / "K01_gst_certificate.png"
    u_path = DOCS_DIR / "K01_udyam_certificate.png"
    sig_path = DOCS_DIR / "K01_signatory_id.png"
    addr_path = DOCS_DIR / "K01_address_proof.png"

    docs_data = {
        "gst_certificate": extract_gst_certificate_fields(cv2.imread(str(gst_path))),
        "udyam_certificate": extract_udyam_certificate_fields(cv2.imread(str(u_path))),
        "signatory_id": extract_signatory_id_fields(cv2.imread(str(sig_path))),
        "address_proof": extract_address_proof_fields(cv2.imread(str(addr_path))),
    }
    res = validate_applicant_kyc("K01", docs_data)
    assert res.decision == "REJECTED"
    assert any("Cancelled" in r for r in res.summary_reasons)


def test_applicant_k04_blurry_gst_manual_review():
    """K04 GST certificate is blurred beyond recognition; must route to MANUAL REVIEW."""
    gst_path = DOCS_DIR / "K04_gst_certificate.png"
    u_path = DOCS_DIR / "K04_udyam_certificate.png"
    sig_path = DOCS_DIR / "K04_signatory_id.png"
    addr_path = DOCS_DIR / "K04_address_proof.png"

    docs_data = {
        "gst_certificate": extract_gst_certificate_fields(cv2.imread(str(gst_path))),
        "udyam_certificate": extract_udyam_certificate_fields(cv2.imread(str(u_path))),
        "signatory_id": extract_signatory_id_fields(cv2.imread(str(sig_path))),
        "address_proof": extract_address_proof_fields(cv2.imread(str(addr_path))),
    }
    res = validate_applicant_kyc("K04", docs_data)
    assert res.decision == "MANUAL REVIEW"
    assert any("Unreadable or missing GST" in r for r in res.summary_reasons)


def test_applicant_k05_missing_udyam_manual_review():
    """K05 has no Udyam certificate; must be flagged as MANUAL REVIEW."""
    gst_path = DOCS_DIR / "K05_gst_certificate.png"
    sig_path = DOCS_DIR / "K05_signatory_id.png"
    addr_path = DOCS_DIR / "K05_address_proof.png"

    docs_data = {
        "gst_certificate": extract_gst_certificate_fields(cv2.imread(str(gst_path))),
        "udyam_certificate": None,  # File does not exist
        "signatory_id": extract_signatory_id_fields(cv2.imread(str(sig_path))),
        "address_proof": extract_address_proof_fields(cv2.imread(str(addr_path))),
    }
    res = validate_applicant_kyc("K05", docs_data)
    assert res.decision == "MANUAL REVIEW"
    assert any("Missing Udyam" in r for r in res.summary_reasons)


def test_applicant_k07_name_mismatch_rejected():
    """K07 GST legal has 'Shri Physio Clinic' while Udyam is 'Neelgiri Physio Clinic'; must be REJECTED."""
    gst_path = DOCS_DIR / "K07_gst_certificate.png"
    u_path = DOCS_DIR / "K07_udyam_certificate.png"
    sig_path = DOCS_DIR / "K07_signatory_id.png"
    addr_path = DOCS_DIR / "K07_address_proof.png"

    docs_data = {
        "gst_certificate": extract_gst_certificate_fields(cv2.imread(str(gst_path))),
        "udyam_certificate": extract_udyam_certificate_fields(cv2.imread(str(u_path))),
        "signatory_id": extract_signatory_id_fields(cv2.imread(str(sig_path))),
        "address_proof": extract_address_proof_fields(cv2.imread(str(addr_path))),
    }
    res = validate_applicant_kyc("K07", docs_data)
    assert res.decision == "REJECTED"
    assert any("mismatch" in r.lower() for r in res.summary_reasons)


def test_applicant_k11_stale_address_proof_rejected():
    """K11 address proof is dated 2025-10-31 (>90 days old from 2026-07-15); must be REJECTED."""
    gst_path = DOCS_DIR / "K11_gst_certificate.png"
    u_path = DOCS_DIR / "K11_udyam_certificate.png"
    sig_path = DOCS_DIR / "K11_signatory_id.png"
    addr_path = DOCS_DIR / "K11_address_proof.png"

    docs_data = {
        "gst_certificate": extract_gst_certificate_fields(cv2.imread(str(gst_path))),
        "udyam_certificate": extract_udyam_certificate_fields(cv2.imread(str(u_path))),
        "signatory_id": extract_signatory_id_fields(cv2.imread(str(sig_path))),
        "address_proof": extract_address_proof_fields(cv2.imread(str(addr_path))),
    }
    res = validate_applicant_kyc("K11", docs_data)
    assert res.decision == "REJECTED"
    assert any("Stale" in r for r in res.summary_reasons)


def test_applicant_k12_clean_pass_approved():
    """K12 has all valid, consistent, active documents; must be APPROVED."""
    gst_path = DOCS_DIR / "K12_gst_certificate.png"
    u_path = DOCS_DIR / "K12_udyam_certificate.png"
    sig_path = DOCS_DIR / "K12_signatory_id.png"
    addr_path = DOCS_DIR / "K12_address_proof.png"

    docs_data = {
        "gst_certificate": extract_gst_certificate_fields(cv2.imread(str(gst_path))),
        "udyam_certificate": extract_udyam_certificate_fields(cv2.imread(str(u_path))),
        "signatory_id": extract_signatory_id_fields(cv2.imread(str(sig_path))),
        "address_proof": extract_address_proof_fields(cv2.imread(str(addr_path))),
    }
    res = validate_applicant_kyc("K12", docs_data)
    assert res.decision == "APPROVED"
    assert sum(1 for c in res.checks if c.passed) == 8
