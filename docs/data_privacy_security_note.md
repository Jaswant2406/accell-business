# Accel Business — Data Privacy & Security Note
**Enterprise Track A: Autonomous SMB Digital Onboarding** • Document ID: `AB-SEC-DPDP-2026-V1` • Date: 2026-07-15 • Status: Active Evaluation

---

### 1. Privacy by Design & Purpose Limitation
Accel Business adheres to the principle of data minimisation under the Digital Personal Data Protection (DPDP) framework. The platform collects only operational data (business size, site count, location, telecom needs) and statutory identifiers (GSTIN, Udyam) necessary for network feasibility and Customer Due Diligence (CDD) under Department of Telecommunications (DoT) mandates. Prior to KYC document ingestion, an affirmative statutory consent gate presents the specified purpose, data categories, 30-day rejection retention schedule, and Data Protection Officer contact (`grievance-officer@accelbusiness.in`).

### 2. Sensitive Data Handling & Local OCR Processing
Statutory identity documents (GST, Udyam, Signatory ID, Address Proof) uploaded via the browser are decoded directly in-memory via OpenCV (`imdecode`) and are never written to disk. Specimen test documents (`K01`–`K12`) are stored locally as static benchmarks. Character extraction is executed locally via Tesseract OCR (`tesseract.exe`), with zero transmission to cloud vision APIs. Sensitive identifiers are masked across the user interface and application logs (`mask_identifier()`), displaying only the last 4 digits of Aadhaar/GSTIN and tokenized Udyam formats.

### 3. Application Security & Guardrails
- **Input Guardrails**: `engine/guardrails.py` clamps numeric boundaries before widget creation (1 to 10,000 employees; 1 to 500 sites; budget &le; &#8377;10,00,000), rejecting hallucinated products and non-catalogue prices.
- **Upload Hardening**: File uploaders enforce MIME/extension whitelisting (`.png`, `.jpg`, `.jpeg`), a 10MB ceiling, empty-file rejection, and image-decoding validation.
- **Session & Secret Hygiene**: State is isolated per session in `st.session_state`. Secrets (`GEMINI_API_KEY`) reside in `.env`, strictly quarantined by `.gitignore`. Streamlit browser telemetry is explicitly disabled (`gatherUsageStats = false`).

### 4. External Integration Boundaries
- **Google Gemini API** `[IMPLEMENTED • OPTIONAL]`: Optional AI requirement extraction (default OFF). Transmits only raw requirements text over IPv4 (`0.0.0.0`) with a 10s hard timeout; zero document or biometric data is shared.
- **Tesseract OCR** `[IMPLEMENTED • LOCAL]`: Localhost binary invocation; zero outbound network activity.
- **Statutory Registries** `[SIMULATED • LOCAL MOCK]`: Fast local lookup against mock CSV datasets with algorithmic Luhn-mod-36 checksum verification.
- **Payment Mandate & Telecom BSS** `[SIMULATED]`: UI-simulated e-NACH/UPI mandate and 5-stage provisioning state machine; no live banking credentials are held.

### 5. Indian Data Protection Considerations
The architecture aligns with the principles of the **Digital Personal Data Protection Act, 2023** and **DPDP Rules, 2025** draft standards: purpose specification, notice, affirmative consent, and reasonable safeguards (local processing, PII masking). *This note reflects technical alignment and does not constitute formal legal certification.*

### 6. Limitations & Future Improvements
1. **Encryption at Rest** `[PLANNED]`: `data/orders.json` is currently stored as plaintext JSON; AES-256 field encryption is required for production.
2. **Access Control (RBAC)** `[PLANNED]`: No role segregation between subscriber onboarding and the compliance audit desk.
3. **Automated Lifecycle Purge** `[PLANNED]`: The 30-day unactivated document purge policy currently requires an automated background worker.
4. **Production Integrations** `[PLANNED]`: Integration with live GSTN/MCA portals, Digilocker, and NPCI e-Mandate gateways.

---
*Classification: Internal Evaluation • Accel Business — Autonomous SMB Onboarding • Single-Page Statutory Brief*
