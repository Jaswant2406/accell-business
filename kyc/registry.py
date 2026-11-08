"""Registry and data loader module for mock GSTIN, Udyam, catalogue, and leads."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re
import pandas as pd

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Global caches
_CATALOGUE_DF: Optional[pd.DataFrame] = None
_GSTIN_DF: Optional[pd.DataFrame] = None
_UDYAM_DF: Optional[pd.DataFrame] = None
_LEADS_DF: Optional[pd.DataFrame] = None
_CITY_TIER_CACHE: Optional[Dict[str, int]] = None
_GSTIN_MAP: Optional[Dict[str, Dict[str, Any]]] = None
_UDYAM_MAP: Optional[Dict[str, Dict[str, Any]]] = None

GSTIN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{3}X[A-Z][0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
UDYAM_REGEX = re.compile(r"^UDYAM-[A-Z]{2}-00-\d{7}$")


def _get_file_path(filename: str) -> Path:
    """Find file in ./data or in project root."""
    path = DATA_DIR / filename
    if path.exists():
        return path
    alt = BASE_DIR / filename
    if alt.exists():
        return alt
    raise FileNotFoundError(f"Could not locate data file: {filename}")


def load_catalogue() -> pd.DataFrame:
    """Load product_catalogue.csv using pandas to handle quoted commas correctly."""
    global _CATALOGUE_DF
    if _CATALOGUE_DF is None:
        path = _get_file_path("product_catalogue.csv")
        df = pd.read_csv(path)
        # Clean string fields
        df["product_id"] = df["product_id"].astype(str).str.strip()
        df["category"] = df["category"].astype(str).str.strip()
        df["product_name"] = df["product_name"].astype(str).str.strip()
        df["unit"] = df["unit"].astype(str).str.strip()
        df["available_city_tiers"] = df["available_city_tiers"].astype(str).str.strip()
        df["requires_gstin"] = df["requires_gstin"].astype(str).str.strip().str.upper()
        df["target_segments"] = df["target_segments"].astype(str).str.strip()
        df["requires_one_of"] = df["requires_one_of"].fillna("").astype(str).str.strip()
        _CATALOGUE_DF = df
    return _CATALOGUE_DF


def load_smb_leads() -> pd.DataFrame:
    """Load smb_leads.csv."""
    global _LEADS_DF
    if _LEADS_DF is None:
        path = _get_file_path("smb_leads.csv")
        _LEADS_DF = pd.read_csv(path)
    return _LEADS_DF


def load_gstin_registry() -> pd.DataFrame:
    """Load mock_gstin_registry.csv."""
    global _GSTIN_DF, _GSTIN_MAP
    if _GSTIN_DF is None:
        path = _get_file_path("mock_gstin_registry.csv")
        df = pd.read_csv(path)
        df["gstin"] = df["gstin"].astype(str).str.strip().str.upper()
        _GSTIN_DF = df
        _GSTIN_MAP = {row["gstin"]: row.to_dict() for _, row in df.iterrows()}
    return _GSTIN_DF


def load_udyam_registry() -> pd.DataFrame:
    """Load mock_udyam_registry.csv."""
    global _UDYAM_DF, _UDYAM_MAP
    if _UDYAM_DF is None:
        path = _get_file_path("mock_udyam_registry.csv")
        df = pd.read_csv(path)
        df["udyam_number"] = df["udyam_number"].astype(str).str.strip().str.upper()
        _UDYAM_DF = df
        _UDYAM_MAP = {row["udyam_number"]: row.to_dict() for _, row in df.iterrows()}
    return _UDYAM_DF


def get_city_tier_map() -> Dict[str, int]:
    """Build a case-insensitive dictionary of city to city_tier from smb_leads.csv."""
    global _CITY_TIER_CACHE
    if _CITY_TIER_CACHE is None:
        leads = load_smb_leads()
        mapping = {}
        for _, row in leads.iterrows():
            city = str(row["city"]).strip().lower()
            try:
                tier = int(row["city_tier"])
                mapping[city] = tier
            except (ValueError, TypeError):
                continue
        _CITY_TIER_CACHE = mapping
    return _CITY_TIER_CACHE


def get_city_tier_info(city_name: str) -> Tuple[int, bool]:
    """
    Derive city tier (1 or 2) from city values in smb_leads.csv.
    Returns (tier, is_known). Defaults to (2, False) if unknown.
    """
    if not city_name:
        return 2, False
    cmap = get_city_tier_map()
    clean = city_name.strip().lower()
    if clean in cmap:
        return cmap[clean], True
    return 2, False


def get_city_tier(city_name: str) -> int:
    """Derive city tier (1 or 2) from city values in smb_leads.csv. Defaults to 2 if unknown."""
    return get_city_tier_info(city_name)[0]


def compute_gstin_check_digit(gstin_14: str) -> str:
    """Calculate the official 15th character checksum for a 14-char GSTIN prefix."""
    gstin_14 = gstin_14.upper()
    factor = 1
    total = 0
    for char in gstin_14:
        if char not in GSTIN_CHARS:
            return ""
        val = GSTIN_CHARS.index(char)
        prod = val * factor
        factor = 2 if factor == 1 else 1
        quotient = prod // 36
        remainder = prod % 36
        total += quotient + remainder
    remainder = total % 36
    check_code = (36 - remainder) % 36
    return GSTIN_CHARS[check_code]


def validate_gstin_format(gstin: Optional[str]) -> Tuple[bool, str]:
    """Validate GSTIN structure, 4th PAN character 'X', and checksum."""
    if not gstin or not isinstance(gstin, str):
        return False, "GSTIN is missing or empty"
    clean = gstin.strip().upper()
    if len(clean) != 15:
        return False, f"GSTIN must be exactly 15 characters (got {len(clean)})"
    if not GSTIN_REGEX.match(clean):
        return False, "GSTIN format invalid (expected 2 digits + 5 letters with 'X' at index 4 + 4 digits + 1 letter + 1 char + 'Z' + checksum)"
    expected_check = compute_gstin_check_digit(clean[:14])
    if clean[14] != expected_check:
        return False, f"GSTIN checksum mismatch (expected {expected_check}, found {clean[14]})"
    return True, "Valid GSTIN format and checksum"


def lookup_gstin(gstin: Optional[str]) -> Optional[Dict[str, Any]]:
    """Lookup GSTIN in mock registry."""
    if not gstin:
        return None
    load_gstin_registry()
    assert _GSTIN_MAP is not None
    return _GSTIN_MAP.get(gstin.strip().upper())


def validate_udyam_format(udyam_number: Optional[str]) -> Tuple[bool, str]:
    """Validate Udyam registration number format: UDYAM-XX-00-NNNNNNN."""
    if not udyam_number or not isinstance(udyam_number, str):
        return False, "Udyam number is missing or empty"
    clean = udyam_number.strip().upper()
    if not UDYAM_REGEX.match(clean):
        return False, "Udyam format invalid (expected format: UDYAM-XX-00-NNNNNNN)"
    return True, "Valid Udyam number format"


def lookup_udyam(udyam_number: Optional[str]) -> Optional[Dict[str, Any]]:
    """Lookup Udyam registration in mock registry."""
    if not udyam_number:
        return None
    load_udyam_registry()
    assert _UDYAM_MAP is not None
    return _UDYAM_MAP.get(udyam_number.strip().upper())
