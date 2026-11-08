"""Smart KYC Validator module enforcing all 8 business and regulatory checks."""

import datetime
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from kyc.ocr import mask_identifier
from kyc.registry import validate_gstin_format, validate_udyam_format

# Ground rule: Treat today as 2026-07-15
TODAY = datetime.date(2026, 7, 15)
MAX_ADDRESS_PROOF_AGE_DAYS = 90


@dataclass
class CheckResult:
    """Result of an individual KYC validation check."""
    check_name: str
    passed: bool
    details: str
    severity: str = "CRITICAL"  # "CRITICAL" or "WARNING"


@dataclass
class KYCVerificationResult:
    """Consolidated KYC outcome across all checks."""
    applicant_id: str
    decision: str              # "APPROVED", "REJECTED", "MANUAL REVIEW"
    checks: List[CheckResult]
    extracted_fields: Dict[str, Any]
    summary_reasons: List[str]
    ocr_corrections: List[str] = field(default_factory=list)
    ocr_failures: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "applicant_id": self.applicant_id,
            "decision": self.decision,
            "summary_reasons": self.summary_reasons,
            "ocr_corrections": self.ocr_corrections,
            "ocr_failures": self.ocr_failures,
            "checks": [
                {
                    "check_name": c.check_name,
                    "passed": c.passed,
                    "details": c.details,
                    "severity": c.severity,
                }
                for c in self.checks
            ],
            "extracted_fields": self.extracted_fields,
        }


def normalize_business_name(name: Optional[str]) -> str:
    """Normalize company name by removing entity designators and proprietor clauses."""
    if not name:
        return ""
    s = name.lower()
    prop_m = re.search(r"prop\.?\s*([^)]+)\)?", s)
    if prop_m:
        s = prop_m.group(1)
        
    for term in [
        "private limited", "pvt ltd", "pvt. ltd.", "pvt.ltd.",
        "limited", "ltd", "ltd.", "llp", "proprietorship", "company"
    ]:
        s = re.sub(r"\b" + re.escape(term) + r"\b", "", s)
        
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return " ".join(s.split())


def extract_proprietor_name(legal_name: Optional[str]) -> Optional[str]:
    """Extract individual proprietor name from 'Neha Kaur (Prop. ...)' or return legal name."""
    if not legal_name:
        return None
    m = re.match(r"^([^(]+?)(?:\s*\(\s*prop\.|\s*\(|\s*$)", legal_name, re.IGNORECASE)
    if m:
        return " ".join(m.group(1).split())
    return legal_name.strip()


GENERIC_TERMS = {
    "clinic", "physio", "physiotherapy", "dental", "care", "hospital", "lab",
    "diagnostics", "store", "shop", "enterprises", "traders", "salon", "bakers",
    "foods", "tech", "technologies", "services", "llp", "pvt", "ltd", "limited",
    "company", "associates", "realty", "medicals", "tours", "travels", "stays",
    "hardware", "general", "optical", "opticals", "unisex", "woodcraft"
}


def brand_token_match(name1: str, name2: str) -> bool:
    """Compare primary non-generic brand keywords."""
    t1 = [w for w in name1.lower().split() if w not in GENERIC_TERMS]
    t2 = [w for w in name2.lower().split() if w not in GENERIC_TERMS]
    if t1 and t2:
        return t1[0] == t2[0] or (t1[0] in t2[0]) or (t2[0] in t1[0])
    return True


def fuzzy_match(str1: Optional[str], str2: Optional[str], threshold: float = 0.70) -> bool:
    """Fuzzy string matching with token set overlap support."""
    if not str1 or not str2:
        return False
    s1, s2 = str1.strip().lower(), str2.strip().lower()
    if s1 == s2 or s1 in s2 or s2 in s1:
        return True
    
    t1 = set(s1.split())
    t2 = set(s2.split())
    if t1 and t2:
        overlap = len(t1.intersection(t2)) / float(max(len(t1), len(t2)))
        if overlap >= 0.55:
            return True
            
    ratio = SequenceMatcher(None, s1, s2).ratio()
    return ratio >= threshold


def extract_pincode(addr: Optional[str]) -> Optional[str]:
    """Extract 6-digit Indian PIN code."""
    if not addr:
        return None
    m = re.search(r"\b(\d{6})\b", addr)
    return m.group(1) if m else None


def validate_applicant_kyc(
    applicant_id: str,
    docs_data: Dict[str, Optional[Dict[str, Any]]],
) -> KYCVerificationResult:
    """
    Validate all 4 KYC documents against regulatory standards and mock registries.
    docs_data keys: 'gst_certificate', 'udyam_certificate', 'signatory_id', 'address_proof'.
    """
    checks: List[CheckResult] = []
    summary_reasons: List[str] = []
    ocr_corrections: List[str] = []
    ocr_failures: List[str] = []
    
    gst_doc = docs_data.get("gst_certificate")
    udyam_doc = docs_data.get("udyam_certificate")
    sig_doc = docs_data.get("signatory_id")
    addr_doc = docs_data.get("address_proof")

    # Record any OCR notes/corrections
    if gst_doc:
        if gst_doc.get("ocr_note") and "OCR-corrected:" in gst_doc["ocr_note"]:
            ocr_corrections.append(gst_doc["ocr_note"])
        elif gst_doc.get("ocr_note") and ("Correction" in gst_doc["ocr_note"] or "Substituted" in gst_doc["ocr_note"]):
            ocr_corrections.append(f"GSTIN: {gst_doc['ocr_note']}")
        if not gst_doc.get("ocr_success"):
            ocr_failures.append("GST certificate OCR failed to extract a readable GSTIN")
            
    if udyam_doc:
        if udyam_doc.get("ocr_note") and ("Correction" in udyam_doc["ocr_note"] or "Substituted" in udyam_doc["ocr_note"]):
            ocr_corrections.append(f"Udyam: {udyam_doc['ocr_note']}")
        if not udyam_doc.get("ocr_success"):
            ocr_failures.append("Udyam certificate OCR failed to extract a readable Udyam registration number")

    # -------------------------------------------------------------------------
    # Check 1: All 4 Documents Present
    # -------------------------------------------------------------------------
    missing_docs = []
    if not gst_doc: missing_docs.append("GST Certificate")
    if not udyam_doc: missing_docs.append("Udyam Certificate")
    if not sig_doc: missing_docs.append("Authorised Signatory ID")
    if not addr_doc: missing_docs.append("Address Proof (Utility Bill)")

    if missing_docs:
        checks.append(
            CheckResult(
                check_name="All 4 Documents Present",
                passed=False,
                details=f"Missing mandatory documents: {', '.join(missing_docs)}",
            )
        )
        summary_reasons.append(f"Incomplete submission: Missing {', '.join(missing_docs)}")
    else:
        checks.append(
            CheckResult(
                check_name="All 4 Documents Present",
                passed=True,
                details="All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded",
            )
        )

    # -------------------------------------------------------------------------
    # Check 2: GSTIN Format, Registry Lookup & Active Status
    # -------------------------------------------------------------------------
    gst_cancelled = False
    gst_match_failed = False
    if not gst_doc or not gst_doc.get("ocr_success"):
        checks.append(
            CheckResult(
                check_name="GSTIN Format & Registry Validation",
                passed=False,
                details="GST certificate could not be read or is missing",
            )
        )
        summary_reasons.append("Unreadable or missing GST Certificate")
        gst_match_failed = True
    else:
        gstin = gst_doc.get("corrected_gstin") or gst_doc.get("raw_gstin")
        reg_record = gst_doc.get("registry_record")
        is_fmt_valid, fmt_msg = validate_gstin_format(gstin)
        
        if not is_fmt_valid or not reg_record:
            checks.append(
                CheckResult(
                    check_name="GSTIN Format & Registry Validation",
                    passed=False,
                    details=f"GSTIN on document does not match registry ({mask_identifier(gstin)})",
                )
            )
            summary_reasons.append("GSTIN on document does not match registry")
            gst_match_failed = True
        else:
            status = str(reg_record.get("status", "")).strip()
            if status.lower() != "active":
                checks.append(
                    CheckResult(
                        check_name="GSTIN Format & Registry Validation",
                        passed=False,
                        details=f"GSTIN {mask_identifier(gstin)} is '{status}' in official registry (Active required)",
                    )
                )
                summary_reasons.append(f"GSTIN registration status is {status} (Active required)")
                if status.lower() == "cancelled":
                    gst_cancelled = True
                else:
                    gst_match_failed = True
            else:
                checks.append(
                    CheckResult(
                        check_name="GSTIN Format & Registry Validation",
                        passed=True,
                        details=f"Valid GSTIN {mask_identifier(gstin)} confirmed Active in GST registry",
                    )
                )

    # -------------------------------------------------------------------------
    # Check 3: Udyam Format & Registry Lookup
    # -------------------------------------------------------------------------
    if not udyam_doc or not udyam_doc.get("ocr_success"):
        checks.append(
            CheckResult(
                check_name="Udyam Registration & Registry Validation",
                passed=False,
                details="Udyam certificate could not be read or is missing",
            )
        )
        summary_reasons.append("Missing or unreadable Udyam registration certificate")
    else:
        u_num = udyam_doc.get("corrected_udyam") or udyam_doc.get("raw_udyam")
        reg_record = udyam_doc.get("registry_record")
        is_fmt_valid, fmt_msg = validate_udyam_format(u_num)
        
        if not is_fmt_valid:
            checks.append(
                CheckResult(
                    check_name="Udyam Registration & Registry Validation",
                    passed=False,
                    details=f"Udyam {mask_identifier(u_num)} format invalid: {fmt_msg}",
                )
            )
            summary_reasons.append(f"Invalid Udyam number format ({fmt_msg})")
        elif not reg_record:
            checks.append(
                CheckResult(
                    check_name="Udyam Registration & Registry Validation",
                    passed=False,
                    details=f"Udyam {mask_identifier(u_num)} not found in Udyam registry",
                )
            )
            summary_reasons.append(f"Udyam registration {mask_identifier(u_num)} not found in registry")
        else:
            checks.append(
                CheckResult(
                    check_name="Udyam Registration & Registry Validation",
                    passed=True,
                    details=f"Valid Udyam {mask_identifier(u_num)} confirmed in mock Udyam registry",
                )
            )

    # -------------------------------------------------------------------------
    # Check 4: Legal / Trade Name Match between GST and Udyam
    # -------------------------------------------------------------------------
    name_mismatch = False
    if gst_doc and udyam_doc and gst_doc.get("ocr_success") and udyam_doc.get("ocr_success"):
        gst_trade = gst_doc.get("trade_name") or ""
        gst_legal = gst_doc.get("legal_name") or ""
        udyam_ent = udyam_doc.get("enterprise_name") or ""
        
        norm_gst_trade = normalize_business_name(gst_trade)
        norm_gst_legal = normalize_business_name(gst_legal)
        norm_udyam = normalize_business_name(udyam_ent)

        # Check for conflicting trade clause inside legal name e.g. "Neha Banerjee (Prop. Shri Physio Clinic)"
        prop_clause_match = re.search(r"prop\.?\s*([^)]+)\)?", gst_legal, re.IGNORECASE)
        prop_entity_name = normalize_business_name(prop_clause_match.group(1)) if prop_clause_match else None
        
        name_matched = False
        if fuzzy_match(norm_gst_trade, norm_udyam) or fuzzy_match(norm_gst_legal, norm_udyam):
            name_matched = True

        # If GST legal explicitly specifies a contradictory trade name (e.g. Shri Physio Clinic vs Neelgiri)
        if prop_entity_name and (not fuzzy_match(prop_entity_name, norm_udyam, threshold=0.85) or not brand_token_match(prop_entity_name, norm_udyam)):
            checks.append(
                CheckResult(
                    check_name="Business Name Consistency (GST vs Udyam)",
                    passed=False,
                    details=f"Name mismatch: GST Legal specifies '{prop_clause_match.group(1).strip()}' while Udyam is '{udyam_ent}'",
                )
            )
            summary_reasons.append(f"Business name mismatch between GST ('{prop_clause_match.group(1).strip()}') and Udyam ('{udyam_ent}')")
            name_mismatch = True
        elif name_matched:
            checks.append(
                CheckResult(
                    check_name="Business Name Consistency (GST vs Udyam)",
                    passed=True,
                    details=f"Matched: '{gst_trade or gst_legal}' ~ '{udyam_ent}'",
                )
            )
        else:
            checks.append(
                CheckResult(
                    check_name="Business Name Consistency (GST vs Udyam)",
                    passed=False,
                    details=f"Name mismatch: GST ('{gst_trade or gst_legal}') does not match Udyam ('{udyam_ent}')",
                )
            )
            summary_reasons.append(f"Business name mismatch: GST '{gst_trade or gst_legal}' vs Udyam '{udyam_ent}'")
            name_mismatch = True
    else:
        checks.append(
            CheckResult(
                check_name="Business Name Consistency (GST vs Udyam)",
                passed=False,
                details="Could not compare business names due to missing document(s)",
            )
        )

    # -------------------------------------------------------------------------
    # Check 5: Authorised Signatory Name vs Proprietor / Legal Name
    # -------------------------------------------------------------------------
    if sig_doc and gst_doc and gst_doc.get("ocr_success"):
        sig_name = sig_doc.get("signatory_name") or ""
        gst_legal = gst_doc.get("legal_name") or ""
        prop_name = extract_proprietor_name(gst_legal) or ""
        
        const = (gst_doc.get("constitution") or "").lower()
        if "proprietor" in const:
            if fuzzy_match(sig_name, prop_name, threshold=0.70):
                checks.append(
                    CheckResult(
                        check_name="Signatory Authority Validation",
                        passed=True,
                        details=f"Signatory '{sig_name}' matches registered proprietor '{prop_name}'",
                    )
                )
            else:
                checks.append(
                    CheckResult(
                        check_name="Signatory Authority Validation",
                        passed=False,
                        details=f"Signatory '{sig_name}' does not match registered proprietor '{prop_name}'",
                    )
                )
                summary_reasons.append(f"Signatory '{sig_name}' does not match registered proprietor '{prop_name}'")
        else:
            # Pvt Ltd / LLP
            desig = (sig_doc.get("designation") or "").lower()
            allowed_desigs = ["director", "partner", "manager", "owner", "authorized signatory", "authorised signatory"]
            if any(d in desig for d in allowed_desigs):
                checks.append(
                    CheckResult(
                        check_name="Signatory Authority Validation",
                        passed=True,
                        details=f"Authorized signatory '{sig_name}' holds valid role '{sig_doc.get('designation')}'",
                    )
                )
            else:
                checks.append(
                    CheckResult(
                        check_name="Signatory Authority Validation",
                        passed=False,
                        details=f"Signatory role '{sig_doc.get('designation')}' not recognized as authorized",
                    )
                )
                summary_reasons.append(f"Signatory '{sig_name}' lacks recognized corporate authorization")
    else:
        checks.append(
            CheckResult(
                check_name="Signatory Authority Validation",
                passed=False,
                details="Could not verify signatory due to missing document(s)",
            )
        )

    # -------------------------------------------------------------------------
    # Check 6: Signatory ID Expiry Date (Relative to 2026-07-15)
    # -------------------------------------------------------------------------
    id_expired = False
    if sig_doc and sig_doc.get("valid_till"):
        try:
            valid_till = datetime.date.fromisoformat(sig_doc["valid_till"])
            if valid_till >= TODAY:
                checks.append(
                    CheckResult(
                        check_name="Signatory ID Validity & Expiry",
                        passed=True,
                        details=f"ID valid till {valid_till} (active as of assessment date {TODAY})",
                    )
                )
            else:
                checks.append(
                    CheckResult(
                        check_name="Signatory ID Validity & Expiry",
                        passed=False,
                        details=f"Signatory ID expired on {valid_till} (assessment date {TODAY})",
                    )
                )
                summary_reasons.append(f"Signatory ID is expired ({valid_till})")
                id_expired = True
        except ValueError:
            checks.append(
                CheckResult(
                    check_name="Signatory ID Validity & Expiry",
                    passed=False,
                    details=f"Invalid date format in signatory ID: {sig_doc['valid_till']}",
                )
            )
    else:
        checks.append(
            CheckResult(
                check_name="Signatory ID Validity & Expiry",
                passed=False,
                details="Missing signatory ID document or validity date",
            )
        )

    # -------------------------------------------------------------------------
    # Check 7: Address Proof Recency (<= 90 days from 2026-07-15)
    # -------------------------------------------------------------------------
    proof_stale = False
    if addr_doc and addr_doc.get("bill_date"):
        try:
            bill_date = datetime.date.fromisoformat(addr_doc["bill_date"])
            age_days = (TODAY - bill_date).days
            if 0 <= age_days <= MAX_ADDRESS_PROOF_AGE_DAYS:
                checks.append(
                    CheckResult(
                        check_name="Address Proof Recency (<= 90 Days)",
                        passed=True,
                        details=f"Bill dated {bill_date} ({age_days} days old, within 90-day DPDP compliance window)",
                    )
                )
            elif age_days < 0:
                checks.append(
                    CheckResult(
                        check_name="Address Proof Recency (<= 90 Days)",
                        passed=False,
                        details=f"Future-dated utility bill detected ({bill_date})",
                    )
                )
                summary_reasons.append(f"Invalid future-dated utility bill ({bill_date})")
                proof_stale = True
            else:
                checks.append(
                    CheckResult(
                        check_name="Address Proof Recency (<= 90 Days)",
                        passed=False,
                        details=f"Stale utility bill dated {bill_date} ({age_days} days old, exceeds 90-day limit)",
                    )
                )
                summary_reasons.append(f"Stale address proof: Utility bill is {age_days} days old (dated {bill_date}, max 90 days allowed)")
                proof_stale = True
        except ValueError:
            checks.append(
                CheckResult(
                    check_name="Address Proof Recency (<= 90 Days)",
                    passed=False,
                    details=f"Invalid date format in utility bill: {addr_doc['bill_date']}",
                )
            )
    else:
        checks.append(
            CheckResult(
                check_name="Address Proof Recency (<= 90 Days)",
                passed=False,
                details="Missing utility bill address proof or bill date",
            )
        )

    # -------------------------------------------------------------------------
    # Check 8: Address Consistency (Utility Bill vs GST Principal Address)
    # -------------------------------------------------------------------------
    if addr_doc and gst_doc and gst_doc.get("address"):
        bill_addr = addr_doc.get("supply_address") or ""
        gst_addr = gst_doc.get("address") or ""
        
        pin_bill = addr_doc.get("pin_code") or extract_pincode(bill_addr)
        pin_gst = extract_pincode(gst_addr)

        if pin_bill and pin_gst and pin_bill == pin_gst:
            checks.append(
                CheckResult(
                    check_name="Address Consistency (Proof vs GST)",
                    passed=True,
                    details=f"Address verified with matching PIN code {pin_bill}",
                )
            )
        elif fuzzy_match(bill_addr, gst_addr, threshold=0.55):
            checks.append(
                CheckResult(
                    check_name="Address Consistency (Proof vs GST)",
                    passed=True,
                    details="Premises address location matches GST principal place of business",
                )
            )
        else:
            checks.append(
                CheckResult(
                    check_name="Address Consistency (Proof vs GST)",
                    passed=False,
                    details=f"Address mismatch: Bill PIN ({pin_bill or 'None'}) vs GST PIN ({pin_gst or 'None'})",
                )
            )
            summary_reasons.append(f"Address mismatch between utility bill and GST registration")
    else:
        checks.append(
            CheckResult(
                check_name="Address Consistency (Proof vs GST)",
                passed=False,
                details="Could not verify address match due to missing address data",
            )
        )

    # -------------------------------------------------------------------------
    # Decision Logic: APPROVED, REJECTED, or MANUAL REVIEW
    # -------------------------------------------------------------------------
    all_passed = all(c.passed for c in checks)
    
    if all_passed:
        decision = "APPROVED"
        summary_reasons.append("All 8 compliance and verification checks passed successfully")
    elif gst_cancelled or proof_stale or name_mismatch or id_expired:
        decision = "REJECTED"
    else:
        # Missing documents (e.g. K05) or OCR unreadable/corrupted (e.g. K04)
        decision = "MANUAL REVIEW"

    # Masked identifiers for security and DPDP compliance
    extracted_summary = {
        "gstin": mask_identifier(gst_doc.get("corrected_gstin") or gst_doc.get("raw_gstin")) if gst_doc else None,
        "udyam_number": mask_identifier(udyam_doc.get("corrected_udyam") or udyam_doc.get("raw_udyam")) if udyam_doc else None,
        "signatory_name": sig_doc.get("signatory_name") if sig_doc else None,
        "signatory_id": sig_doc.get("id_number") if sig_doc else None,
        "signatory_valid_till": sig_doc.get("valid_till") if sig_doc else None,
        "bill_date": addr_doc.get("bill_date") if addr_doc else None,
        "bill_address": addr_doc.get("supply_address") if addr_doc else None,
        "pin_code": addr_doc.get("pin_code") if addr_doc else None,
    }

    return KYCVerificationResult(
        applicant_id=applicant_id,
        decision=decision,
        checks=checks,
        extracted_fields=extracted_summary,
        summary_reasons=summary_reasons,
        ocr_corrections=ocr_corrections,
        ocr_failures=ocr_failures,
    )
