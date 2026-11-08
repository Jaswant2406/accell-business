# Smart KYC Verification Report: Specimen Applicants K01 - K12

**Evaluation Reference Date:** `2026-07-15` (per ground rules)

## 1. Executive Summary Table

| Applicant | Decision | Checks Passed | Matched GSTIN (Masked) | Matched Udyam (Masked) | Key Reason / Audit Trail |
|:---:|:---:|:---:|:---:|:---:|:---|
| **K01** | `REJECTED` | 5/8 | `37XXXXXXXXXX1ZS` | `N/A` | GSTIN registration status is Cancelled (Active required); Missing or unreadable Udyam registration certificate |
| **K02** | `APPROVED` | 8/8 | `19XXXXXXXXXX1ZL` | `UDYAM-**-00-****330` | All 8 compliance and verification checks passed successfully |
| **K03** | `APPROVED` | 8/8 | `27XXXXXXXXXX1ZP` | `UDYAM-**-00-****696` | All 8 compliance and verification checks passed successfully |
| **K04** | `MANUAL REVIEW` | 4/8 | `N/A` | `UDYAM-**-00-****836` | Unreadable or missing GST Certificate |
| **K05** | `MANUAL REVIEW` | 5/8 | `32XXXXXXXXXX1Z1` | `N/A` | Incomplete submission: Missing Udyam Certificate; Missing or unreadable Udyam registration certificate |
| **K06** | `MANUAL REVIEW` | 7/8 | `O8XXXXXXXXXX1Z0` | `UDYAM-**-00-****157` | GSTIN on document does not match registry |
| **K07** | `REJECTED` | 7/8 | `07XXXXXXXXXX1ZT` | `UDYAM-**-00-****547` | Business name mismatch between GST ('Shri Physio Clinic') and Udyam ('Neelgiri Physio Clinic') |
| **K08** | `APPROVED` | 8/8 | `24XXXXXXXXXX1Z3` | `UDYAM-**-00-****445` | All 8 compliance and verification checks passed successfully |
| **K09** | `APPROVED` | 8/8 | `37XXXXXXXXXX1ZB` | `UDYAM-**-00-****562` | All 8 compliance and verification checks passed successfully |
| **K10** | `APPROVED` | 8/8 | `27XXXXXXXXXX1ZL` | `UDYAM-**-00-****141` | All 8 compliance and verification checks passed successfully |
| **K11** | `REJECTED` | 7/8 | `03XXXXXXXXXX1ZZ` | `UDYAM-**-00-****478` | Stale address proof: Utility bill is 257 days old (dated 2025-10-31, max 90 days allowed) |
| **K12** | `APPROVED` | 8/8 | `37XXXXXXXXXX1ZU` | `UDYAM-**-00-****772` | All 8 compliance and verification checks passed successfully |

---

## 2. In-Depth Per-Applicant Verification Audit

### 🔴 Applicant K01: REJECTED

- **Checks Passed:** 5 of 8
- **GSTIN:** Raw `37XXXXXXXXXX1ZS` -> Matched `37XXXXXXXXXX1ZS` (Exact registry match)
- **GST Trade / Legal:** Vindhya Tours & Travels / Neha Kaur (Prop. Vindhya Tours & Travels)
- **Udyam:** Raw `N/A` -> Matched `N/A` (Udyam registration number not detected)
- **Enterprise Name:** Vindhya Tours & Travels
- **Signatory ID:** Neha Kaur (Valid till: 2028-03-26)
- **Address Proof Date:** 2026-06-26 | **PIN:** 118383

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **PASS** | All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded |
| GSTIN Format & Registry Validation | **FAIL** | GSTIN 37XXXXXXXXXX1ZS is 'Cancelled' in official registry (Active required) |
| Udyam Registration & Registry Validation | **FAIL** | Udyam certificate could not be read or is missing |
| Business Name Consistency (GST vs Udyam) | **FAIL** | Could not compare business names due to missing document(s) |
| Signatory Authority Validation | **PASS** | Signatory 'Neha Kaur' matches registered proprietor 'Neha Kaur' |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2028-03-26 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **PASS** | Bill dated 2026-06-26 (19 days old, within 90-day DPDP compliance window) |
| Address Consistency (Proof vs GST) | **PASS** | Address verified with matching PIN code 118383 |

### 🟢 Applicant K02: APPROVED

- **Checks Passed:** 8 of 8
- **GSTIN:** Raw `19XXXXXXXXXX1ZL` -> Matched `19XXXXXXXXXX1ZL` (Exact registry match)
- **GST Trade / Legal:** Harmony Dental Care / Joseph Shah (Prop. Harmony Dental Care)
- **Udyam:** Raw `UDYAM-**-00-****330` -> Matched `UDYAM-**-00-****330` (Exact registry match)
- **Enterprise Name:** Harmony Dental Care
- **Signatory ID:** Joseph Shah (Valid till: 2028-09-10)
- **Address Proof Date:** 2026-05-22 | **PIN:** 347550

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **PASS** | All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded |
| GSTIN Format & Registry Validation | **PASS** | Valid GSTIN 19XXXXXXXXXX1ZL confirmed Active in GST registry |
| Udyam Registration & Registry Validation | **PASS** | Valid Udyam UDYAM-**-00-****330 confirmed in mock Udyam registry |
| Business Name Consistency (GST vs Udyam) | **PASS** | Matched: 'Harmony Dental Care' ~ 'Harmony Dental Care' |
| Signatory Authority Validation | **PASS** | Signatory 'Joseph Shah' matches registered proprietor 'Joseph Shah' |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2028-09-10 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **PASS** | Bill dated 2026-05-22 (54 days old, within 90-day DPDP compliance window) |
| Address Consistency (Proof vs GST) | **PASS** | Address verified with matching PIN code 347550 |

### 🟢 Applicant K03: APPROVED

- **Checks Passed:** 8 of 8
- **GSTIN:** Raw `27XXXXXXXXXX1ZP` -> Matched `27XXXXXXXXXX1ZP` (OCR-corrected: 27XXXXXXXXXX1ZP -> 27XXXXXXXXXX1ZP (Substituted 'O' -> '0' at position 8))
- **GST Trade / Legal:** Ganesh Woodcraft / Joseph Singh (Prop. Ganesh Woodcraft)
- **Udyam:** Raw `UDYAM-**-00-****696` -> Matched `UDYAM-**-00-****696` (Exact registry match)
- **Enterprise Name:** Ganesh Woodcraft
- **Signatory ID:** Joseph Singh (Valid till: 2028-07-04)
- **Address Proof Date:** 2026-05-30 | **PIN:** 411231

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **PASS** | All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded |
| GSTIN Format & Registry Validation | **PASS** | Valid GSTIN 27XXXXXXXXXX1ZP confirmed Active in GST registry |
| Udyam Registration & Registry Validation | **PASS** | Valid Udyam UDYAM-**-00-****696 confirmed in mock Udyam registry |
| Business Name Consistency (GST vs Udyam) | **PASS** | Matched: 'Ganesh Woodcraft' ~ 'Ganesh Woodcraft' |
| Signatory Authority Validation | **PASS** | Signatory 'Joseph Singh' matches registered proprietor 'Joseph Singh' |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2028-07-04 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **PASS** | Bill dated 2026-05-30 (46 days old, within 90-day DPDP compliance window) |
| Address Consistency (Proof vs GST) | **PASS** | Address verified with matching PIN code 411231 |

### 🟡 Applicant K04: MANUAL REVIEW

- **Checks Passed:** 4 of 8
- **GSTIN:** Raw `N/A` -> Matched `N/A` (GSTIN not detected)
- **GST Trade / Legal:** Unknown / Unknown
- **Udyam:** Raw `UDYAM-**-00-****836` -> Matched `UDYAM-**-00-****836` (Exact registry match)
- **Enterprise Name:** Saffron Dental Care LLP
- **Signatory ID:** Fatima Pillai (Valid till: 2028-08-03)
- **Address Proof Date:** 2026-05-28 | **PIN:** 137452

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **PASS** | All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded |
| GSTIN Format & Registry Validation | **FAIL** | GST certificate could not be read or is missing |
| Udyam Registration & Registry Validation | **PASS** | Valid Udyam UDYAM-**-00-****836 confirmed in mock Udyam registry |
| Business Name Consistency (GST vs Udyam) | **FAIL** | Could not compare business names due to missing document(s) |
| Signatory Authority Validation | **FAIL** | Could not verify signatory due to missing document(s) |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2028-08-03 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **PASS** | Bill dated 2026-05-28 (48 days old, within 90-day DPDP compliance window) |
| Address Consistency (Proof vs GST) | **FAIL** | Could not verify address match due to missing address data |

### 🟡 Applicant K05: MANUAL REVIEW

- **Checks Passed:** 5 of 8
- **GSTIN:** Raw `32XXXXXXXXXX1Z1` -> Matched `32XXXXXXXXXX1Z1` (Exact registry match)
- **GST Trade / Legal:** Balaji Realty LLP / Balaji Realty LLP
- **Signatory ID:** Anita Shah (Valid till: 2029-09-11)
- **Address Proof Date:** 2026-06-11 | **PIN:** 752083

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **FAIL** | Missing mandatory documents: Udyam Certificate |
| GSTIN Format & Registry Validation | **PASS** | Valid GSTIN 32XXXXXXXXXX1Z1 confirmed Active in GST registry |
| Udyam Registration & Registry Validation | **FAIL** | Udyam certificate could not be read or is missing |
| Business Name Consistency (GST vs Udyam) | **FAIL** | Could not compare business names due to missing document(s) |
| Signatory Authority Validation | **PASS** | Authorized signatory 'Anita Shah' holds valid role 'Owner' |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2029-09-11 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **PASS** | Bill dated 2026-06-11 (34 days old, within 90-day DPDP compliance window) |
| Address Consistency (Proof vs GST) | **PASS** | Premises address location matches GST principal place of business |

### 🟡 Applicant K06: MANUAL REVIEW

- **Checks Passed:** 7 of 8
- **GSTIN:** Raw `O8XXXXXXXXXX1Z0` -> Matched `O8XXXXXXXXXX1Z0` (GSTIN on document does not match registry)
- **GST Trade / Legal:** Saffron Unisex Salon / Pooja Shah (Prop. Saffron Unisex Salon)
- **Udyam:** Raw `UDYAM-**-00-****157` -> Matched `UDYAM-**-00-****157` (Exact registry match)
- **Enterprise Name:** Saffron Unisex Salon
- **Signatory ID:** Pooja Shah (Valid till: 2028-09-15)
- **Address Proof Date:** 2026-06-11 | **PIN:** 194057

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **PASS** | All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded |
| GSTIN Format & Registry Validation | **FAIL** | GSTIN on document does not match registry (O8XXXXXXXXXX1Z0) |
| Udyam Registration & Registry Validation | **PASS** | Valid Udyam UDYAM-**-00-****157 confirmed in mock Udyam registry |
| Business Name Consistency (GST vs Udyam) | **PASS** | Matched: 'Saffron Unisex Salon' ~ 'Saffron Unisex Salon' |
| Signatory Authority Validation | **PASS** | Signatory 'Pooja Shah' matches registered proprietor 'Pooja Shah' |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2028-09-15 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **PASS** | Bill dated 2026-06-11 (34 days old, within 90-day DPDP compliance window) |
| Address Consistency (Proof vs GST) | **PASS** | Address verified with matching PIN code 194057 |

### 🔴 Applicant K07: REJECTED

- **Checks Passed:** 7 of 8
- **GSTIN:** Raw `O7XXXXXXXXXX1ZT` -> Matched `07XXXXXXXXXX1ZT` (OCR-corrected: O7XXXXXXXXXX1ZT -> 07XXXXXXXXXX1ZT (Substituted 'O' -> '0' at position 1, 'O' -> '0' at position 8))
- **GST Trade / Legal:** Neelgiri Physio Clinic / Neha Banerjee (Prop. Neelgiri Physio Clinic)
- **Udyam:** Raw `UDYAM-**-00-****547` -> Matched `UDYAM-**-00-****547` (Exact registry match)
- **Enterprise Name:** Neelgiri Physio Clinic
- **Signatory ID:** Neha Banerjee (Valid till: 2030-05-05)
- **Address Proof Date:** 2026-07-05 | **PIN:** 334596

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **PASS** | All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded |
| GSTIN Format & Registry Validation | **PASS** | Valid GSTIN 07XXXXXXXXXX1ZT confirmed Active in GST registry |
| Udyam Registration & Registry Validation | **PASS** | Valid Udyam UDYAM-**-00-****547 confirmed in mock Udyam registry |
| Business Name Consistency (GST vs Udyam) | **FAIL** | Name mismatch: GST Legal specifies 'Shri Physio Clinic' while Udyam is 'Neelgiri Physio Clinic' |
| Signatory Authority Validation | **PASS** | Signatory 'Neha Banerjee' matches registered proprietor 'Neha Banerjee' |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2030-05-05 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **PASS** | Bill dated 2026-07-05 (10 days old, within 90-day DPDP compliance window) |
| Address Consistency (Proof vs GST) | **PASS** | Address verified with matching PIN code 334596 |

### 🟢 Applicant K08: APPROVED

- **Checks Passed:** 8 of 8
- **GSTIN:** Raw `24XXXXXXXXXX1Z3` -> Matched `24XXXXXXXXXX1Z3` (OCR-corrected: 24XXXXXXXXXX1Z3 -> 24XXXXXXXXXX1Z3 (Substituted '0' -> 'O' at position 4))
- **GST Trade / Legal:** Green Leaf Legal Associates / Joseph Rao (Prop. Green Leaf Legal Associates)
- **Udyam:** Raw `UDYAM-**-00-****445` -> Matched `UDYAM-**-00-****445` (Exact registry match)
- **Enterprise Name:** Green Leaf Legal Associates
- **Signatory ID:** Joseph Rao (Valid till: 2027-09-18)
- **Address Proof Date:** 2026-05-26 | **PIN:** 348176

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **PASS** | All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded |
| GSTIN Format & Registry Validation | **PASS** | Valid GSTIN 24XXXXXXXXXX1Z3 confirmed Active in GST registry |
| Udyam Registration & Registry Validation | **PASS** | Valid Udyam UDYAM-**-00-****445 confirmed in mock Udyam registry |
| Business Name Consistency (GST vs Udyam) | **PASS** | Matched: 'Green Leaf Legal Associates' ~ 'Green Leaf Legal Associates' |
| Signatory Authority Validation | **PASS** | Signatory 'Joseph Rao' matches registered proprietor 'Joseph Rao' |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2027-09-18 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **PASS** | Bill dated 2026-05-26 (50 days old, within 90-day DPDP compliance window) |
| Address Consistency (Proof vs GST) | **PASS** | Address verified with matching PIN code 348176 |

### 🟢 Applicant K09: APPROVED

- **Checks Passed:** 8 of 8
- **GSTIN:** Raw `37XXXXXXXXXX1ZB` -> Matched `37XXXXXXXXXX1ZB` (OCR-corrected: 37XXXXXXXXXX1ZB -> 37XXXXXXXXXX1ZB (Substituted 'O' -> '0' at position 8))
- **GST Trade / Legal:** Kaveri Insurance Advisors / Anita Kulkarni (Prop. Kaveri Insurance Advisors)
- **Udyam:** Raw `UDYAM-**-00-****562` -> Matched `UDYAM-**-00-****562` (Exact registry match)
- **Enterprise Name:** Kaveri Insurance Advisors
- **Signatory ID:** Anita Kulkarni (Valid till: 2027-12-22)
- **Address Proof Date:** 2026-07-10 | **PIN:** 405337

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **PASS** | All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded |
| GSTIN Format & Registry Validation | **PASS** | Valid GSTIN 37XXXXXXXXXX1ZB confirmed Active in GST registry |
| Udyam Registration & Registry Validation | **PASS** | Valid Udyam UDYAM-**-00-****562 confirmed in mock Udyam registry |
| Business Name Consistency (GST vs Udyam) | **PASS** | Matched: 'Kaveri Insurance Advisors' ~ 'Kaveri Insurance Advisors' |
| Signatory Authority Validation | **PASS** | Signatory 'Anita Kulkarni' matches registered proprietor 'Anita Kulkarni' |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2027-12-22 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **PASS** | Bill dated 2026-07-10 (5 days old, within 90-day DPDP compliance window) |
| Address Consistency (Proof vs GST) | **PASS** | Address verified with matching PIN code 405337 |

### 🟢 Applicant K10: APPROVED

- **Checks Passed:** 8 of 8
- **GSTIN:** Raw `27XXXXXXXXXX1ZL` -> Matched `27XXXXXXXXXX1ZL` (OCR-corrected: 27XXXXXXXXXX1ZL -> 27XXXXXXXXXX1ZL (Substituted 'I' -> 'J' at position 5, 'O' -> '0' at position 8))
- **GST Trade / Legal:** Kaveri Stays LLP / Kaveri Stays LLP
- **Udyam:** Raw `UDYAM-**-00-****141` -> Matched `UDYAM-**-00-****141` (Exact registry match)
- **Enterprise Name:** Kaveri Stays LLP
- **Signatory ID:** Nisha Arora (Valid till: 2029-06-01)
- **Address Proof Date:** 2026-06-18 | **PIN:** 570043

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **PASS** | All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded |
| GSTIN Format & Registry Validation | **PASS** | Valid GSTIN 27XXXXXXXXXX1ZL confirmed Active in GST registry |
| Udyam Registration & Registry Validation | **PASS** | Valid Udyam UDYAM-**-00-****141 confirmed in mock Udyam registry |
| Business Name Consistency (GST vs Udyam) | **PASS** | Matched: 'Kaveri Stays LLP' ~ 'Kaveri Stays LLP' |
| Signatory Authority Validation | **PASS** | Authorized signatory 'Nisha Arora' holds valid role 'Owner' |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2029-06-01 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **PASS** | Bill dated 2026-06-18 (27 days old, within 90-day DPDP compliance window) |
| Address Consistency (Proof vs GST) | **PASS** | Address verified with matching PIN code 570043 |

### 🔴 Applicant K11: REJECTED

- **Checks Passed:** 7 of 8
- **GSTIN:** Raw `O3XXXXXXXXXX1ZZ` -> Matched `03XXXXXXXXXX1ZZ` (OCR-corrected: O3XXXXXXXXXX1ZZ -> 03XXXXXXXXXX1ZZ (Substituted 'O' -> '0' at position 1))
- **GST Trade / Legal:** Trinity Bake House Pvt Ltd / Trinity Bake House Pvt Ltd
- **Udyam:** Raw `UDYAM-**-00-****478` -> Matched `UDYAM-**-00-****478` (Exact registry match)
- **Enterprise Name:** Trinity Bake House Pvt Ltd
- **Signatory ID:** Vikram Pillai (Valid till: 2028-12-23)
- **Address Proof Date:** 2025-10-31 | **PIN:** 541498

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **PASS** | All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded |
| GSTIN Format & Registry Validation | **PASS** | Valid GSTIN 03XXXXXXXXXX1ZZ confirmed Active in GST registry |
| Udyam Registration & Registry Validation | **PASS** | Valid Udyam UDYAM-**-00-****478 confirmed in mock Udyam registry |
| Business Name Consistency (GST vs Udyam) | **PASS** | Matched: 'Trinity Bake House Pvt Ltd' ~ 'Trinity Bake House Pvt Ltd' |
| Signatory Authority Validation | **PASS** | Authorized signatory 'Vikram Pillai' holds valid role 'Owner' |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2028-12-23 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **FAIL** | Stale utility bill dated 2025-10-31 (257 days old, exceeds 90-day limit) |
| Address Consistency (Proof vs GST) | **PASS** | Address verified with matching PIN code 541498 |

### 🟢 Applicant K12: APPROVED

- **Checks Passed:** 8 of 8
- **GSTIN:** Raw `37XXXXXXXXXX1ZU` -> Matched `37XXXXXXXXXX1ZU` (Exact registry match)
- **GST Trade / Legal:** Star Electronics / Pooja Agarwal (Prop. Star Electronics)
- **Udyam:** Raw `UDYAM-**-00-****772` -> Matched `UDYAM-**-00-****772` (Exact registry match)
- **Enterprise Name:** Star Electronics
- **Signatory ID:** Pooja Agarwal (Valid till: 2029-03-03)
- **Address Proof Date:** 2026-07-06 | **PIN:** 762071

**Compliance Check Matrix:**
| Check | Result | Details |
|:---|:---:|:---|
| All 4 Documents Present | **PASS** | All 4 required documents (GST, Udyam, Signatory ID, Address Proof) uploaded |
| GSTIN Format & Registry Validation | **PASS** | Valid GSTIN 37XXXXXXXXXX1ZU confirmed Active in GST registry |
| Udyam Registration & Registry Validation | **PASS** | Valid Udyam UDYAM-**-00-****772 confirmed in mock Udyam registry |
| Business Name Consistency (GST vs Udyam) | **PASS** | Matched: 'Star Electronics' ~ 'Star Electronics' |
| Signatory Authority Validation | **PASS** | Signatory 'Pooja Agarwal' matches registered proprietor 'Pooja Agarwal' |
| Signatory ID Validity & Expiry | **PASS** | ID valid till 2029-03-03 (active as of assessment date 2026-07-15) |
| Address Proof Recency (<= 90 Days) | **PASS** | Bill dated 2026-07-06 (9 days old, within 90-day DPDP compliance window) |
| Address Consistency (Proof vs GST) | **PASS** | Address verified with matching PIN code 762071 |
