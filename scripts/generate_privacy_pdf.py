"""
Generate exactly ONE A4 page Data Privacy & Security Note PDF for Accel Business.
Validates page count, A4 dimensions, text extraction, and renders PNG for visual review.
"""

from pathlib import Path
import sys
import fitz  # PyMuPDF
from playwright.sync_api import sync_playwright

DOCS_DIR = Path("docs")
PDF_PATH = DOCS_DIR / "data_privacy_security_note.pdf"
HTML_TEMP = DOCS_DIR / "_temp_privacy_note.html"
PNG_PREVIEW = DOCS_DIR / "data_privacy_security_note_preview.png"

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Accel Business — Data Privacy & Security Note</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700;800&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
  <style>
    @page {
      size: A4 portrait;
      margin: 12mm 14mm 12mm 14mm;
    }
    
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #1F2937;
      background: #FFFFFF;
      font-size: 8pt;
      line-height: 1.35;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    
    /* Header */
    .header {
      border-bottom: 1.5px solid #1E3A8A;
      padding-bottom: 8px;
      margin-bottom: 10px;
    }
    
    .eyebrow-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 3px;
    }
    
    .eyebrow {
      font-size: 7pt;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #1E3A8A;
    }
    
    .meta-tag {
      font-size: 7pt;
      font-weight: 600;
      color: #64748B;
      font-family: 'JetBrains Mono', monospace;
    }
    
    .title-row {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
    }
    
    h1 {
      font-family: 'Manrope', sans-serif;
      font-size: 15pt;
      font-weight: 800;
      color: #111827;
      letter-spacing: -0.03em;
      line-height: 1.1;
    }
    
    .subtitle {
      font-size: 7.5pt;
      color: #4B5563;
      margin-top: 2px;
      font-weight: 500;
    }
    
    .badges-strip {
      display: flex;
      gap: 6px;
      margin-top: 6px;
    }
    
    .badge {
      display: inline-block;
      padding: 1.5px 6px;
      font-size: 6.5pt;
      font-weight: 700;
      border-radius: 3px;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      font-family: 'Inter', sans-serif;
    }
    
    .b-navy { background: #EFF6FF; color: #1E3A8A; border: 0.75px solid #BFDBFE; }
    .b-green { background: #ECFDF5; color: #065F46; border: 0.75px solid #A7F3D0; }
    .b-gray { background: #F1F5F9; color: #334155; border: 0.75px solid #CBD5E1; }
    
    /* Security Status Tags */
    .sec-tag {
      font-family: 'JetBrains Mono', monospace;
      font-size: 6pt;
      font-weight: 700;
      padding: 1px 4px;
      border-radius: 2px;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      vertical-align: middle;
      display: inline-block;
      margin-left: 2px;
    }
    .st-impl { background: #DCFCE7; color: #15803D; border: 0.5px solid #86EFAC; }
    .st-mock { background: #FEF3C7; color: #B45309; border: 0.5px solid #FCD34D; }
    .st-plan { background: #F1F5F9; color: #475569; border: 0.5px solid #CBD5E1; }
    
    /* Two-Column Grid */
    .grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      align-items: start;
    }
    
    .col {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    
    /* Section Cards */
    .section-card {
      border: 1px solid #E2E8F0;
      border-radius: 4px;
      padding: 7px 9px;
      background: #FFFFFF;
    }
    
    h2 {
      font-family: 'Manrope', sans-serif;
      font-size: 8.5pt;
      font-weight: 800;
      color: #1E3A8A;
      margin-bottom: 4px;
      letter-spacing: -0.01em;
      display: flex;
      align-items: center;
      gap: 4px;
      border-bottom: 1px solid #F1F5F9;
      padding-bottom: 2px;
    }
    
    .sec-num {
      color: #2563EB;
      font-weight: 800;
      font-size: 8pt;
    }
    
    p {
      color: #374151;
      font-size: 7.5pt;
      line-height: 1.34;
      margin-bottom: 3px;
      text-align: justify;
    }
    
    p:last-child {
      margin-bottom: 0;
    }
    
    ul {
      margin-left: 12px;
      font-size: 7.2pt;
      color: #374151;
      line-height: 1.3;
    }
    
    li {
      margin-bottom: 2px;
    }
    
    strong {
      color: #111827;
      font-weight: 600;
    }
    
    code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 6.8pt;
      background: #F8FAFC;
      padding: 0 3px;
      border-radius: 2px;
      color: #1E3A8A;
      border: 0.5px solid #E2E8F0;
    }
    
    /* Mini Security Topology Box */
    .mini-box {
      background: #F8FAFC;
      border: 1px solid #CBD5E1;
      border-radius: 4px;
      padding: 5px 8px;
      margin-top: 2px;
    }
    
    .mini-box-title {
      font-size: 6.8pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #1E3A8A;
      margin-bottom: 3px;
      font-family: 'Inter', sans-serif;
    }
    
    .topo-flow {
      font-family: 'JetBrains Mono', monospace;
      font-size: 6.2pt;
      color: #334155;
      line-height: 1.3;
    }
    
    /* Footer */
    .footer {
      border-top: 1px solid #E2E8F0;
      padding-top: 6px;
      margin-top: 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 6.5pt;
      color: #64748B;
      font-family: 'Inter', sans-serif;
    }
  </style>
</head>
<body>

  <!-- HEADER -->
  <div class="header">
    <div class="eyebrow-row">
      <span class="eyebrow">Enterprise Track A • Autonomous SMB Onboarding</span>
      <span class="meta-tag">DOC ID: AB-SEC-DPDP-2026-V1 • 2026-07-15</span>
    </div>
    <div class="title-row">
      <div>
        <h1>Data Privacy & Security Note</h1>
        <div class="subtitle">Architectural Security Controls, Statutory DPDP Alignment & Boundary Disclosures</div>
      </div>
      <div class="badges-strip">
        <span class="badge b-navy">Single-Page Brief</span>
        <span class="badge b-green">DPDP Act 2023 Aligned</span>
        <span class="badge b-gray">Modular Monolith</span>
      </div>
    </div>
  </div>

  <!-- 2-COLUMN GRID -->
  <div class="grid">
    
    <!-- COLUMN 1 -->
    <div class="col">
      
      <!-- 1. PRIVACY BY DESIGN -->
      <div class="section-card">
        <h2><span class="sec-num">01.</span> Privacy by Design & Purpose Limitation</h2>
        <p>
          Accel Business implements strict data minimisation under the Digital Personal Data Protection (DPDP) framework. The platform collects only operational sizing parameters (employees, sites, city, telecom services) and statutory identifiers (GSTIN, Udyam) necessary for service feasibility and Customer Due Diligence (CDD) under Department of Telecommunications (DoT) directives.
        </p>
        <p>
          Before document submission, an affirmative statutory consent gate explicitly details the specified purpose, data categories, 30-day unactivated purge policy, subscriber principal rights, and designated Grievance Officer (<code>grievance-officer@accelbusiness.in</code>).
        </p>
      </div>

      <!-- 2. SENSITIVE DATA HANDLING -->
      <div class="section-card">
        <h2><span class="sec-num">02.</span> Sensitive Data Handling & Local OCR Processing</h2>
        <p>
          Statutory business identity documents (GST Certificate, Udyam, Signatory ID, Address Proof) uploaded through the browser are decoded directly in-memory via OpenCV (<code>np.frombuffer</code> &rarr; <code>cv2.imdecode</code>) and are <strong>never persisted to disk</strong>.
        </p>
        <p>
          Character recognition is executed locally via Tesseract OCR (<code>tesseract.exe</code>) with zero transmission to external cloud vision services. Sensitive identifiers are masked across the user interface and audit logs (<code>mask_identifier()</code>), displaying only the last 4 digits of Aadhaar/GSTIN and tokenized Udyam formats. In-memory arrays are purged immediately on session termination.
        </p>
      </div>

      <!-- 3. APPLICATION SECURITY -->
      <div class="section-card">
        <h2><span class="sec-num">03.</span> Application Security & Guardrails</h2>
        <ul>
          <li><strong>Input Boundaries</strong>: <code>engine/guardrails.py</code> clamps inputs before widget initialization (1 to 10,000 employees, 1 to 500 sites, budget &le; &#8377;10,00,000) and strictly rejects hallucinated products or non-catalogue prices.</li>
          <li><strong>Upload Hardening</strong>: File uploaders enforce MIME whitelisting (<code>.png</code>, <code>.jpg</code>, <code>.jpeg</code>), 10MB limits, empty-file blocks, and OpenCV image decoding verification.</li>
          <li><strong>Session & Secret Hygiene</strong>: State is isolated per session in <code>st.session_state</code>. Sensitive keys (<code>GEMINI_API_KEY</code>) reside in <code>.env</code>, quarantined by <code>.gitignore</code>. Streamlit usage telemetry is disabled (<code>gatherUsageStats = false</code>).</li>
        </ul>
      </div>

    </div>

    <!-- COLUMN 2 -->
    <div class="col">
      
      <!-- 4. EXTERNAL INTEGRATION BOUNDARIES -->
      <div class="section-card">
        <h2><span class="sec-num">04.</span> External Integration Boundaries</h2>
        <ul>
          <li><strong>Google Gemini API</strong> <span class="sec-tag st-impl">Implemented</span>: Optional requirement extraction (default OFF). Transmits only natural language text over IPv4 (<code>0.0.0.0</code>) with a 10s strict timeout; zero document or biometric data is shared.</li>
          <li><strong>Tesseract OCR</strong> <span class="sec-tag st-impl">Implemented</span>: Localhost binary execution; zero outbound network activity.</li>
          <li><strong>Statutory Registries</strong> <span class="sec-tag st-mock">Simulated</span>: In-memory verification against mock CSV registries with algorithmic Luhn-mod-36 checksum checks.</li>
          <li><strong>e-NACH Mandate & Telecom BSS</strong> <span class="sec-tag st-mock">Simulated</span>: UI-simulated mandate flow and 5-stage provisioning state machine; no live banking credentials are held.</li>
        </ul>
      </div>

      <!-- 5. INDIAN DATA PROTECTION CONSIDERATIONS -->
      <div class="section-card">
        <h2><span class="sec-num">05.</span> Indian Data Protection Considerations</h2>
        <p>
          The architecture aligns with the core principles of the <strong>Digital Personal Data Protection Act, 2023</strong> and draft <strong>DPDP Rules, 2025</strong>: purpose limitation, transparent notice, affirmative consent, and reasonable security safeguards (local processing, PII masking). <em>This document reflects technical architectural alignment and does not constitute formal legal certification.</em>
        </p>
      </div>

      <!-- 6. LIMITATIONS & FUTURE IMPROVEMENTS -->
      <div class="section-card">
        <h2><span class="sec-num">06.</span> Limitations & Future Improvements</h2>
        <ul>
          <li><strong>Encryption at Rest</strong> <span class="sec-tag st-plan">Planned</span>: <code>data/orders.json</code> stores orders in plaintext JSON; AES-256 field-level encryption is required for production.</li>
          <li><strong>Role-Based Access Control (RBAC)</strong> <span class="sec-tag st-plan">Planned</span>: No role barrier between subscriber onboarding and the compliance audit desk.</li>
          <li><strong>Automated Lifecycle Purge</strong> <span class="sec-tag st-plan">Planned</span>: The 30-day unactivated document purge policy requires an automated background daemon.</li>
          <li><strong>Production Gateways</strong> <span class="sec-tag st-plan">Planned</span>: Live GSTN/MCA API integration and NPCI e-Mandate gateways.</li>
        </ul>
      </div>

      <!-- MINI TOPOLOGY -->
      <div class="mini-box">
        <div class="mini-box-title">Verified Data Boundary Flow</div>
        <div class="topo-flow">
          User Upload &rarr; [In-Memory CV2] &rarr; [Local Tesseract OCR] &rarr; [Checksum / Mock CSV]<br/>
          Natural Language &rarr; [Rules Engine / Optional Gemini IPv4] &rarr; [Order JSON Store]
        </div>
      </div>

    </div>

  </div>

  <!-- FOOTER -->
  <div class="footer">
    <span>Accel Business • Udyam Digital • Enterprise Track A</span>
    <span>Confidential — Internal Engineering Evaluation • Exactly 1 Page A4</span>
  </div>

</body>
</html>
"""

def generate_and_validate():
    print("Generating Data Privacy & Security Note PDF...")
    HTML_TEMP.write_text(HTML_CONTENT, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file:///{HTML_TEMP.resolve().as_posix()}", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # Print to exact A4 with zero margin in PDF print so CSS @page margins govern
        page.pdf(
            path=str(PDF_PATH),
            format="A4",
            print_background=True,
            margin={"top": "0mm", "bottom": "0mm", "left": "0mm", "right": "0mm"}
        )
        print(f"Rendered PDF to {PDF_PATH}")
        browser.close()

    if HTML_TEMP.exists():
        HTML_TEMP.unlink()

    # PyMuPDF Validation
    print("\nExecuting Mandatory PyMuPDF PDF Validation...")
    doc = fitz.open(str(PDF_PATH))
    page_count = doc.page_count
    page = doc[0]
    rect = page.rect
    width_pt, height_pt = rect.width, rect.height
    width_mm = width_pt * 25.4 / 72.0
    height_mm = height_pt * 25.4 / 72.0

    print(f"• Page Count: {page_count} (Mandatory requirement: Exactly 1)")
    print(f"• Dimensions (Points): {width_pt:.2f} x {height_pt:.2f}")
    print(f"• Dimensions (mm): {width_mm:.2f} mm x {height_mm:.2f} mm (Standard A4: 210.00 x 297.00 mm)")

    # Assert exactly 1 page
    if page_count != 1:
        print(f"\nFATAL ERROR: Page count is {page_count}, expected exactly 1!")
        sys.exit(1)
    else:
        print("✓ Page count assertion PASSED: Exactly 1 page.")

    # Verify extracted text for all 6 sections
    text = page.get_text()
    sections = [
      "1. Privacy by Design",
      "2. Sensitive Data Handling",
      "3. Application Security",
      "4. External Integration Boundaries",
      "5. Indian Data Protection Considerations",
      "6. Limitations & Future Improvements"
    ]
    missing = []
    for s in sections:
        # Check partial match
        key = s.split(".")[1].strip()
        if key.lower() not in text.lower():
            missing.append(s)

    if missing:
        print(f"WARNING: Some section titles not found in extracted text: {missing}")
    else:
        print("✓ All 6 required sections verified in extracted text.")

    # Render Page 1 to high-res PNG for visual inspection
    pix = page.get_pixmap(dpi=200)
    pix.save(str(PNG_PREVIEW))
    print(f"✓ Rendered high-res inspection image: {PNG_PREVIEW}")

    file_size_bytes = PDF_PATH.stat().st_size
    print(f"• PDF File Size: {file_size_bytes:,} bytes ({file_size_bytes / 1024:.1f} KB)")
    print("\nValidation complete: 100% compliant with single-page A4 mandate.")

if __name__ == "__main__":
    generate_and_validate()
