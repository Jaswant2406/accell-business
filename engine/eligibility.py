"""Rules-based deterministic eligibility engine for Accel Business Udyam Digital."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd

from kyc.registry import (
    get_city_tier,
    get_city_tier_info,
    load_catalogue,
    lookup_gstin,
    validate_gstin_format,
)


@dataclass
class BusinessProfile:
    """Structured customer business profile."""
    business_name: str = ""
    business_type: str = "General"  # e.g., Clinic, Kirana, Restaurant, Manufacturer
    segment: Optional[str] = None   # "micro", "prof", "multi", "mfg" (auto-inferred if None)
    employee_count: int = 1
    num_sites: int = 1
    city: str = ""
    city_tier: Optional[int] = None # 1 or 2 (derived from city via smb_leads if None)
    city_tier_unconfirmed: bool = False
    city_tier_disclosure: Optional[str] = None
    has_gstin: bool = False
    gstin: Optional[str] = None
    gstin_pending_verification: bool = False
    gstin_disclosure: Optional[str] = None
    static_ip_disclosure: Optional[str] = None
    budget: Optional[int] = None
    current_internet: str = "None"  # None, Mobile hotspot, Home broadband, Business broadband, Leased line
    stated_needs: List[str] = field(default_factory=list) # e.g. ["broadband", "cctv", "pos", "security", "telephony", "backup", "website"]
    custom_quantities: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        # Clamp employee_count, num_sites, and budget into sensible ranges
        try:
            self.employee_count = max(1, min(10000, int(self.employee_count)))
        except (TypeError, ValueError):
            self.employee_count = 1

        try:
            self.num_sites = max(1, min(500, int(self.num_sites)))
        except (TypeError, ValueError):
            self.num_sites = 1

        if self.budget is not None:
            try:
                self.budget = max(0, min(1000000, int(self.budget)))
            except (TypeError, ValueError):
                self.budget = None

        # Auto-derive city tier and check if city is unconfirmed
        if self.city_tier is None:
            tier, is_known = get_city_tier_info(self.city)
            self.city_tier = tier
            if not is_known and self.city and self.city.strip():
                self.city_tier_unconfirmed = True
                self.city_tier_disclosure = "We couldn't confirm your city tier, assuming Tier 2"
        # Check if GST registration declared without a number
        if self.has_gstin and (not self.gstin or not str(self.gstin).strip()):
            self.gstin_pending_verification = True
            self.gstin_disclosure = (
                "Please provide your 15-character GSTIN before GSTIN-exclusive products "
                "can be activated (the number will be verified at KYC)."
            )
        # Auto-infer segment if not explicitly provided
        if not self.segment:
            self.segment = infer_segment(self.business_type, self.num_sites, self.employee_count)


def infer_segment(business_type: str, num_sites: int, employee_count: int) -> str:
    """Infer customer segment ('micro', 'prof', 'multi', 'mfg') from business attributes."""
    if num_sites >= 2:
        return "multi"
    
    b_type = (business_type or "").lower()
    
    # Manufacturing indicators
    mfg_keywords = ["mfg", "manufactur", "factory", "auto", "parts", "textile", "plant", "fabricat", "industr"]
    if any(k in b_type for k in mfg_keywords) or employee_count >= 30:
        return "mfg"
    
    # Professional indicators
    prof_keywords = ["clinic", "doctor", "health", "physio", "dental", "law", "advocate", "legal", "ca", "audit",
                     "account", "consult", "agency", "architect", "office", "lab", "diagnost", "realty"]
    if any(k in b_type for k in prof_keywords):
        return "prof"
    
    # Default small / micro business (kirana, bakery, shop, restaurant single site)
    return "micro"


def compute_unlock_suggestion(
    row: pd.Series,
    profile: BusinessProfile,
    gstin_record: Optional[Dict[str, Any]] = None,
    eligible_pids: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Deterministically computes exact requirements that would make an ineligible product eligible.
    Never invents requirements; strictly references product_catalogue rules.
    Returns structured unlock criteria and exact plain-language unlock text.
    """
    pid = str(row["product_id"] if "product_id" in row else row.name)
    pname = str(row["product_name"])

    unlock_actions: List[str] = []
    criteria: Dict[str, Any] = {
        "needs_gstin": False,
        "min_employees_needed": None,
        "min_sites_needed": None,
        "city_tiers_needed": [],
        "missing_dependencies": [],
    }

    # 1. GSTIN requirement
    requires_gst = str(row["requires_gstin"]).upper() == "Y"
    if requires_gst:
        if not profile.has_gstin or not profile.gstin:
            criteria["needs_gstin"] = True
            unlock_actions.append("Provide an active GSTIN registration (statutory requirement)")
        else:
            is_valid_fmt, _ = validate_gstin_format(profile.gstin)
            if not is_valid_fmt:
                criteria["needs_gstin"] = True
                unlock_actions.append("Provide a checksum-valid 15-character GSTIN")
            else:
                if gstin_record is None:
                    gstin_record = lookup_gstin(profile.gstin)
                if not gstin_record:
                    criteria["needs_gstin"] = True
                    unlock_actions.append("Verify GSTIN is registered in the GSTN portal")
                elif str(gstin_record.get("status", "")).strip().lower() != "active":
                    criteria["needs_gstin"] = True
                    status = gstin_record.get("status", "Inactive")
                    unlock_actions.append(f"Restore GSTIN status to Active (currently {status})")

    # 2. City Tier requirement
    tiers_allowed = [int(t.strip()) for t in str(row["available_city_tiers"]).split(";") if t.strip().isdigit()]
    criteria["city_tiers_needed"] = tiers_allowed
    current_tier = profile.city_tier or 2
    if current_tier not in tiers_allowed:
        tier_names = "Tier 1" if tiers_allowed == [1] else f"Tier {','.join(map(str, tiers_allowed))}"
        unlock_actions.append(f"Service available in {tier_names} locations (current city is Tier {current_tier})")

    # 3. Site count requirement
    min_sites = int(row["min_sites"])
    criteria["min_sites_needed"] = min_sites
    if profile.num_sites < min_sites:
        unlock_actions.append(f"Expand operations to at least {min_sites} operating sites (currently {profile.num_sites})")

    # 4. Employee count requirement
    min_emp = int(row["min_employees"])
    criteria["min_employees_needed"] = min_emp
    if profile.employee_count < min_emp:
        unlock_actions.append(f"Grow workforce to at least {min_emp} employees (currently {profile.employee_count})")

    # 5. Dependency requirement (requires_one_of)
    req_one_of = str(row["requires_one_of"]).strip() if pd.notna(row.get("requires_one_of")) else ""
    if req_one_of and req_one_of.lower() not in ["nan", "none", ""]:
        parent_options = [p.strip() for p in req_one_of.split("|") if p.strip()]
        criteria["missing_dependencies"] = parent_options
        if eligible_pids is not None:
            has_parent = any(p in eligible_pids for p in parent_options)
            if not has_parent:
                unlock_actions.append(f"Subscribe to a base connectivity plan (requires one of: {', '.join(parent_options)})")

    unlock_text = "; ".join(unlock_actions) if unlock_actions else "Currently eligible"

    return {
        "product_id": pid,
        "product_name": pname,
        "is_eligible": len(unlock_actions) == 0,
        "unlock_actions": unlock_actions,
        "unlock_text": unlock_text,
        "criteria": criteria,
    }


def evaluate_product_eligibility(
    row: pd.Series,
    profile: BusinessProfile,
    gstin_record: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """Check individual product eligibility against city tier, size limits, and GSTIN requirements."""
    pid = str(row["product_id"] if "product_id" in row else row.name)
    pname = str(row["product_name"])
    
    failure_reasons: List[str] = []

    # 1. GSTIN check
    requires_gst = str(row["requires_gstin"]).upper() == "Y"
    if requires_gst:
        if not profile.has_gstin or not profile.gstin:
            failure_reasons.append("Requires an active GSTIN registration")
        else:
            is_valid_fmt, fmt_msg = validate_gstin_format(profile.gstin)
            if not is_valid_fmt:
                failure_reasons.append(f"Requires a valid GSTIN ({fmt_msg})")
            else:
                if gstin_record is None:
                    gstin_record = lookup_gstin(profile.gstin)
                if not gstin_record:
                    failure_reasons.append("GSTIN not found in mock GST registry")
                else:
                    status = str(gstin_record.get("status", "")).strip()
                    if status.lower() != "active":
                        failure_reasons.append(f"GSTIN is {status} in registry (Active status required)")

    # 2. City Tier check
    tiers_allowed = [int(t.strip()) for t in str(row["available_city_tiers"]).split(";") if t.strip().isdigit()]
    current_tier = profile.city_tier or 2
    if current_tier not in tiers_allowed:
        failure_reasons.append(f"Available only in Tier {','.join(map(str, tiers_allowed))} cities (current location is Tier {current_tier})")

    # 3. Site count check
    min_sites = int(row["min_sites"])
    if profile.num_sites < min_sites:
        failure_reasons.append(f"Requires at least {min_sites} site(s) (current: {profile.num_sites})")

    # 4. Employee count check
    min_emp = int(row["min_employees"])
    if profile.employee_count < min_emp:
        failure_reasons.append(f"Requires at least {min_emp} employee(s) (current: {profile.employee_count})")

    if failure_reasons:
        return False, "; ".join(failure_reasons)

    return True, "Eligible"


def determine_quantity(row: pd.Series, profile: BusinessProfile) -> Tuple[int, str]:
    """Determine product quantity by unit according to business rules with plain-language assumption."""
    pid = str(row["product_id"] if "product_id" in row else row.name)
    unit = str(row["unit"]).lower()
    
    # Check custom quantity override first
    if pid in profile.custom_quantities:
        q = max(1, int(profile.custom_quantities[pid]))
        return q, f"Custom user quantity of {q}"

    if unit == "per site":
        q = max(1, profile.num_sites)
        return q, f"1 deployment per site across {profile.num_sites} site(s)"
    
    elif unit == "per user":
        q = max(1, profile.employee_count)
        return q, f"1 user seat per employee ({profile.employee_count} employees)"
    
    elif unit == "per line":
        # Business postpaid lines
        q = max(1, profile.employee_count)
        return q, f"1 business mobile connection per employee ({profile.employee_count} lines)"
    
    elif unit == "per account":
        return 1, "1 primary organizational subscription account"
    
    elif unit == "per counter":
        q = max(1, profile.num_sites)
        return q, f"1 POS billing counter per site ({profile.num_sites} counter(s))"
    
    elif unit == "per camera":
        q = max(2, profile.num_sites * 2)
        return q, f"Standard coverage: 2 cloud CCTV cameras per site ({q} cameras total)"
    
    elif unit == "per device":
        if pid == "P20":  # Endpoint Security
            q = max(1, profile.employee_count)
            return q, f"1 antivirus license per employee PC/workstation ({profile.employee_count} devices)"
        elif pid == "P24":  # Machine Monitoring IoT
            q = max(2, min(profile.employee_count, 10))
            return q, f"Standard industrial starter kit: {q} machine sensors"
        return 1, "1 device kit"
    
    elif unit == "per vehicle":
        q = max(1, min(profile.num_sites, 5))
        return q, f"Default fleet tracking for {q} company vehicle(s)"
    
    elif unit == "per ip":
        return 1, "1 static public IPv4 allocation for secure remote access"
    
    elif unit == "per channel":
        q = max(2, min(profile.employee_count, 8))
        return q, f"{q} SIP trunk channels for simultaneous customer calls"
    
    elif unit == "per number":
        return 1, "1 dedicated 1800 toll-free virtual number"
    
    elif unit == "per pack":
        return 1, "1 starter pack (10,000 promotional and transactional SMS/month)"
    
    return 1, "1 unit"


def matches_stated_need(pid: str, needs: List[str], category: str = "") -> bool:
    """Public helper to check if a product relates to user's stated needs."""
    return _matches_stated_needs(pid, category, needs)


PRIMARY_CONNECTIVITY_PIDS = ["P01", "P02", "P03", "P04", "P05", "P06"]

MULTILINGUAL_NEEDS_MAPPING: Dict[str, List[str]] = {
    # Connectivity (for classification & budget fit utility)
    "broadband": ["P01", "P02", "P03", "P04", "P05", "P06"],
    "internet": ["P01", "P02", "P03", "P04", "P05", "P06"],
    "fibre": ["P01", "P02", "P03"],
    "fiber": ["P01", "P02", "P03"],
    "ब्रॉडबैंड": ["P01", "P02", "P03", "P04", "P05", "P06"],
    "इंटरनेट": ["P01", "P02", "P03", "P04", "P05", "P06"],
    "இணையம்": ["P01", "P02", "P03", "P04", "P05", "P06"],
    "பிராட்பேண்ட்": ["P01", "P02", "P03", "P04", "P05", "P06"],

    # Mobile Lines (Starter P07 vs Priority P08)
    "mobile": ["P07"],
    "calling": ["P07"],
    "postpaid": ["P07"],
    "sim": ["P07"],
    "priority mobile": ["P08"],
    "roaming": ["P08"],
    "मोबाइल": ["P07"],
    "மொபைல்": ["P07"],

    # Failover / Redundancy Link (P09)
    "failover": ["P09"],
    "backup link": ["P09"],
    "backup connectivity": ["P09"],
    "backup internet": ["P09"],
    "automatic backup connectivity": ["P09"],
    "automatic backup connectivity to prevent downtime": ["P09"],
    "automatic backup": ["P09"],
    "prevent downtime": ["P09"],
    "downtime": ["P09"],
    "redundancy": ["P09"],
    "redundant": ["P09"],
    "redundant link": ["P09"],
    "फेलओवर": ["P09"],
    "बैकअप कनेक्टिविटी": ["P09"],
    "डाउनटाइम": ["P09"],
    "डाउनटाइम रोकें": ["P09"],
    "காப்பு இணைப்பு": ["P09"],
    "செயலிழப்பைத் தடுக்க": ["P09"],
    "இணைப்பு காப்பு": ["P09"],

    # Managed SD-WAN
    "sdwan": ["P10"],
    "sd-wan": ["P10"],
    "multi-site": ["P10"],
    "एसडी-वैन": ["P10"],

    # Static IP
    "static ip": ["P11"],
    "dedicated_ip": ["P11"],
    "dedicated ip": ["P11"],
    "public ip": ["P11"],
    "स्थिर आईपी": ["P11"],
    "நிலையான ஐபி": ["P11"],

    # Cloud Telephony / SIP Trunk (P12)
    "telephony": ["P12"],
    "voice_lines": ["P12"],
    "voice lines": ["P12"],
    "voice": ["P12"],
    "sip": ["P12"],
    "ivr": ["P12"],
    "फ़ोन": ["P12"],
    "தொலைபேசி": ["P12"],

    # Toll-Free 1800 Number (P13) - Only when explicitly requested
    "tollfree": ["P13"],
    "toll-free": ["P13"],
    "1800": ["P13"],
    "toll free": ["P13"],
    "टोल फ्री": ["P13"],
    "கட்டணமில்லா எண்": ["P13"],

    # SMS Pack (P14)
    "sms": ["P14"],
    "alerts": ["P14"],
    "promotions": ["P14"],
    "एसएमएस": ["P14"],
    "குறுஞ்செய்தி": ["P14"],

    # WhatsApp Business API (P15)
    "whatsapp": ["P15"],
    "व्हाट्सएप": ["P15"],
    "வாட்ஸ்அப்": ["P15"],

    # Cloud Email & Office Suite (P16)
    "email": ["P16"],
    "office": ["P16"],
    "suite": ["P16"],
    "productivity": ["P16"],
    "ईमेल": ["P16"],
    "மின்னஞ்சல்": ["P16"],

    # Cloud Backup (P17)
    "backup": ["P17"],
    "cloud backup": ["P17"],
    "cloud_storage": ["P17"],
    "storage": ["P17"],
    "क्लाउड बैकअप": ["P17"],
    "மேகக்கணி காப்புப்பிரதி": ["P17"],

    # Website Starter (P18)
    "website": ["P18"],
    "domain": ["P18"],
    "वेबसाइट": ["P18"],
    "வலைத்தளம்": ["P18"],

    # POS & Billing & Payments / UPI (P19)
    "pos": ["P19"],
    "billing": ["P19"],
    "payments": ["P19"],
    "upi": ["P19"],
    "बिलिंग": ["P19"],
    "பில்லிங்": ["P19"],
    "விற்பனை முனை": ["P19"],

    # Endpoint Security / Antivirus (P20)
    "security": ["P20"],
    "antivirus": ["P20"],
    "endpoint": ["P20"],
    "सुरक्षा": ["P20"],
    "பாதுகாப்பு": ["P20"],

    # Managed Firewall (P21)
    "firewall": ["P21"],
    "फ़ायरवॉल": ["P21"],
    "ஃபயர்வால்": ["P21"],
    "cybersecurity": ["P21"],
    "network security": ["P21"],

    # Secure Wi-Fi with Guest Network (P22)
    "wifi": ["P22"],
    "wi-fi": ["P22"],
    "guest wifi": ["P22"],
    "वाईफाई": ["P22"],
    "வைஃபை": ["P22"],

    # Cloud CCTV (P23)
    "cctv": ["P23"],
    "camera": ["P23"],
    "surveillance": ["P23"],
    "surveillance_cctv": ["P23"],
    "कैमरा": ["P23"],
    "கண்காணிப்பு கேமரா": ["P23"],
    "सीसीटीवी": ["P23"],

    # Machine Monitoring IoT (P24) - Only for machinery / plant IoT
    "iot": ["P24"],
    "machine": ["P24"],
    "machine monitoring": ["P24"],
    "sensors": ["P24"],
    "मशीन": ["P24"],
    "आईओटी": ["P24"],
    "சென்சார்": ["P24"],
    "இயந்திரம்": ["P24"],

    # Fleet Tracker (P25) - Only for vehicle / fleet tracking
    "fleet": ["P25"],
    "fleet_tracking": ["P25"],
    "vehicle": ["P25"],
    "vehicles": ["P25"],
    "tracking": ["P25"],
    "gps": ["P25"],
    "वाहन": ["P25"],
    "வாகனம்": ["P25"],
}


P09_FAILOVER_INDICATORS = [
    "backup connectivity",
    "automatic backup connectivity",
    "prevent downtime",
    "backup link",
    "backup internet",
    "automatic backup",
    "failover",
    "downtime",
    "redundancy",
    "redundant",
    "फेलओवर",
    "बैकअप कनेक्टिविटी",
    "डाउनटाइम",
    "डाउनटाइम रोकें",
    "காப்பு இணைப்பு",
    "செயலிழப்பைத் தடுக்க",
    "இணைப்பு காப்பு",
]


def matches_stated_need(pid: str, needs: List[str], category: str = "") -> bool:
    """Public helper to check if a product relates to user's stated needs."""
    return _matches_stated_needs(pid, category, needs)


def _matches_stated_needs(pid: str, cat: str, needs: List[str]) -> bool:
    """Check if product relates to user's stated needs using robust multilingual matching."""
    clean_needs = [n.lower() for n in needs]
    if not clean_needs:
        return False
    
    for need in clean_needs:
        # Prevent link failover / downtime phrases from matching Cloud Backup (P17)
        if pid == "P17" and any(ind in need for ind in P09_FAILOVER_INDICATORS):
            continue

        # Match P09 explicitly on failover / backup connectivity / prevent downtime phrases
        if pid == "P09" and any(ind in need for ind in P09_FAILOVER_INDICATORS):
            return True

        for kw, pids in MULTILINGUAL_NEEDS_MAPPING.items():
            if kw in need and pid in pids:
                return True
    return False


def recommend_products(profile: BusinessProfile) -> Dict[str, Any]:
    """
    Deterministic rules engine to decide products for a business profile.
    Enforces strict business rules:
      - At most ONE primary connectivity product (P01-P06) per site, selected by stated need.
      - Unselected eligible connectivity options surfaced as 'alternatives'.
      - Only products explicitly stated in needs or required dependencies are placed in the bundle.
      - Other eligible products placed in 'optional_addons' outside totals.
      - Automatic budget compliance if profile.budget is specified.
    """
    df = load_catalogue()
    gstin_record = lookup_gstin(profile.gstin) if profile.gstin else None
    
    # 1. Evaluate baseline eligibility for all 25 products
    catalogue_status: Dict[str, Dict[str, Any]] = {}
    eligible_pids: Set[str] = set()
    
    for _, row in df.iterrows():
        pid = str(row["product_id"])
        is_elig, reason = evaluate_product_eligibility(row, profile, gstin_record)
        unlock_info = compute_unlock_suggestion(row, profile, gstin_record)
        catalogue_status[pid] = {
            "product_id": pid,
            "product_name": str(row["product_name"]),
            "category": str(row["category"]),
            "unit": str(row["unit"]),
            "price_min": int(row["price_min_inr_per_month"]),
            "price_max": int(row["price_max_inr_per_month"]),
            "one_time_setup": int(row["one_time_setup_inr"]),
            "min_contract_months": int(row["min_contract_months"]),
            "typical_install_days": int(row["typical_install_days"]),
            "requires_one_of": str(row["requires_one_of"]) if pd.notna(row["requires_one_of"]) else "",
            "target_segments": str(row["target_segments"]),
            "eligible": is_elig,
            "reason": reason,
            "unlock_requirement": unlock_info["unlock_text"] if not is_elig else "Already eligible",
            "unlock_actions": unlock_info["unlock_actions"],
        }
        if is_elig:
            eligible_pids.add(pid)

    # 2. Select initial bundle
    selected_pids: Set[str] = set()
    reasons_map: Dict[str, str] = {}
    segment = profile.segment or "micro"
    needs = profile.stated_needs
    needs_text = " ".join([str(n).lower() for n in needs])
    
    # -------------------------------------------------------------------------
    # RULE 3a: Select EXACTLY ONE primary connectivity product per site
    # -------------------------------------------------------------------------
    conn_keywords = [
        "broadband", "internet", "fibre", "fiber", "connect", "wifi", "wi-fi",
        "wireless", "airfiber", "fwa", "leased line", "leased", "dedicated",
        "sla", "ill", "1g", "1 gbps", "1gbps", "gigabit",
        "ब्रॉडबैंड", "इंटरनेट", "இணையம்", "பிராட்பேண்ட்"
    ]
    needs_conn = any(kw in needs_text for kw in conn_keywords) or \
                 profile.current_internet in ["None", "Mobile hotspot", "Home broadband"] or \
                 len(needs) == 0

    selected_primary: Optional[str] = None
    if needs_conn:
        is_1g = any(kw in needs_text for kw in ["1g", "1 gbps", "1gbps", "gigabit", "1 ஜிபி", "1 जीबी"])
        is_dedicated = any(kw in needs_text for kw in ["dedicated", "leased line", "leased", "sla", "ill", "समर्पित", "குத்தகை கோடு"]) or (segment == "mfg" and profile.employee_count >= 10)
        is_wireless = any(kw in needs_text for kw in ["wireless", "no fibre", "no fiber", "airfiber", "fwa", "वायरलेस", "வயர்லெஸ்"])

        if is_1g:
            if "P03" in eligible_pids:
                selected_primary = "P03"
                reasons_map["P03"] = "Biz Fibre 1 Gbps ultra-high throughput business fibre with priority support"
            elif "P02" in eligible_pids:
                selected_primary = "P02"
                reasons_map["P02"] = f"Biz Fibre 300 Mbps primary connection (Biz Fibre 1G locked: {catalogue_status['P03']['reason']})"
            elif "P01" in eligible_pids:
                selected_primary = "P01"
                reasons_map["P01"] = f"Biz Fibre 100 Mbps primary connection (Biz Fibre 1G locked: {catalogue_status['P03']['reason']})"

        elif is_dedicated:
            if profile.employee_count >= 25 and "P06" in eligible_pids:
                selected_primary = "P06"
                reasons_map["P06"] = "Internet Leased Line 100 Mbps (1:1 dedicated bandwidth, 99.9% enterprise SLA)"
            elif profile.employee_count >= 10 and "P05" in eligible_pids:
                selected_primary = "P05"
                reasons_map["P05"] = "Internet Leased Line 20 Mbps (1:1 dedicated bandwidth, 99.5% enterprise SLA)"
            elif "P02" in eligible_pids:
                selected_primary = "P02"
                reasons_map["P02"] = f"Biz Fibre 300 Mbps primary connection (Internet Leased Line locked: {catalogue_status['P05']['reason']})"
            elif "P01" in eligible_pids:
                selected_primary = "P01"
                reasons_map["P01"] = f"Biz Fibre 100 Mbps primary connection (Internet Leased Line locked: {catalogue_status['P05']['reason']})"

        elif is_wireless or (profile.current_internet == "None" and "wireless" in needs_text):
            if "P04" in eligible_pids:
                selected_primary = "P04"
                reasons_map["P04"] = "Biz 5G AirFiber 100 Mbps wireless broadband for sites without fibre"
            elif "P01" in eligible_pids:
                selected_primary = "P01"
                reasons_map["P01"] = "Biz Fibre 100 Mbps high-speed business broadband"
            elif "P02" in eligible_pids:
                selected_primary = "P02"
                reasons_map["P02"] = "Biz Fibre 300 Mbps business broadband"

        else:
            # General / standard broadband
            if segment in ["prof", "multi"] or profile.employee_count > 5:
                if "P02" in eligible_pids:
                    selected_primary = "P02"
                    reasons_map["P02"] = f"Biz Fibre 300 Mbps high-performance business broadband across {profile.num_sites} site(s)"
                elif "P01" in eligible_pids:
                    selected_primary = "P01"
                    reasons_map["P01"] = f"Biz Fibre 100 Mbps business broadband across {profile.num_sites} site(s)"
            else: # micro or <= 5 employees
                if "P01" in eligible_pids:
                    selected_primary = "P01"
                    reasons_map["P01"] = "Cost-effective Biz Fibre 100 Mbps unlimited business broadband"
                elif "P04" in eligible_pids:
                    selected_primary = "P04"
                    reasons_map["P04"] = "Plug-and-play Biz 5G AirFiber 100 Mbps wireless broadband"
                elif "P02" in eligible_pids:
                    selected_primary = "P02"
                    reasons_map["P02"] = "Biz Fibre 300 Mbps business broadband"

        if selected_primary:
            selected_pids.add(selected_primary)

    # -------------------------------------------------------------------------
    # RULE 3b: Only recommend products that were stated as needs or dependencies
    # Primary connectivity is NEVER added in this loop (handled above)
    # -------------------------------------------------------------------------
    static_ip_disclosure: Optional[str] = None
    needs_static_ip = any(kw in needs_text for kw in ["static ip", "dedicated_ip", "dedicated ip", "public ip", "स्थिर आईपी", "நிலையான ஐபி"])
    if needs_static_ip and selected_primary in ["P05", "P06"]:
        static_ip_disclosure = "Static IP (P11) is only available with Biz Fibre 100/300/1G in our catalogue"

    for pid in eligible_pids:
        if pid in PRIMARY_CONNECTIVITY_PIDS:
            continue
        row_info = catalogue_status[pid]
        pname = row_info["product_name"]
        cat = row_info["category"]
        
        # Stated needs match
        if _matches_stated_needs(pid, cat, needs):
            # If product requires a base connection, verify compatibility with selected_primary
            req_str = row_info["requires_one_of"]
            if req_str and selected_primary:
                candidates = [c.strip() for c in req_str.split("|") if c.strip()]
                if selected_primary not in candidates:
                    # Incompatible with chosen primary connectivity without adding a second connection
                    if pid == "P11" and selected_primary in ["P05", "P06"]:
                        static_ip_disclosure = "Static IP (P11) is only available with Biz Fibre 100/300/1G in our catalogue"
                    continue

            selected_pids.add(pid)
            if pid not in reasons_map:
                reasons_map[pid] = f"Matched your request for {pname} to boost business operations"
        
        # When needs list is completely empty, provide minimal segment defaults
        elif len(needs) == 0:
            if segment == "micro" and pid in ["P07", "P19"]:
                selected_pids.add(pid)
                reasons_map[pid] = f"Recommended standard for micro businesses: {pname}"
            elif segment == "prof" and pid in ["P16", "P20"]:
                selected_pids.add(pid)
                reasons_map[pid] = f"Digital productivity for professional offices: {pname}"
            elif segment == "multi" and pid in ["P09", "P23"]:
                selected_pids.add(pid)
                reasons_map[pid] = f"Essential multi-site infrastructure: {pname}"
            elif segment == "mfg" and pid in ["P21", "P24"]:
                selected_pids.add(pid)
                reasons_map[pid] = f"Industrial-grade security & asset monitoring: {pname}"

    # -------------------------------------------------------------------------
    # RULE 3c: Resolve dependencies (requires_one_of)
    # Auto-add cheapest valid parent inside bundle and explain why
    # -------------------------------------------------------------------------
    auto_added_info: Dict[str, str] = {}
    has_primary_conn = any(p in selected_pids for p in PRIMARY_CONNECTIVITY_PIDS)
    changed = True
    while changed:
        changed = False
        for pid in list(selected_pids):
            req_str = catalogue_status[pid]["requires_one_of"]
            if not req_str:
                continue
            candidates = [c.strip() for c in req_str.split("|") if c.strip()]
            if any(c in selected_pids for c in candidates):
                continue

            # If a primary connection is already in the bundle and no candidate can be added
            # without violating single connectivity, drop the dependent product rather than violating dependencies
            if has_primary_conn:
                selected_pids.remove(pid)
                if pid == "P11":
                    static_ip_disclosure = "Static IP (P11) is only available with Biz Fibre 100/300/1G in our catalogue"
                changed = True
                continue

            eligible_parents = [c for c in candidates if c in eligible_pids]
            if not eligible_parents:
                selected_pids.remove(pid)
                changed = True
                continue
            
            # Pick cheapest eligible parent
            cheapest_parent = min(eligible_parents, key=lambda c: catalogue_status[c]["price_min"])
            parent_name = catalogue_status[cheapest_parent]["product_name"]
            dep_name = catalogue_status[pid]["product_name"]
            
            selected_pids.add(cheapest_parent)
            if cheapest_parent in PRIMARY_CONNECTIVITY_PIDS:
                has_primary_conn = True
            auto_msg = f"Auto-added prerequisite {parent_name} (cheapest broadband parent) required for {dep_name}"
            reasons_map[cheapest_parent] = auto_msg
            auto_added_info[cheapest_parent] = auto_msg
            changed = True

    # Fallback if bundle is still empty
    if not selected_pids:
        if "P01" in eligible_pids:
            selected_pids.add("P01")
            reasons_map["P01"] = "Baseline enterprise connectivity: Biz Fibre 100 Mbps"
        elif "P02" in eligible_pids:
            selected_pids.add("P02")
            reasons_map["P02"] = "Baseline enterprise connectivity: Biz Fibre 300 Mbps"

    # Construct recommended bundle items
    df_indexed = df.set_index("product_id")
    recommended_bundle: List[Dict[str, Any]] = []
    
    for pid in sorted(list(selected_pids)):
        row = df_indexed.loc[pid]
        qty, assumption = determine_quantity(row, profile)
        p_info = catalogue_status[pid]
        
        recommended_bundle.append({
            "product_id": pid,
            "product_name": p_info["product_name"],
            "category": p_info["category"],
            "unit": p_info["unit"],
            "quantity": qty,
            "assumption": assumption,
            "price_min": p_info["price_min"],
            "price_max": p_info["price_max"],
            "quoted_price": p_info["price_min"],
            "one_time_setup": p_info["one_time_setup"],
            "min_contract_months": p_info["min_contract_months"],
            "typical_install_days": p_info["typical_install_days"],
            "reason": reasons_map.get(pid, f"Tailored for {segment} segment"),
            "auto_added": pid in auto_added_info,
        })

    # -------------------------------------------------------------------------
    # RULE 3c: Automatic budget compliance
    # -------------------------------------------------------------------------
    budget_fit_summary: Optional[Dict[str, Any]] = None
    effective_budget = profile.budget
    if effective_budget is not None and effective_budget > 0:
        from engine.budget_fit import fit_bundle_to_budget
        b_res = fit_bundle_to_budget(profile, monthly_budget=effective_budget)
        curr_total = sum(it["price_min"] * it["quantity"] for it in recommended_bundle)
        if curr_total > effective_budget:
            # Bundle exceeded budget - adopt budget-fitted selection completely
            recommended_bundle = b_res.selected_items
            recommended_bundle.sort(key=lambda x: x["product_id"])
            budget_fit_summary = {
                "budget": effective_budget,
                "fitted_monthly_total": b_res.total_monthly_cost,
                "fitted_setup_total": b_res.total_setup_cost,
                "dropped_items": [
                    {"product_id": d.product_id, "product_name": d.product_name, "cost": d.monthly_cost, "reason": d.reason}
                    for d in b_res.dropped_items
                ],
                "explanation": b_res.explanation,
            }

    # -------------------------------------------------------------------------
    # Surfaced Alternatives & Optional Add-ons outside bundle totals
    # -------------------------------------------------------------------------
    bundle_pids = {it["product_id"] for it in recommended_bundle}

    # Alternatives: unselected eligible primary connectivity options
    alternatives: List[Dict[str, Any]] = []
    for pid in sorted(PRIMARY_CONNECTIVITY_PIDS):
        if pid in eligible_pids and pid not in bundle_pids:
            p_info = catalogue_status[pid]
            alternatives.append({
                "product_id": pid,
                "product_name": p_info["product_name"],
                "category": p_info["category"],
                "unit": p_info["unit"],
                "price_min": p_info["price_min"],
                "price_max": p_info["price_max"],
                "reason": f"Alternative connectivity: {p_info['product_name']}",
            })

    # Optional Add-ons: unselected eligible products outside primary connectivity
    optional_addons: List[Dict[str, Any]] = []
    for pid in sorted(list(eligible_pids)):
        if pid not in bundle_pids and pid not in PRIMARY_CONNECTIVITY_PIDS:
            p_info = catalogue_status[pid]
            row = df_indexed.loc[pid]
            qty, assumption = determine_quantity(row, profile)
            optional_addons.append({
                "product_id": pid,
                "product_name": p_info["product_name"],
                "category": p_info["category"],
                "unit": p_info["unit"],
                "quantity": qty,
                "price_min": p_info["price_min"],
                "price_max": p_info["price_max"],
                "one_time_setup": p_info["one_time_setup"],
                "min_contract_months": p_info["min_contract_months"],
                "typical_install_days": p_info["typical_install_days"],
                "reason": f"Optional business add-on for {segment} segment",
            })

    return {
        "recommended": recommended_bundle,
        "optional_addons": optional_addons,
        "alternatives": alternatives,
        "catalogue_status": catalogue_status,
        "segment": segment,
        "city_tier": profile.city_tier,
        "city_tier_unconfirmed": profile.city_tier_unconfirmed,
        "city_tier_disclosure": profile.city_tier_disclosure,
        "gstin_pending_verification": profile.gstin_pending_verification,
        "gstin_disclosure": profile.gstin_disclosure,
        "static_ip_disclosure": static_ip_disclosure,
        "budget_fit_summary": budget_fit_summary,
    }


def validate_bundle_selection(
    selected_pids: List[str],
    profile: BusinessProfile,
) -> Tuple[bool, List[str], List[Dict[str, Any]]]:
    """
    Validate a user-customised bundle selection.
    Returns:
      - is_valid: bool
      - errors: list of error strings (ineligible products or missing dependencies)
      - dependency_fixes: list of suggested parent additions if any dependency is missing
    """
    df = load_catalogue()
    gstin_record = lookup_gstin(profile.gstin) if profile.gstin else None
    df_indexed = df.set_index("product_id")
    
    errors: List[str] = []
    fixes: List[Dict[str, Any]] = []
    selected_set = set(selected_pids)
    
    # 1. Check each selected product's direct eligibility
    for pid in selected_set:
        if pid not in df_indexed.index:
            errors.append(f"Unknown product {pid}")
            continue
        row = df_indexed.loc[pid]
        is_elig, reason = evaluate_product_eligibility(row, profile, gstin_record)
        if not is_elig:
            errors.append(f"{row['product_name']} ({pid}) is ineligible: {reason}")

    # 2. Check dependencies
    for pid in selected_set:
        if pid not in df_indexed.index:
            continue
        row = df_indexed.loc[pid]
        req_str = str(row["requires_one_of"]) if pd.notna(row["requires_one_of"]) else ""
        if not req_str:
            continue
        
        candidates = [c.strip() for c in req_str.split("|") if c.strip()]
        if not any(c in selected_set for c in candidates):
            # Missing dependency!
            eligible_parents = []
            for c in candidates:
                if c in df_indexed.index:
                    c_row = df_indexed.loc[c]
                    is_elig, _ = evaluate_product_eligibility(c_row, profile, gstin_record)
                    if is_elig:
                        eligible_parents.append(c)
            
            pname = row["product_name"]
            if eligible_parents:
                cheapest = min(eligible_parents, key=lambda c: int(df_indexed.loc[c]["price_min_inr_per_month"]))
                fixes.append({
                    "dependent_pid": pid,
                    "dependent_name": pname,
                    "suggested_parent_pid": cheapest,
                    "suggested_parent_name": df_indexed.loc[cheapest]["product_name"],
                    "candidates": candidates,
                })
                errors.append(f"{pname} requires one of ({' / '.join(candidates)}). Prerequisite '{df_indexed.loc[cheapest]['product_name']}' is recommended.")
            else:
                errors.append(f"{pname} requires one of ({' / '.join(candidates)}), but none are eligible for this business profile.")

    return len(errors) == 0, errors, fixes
