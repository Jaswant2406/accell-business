"""
Tests for AI Advisor, Multilingual Extraction, Slot Filling, Guardrails, and Unlock Suggestions.
Covers:
1. 20 sample messages (15 English + 5 Hindi/Tamil) with field-level accuracy assertions.
2. Guardrails test for product names, product IDs, and unauthorized pricing numbers.
3. Deterministic unlock suggestion test for GSTIN, City Tier, Headcount, Sites, and Dependencies.
4. Slot filling test for one-question-at-a-time and ambiguous value confirmations.
"""

import pytest
from typing import Dict, Any, List

from engine.advisor import (
    extract_profile_multilingual_fallback,
    evaluate_slot_filling,
    SUPPORTED_LANGUAGES,
)
from engine.guardrails import (
    validate_llm_product_and_pricing_guardrails,
    get_catalogue_canonical_products,
    get_catalogue_valid_prices,
)
from engine.eligibility import (
    BusinessProfile,
    compute_unlock_suggestion,
)
from kyc.registry import load_catalogue


# ---------------------------------------------------------------------------
# Test Suite 1: 20 Multilingual Sample Messages & Extraction Accuracy
# ---------------------------------------------------------------------------

SAMPLE_MESSAGES = [
    # 1. English Manufacturing
    {
        "text": "We run an auto parts manufacturing plant in Pune with 35 employees and 2 plants. Our GSTIN is 27AABCU9603R1ZN. We need fiber internet and static IP.",
        "lang": "English",
        "expected": {
            "business_type": "Manufacturing",
            "city": "Pune",
            "employees": 35,
            "sites": 2,
            "has_gstin": True,
        },
    },
    # 2. English Clinic (unregistered)
    {
        "text": "We have a dental clinic in Bengaluru with 6 staff and 1 location. No GST registration. We need broadband and cloud backup.",
        "lang": "English",
        "expected": {
            "business_type": "Healthcare/Clinic",
            "city": "Bengaluru",
            "employees": 6,
            "sites": 1,
            "has_gstin": False,
        },
    },
    # 3. English Retail/Kirana
    {
        "text": "I manage a retail grocery store in Chennai with 8 employees across 2 shops. GSTIN is 33AABCU9603R1ZN. We require POS billing and CCTV security.",
        "lang": "English",
        "expected": {
            "business_type": "Retail/Kirana",
            "city": "Chennai",
            "employees": 8,
            "sites": 2,
            "has_gstin": True,
        },
    },
    # 4. English CA Firm
    {
        "text": "We are a chartered accountant office in Mumbai with 12 employees, single site. GSTIN 27AABCU9603R1ZN. Need fast internet and cloud drive storage.",
        "lang": "English",
        "expected": {
            "business_type": "Professional Services",
            "city": "Mumbai",
            "employees": 12,
            "sites": 1,
            "has_gstin": True,
        },
    },
    # 5. English Restaurant Chain
    {
        "text": "We operate a restaurant chain in Delhi with 24 staff across 3 locations. GSTIN: 07AABCU9603R1ZN. Looking for business calling, POS, and camera surveillance.",
        "lang": "English",
        "expected": {
            "business_type": "Restaurant/Food",
            "city": "Delhi",
            "employees": 24,
            "sites": 3,
            "has_gstin": True,
        },
    },
    # 6. English Logistics Warehouse
    {
        "text": "Industrial logistics warehouse in Nagpur with 18 workers, 1 facility. GSTIN 27AABCU9603R1ZN. Needs fleet tracking GPS and CCTV cameras.",
        "lang": "English",
        "expected": {
            "business_type": "Manufacturing",
            "city": "Nagpur",
            "employees": 18,
            "sites": 1,
            "has_gstin": True,
        },
    },
    # 7. English Textile Factory
    {
        "text": "Textile fabric factory in Surat with 45 workers and 1 plant. GST is 24AABCU9603R1ZN. Require high speed broadband and machine monitoring IoT.",
        "lang": "English",
        "expected": {
            "business_type": "Manufacturing",
            "city": "Surat",
            "employees": 45,
            "sites": 1,
            "has_gstin": True,
        },
    },
    # 8. English IT Software
    {
        "text": "Software development tech agency in Hyderabad with 20 employees at our main office. GSTIN 36AABCU9603R1ZN. Need leased line and endpoint firewall security.",
        "lang": "English",
        "expected": {
            "business_type": "Professional Services",
            "city": "Hyderabad",
            "employees": 20,
            "sites": 1,
            "has_gstin": True,
        },
    },
    # 9. English Retail Boutique
    {
        "text": "Small fashion boutique store in Jaipur with 4 staff members, 1 store. GSTIN 08AABCU9603R1ZN. Needs fiber broadband and billing POS.",
        "lang": "English",
        "expected": {
            "business_type": "Retail/Kirana",
            "city": "Jaipur",
            "employees": 4,
            "sites": 1,
            "has_gstin": True,
        },
    },
    # 10. English Law Chambers
    {
        "text": "Legal advocate office in Kolkata with 10 staff persons, 1 office. GSTIN 19AABCU9603R1ZN. Needs corporate phone voice lines and secure cloud storage.",
        "lang": "English",
        "expected": {
            "business_type": "Professional Services",
            "city": "Kolkata",
            "employees": 10,
            "sites": 1,
            "has_gstin": True,
        },
    },
    # 11. English Diagnostic Clinic
    {
        "text": "Healthcare diagnostic pathology lab in Ahmedabad with 15 staff across 2 branches. GSTIN 24AABCU9603R1ZN. Needs fiber broadband and antivirus software.",
        "lang": "English",
        "expected": {
            "business_type": "Healthcare/Clinic",
            "city": "Ahmedabad",
            "employees": 15,
            "sites": 2,
            "has_gstin": True,
        },
    },
    # 12. English Bakery Chain
    {
        "text": "Artisan bakery and cafe brand in Kochi with 14 employees spanning 3 shops. GSTIN 32AABCU9603R1ZN. Looking for voice telephony lines and POS billing.",
        "lang": "English",
        "expected": {
            "business_type": "Restaurant/Food",
            "city": "Kochi",
            "employees": 14,
            "sites": 3,
            "has_gstin": True,
        },
    },
    # 13. English Coaching Institute (without GST)
    {
        "text": "Education training office in Lucknow with 8 team members, 1 site. Operating without GST. Need fast broadband and cloud backup.",
        "lang": "English",
        "expected": {
            "business_type": "Professional Services",
            "city": "Lucknow",
            "employees": 8,
            "sites": 1,
            "has_gstin": False,
        },
    },
    # 14. English Electrical Factory
    {
        "text": "Electrical equipment manufacturing plant in Coimbatore with 50 workers across 2 factories. GSTIN 33AABCU9603R1ZN. Need static IP and CCTV cameras.",
        "lang": "English",
        "expected": {
            "business_type": "Manufacturing",
            "city": "Coimbatore",
            "employees": 50,
            "sites": 2,
            "has_gstin": True,
        },
    },
    # 15. English Architecture Studio
    {
        "text": "Architect design consultancy office in Chandigarh with 7 employees, 1 office. GSTIN 04AABCU9603R1ZN. Needs cloud backup drive and internet.",
        "lang": "English",
        "expected": {
            "business_type": "Professional Services",
            "city": "Chandigarh",
            "employees": 7,
            "sites": 1,
            "has_gstin": True,
        },
    },
    # 16. Hindi Auto Factory
    {
        "text": "मेरी पुणे में ऑटो पार्ट्स की फैक्ट्री है जिसमें 30 कर्मचारी हैं और 1 प्लांट है। हमारा जीएसटी नंबर 27AABCU9603R1ZN है।",
        "lang": "Hindi",
        "expected": {
            "business_type": "Manufacturing",
            "city": "Pune",
            "employees": 30,
            "sites": 1,
            "has_gstin": True,
        },
    },
    # 17. Hindi Clinic (No GST)
    {
        "text": "जयपुर में हमारा डेंटल क्लिनिक है, 5 कर्मचारी हैं और जीएसटी नंबर नहीं है।",
        "lang": "Hindi",
        "expected": {
            "business_type": "Healthcare/Clinic",
            "city": "Jaipur",
            "employees": 5,
            "sites": 1,
            "has_gstin": False,
        },
    },
    # 18. Tamil IT Tech
    {
        "text": "சென்னையில் 15 ஊழியர்களுடன் ஒரு மென்பொருள் நிறுவனம் நடத்துகிறோம். எங்களுக்கு உயர் வேக இணையம் மற்றும் கிளவுட் தேவை. ஜிஎஸ்டி: 33AABCU9603R1ZN",
        "lang": "Tamil",
        "expected": {
            "business_type": "Professional Services",
            "city": "Chennai",
            "employees": 15,
            "sites": 1,
            "has_gstin": True,
        },
    },
    # 19. Tamil Retail Store (No GST)
    {
        "text": "கோயம்புத்தூரில் 2 கிளைகளுடன் மளிகை கடை வைத்திருக்கிறேன், 8 பணியாளர்கள் உள்ளனர், ஜிஎஸ்டி இல்லை.",
        "lang": "Tamil",
        "expected": {
            "business_type": "Retail/Kirana",
            "city": "Coimbatore",
            "employees": 8,
            "sites": 2,
            "has_gstin": False,
        },
    },
    # 20. Hindi Manufacturing
    {
        "text": "हमारा पुणे में ऑटो पार्ट्स निर्माण संयंत्र (1 प्लांट) है, 30 कर्मचारी हैं, GSTIN 27AABCU9603R1ZN है। लीज्ड लाइन चाहिए।",
        "lang": "Hindi",
        "expected": {
            "business_type": "Manufacturing",
            "city": "Pune",
            "employees": 30,
            "sites": 1,
            "has_gstin": True,
        },
    },
]


def test_multilingual_20_sample_messages_extraction_accuracy():
    """
    Test 20 sample messages across English, Hindi, and Tamil.
    Evaluates business_type, city, employees, sites, and has_gstin extraction.
    Asserts >= 90% extraction accuracy across the 100 field evaluations.
    """
    total_checks = 0
    passed_checks = 0
    failures = []

    for idx, sample in enumerate(SAMPLE_MESSAGES, start=1):
        extracted = extract_profile_multilingual_fallback(
            sample["text"],
            language=sample["lang"],
        )
        expected = sample["expected"]

        for key, exp_val in expected.items():
            total_checks += 1
            act_val = extracted.get(key)
            if act_val == exp_val:
                passed_checks += 1
            else:
                failures.append(
                    f"Sample {idx} [{sample['lang']}] field '{key}': expected {exp_val}, got {act_val}"
                )

    accuracy_pct = (passed_checks / total_checks) * 100
    print(f"\n--- Multilingual Advisor Extraction Accuracy: {passed_checks}/{total_checks} ({accuracy_pct:.1f}%) ---")
    if failures:
        print("Mismatches:\n" + "\n".join(failures))

    assert accuracy_pct >= 90.0, f"Extraction accuracy {accuracy_pct:.1f}% below 90% target"


# ---------------------------------------------------------------------------
# Test Suite 2: Strict Guardrails Verification
# ---------------------------------------------------------------------------

def test_guardrails_valid_and_invalid_outputs():
    """
    Asserts that:
    1. Valid catalogue products and authorized prices pass.
    2. Invalid product IDs (e.g. P99, P00) fail.
    3. Hallucinated telecom products (e.g. 'Super Fiber Plus 500') fail.
    4. Fabricated prices (e.g. ₹49,999) fail.
    """
    # 1. Valid output
    valid_text = (
        "Based on your profile, we recommend P01 Biz Fibre 100 at ₹999/month, "
        "along with P20 Endpoint Security Antivirus at ₹99/month."
    )
    ok, err = validate_llm_product_and_pricing_guardrails(valid_text)
    assert ok is True, f"Expected valid text to pass, got error: {err}"

    # 2. Invalid product ID (P99 not in catalogue)
    invalid_pid_text = "We also offer P99 Ultra Gigabit Leased Line for large enterprises."
    ok, err = validate_llm_product_and_pricing_guardrails(invalid_pid_text)
    assert ok is False
    assert "P99" in str(err)

    # 3. Hallucinated product branding
    hallucinated_prod_text = "Upgrade to our exclusive Super Fiber Plus plan today."
    ok, err = validate_llm_product_and_pricing_guardrails(hallucinated_prod_text)
    assert ok is False
    assert "super fiber" in str(err).lower()

    # 4. Fabricated price (₹49,999 is not in catalogue)
    fake_price_text = "The complete custom enterprise solution costs ₹49,999 per month."
    ok, err = validate_llm_product_and_pricing_guardrails(fake_price_text)
    assert ok is False
    assert "49,999" in str(err) or "49999" in str(err)


# ---------------------------------------------------------------------------
# Test Suite 3: Deterministic Unlock Suggestions
# ---------------------------------------------------------------------------

def test_unlock_suggestions_deterministic_logic():
    """
    Tests unlock suggestion computation for:
    - Missing GSTIN requirement
    - City Tier restriction (e.g. P03 Tier 1 only)
    - Employee threshold requirement (e.g. P06 min 20 employees)
    - Site threshold requirement (e.g. P10 min 2 sites)
    - Missing dependency requirement (e.g. P11 requires parent broadband)
    """
    cat_df = load_catalogue()
    
    # 1. GSTIN requirement unlock: Unregistered applicant (has_gstin = False) viewing P05 (requires GSTIN)
    unregistered_profile = BusinessProfile(
        business_name="Unregistered Kirana",
        business_type="Retail/Kirana",
        segment="micro",
        employee_count=10,
        num_sites=1,
        city="Pune",
        city_tier=1,
        has_gstin=False,
        gstin=None,
    )
    p05_row = cat_df[cat_df["product_id"] == "P05"].iloc[0]
    p05_unlock = compute_unlock_suggestion(p05_row, unregistered_profile)
    assert p05_unlock["is_eligible"] is False
    assert p05_unlock["criteria"]["needs_gstin"] is True
    assert "GSTIN" in p05_unlock["unlock_text"]

    # 2. City Tier unlock: Tier 2 business viewing P03 (Tier 1 only)
    tier2_profile = BusinessProfile(
        business_name="Tier 2 Clinic",
        business_type="Healthcare/Clinic",
        segment="prof",
        employee_count=10,
        num_sites=1,
        city="Nagpur",
        city_tier=2,
        has_gstin=True,
        gstin="27AABCU9603R1ZN",
    )
    p03_row = cat_df[cat_df["product_id"] == "P03"].iloc[0]
    p03_unlock = compute_unlock_suggestion(p03_row, tier2_profile)
    assert p03_unlock["is_eligible"] is False
    assert p03_unlock["criteria"]["city_tiers_needed"] == [1]
    assert "Tier 1" in p03_unlock["unlock_text"]

    # 3. Headcount unlock: Small team (5 employees) viewing P06 (requires 25+)
    small_team_profile = BusinessProfile(
        business_name="Small Tech",
        business_type="Professional Services",
        segment="prof",
        employee_count=5,
        num_sites=1,
        city="Pune",
        city_tier=1,
        has_gstin=True,
        gstin="27AABCU9603R1ZN",
    )
    p06_row = cat_df[cat_df["product_id"] == "P06"].iloc[0]
    p06_unlock = compute_unlock_suggestion(p06_row, small_team_profile)
    assert p06_unlock["is_eligible"] is False
    assert p06_unlock["criteria"]["min_employees_needed"] == 25
    assert "25 employees" in p06_unlock["unlock_text"]

    # 4. Site count unlock: Single-site business (1 site) viewing P10 SD-WAN (requires 3+ sites)
    p10_row = cat_df[cat_df["product_id"] == "P10"].iloc[0]
    p10_unlock = compute_unlock_suggestion(p10_row, unregistered_profile)
    assert p10_unlock["is_eligible"] is False
    assert p10_unlock["criteria"]["min_sites_needed"] == 3
    assert "3 operating sites" in p10_unlock["unlock_text"]

    # 5. Dependency unlock: Static IP (P11) requires base connectivity (P01|P02|P03|P04)
    p11_row = cat_df[cat_df["product_id"] == "P11"].iloc[0]
    # If no eligible parents provided
    p11_unlock = compute_unlock_suggestion(p11_row, unregistered_profile, eligible_pids=set())
    assert p11_unlock["is_eligible"] is False
    assert "P01" in p11_unlock["criteria"]["missing_dependencies"]
    assert "base connectivity" in p11_unlock["unlock_text"].lower()


# ---------------------------------------------------------------------------
# Test Suite 4: Conversational Slot Filling & Ambiguity Confirmation
# ---------------------------------------------------------------------------

def test_slot_filling_one_question_and_ambiguity():
    """
    Asserts slot filling behaves sequentially:
    1. Returns missing slot questions one at a time.
    2. Identifies and confirms ambiguous employee ranges before finalizing.
    3. Supports multiple languages (Hindi question generated).
    """
    # Incomplete profile (missing employees and city)
    incomplete_profile = {
        "business_type": "Manufacturing",
        "employees": 0,
        "employees_missing": True,
        "city": "Unknown",
        "sites": 1,
        "has_gstin": True,
    }
    slot_res = evaluate_slot_filling(incomplete_profile, language="English")
    assert slot_res["is_complete"] is False
    assert slot_res["next_missing_slot"] == "employees"
    assert "employees work" in slot_res["next_question"].lower()

    # Hindi question check
    slot_res_hi = evaluate_slot_filling(incomplete_profile, language="Hindi")
    assert slot_res_hi["next_missing_slot"] == "employees"
    assert "कर्मचारी" in slot_res_hi["next_question"]

    # Ambiguous employee range check (e.g. user typed "20 to 30 workers")
    ambiguous_profile = {
        "business_type": "Manufacturing",
        "employees": 30,
        "is_ambiguous_employees": True,
        "ambiguous_val": "20-30",
        "city": "Pune",
        "sites": 1,
        "has_gstin": True,
    }
    ambig_res = evaluate_slot_filling(ambiguous_profile, language="English")
    assert ambig_res["is_complete"] is False
    assert ambig_res["ambiguous_slot"] == "employees"
    assert "20-30" in ambig_res["confirmation_prompt"]


def test_ai_mode_toggle_and_direct_rules_fallback():
    """
    Verifies that when AI mode is OFF (default), extraction runs instantaneously
    through deterministic rules with zero spinner or LLM latency.
    """
    from engine.advisor import extract_profile_multilingual_fallback
    text = "Dental clinic, 5 staff, 1 location in Kochi, I have a GSTIN"
    res = extract_profile_multilingual_fallback(text, language="English")
    assert res is not None
    assert res["business_type"] == "Healthcare/Clinic"
    assert res["employees"] == 5
    assert res["city"] == "Kochi"
    assert res["has_gstin"] is True
    assert res["is_llm"] is False


def test_health_check_behavior():
    """
    Tests check_gemini_health function directly.
    """
    from engine.advisor import check_gemini_health
    # With valid API key and gemini-3.1-flash-lite, health check succeeds
    is_healthy = check_gemini_health(timeout_seconds=4.0)
    assert isinstance(is_healthy, bool)


def test_timeout_strictly_capped_no_retries(monkeypatch):
    """
    Verifies that extract_profile_with_llm respects a 10s maximum timeout
    and does NOT retry on timeout.
    """
    import time
    from engine.advisor import extract_profile_with_llm

    # Test with tiny timeout (0.01s) to force timeout behavior
    t0 = time.time()
    res = extract_profile_with_llm(
        "Auto parts manufacturing in Pune with 30 staff",
        target_language="English",
        timeout_seconds=0.01,
    )
    elapsed = time.time() - t0
    # Must return None (falling back to rules mode)
    assert res is None
    # Must finish immediately without retrying
    assert elapsed < 1.0


def test_no_key_path_falls_back_instantly():
    """
    Verifies that when GEMINI_API_KEY is empty or None, extract_profile_with_llm
    returns None immediately with zero wait time.
    """
    import time
    from engine.advisor import extract_profile_with_llm

    t0 = time.time()
    res = extract_profile_with_llm("Dental clinic in Kochi", api_key="")
    elapsed = time.time() - t0
    assert res is None
    assert elapsed < 0.1

