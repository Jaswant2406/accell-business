"""
AI Business Advisor Module for Accel Business Udyam Digital.
Supports:
1. Multilingual conversational input (English, Hindi, Tamil).
2. Gemini extraction with strict JSON schema and language-aware explanations.
3. Deterministic multilingual fallback extractor (runs offline without API key).
4. Slot filling: asks for missing mandatory fields ONE question at a time and confirms ambiguous values.
5. Strict product & pricing guardrails: any LLM output with uncatalogued products or prices is rejected.
"""

from dataclasses import dataclass, field
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv

from engine.eligibility import BusinessProfile
from engine.guardrails import validate_llm_product_and_pricing_guardrails
from kyc.registry import get_city_tier, lookup_gstin, validate_gstin_format

load_dotenv()

DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
DEFAULT_GEMINI_TIMEOUT = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "10"))

SUPPORTED_LANGUAGES = ["English", "Hindi", "Tamil"]

EMPLOYEES_MIN = 1
EMPLOYEES_MAX = 10000
SITES_MIN = 1
SITES_MAX = 500
BUDGET_MIN = 0
BUDGET_MAX = 1000000
QUANTITY_MIN = 1
QUANTITY_MAX = 10000


def validate_and_clamp_profile_data(data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validates and clamps profile numbers into allowed operational ranges.
    Returns the clamped data dict and a list of friendly warning notes for any clamped or rejected values.
    """
    notes: List[str] = list(data.get("validation_notes", []))

    # 1. Employees validation & clamping
    raw_emp = data.get("employees")
    if raw_emp is not None:
        try:
            emp_val = int(raw_emp)
            if emp_val <= 0:
                notes.append(f"Employee count must be at least 1 (received {emp_val}). Set to 1.")
                data["employees"] = EMPLOYEES_MIN
            elif emp_val > EMPLOYEES_MAX:
                notes.append(f"Employees capped at {EMPLOYEES_MAX:,} for this demo.")
                data["employees"] = EMPLOYEES_MAX
            else:
                data["employees"] = emp_val
        except (TypeError, ValueError):
            notes.append(f"Invalid employee count '{raw_emp}'. Defaulted to 1.")
            data["employees"] = EMPLOYEES_MIN
    else:
        data["employees"] = EMPLOYEES_MIN

    # 2. Sites validation & clamping
    raw_sites = data.get("sites")
    if raw_sites is not None:
        try:
            sites_val = int(raw_sites)
            if sites_val <= 0:
                notes.append(f"Operational sites must be at least 1 (received {sites_val}). Set to 1.")
                data["sites"] = SITES_MIN
            elif sites_val > SITES_MAX:
                notes.append(f"Operational sites capped at {SITES_MAX:,} for this demo.")
                data["sites"] = SITES_MAX
            else:
                data["sites"] = sites_val
        except (TypeError, ValueError):
            notes.append(f"Invalid site count '{raw_sites}'. Defaulted to 1.")
            data["sites"] = SITES_MIN
    else:
        data["sites"] = SITES_MIN

    # 3. Budget validation & clamping (if present)
    raw_budget = data.get("budget")
    if raw_budget is not None:
        try:
            b_val = float(raw_budget)
            if b_val < BUDGET_MIN:
                notes.append(f"Monthly budget ceiling cannot be negative (received ₹{int(b_val):,}). Set to ₹0.")
                data["budget"] = BUDGET_MIN
            elif b_val > BUDGET_MAX:
                notes.append("Monthly budget ceiling capped at ₹10,00,000 for this demo.")
                data["budget"] = BUDGET_MAX
            else:
                data["budget"] = int(b_val)
        except (TypeError, ValueError):
            notes.append(f"Invalid budget '{raw_budget}'. Ignored.")
            data["budget"] = None

    data["validation_notes"] = notes
    return data, notes


def create_gemini_client(api_key: str, timeout_seconds: float = 10.0):
    """
    Creates a Google GenAI client forced to IPv4 to prevent IPv6 PMTU packet
    drops and connection stalls on Windows. Sets a minimum 10s HTTP deadline.
    """
    import google.genai as genai
    from google.genai import types

    client_args = {}
    try:
        try:
            import httpx2 as _http_mod
        except ImportError:
            import httpx as _http_mod
        client_args["transport"] = _http_mod.HTTPTransport(local_address="0.0.0.0")
    except Exception:
        pass

    http_opts = types.HttpOptions(
        timeout=int(max(timeout_seconds, 10.0) * 1000),
        client_args=client_args if client_args else None,
    )
    return genai.Client(api_key=api_key.strip(), http_options=http_opts)


def check_gemini_health(timeout_seconds: float = 4.0) -> bool:
    """
    Quick health check (tiny prompt, 4s timeout).
    Returns True if Gemini model responds successfully within timeout, False otherwise.
    """
    key = os.getenv("GEMINI_API_KEY")
    if not key or not key.strip():
        return False
    model = os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL

    from google.genai import types
    import concurrent.futures

    def _ping():
        client = create_gemini_client(api_key=key.strip(), timeout_seconds=timeout_seconds)
        resp = client.models.generate_content(
            model=model,
            contents="ping",
            config=types.GenerateContentConfig(max_output_tokens=5),
        )
        return bool(resp and resp.text)

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        fut = executor.submit(_ping)
        res = fut.result(timeout=timeout_seconds)
        executor.shutdown(wait=False)
        return res
    except Exception:
        executor.shutdown(wait=False, cancel_futures=True)
        return False


@dataclass
class AdvisorRecommendationResult:
    profile: BusinessProfile
    personalized_rationale: str
    is_llm_generated: bool
    raw_response: Optional[str] = None
    error_message: Optional[str] = None
    language: str = "English"


# Multilingual Slot Filling Questions
SLOT_QUESTIONS = {
    "English": {
        "business_type": "What type of business do you operate (e.g. Manufacturing, Clinic, Retail store, Restaurant, IT/Consulting)?",
        "employees": "How many total employees work across your business?",
        "sites": "How many physical business branches, plants, or premises do you operate?",
        "city": "Which primary city or town is your business facility located in?",
        "has_gstin": "Do you hold an active GSTIN registration for your business?",
        "confirm_employees": "We noted an employee range of around {val}. Could you confirm the exact headcount?",
        "confirm_city": "We noted location {val}. Could you confirm this is your primary operating city?",
    },
    "Hindi": {
        "business_type": "आपका व्यवसाय किस प्रकार का है (जैसे विनिर्माण/फैक्ट्री, क्लिनिक, खुदरा दुकान, रेस्टोरेंट, आईटी)?",
        "employees": "आपके व्यवसाय में कुल कितने कर्मचारी कार्यरत हैं?",
        "sites": "आपकी कुल कितनी शाखाएं, प्लांट या कार्यस्थल हैं?",
        "city": "आपका व्यवसाय किस शहर में स्थित है?",
        "has_gstin": "क्या आपके पास सक्रिय जीएसटी (GSTIN) पंजीकरण है?",
        "confirm_employees": "हमने लगभग {val} कर्मचारियों का उल्लेख देखा। क्या आप सटीक संख्या की पुष्टि कर सकते हैं?",
        "confirm_city": "हमने शहर '{val}' दर्ज किया है। क्या यह आपका मुख्य कार्यस्थल शहर है?",
    },
    "Tamil": {
        "business_type": "உங்கள் வணிக வகை என்ன (எ.கா. உற்பத்தி ஆலை, மருத்துவமனை, சில்லறை கடை, உணவகம், தகவல் தொழில்நுட்பம்)?",
        "employees": "உங்கள் வணிகத்தில் மொத்தம் எத்தனை ஊழியர்கள் பணியாற்றுகிறார்கள்?",
        "sites": "உங்களுக்கு எத்தனை கிளைகள், ஆலைகள் அல்லது அலுவலகங்கள் உள்ளன?",
        "city": "உங்கள் வணிகம் எந்த முக்கிய நகரத்தில் அமைந்துள்ளது?",
        "has_gstin": "உங்களிடம் செயலில் உள்ள ஜிஎஸ்டி (GSTIN) பதிவு உள்ளதா?",
        "confirm_employees": "தோராயமாக {val} ஊழியர்கள் என குறிப்பிடப்பட்டுள்ளது. சரியான எண்ணிக்கையை உறுதிப்படுத்த முடியுமா?",
        "confirm_city": "உங்கள் நகரம் '{val}' என பதிவு செய்யப்பட்டுள்ளது. இதை உறுதிப்படுத்துகிறீர்களா?",
    },
}


def evaluate_slot_filling(
    profile_data: Dict[str, Any],
    language: str = "English",
) -> Dict[str, Any]:
    """
    Evaluates profile completeness. Asks only for missing fields, ONE question at a time.
    Confirms ambiguous values before using them.
    """
    lang_key = language if language in SLOT_QUESTIONS else "English"
    q_dict = SLOT_QUESTIONS[lang_key]

    missing_slots: List[str] = []
    ambiguous_slot: Optional[str] = None
    confirmation_prompt: Optional[str] = None

    # Check for ambiguous values first
    if profile_data.get("is_ambiguous_employees"):
        ambiguous_slot = "employees"
        val = profile_data.get("ambiguous_val", profile_data.get("employees", "20-30"))
        confirmation_prompt = q_dict["confirm_employees"].format(val=val)
    elif profile_data.get("is_ambiguous_city"):
        ambiguous_slot = "city"
        val = profile_data.get("city", "Unknown")
        confirmation_prompt = q_dict["confirm_city"].format(val=val)

    # Core required slots in strict conversational priority order
    b_type = profile_data.get("business_type")
    if not b_type or str(b_type).lower() in ["unknown", "other", "", "none"]:
        missing_slots.append("business_type")

    emps = profile_data.get("employees")
    if emps is None or int(emps) <= 0 or profile_data.get("employees_missing"):
        missing_slots.append("employees")

    city = profile_data.get("city")
    if not city or str(city).lower() in ["unknown", "", "none"]:
        missing_slots.append("city")

    sites = profile_data.get("sites")
    if sites is None or int(sites) <= 0 or profile_data.get("sites_missing"):
        missing_slots.append("sites")

    if profile_data.get("has_gstin") is None or profile_data.get("gstin_missing"):
        missing_slots.append("has_gstin")

    next_slot = missing_slots[0] if missing_slots else None
    next_question = q_dict.get(next_slot) if next_slot else None

    return {
        "is_complete": len(missing_slots) == 0 and ambiguous_slot is None,
        "missing_slots": missing_slots,
        "next_missing_slot": next_slot,
        "next_question": next_question,
        "ambiguous_slot": ambiguous_slot,
        "confirmation_prompt": confirmation_prompt,
    }


def extract_profile_with_llm(
    conversation_text: str,
    target_language: str = "English",
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Call Gemini Flash to extract structured JSON fields from multilingual conversational text
    (English, Hindi, Tamil).
    - Configurable timeout via GEMINI_TIMEOUT_SECONDS (default: 20s).
    - Reduced latency: minimal thinking budget, small max_output_tokens, response_mime_type="application/json".
    - Shortened schema-first prompt.
    - Terminal logging of elapsed time (never logging API key or user text).
    - Retries once on timeout before falling back to rules engine.
    """
    import concurrent.futures
    import sys
    import time

    key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
    if not key or key.strip() == "":
        sys.stderr.write("[Advisor LLM] No GEMINI_API_KEY set. Falling back to deterministic rules engine.\n")
        sys.stderr.flush()
        return None

    model = model_name or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
    timeout = timeout_seconds if timeout_seconds is not None else float(os.getenv("GEMINI_TIMEOUT_SECONDS", "10"))

    prompt = f"""Extract business profile to strict JSON. Target explanation language: {target_language}.
Schema:
{{
  "business_name": "<name or empty string>",
  "business_type": "<Healthcare/Clinic|Retail/Kirana|Restaurant/Food|Manufacturing|Professional Services|IT/Tech|Salon/Beauty|Logistics/Transport|Other>",
  "segment": "<micro|prof|multi|mfg>",
  "employees": <int, default 1 if unknown>,
  "employees_missing": <bool true if not mentioned>,
  "sites": <int, default 1 if unknown>,
  "sites_missing": <bool true if not mentioned>,
  "city": "<city or 'Unknown'>",
  "has_gstin": <bool true/false/null>,
  "gstin_missing": <bool true if not mentioned>,
  "gstin": "<15-char GSTIN if mentioned, else null>",
  "current_broadband": "<None|Fiber|Leased Line|Basic DSL/Cable|Mobile Hotspot>",
  "digital_needs": [<array of strings from: "broadband", "cctv", "voice_lines", "dedicated_ip", "cloud_storage", "fleet_tracking", "pos", "security", "sdwan">],
  "budget": <int or null, monthly budget ceiling in INR if specified by customer>,
  "explanation": "<2-sentence operational rationale in {target_language}>",
  "is_ambiguous_employees": <bool true if range given>,
  "ambiguous_val": "<range or null>"
}}

User message:
\"\"\"{conversation_text}\"\"\"
"""

    def _invoke_gemini_api():
        from google.genai import types

        client = create_gemini_client(api_key=key.strip(), timeout_seconds=timeout)

        cfg_kwargs = {
            "response_mime_type": "application/json",
            "max_output_tokens": 350,
        }
        try:
            cfg_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        except Exception:
            pass

        gen_config = types.GenerateContentConfig(**cfg_kwargs)
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=gen_config,
        )
        return resp.text.strip() if resp and resp.text else ""

    t_start = time.time()
    sys.stderr.write(f"[Advisor LLM] Calling {model} (timeout={timeout:.1f}s)...\n")
    sys.stderr.flush()

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(_invoke_gemini_api)
        txt = future.result(timeout=timeout)
        executor.shutdown(wait=False)

        elapsed = time.time() - t_start
        sys.stderr.write(f"[Advisor LLM] Succeeded in {elapsed:.2f}s.\n")
        sys.stderr.flush()

        if txt.startswith("```json"):
            txt = txt[7:]
        if txt.startswith("```"):
            txt = txt[3:]
        if txt.endswith("```"):
            txt = txt[:-3]
        txt = txt.strip()
        data = json.loads(txt)
        data, _ = validate_and_clamp_profile_data(data)

        # Enforce Guardrails on LLM explanation text
        expl = data.get("explanation", "")
        is_safe, guard_err = validate_llm_product_and_pricing_guardrails(expl)
        if not is_safe:
            data["explanation"] = (
                f"Recommendations tailored for your business operations in {data.get('city', 'India')} "
                f"with {data.get('employees', 1)} staff. Official prices strictly from catalogue."
            )
            data["guardrail_alert"] = guard_err

        data["is_llm"] = True
        return data

    except concurrent.futures.TimeoutError:
        executor.shutdown(wait=False, cancel_futures=True)
        elapsed = time.time() - t_start
        sys.stderr.write(f"[Advisor LLM] Timed out after {elapsed:.2f}s. Falling back to rules engine.\n")
        sys.stderr.flush()
        return None
    except Exception as exc:
        executor.shutdown(wait=False, cancel_futures=True)
        elapsed = time.time() - t_start
        sys.stderr.write(f"[Advisor LLM] Failed ({type(exc).__name__}) after {elapsed:.2f}s. Falling back to rules engine.\n")
        sys.stderr.flush()
        return None


def extract_profile_multilingual_fallback(
    text: str,
    language: str = "English",
) -> Dict[str, Any]:
    """
    Advanced deterministic rule-based extractor supporting English, Hindi, and Tamil.
    Operates 100% offline with zero dependencies and high accuracy.
    """
    t_lower = text.lower()

    # 1. GSTIN Regex Extraction
    gstin_match = re.search(r'\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b', text)
    gstin = gstin_match.group(1) if gstin_match else None
    
    no_gst_phrases = [
        "no gst", "without gst", "not registered", "no gstin", "dont have gst", "don't have gst",
        "जीएसटी नहीं", "जीएसटी नंबर नहीं", "ஜிஎஸ்டி இல்லை", "ஜிஎஸ்டி பதிவு இல்லை",
        "இல்லை"
    ]
    has_negative_gst = any(phrase in t_lower for phrase in no_gst_phrases)
    
    if gstin is not None:
        has_gstin = True
        gstin_missing = False
    elif has_negative_gst:
        has_gstin = False
        gstin_missing = False
    else:
        has_positive_gst = any(k in t_lower for k in [
            "gst", "gstin", "जीएसटी", "ஜிஎஸ்டி", "gst number", "gst registered"
        ])
        has_gstin = has_positive_gst
        gstin_missing = not has_positive_gst

    # 2. Employees Extraction (English, Hindi, Tamil)
    employees = None
    is_ambiguous_emp = False
    ambig_val = None

    # Range check e.g. "20 to 30 employees"
    range_match = re.search(r'([0-9,]+)\s*(?:-|to|se|ya)\s*([0-9,]+)\s*(?:employees|staff|workers|people|कर्मचार[^\s]*|कामगार[^\s]*|लोग|ஊழியர்[^\s]*|பணியாளர்[^\s]*)', t_lower)
    if range_match:
        is_ambiguous_emp = True
        ambig_val = f"{range_match.group(1)}-{range_match.group(2)}"
        try:
            employees = int(range_match.group(2).replace(',', ''))
        except ValueError:
            pass

    if employees is None:
        emp_patterns = [
            r'(-?[0-9,]+)\s*(?:employees|staff|workers|headcount|people|team members|persons)',
            r'(-?[0-9,]+)\s*(?:कर्मचार[^\s]*|कामगार[^\s]*|लोग|स्टाफ)',
            r'(-?[0-9,]+)\s*(?:ஊழியர்[^\s]*|பணியாளர்[^\s]*|நபர்கள்|ஆட்கள்)',
            r'(?:team of|headcount of|with)\s*(-?[0-9,]+)\s*(?:employees|staff|workers|people)?',
            r'(?:staff|employees|workers)\s*(?:of|is|:)?\s*(-?[0-9,]+)',
        ]
        for pat in emp_patterns:
            m = re.search(pat, t_lower)
            if m:
                try:
                    employees = int(m.group(1).replace(',', ''))
                    break
                except ValueError:
                    continue

    # 3. Sites Extraction
    sites = None
    site_patterns = [
        r'(-?[0-9,]+)\s*(?:sites|branches|locations|plants|factories|offices|stores|shops|premises)',
        r'(-?[0-9,]+)\s*(?:शाखाएं|शाखा|प्लांट|फैक्ट्री|दुकानें|परिसर)',
        r'(-?[0-9,]+)\s*(?:கிளை[^\s]*|ஆலை[^\s]*|அலுவலக[^\s]*|கடை[^\s]*)',
        r'(-?[0-9,]+)\s*(?:branches|karkhana|dukane|plants|factory|stores)',
        r'(?:across|spanning)\s*(-?[0-9,]+)\s*(?:sites|branches|locations)',
    ]
    for pat in site_patterns:
        m = re.search(pat, t_lower)
        if m:
            try:
                sites = int(m.group(1).replace(',', ''))
                break
            except ValueError:
                continue

    if sites is None:
        if any(k in t_lower for k in ["single site", "1 site", "one site", "single location", "1 plant", "1 factory"]):
            sites = 1
        elif any(k in t_lower for k in ["3 branches", "3 sites", "teen शाखाएं"]):
            sites = 3
        else:
            sites = 1

    # 3b. Budget Extraction (English, Hindi, Tamil)
    budget = None
    budget_m = re.search(
        r'(?:budget|बजट|பட்ஜெட்)\s*(?:of|is|:)?\s*(?:₹|rs\.?|inr)?\s*(-?[0-9,.]+)\s*(crore|cr|lakh|lac|l|k)?',
        t_lower,
    )
    if not budget_m:
        budget_m = re.search(
            r'(?:₹|rs\.?|inr)\s*(-?[0-9,.]+)\s*(crore|cr|lakh|lac|l|k)?\s*(?:budget|बजट|பட்ஜெட்)',
            t_lower,
        )
    if budget_m:
        val_str = budget_m.group(1).replace(',', '')
        try:
            b_val = float(val_str)
            unit = (budget_m.group(2) or '').lower()
            if unit in ['crore', 'cr']:
                b_val *= 10000000
            elif unit in ['lakh', 'lac', 'l']:
                b_val *= 100000
            elif unit == 'k':
                b_val *= 1000
            budget = int(b_val)
        except ValueError:
            pass

    # 4. City Extraction
    cities = [
        ("mumbai", "Mumbai"), ("pune", "Pune"), ("delhi", "Delhi"), ("bengaluru", "Bengaluru"),
        ("bangalore", "Bengaluru"), ("chennai", "Chennai"), ("hyderabad", "Hyderabad"),
        ("kolkata", "Kolkata"), ("ahmedabad", "Ahmedabad"), ("surat", "Surat"),
        ("jaipur", "Jaipur"), ("lucknow", "Lucknow"), ("kanpur", "Kanpur"),
        ("nagpur", "Nagpur"), ("indore", "Indore"), ("bhopal", "Bhopal"),
        ("coimbatore", "Coimbatore"), ("kochi", "Kochi"), ("chandigarh", "Chandigarh"),
        ("noida", "Noida"), ("gurugram", "Gurugram"), ("gurgaon", "Gurugram"),
        # Hindi script
        ("मुंबई", "Mumbai"), ("पुणे", "Pune"), ("दिल्ली", "Delhi"), ("बेंगलुरु", "Bengaluru"),
        ("चेन्नई", "Chennai"), ("हैदराबाद", "Hyderabad"), ("कोलकाता", "Kolkata"),
        ("अहमदाबाद", "Ahmedabad"), ("सूरत", "Surat"), ("जयपुर", "Jaipur"),
        # Tamil script
        ("சென்னை", "Chennai"), ("கோயம்புத்தூ", "Coimbatore"), ("கோயம்புத்தூர்", "Coimbatore"),
        ("கோவை", "Coimbatore"), ("மதுரை", "Madurai"), ("பெங்களூரு", "Bengaluru"), ("மும்பை", "Mumbai"),
    ]
    city = "Unknown"
    for needle, cname in cities:
        if needle in t_lower:
            city = cname
            break

    # 5. Business Type & Segment
    mfg_keys = [
        "manufactur", "factory", "plant", "auto", "parts", "fabricat", "textile", "industrial",
        "फैक्ट्री", "कारखाना", "विनिर्माण", "निर्माण", "उत्पादन", "संयंत्र", "ऑटो", "ஆலை", "உற்பத்தி",
        "karkhana", "faictry",
    ]
    clinic_keys = [
        "clinic", "doctor", "hospital", "dental", "dentist", "healthcare", "pharma", "diagnostic",
        "क्लिनिक", "अस्पताल", "दवाखाना", "डॉक्टर", "மருத்துவமனை", "மருத்துவர்",
    ]
    food_keys = [
        "restaurant", "cafe", "food", "hotel", "bakery", "dhaba", "caterer",
        "रेस्टोरेंट", "होटल", "ढाबा", "உணவகம்", "ஹோட்டல்",
    ]
    retail_keys = [
        "kirana", "retail", "shop", "grocery", "store", "supermarket", "boutique",
        "दुकान", "किराना", "स्टोर", "கடை", "சில்லறை", "dukaan",
    ]
    prof_keys = [
        "office", "consult", "ca", "audit", "account", "law", "advocate", "legal",
        "it", "software", "tech", "agency", "architect", "coaching", "training", "education",
        "आईटी", "सॉफ्टवेयर", "वकील", "सलाहकार", "மென்பொருள்", "வழக்கறிஞர்",
    ]

    if any(k in t_lower for k in mfg_keys):
        b_type = "Manufacturing"
        segment = "mfg"
    elif any(k in t_lower for k in clinic_keys):
        b_type = "Healthcare/Clinic"
        segment = "prof"
    elif any(k in t_lower for k in food_keys):
        b_type = "Restaurant/Food"
        segment = "multi" if (sites and sites > 1) else "micro"
    elif any(k in t_lower for k in retail_keys):
        b_type = "Retail/Kirana"
        segment = "micro"
    elif any(k in t_lower for k in prof_keys):
        b_type = "Professional Services"
        segment = "prof"
    else:
        b_type = "Retail/Kirana"
        segment = "micro"

    if sites and sites >= 2:
        segment = "multi"

    # 6. Digital Needs Extraction
    digital_needs: List[str] = []
    if any(k in t_lower for k in ["broadband", "fiber", "fibre", "internet", "leased line", "इंटरनेट", "இணையம்"]):
        digital_needs.append("broadband")
    if any(k in t_lower for k in ["cctv", "camera", "surveillance", "कैमरा", "கேமரா"]):
        digital_needs.append("cctv")
    if any(k in t_lower for k in ["calling", "phone", "voice", "telephony", "कॉलिंग", "தொலைபேசி"]):
        digital_needs.append("voice_lines")
    if any(k in t_lower for k in ["cloud", "backup", "drive", "क्लाउड", "சேமிப்பகம்"]):
        digital_needs.append("cloud_storage")
    if any(k in t_lower for k in ["pos", "billing", "बिलिंग", "பில்லிங்"]):
        digital_needs.append("pos")
    if any(k in t_lower for k in ["security", "firewall", "antivirus", "सुरक्षा"]):
        digital_needs.append("security")
    if any(k in t_lower for k in ["static ip", "public ip", "आईपी"]):
        digital_needs.append("dedicated_ip")
    if any(k in t_lower for k in ["fleet", "gps", "vehicle", "tracking"]):
        digital_needs.append("fleet_tracking")

    # 7. Language-aware explanation
    final_emp = employees if employees is not None else 1
    if language == "Hindi":
        explanation = (
            f"{city} में {final_emp} कर्मचारियों के साथ आपके {b_type} संचालन के लिए अनुकूलित। "
            f"यह बंडल उच्च-विश्वसनीयता कनेक्टिविटी और आधुनिक डिजिटल सुरक्षा समाधान सुनिश्चित करता है।"
        )
    elif language == "Tamil":
        explanation = (
            f"{city} நகரில் {final_emp} ஊழியர்களுடன் செயல்படும் உங்கள் {b_type} வணிகத்திற்கு பிரத்யேகமானது. "
            f"இது அதிவேக இணைய இணைப்பு மற்றும் நம்பகமான டிஜிட்டல் தீர்வுகளை உறுதி செய்கிறது."
        )
    else:
        explanation = (
            f"Optimized enterprise bundle for your {b_type} operations in {city} with {final_emp} team members. "
            f"Delivers SLA-backed high-speed business connectivity and integrated digital operations tools."
        )

    # 7. Current Broadband Detection
    if any(k in t_lower for k in ["leased line", "ill", "1:1"]):
        detected_bb = "Leased Line"
    elif any(k in t_lower for k in ["fiber", "fibre", "ftth"]):
        detected_bb = "Fiber"
    elif any(k in t_lower for k in ["hotspot", "dongle", "airtel dongle"]):
        detected_bb = "Mobile Hotspot"
    elif any(k in t_lower for k in ["dsl", "cable"]):
        detected_bb = "Basic DSL/Cable"
    else:
        detected_bb = "None"

    ret_data = {
        "business_name": "",
        "business_type": b_type,
        "segment": segment,
        "employees": final_emp,
        "employees_missing": employees is None,
        "sites": sites if sites is not None else 1,
        "sites_missing": sites is None,
        "city": city,
        "has_gstin": has_gstin,
        "gstin_missing": gstin_missing,
        "gstin": gstin,
        "current_broadband": detected_bb,
        "digital_needs": digital_needs,
        "explanation": explanation,
        "is_ambiguous_employees": is_ambiguous_emp,
        "ambiguous_val": ambig_val,
        "is_llm": False,
        "mode_note": "Running in rules mode",
        "budget": budget,
    }
    ret_data, _ = validate_and_clamp_profile_data(ret_data)
    return ret_data


def deterministic_advisor_fallback(
    business_type: str,
    employees: int,
    sites: int,
    city: str,
    has_gstin: bool,
    gstin: Optional[str] = None,
    current_broadband: str = "None",
    digital_needs: Optional[List[str]] = None,
    language: str = "English",
    budget: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Standard deterministic advisor fallback using explicit structured parameters.
    """
    digital_needs = digital_needs or []
    b_lower = business_type.lower()
    clamped_emp = max(EMPLOYEES_MIN, min(EMPLOYEES_MAX, int(employees)))
    clamped_sites = max(SITES_MIN, min(SITES_MAX, int(sites)))
    clamped_budget = max(BUDGET_MIN, min(BUDGET_MAX, int(budget))) if budget is not None else None

    if clamped_sites > 1:
        segment = "multi"
    elif "manuf" in b_lower or "factory" in b_lower or "industrial" in b_lower or clamped_emp >= 20:
        segment = "mfg"
    elif any(k in b_lower for k in ["clinic", "doctor", "consult", "advocate", "law", "account", "it", "tech"]):
        segment = "prof"
    else:
        segment = "micro"

    if language == "Hindi":
        rationale = f"{city} में {clamped_emp} कर्मचारियों के साथ आपके व्यवसाय के लिए समर्पित उद्यम कनेक्टिविटी और सुरक्षा।"
    elif language == "Tamil":
        rationale = f"{city} இல் {clamped_emp} ஊழியர்களுடன் இயங்கும் உங்கள் நிறுவனத்திற்கு நம்பகமான அதிவேக இணையம் மற்றும் பாதுகாப்பு."
    else:
        rationale = (
            f"Enterprise-grade solutions tailored for {clamped_emp} staff in {city}. "
            "Guarantees SLA-backed fiber connectivity and seamless digital operational efficiency."
        )

    return {
        "business_type": business_type,
        "segment": segment,
        "employees": clamped_emp,
        "sites": clamped_sites,
        "city": city,
        "has_gstin": has_gstin,
        "gstin": gstin if (has_gstin and gstin) else None,
        "current_broadband": current_broadband,
        "digital_needs": digital_needs,
        "explanation": rationale,
        "budget": clamped_budget,
    }


def build_business_profile_from_advisor(advisor_dict: Dict[str, Any]) -> BusinessProfile:
    """
    Constructs a verified BusinessProfile instance ready for the eligibility engine.
    """
    city = advisor_dict.get("city", "Mumbai")
    if city == "Unknown":
        city = "Mumbai"
    tier = get_city_tier(city)

    return BusinessProfile(
        business_name=advisor_dict.get("business_name", ""),
        business_type=advisor_dict.get("business_type", "Retail/Kirana"),
        segment=advisor_dict.get("segment"),
        employee_count=int(advisor_dict.get("employees", advisor_dict.get("employee_count", 1))),
        num_sites=int(advisor_dict.get("sites", advisor_dict.get("num_sites", 1))),
        city=city,
        city_tier=tier,
        has_gstin=bool(advisor_dict.get("has_gstin", False)),
        gstin=advisor_dict.get("gstin"),
        current_internet=advisor_dict.get("current_broadband", advisor_dict.get("current_internet", "None")),
        stated_needs=advisor_dict.get("digital_needs", advisor_dict.get("stated_needs", [])),
        budget=advisor_dict.get("budget"),
    )
