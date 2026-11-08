"""Script to run KYC pipeline across all 12 applicants and write docs/kyc_results.md."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import cv2

from kyc.ocr import (
    extract_address_proof_fields,
    extract_gst_certificate_fields,
    extract_signatory_id_fields,
    extract_udyam_certificate_fields,
    mask_identifier,
)
from kyc.validators import validate_applicant_kyc


def main():
    docs_dir = Path("data/kyc_documents")
    lines = [
        "# Smart KYC Verification Report: Specimen Applicants K01 - K12\n\n",
        "**Evaluation Reference Date:** `2026-07-15` (per ground rules)\n\n",
        "## 1. Executive Summary Table\n\n",
        "| Applicant | Decision | Checks Passed | Matched GSTIN (Masked) | Matched Udyam (Masked) | Key Reason / Audit Trail |\n",
        "|:---:|:---:|:---:|:---:|:---:|:---|\n",
    ]

    details = ["\n---\n\n## 2. In-Depth Per-Applicant Verification Audit\n"]

    for i in range(1, 13):
        app_id = f"K{i:02d}"
        gst_p = docs_dir / f"{app_id}_gst_certificate.png"
        u_p = docs_dir / f"{app_id}_udyam_certificate.png"
        sig_p = docs_dir / f"{app_id}_signatory_id.png"
        addr_p = docs_dir / f"{app_id}_address_proof.png"

        gst_f = extract_gst_certificate_fields(cv2.imread(str(gst_p))) if gst_p.exists() else None
        u_f = extract_udyam_certificate_fields(cv2.imread(str(u_p))) if u_p.exists() else None
        sig_f = extract_signatory_id_fields(cv2.imread(str(sig_p))) if sig_p.exists() else None
        addr_f = extract_address_proof_fields(cv2.imread(str(addr_p))) if addr_p.exists() else None

        res = validate_applicant_kyc(
            app_id,
            {
                "gst_certificate": gst_f,
                "udyam_certificate": u_f,
                "signatory_id": sig_f,
                "address_proof": addr_f,
            },
        )
        passed = sum(1 for c in res.checks if c.passed)
        gst_val = mask_identifier(gst_f.get("corrected_gstin")) if (gst_f and gst_f.get("corrected_gstin")) else "N/A"
        ud_val = mask_identifier(u_f.get("corrected_udyam")) if (u_f and u_f.get("corrected_udyam")) else "N/A"
        audit_note = "; ".join(res.summary_reasons)

        icon = "🟢" if res.decision == "APPROVED" else ("🟡" if res.decision == "MANUAL REVIEW" else "🔴")
        lines.append(f"| **{app_id}** | `{res.decision}` | {passed}/8 | `{gst_val}` | `{ud_val}` | {audit_note} |\n")

        details.append(f"\n### {icon} Applicant {app_id}: {res.decision}\n\n")
        details.append(f"- **Checks Passed:** {passed} of 8\n")
        if gst_f:
            raw_gst = mask_identifier(gst_f.get("raw_gstin"))
            rec = gst_f.get("registry_record")
            trade_show = (rec.get("trade_name") if rec else None) or gst_f.get("trade_name") or "Unknown"
            legal_show = (rec.get("legal_name") if rec else None) or gst_f.get("legal_name") or "Unknown"
            details.append(f"- **GSTIN:** Raw `{raw_gst}` -> Matched `{gst_val}` ({gst_f.get('ocr_note')})\n")
            details.append(f"- **GST Trade / Legal:** {trade_show} / {legal_show}\n")
        if u_f:
            raw_u = mask_identifier(u_f.get("raw_udyam"))
            details.append(f"- **Udyam:** Raw `{raw_u}` -> Matched `{ud_val}` ({u_f.get('ocr_note')})\n")
            details.append(f"- **Enterprise Name:** {u_f.get('enterprise_name') or 'N/A'}\n")
        if sig_f:
            sig_name = sig_f.get("signatory_name") or "N/A"
            sig_expiry = sig_f.get("valid_till") or "N/A"
            details.append(f"- **Signatory ID:** {sig_name} (Valid till: {sig_expiry})\n")
        if addr_f:
            import re
            pin_m = re.search(r'\b\d{6}\b', addr_f.get("supply_address") or "")
            pin_str = pin_m.group(0) if pin_m else "N/A"
            details.append(f"- **Address Proof Date:** {addr_f.get('bill_date') or 'N/A'} | **PIN:** {pin_str}\n")

        details.append("\n**Compliance Check Matrix:**\n")
        details.append("| Check | Result | Details |\n|:---|:---:|:---|\n")
        for c in res.checks:
            status_badge = "**PASS**" if c.passed else "**FAIL**"
            details.append(f"| {c.check_name} | {status_badge} | {c.details} |\n")

    Path("docs/kyc_results.md").write_text("".join(lines) + "".join(details), encoding="utf-8")
    print("Updated docs/kyc_results.md successfully.")


if __name__ == "__main__":
    main()
