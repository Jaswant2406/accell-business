# Track A: Project Udyam Digital - Synthetic dataset

All businesses, people, identifiers, documents and figures in this pack are **fictional** and generated for the Accel YTL Hackathon. They do not describe any real company or customer.

## What's in the pack

| File | Rows | What it is |
| --- | --- | --- |
| `product_catalogue.csv` | 25 | Accel Business products with price range, setup fee, contract, eligibility rules and dependencies. Use it to power the advisor and the quote. |
| `smb_leads.csv` | 5,000 | One quarter (Apr-Jun 2026) of small-business leads with profile, funnel stage reached, drop reason, dates, and - for activated leads - bundle bought, value, churn and NPS. |
| `mock_gstin_registry.csv` | 3,534 | Mock GST registry. Back your "GSTIN lookup" API with this file. |
| `mock_udyam_registry.csv` | 2,723 | Mock Udyam registry. Back your "Udyam lookup" API with this file. |
| `kyc_documents/` | 47 images | Specimen KYC documents for 12 applicants (K01-K12): business registration, Udyam certificate, signatory ID and address proof. Some have problems your Smart KYC should catch. |

## Funnel at a glance

| Stage | Leads | % of previous stage |
| --- | --- | --- |
| Lead | 5,000 | - |
| Contacted | 3,406 | 68% |
| Needs assessed | 1,974 | 58% |
| Quote accepted | 861 | 44% |
| KYC complete | 588 | 68% |
| Activated | 368 | 63% |

Activated customers took 17.6 days on average from lead to activation and made 3 follow-up calls. Blended acquisition cost is about Rs 15,000 per activated customer.

## smb_leads.csv - column guide

| Column | Meaning |
| --- | --- |
| lead_id | Unique lead ID (L00001...) |
| created_date | Date lead was created |
| lead_source | Field sales, Website form, Channel partner, Inbound call, Referral, WhatsApp campaign |
| business_name, business_type, segment | Fictional business, its type and one of 4 segments |
| city, city_tier, state | Location; tier 1 or 2 |
| preferred_language | Language the owner prefers |
| employee_count, num_sites, annual_turnover_band | Size of the business |
| has_gstin, gstin, has_udyam, udyam_number | Registration status and numbers (match the mock registries) |
| current_internet, current_provider, monthly_telecom_spend_inr | Current setup and spend |
| products_of_interest | Product IDs the lead asked about (`;`-separated) |
| contact_name, contact_role | Fictional contact person |
| stage_reached | Last funnel stage reached |
| outcome, drop_reason | Activated or Dropped, with reason |
| contacted_date ... activated_date | Date each stage was reached (blank if not reached) |
| days_lead_to_activation | Days from lead to activation (activated only) |
| customer_follow_up_calls | Times the customer called to chase status |
| bundle_products | Products bought, as `P01x1;P07x2` (product x quantity) |
| monthly_bundle_value_inr, one_time_setup_inr, contract_months | Value of what was bought |
| churned_within_6_months, nps_score | Outcome after activation (0-10 NPS) |
| acquisition_cost_inr | Sales and partner cost spent on this lead |

## product_catalogue.csv - eligibility rules

- `available_city_tiers`: tiers where the product is sold
- `min_employees`, `min_sites`: product is only offered at or above these sizes
- `requires_gstin = Y`: cannot be sold without a valid, active GSTIN
- `requires_one_of`: product needs at least one of these products in the same bundle (`|`-separated)
- `typical_install_days`: use for the order tracker and for expected activation dates


 Screenshots

<img width="1917" height="1035" alt="Screenshot 2026-11-08 202539" src="https://github.com/user-attachments/assets/96eee5e9-749e-4b59-bc62-6ec8fefb4044" />

<img width="1917" height="1078" alt="Screenshot 2026-11-08 202548" src="https://github.com/user-attachments/assets/1615fb70-30ad-4a42-9fbd-4338cbe31f54" />

<img width="1917" height="1077" alt="Screenshot 2026-11-08 202606" src="https://github.com/user-attachments/assets/9a274bb5-09c6-4021-af28-2d5ce956f1e0" />

<img width="1917" height="1078" alt="Screenshot 2026-11-08 202626" src="https://github.com/user-attachments/assets/c1894dca-bad7-4a76-942f-b2009a4e3aa9" />

<img width="1917" height="1078" alt="Screenshot 2026-11-08 202633" src="https://github.com/user-attachments/assets/c60e2793-2d70-451c-9996-948e5e0ab1e6" />

<img width="1917" height="985" alt="Screenshot 2026-11-08 202640" src="https://github.com/user-attachments/assets/17fabedc-b5db-4cb8-9a6f-1e2199e66337" />

<img width="1917" height="911" alt="Screenshot 2026-11-08 202700" src="https://github.com/user-attachments/assets/08f30c62-258b-4888-be5d-f42d5ccc5fc9" />

<img width="1917" height="1078" alt="Screenshot 2026-11-08 202705" src="https://github.com/user-attachments/assets/d49e7c2e-4c88-4e41-b3f9-ceb375232c41" />

<img width="1917" height="1078" alt="Screenshot 2026-11-08 202711" src="https://github.com/user-attachments/assets/24f50845-15ab-4071-a348-0d571638c758" />

## Notes on identifiers

- GSTINs follow the real 15-character structure with a valid checksum, so you can build a real format check. The 4th character of the embedded PAN is always `X`, which is not a valid entity type, so none of them can match a real taxpayer. Accept `X` in your validator.
- Udyam numbers use district code `00`, which does not exist.
- Use 2026-07-15 as "today" for any date-based check (e.g. address proof must be no older than 90 days).

## Privacy & Telemetry Expectations

Treat this data as if it were real customer data: collect only what each step needs, show a clear consent notice before KYC, mask identifiers in logs and UI, and explain how long documents are retained. Your 1-page privacy note should cover these choices.

- **Usage Telemetry Disabled**: Streamlit browser usage telemetry is explicitly disabled (`gatherUsageStats = false` in `.streamlit/config.toml`). All computations, OCR extractions, and registry evaluations run locally in compliance with the Digital Personal Data Protection (DPDP) Act 2023.

## Environment & Model Configuration

Configure the application via `.env` (refer to `.env.example`):
- `GEMINI_API_KEY`: Google Gemini API key for multilingual conversational requirement extraction. AI mode is completely optional; the deterministic rules engine makes all product eligibility, dependency, and pricing decisions. If unset or disabled, the application operates 100% offline via deterministic multilingual rules.
- `GEMINI_MODEL`: Model identifier (defaults to `gemini-3.1-flash-lite`, the fastest reliable model with sub-second extraction latency).
- `GEMINI_TIMEOUT_SECONDS`: Configurable Gemini invocation timeout in seconds (defaults to `10`, strictly enforced with zero retries on timeout so total AI wait never exceeds 10s).
- `TESSERACT_CMD`: Local path to the Tesseract OCR executable for document processing.

### AI Mode (Gemini) Sidebar Toggle & Network Optimisation
- In the application sidebar, an **"AI mode (Gemini)"** toggle is available (default **OFF**).
- **When OFF**: The Advisor bypasses LLM calls completely and executes instant deterministic rules extraction with zero spinner delay.
- **When ON**: A lightweight health check (tiny ping, 4-second timeout) executes once per session and caches the result. If the health check fails or the API is unavailable, the toggle automatically switches itself off and notifies the user (*"Gemini unavailable, using rules mode"*).
- **IPv4 Transport Forcing**: Gemini HTTP transports are explicitly bound to IPv4 (`local_address="0.0.0.0"`). This eliminates IPv6 PMTU black-holing and connection stalls to Google API endpoints, ensuring reliable 1-second responses without timeouts.
- **Rules Engine Authority**: AI mode is strictly optional. The deterministic rules engine makes **every product eligibility, dependency, bundle construction, and pricing decision**, ensuring 100% compliance with `product_catalogue.csv`.



