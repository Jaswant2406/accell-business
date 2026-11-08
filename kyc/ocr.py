"""Smart KYC OCR extraction pipeline with multi-pass preprocessing and self-correcting lookup."""

import itertools
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import cv2
import numpy as np
import pytesseract
from dotenv import load_dotenv

from kyc.registry import (
    load_gstin_registry,
    load_udyam_registry,
    lookup_gstin,
    lookup_udyam,
    validate_gstin_format,
    validate_udyam_format,
)

load_dotenv()

# Configure Tesseract
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
if TESSERACT_CMD and Path(TESSERACT_CMD).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# Common OCR confusion character map
CONFUSION_MAP: Dict[str, List[str]] = {
    "O": ["0", "D", "Q"],
    "0": ["O", "Q", "D"],
    "I": ["1", "J", "L", "T"],
    "1": ["I", "L", "T"],
    "J": ["I"],
    "G": ["6", "C"],
    "6": ["G", "B"],
    "S": ["5", "9"],
    "5": ["S", "8"],
    "9": ["S", "g"],
    "B": ["8", "6"],
    "8": ["B", "5"],
    "Z": ["2"],
    "2": ["Z"],
}


def mask_identifier(ident: Optional[str]) -> str:
    """Mask sensitive identifier for privacy (e.g. 37XXXXXXXXXX7ZS)."""
    if not ident:
        return "N/A"
    s = str(ident).strip()
    if len(s) <= 4:
        return "****"
    if s.startswith("UDYAM"):
        # Format: UDYAM-XX-00-1234567 -> UDYAM-**-00-****567
        parts = s.split("-")
        if len(parts) == 4:
            return f"UDYAM-**-00-****{parts[3][-3:]}"
        return s[:6] + "********" + s[-3:]
    # GSTIN 15 chars: show first 2 and last 3
    if len(s) >= 10:
        return s[:2] + "X" * (len(s) - 5) + s[-3:]
    return s[:2] + "******" + s[-2:]


def deskew_image(img: np.ndarray) -> np.ndarray:
    """Detect skew angle and rotate image to upright orientation."""
    if img is None or not isinstance(img, np.ndarray) or img.size == 0:
        return img
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 50:
        return img
    
    rect = cv2.minAreaRect(coords)
    angle = rect[-1]
    
    if angle < -45:
        skew = -(90 + angle)
    else:
        skew = -angle
        
    # Rotate if skew detected (between 2 and 45 degrees)
    if 2.0 <= abs(skew) <= 45.0:
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        rot_angle = -skew if skew < 0 else skew
        M = cv2.getRotationMatrix2D(center, rot_angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
    return img


def correct_gstin_via_substitutions(raw_gstin: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], str, bool]:
    """
    Validate and correct GSTIN:
    1. Direct format & checksum match against mock_gstin_registry.csv.
    2. Ambiguous pairs {O, 0} and {I, J} tested at the checksum level against registry.
    3. Fallback: single-character substitution cap from CONFUSION_MAP.
    Accept ONLY if candidate passes checksum AND exists in registry.

    Returns:
      (corrected_gstin, registry_record, note, is_ocr_corrected)
    """
    if not raw_gstin:
        return None, None, "GSTIN missing", False
    
    clean = re.sub(r"[^A-Z0-9]", "", raw_gstin.strip().upper())
    if len(clean) > 15:
        clean = clean[:15]

    # Direct lookup: must pass checksum and exist in registry
    is_fmt_valid, _ = validate_gstin_format(clean)
    if is_fmt_valid:
        rec = lookup_gstin(clean)
        if rec:
            return clean, rec, "Exact registry match", False

    load_gstin_registry()
    chars = list(clean)

    # 2. Checksum-level resolution for ambiguous {O, 0} and {I, J} interpretations
    options = []
    has_ambiguity = False
    for ch in chars:
        if ch in ("O", "0"):
            options.append(("0", "O"))
            has_ambiguity = True
        elif ch in ("I", "J"):
            options.append(("I", "J"))
            has_ambiguity = True
        else:
            options.append((ch,))

    if has_ambiguity:
        checksum_matches: Dict[str, Dict[str, Any]] = {}
        for combo in itertools.islice(itertools.product(*options), 64):
            variant = "".join(combo)
            if len(variant) == 15:
                is_v, _ = validate_gstin_format(variant)
                if is_v:
                    rec = lookup_gstin(variant)
                    if rec:
                        checksum_matches[variant] = rec

        if len(checksum_matches) == 1:
            corr_gstin, rec = list(checksum_matches.items())[0]
            if corr_gstin == clean:
                return corr_gstin, rec, "Exact registry match", False
            diffs = [f"'{c1}' -> '{c2}' at position {idx+1}" for idx, (c1, c2) in enumerate(zip(clean, corr_gstin)) if c1 != c2]
            audit_note = f"OCR-corrected: {mask_identifier(clean)} -> {mask_identifier(corr_gstin)} (Substituted {', '.join(diffs)})"
            return corr_gstin, rec, audit_note, True

    # 3. Fallback: Strictly 1-character substitution cap from CONFUSION_MAP
    candidates: Dict[str, str] = {}
    for i, ch in enumerate(chars):
        if ch in CONFUSION_MAP:
            for alt in CONFUSION_MAP[ch]:
                mutated = "".join(chars[:i] + [alt] + chars[i+1:])
                if len(mutated) == 15:
                    is_valid_mut, _ = validate_gstin_format(mutated)
                    if is_valid_mut:
                        match = lookup_gstin(mutated)
                        if match:
                            candidates[mutated] = f"Substituted '{ch}' -> '{alt}' at position {i+1}"

    if len(candidates) == 1:
        corr_gstin, note = list(candidates.items())[0]
        audit_note = f"OCR-corrected: {mask_identifier(clean)} -> {mask_identifier(corr_gstin)} ({note})"
        return corr_gstin, lookup_gstin(corr_gstin), audit_note, True
    elif len(candidates) > 1:
        return None, None, "GSTIN on document does not match registry (ambiguous OCR matches)", False

    return None, None, "GSTIN on document does not match registry", False


def correct_udyam_via_substitutions(raw_udyam: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], str]:
    """
    Attempt substitutions on Udyam number to match mock_udyam_registry.csv.
    Accept ONLY if exactly ONE registry match results.
    """
    if not raw_udyam:
        return None, None, "Udyam number missing"
        
    clean = re.sub(r"\s+", "", raw_udyam.strip().upper())
    rec = lookup_udyam(clean)
    if rec:
        return clean, rec, "Exact registry match"

    load_udyam_registry()
    candidates: Dict[str, str] = {}

    chars = list(clean)
    # Pass 1: Single char substitutions
    for i, ch in enumerate(chars):
        if ch in CONFUSION_MAP:
            for alt in CONFUSION_MAP[ch]:
                mutated = "".join(chars[:i] + [alt] + chars[i+1:])
                if re.match(r"^UDYAM-[A-Z]{2}-00-\d{7}$", mutated):
                    match = lookup_udyam(mutated)
                    if match:
                        candidates[mutated] = f"Substituted '{ch}' -> '{alt}' at position {i+1}"

    if len(candidates) == 1:
        corr_u, note = list(candidates.items())[0]
        return corr_u, lookup_udyam(corr_u), f"Single-character correction applied: {note}"

    # Pass 2: Double char substitutions
    for i in range(len(chars)):
        ch1 = chars[i]
        if ch1 not in CONFUSION_MAP:
            continue
        for alt1 in CONFUSION_MAP[ch1]:
            for j in range(i + 1, len(chars)):
                ch2 = chars[j]
                if ch2 not in CONFUSION_MAP:
                    continue
                for alt2 in CONFUSION_MAP[ch2]:
                    mutated = chars.copy()
                    mutated[i] = alt1
                    mutated[j] = alt2
                    mut_str = "".join(mutated)
                    if re.match(r"^UDYAM-[A-Z]{2}-00-\d{7}$", mut_str):
                        match = lookup_udyam(mut_str)
                        if match:
                            candidates[mut_str] = f"Substituted ('{ch1}'->'{alt1}' at {i+1}, '{ch2}'->'{alt2}' at {j+1})"

    if len(candidates) == 1:
        corr_u, note = list(candidates.items())[0]
        return corr_u, lookup_udyam(corr_u), f"Two-character correction applied: {note}"

    return None, None, "No Udyam registry match found even after substitutions"


def extract_gst_certificate_fields(img: np.ndarray) -> Dict[str, Any]:
    """
    Multi-pass extraction for GST Registration Certificate:
    1. Dedicated crop of GSTIN value region, upscaled 3.5x with character whitelist (0-9 A-Z) and PSM 7.
    2. Multi-pass whole-image OCR passes.
    3. Checksum-level resolution of ambiguous pairs (O/0 and I/J) and registry verification.
    """
    if img is None or not isinstance(img, np.ndarray) or img.size == 0:
        return {
            "doc_type": "gst_certificate",
            "raw_gstin": None,
            "corrected_gstin": None,
            "registry_record": None,
            "ocr_note": "Invalid or unreadable GST document",
            "legal_name": None,
            "trade_name": None,
            "constitution": None,
            "address": None,
            "date_of_liability": None,
            "ocr_success": False,
        }

    deskewed = deskew_image(img)
    clean_text = pytesseract.image_to_string(deskewed)
    gray = cv2.cvtColor(deskewed, cv2.COLOR_BGR2GRAY) if len(deskewed.shape) == 3 else deskewed
    scaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    candidates_to_try: List[str] = []

    # 1. Bounding-box crop of GSTIN value region
    try:
        data = pytesseract.image_to_data(deskewed, output_type=pytesseract.Output.DICT)
        h, w = deskewed.shape[:2]
        for i in range(len(data.get("text", []))):
            word = str(data["text"][i]).strip()
            if "GSTIN" in word.upper():
                gx = data["left"][i]
                gy = data["top"][i]
                gw = data["width"][i]
                gh = data["height"][i]
                crop_x1 = max(0, gx + gw - 5)
                crop_x2 = min(w, gx + gw + int(gw * 8))
                crop_y1 = max(0, gy - int(gh * 0.4))
                crop_y2 = min(h, gy + int(gh * 1.4))
                if crop_x2 > crop_x1 and crop_y2 > crop_y1:
                    crop = deskewed[crop_y1:crop_y2, crop_x1:crop_x2]
                    scaled_crop = cv2.resize(crop, None, fx=3.5, fy=3.5, interpolation=cv2.INTER_CUBIC)
                    gray_crop = cv2.cvtColor(scaled_crop, cv2.COLOR_BGR2GRAY) if len(scaled_crop.shape) == 3 else scaled_crop
                    cfg_wl = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                    t_raw = pytesseract.image_to_string(gray_crop, config=cfg_wl).strip()
                    _, thresh_crop = cv2.threshold(gray_crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    t_th = pytesseract.image_to_string(thresh_crop, config=cfg_wl).strip()
                    for t in [t_raw, t_th]:
                        cl = re.sub(r"[^A-Z0-9]", "", t.upper())
                        if 14 <= len(cl) <= 16:
                            candidates_to_try.append(cl[:15])
    except Exception:
        pass

    # 2. Whole-image passes
    passes = [
        (deskewed, ""),
        (deskewed, "--psm 6"),
        (scaled, ""),
        (scaled, "--psm 6"),
    ]

    for im_pass, cfg in passes:
        txt = pytesseract.image_to_string(im_pass, config=cfg)
        m = re.search(r"GSTIN\s+([A-Z0-9]{14,17})", txt)
        if m:
            cand = m.group(1).strip()
            candidates_to_try.append(cand)

    best_text = clean_text
    best_gstin = None
    best_corr = None
    best_record = None
    best_note = "GSTIN not detected"

    for cand in candidates_to_try:
        corr, rec, note, is_corr = correct_gstin_via_substitutions(cand)
        if rec and (not best_record):
            best_gstin = cand
            best_corr = corr
            best_record = rec
            best_note = note
            break
        elif not best_gstin:
            best_gstin = cand
            best_corr = corr
            best_record = rec
            best_note = note

    # Extract auxiliary fields prioritizing clean line-by-line format
    legal_m = re.search(r"Legal\s*name\s+(.+)", best_text, re.IGNORECASE)
    legal_name = legal_m.group(1).strip() if legal_m else None
    if legal_name and legal_name.lower().startswith("trade"):
        legal_name = None

    trade_m = re.search(r"Trade\s*-?\s*name\s+(.+)", best_text, re.IGNORECASE)
    trade_name = trade_m.group(1).strip() if trade_m else None
    if trade_name and trade_name.lower().startswith("constitution"):
        trade_name = None

    const_m = re.search(r"Constitution\s+(.+)", best_text, re.IGNORECASE)
    constitution = const_m.group(1).strip() if const_m else None

    addr_m = re.search(
        r"Address\s+of\s+principal\s*(?:place\s*of\s*business)?\s+(.+?)(?:Date\s+of\s+liability|Type\s+of\s+registration|$)",
        best_text,
        re.DOTALL | re.IGNORECASE,
    )
    address = " ".join(addr_m.group(1).split()) if addr_m else None

    date_m = re.search(r"Date\s+of\s+liability\s+(\d{4}-\d{2}-\d{2})", best_text, re.IGNORECASE)
    date_of_liability = date_m.group(1) if date_m else None

    return {
        "doc_type": "gst_certificate",
        "raw_gstin": best_gstin,
        "corrected_gstin": best_corr or best_gstin,
        "registry_record": best_record,
        "ocr_note": best_note,
        "legal_name": legal_name,
        "trade_name": trade_name,
        "constitution": constitution,
        "address": address,
        "date_of_liability": date_of_liability,
        "ocr_success": best_gstin is not None,
    }


def extract_udyam_certificate_fields(img: np.ndarray) -> Dict[str, Any]:
    """
    Multi-pass extraction for Udyam Registration Certificate.
    """
    if img is None or not isinstance(img, np.ndarray) or img.size == 0:
        return {
            "doc_type": "udyam_certificate",
            "raw_udyam": None,
            "corrected_udyam": None,
            "registry_record": None,
            "ocr_note": "Invalid or unreadable Udyam document",
            "enterprise_name": None,
            "major_activity": None,
            "city": None,
            "state": None,
            "date_of_registration": None,
            "ocr_success": False,
        }

    deskewed = deskew_image(img)
    passes = [
        (deskewed, "--psm 6"),
        (deskewed, ""),
    ]

    best_text = ""
    best_udyam = None
    best_corr = None
    best_record = None
    best_note = "Udyam registration number not detected"

    for im_pass, cfg in passes:
        txt = pytesseract.image_to_string(im_pass, config=cfg)
        if len(txt) > len(best_text):
            best_text = txt
            
        m = re.search(r"UDYAM-[A-Z0-9]{2}-[A-Z0-9]{2}-\s*([0-9]{7})", txt, re.IGNORECASE)
        if m:
            clean_u = re.sub(r"\s+", "", m.group(0).strip().upper())
            corr, rec, note = correct_udyam_via_substitutions(clean_u)
            best_udyam = clean_u
            best_corr = corr
            best_record = rec
            best_note = note
            if rec:
                break

    ent_m = re.search(r"Enterprise\s*name\s+(.+)", best_text, re.IGNORECASE)
    enterprise_name = ent_m.group(1).strip() if ent_m else None

    act_m = re.search(r"Major\s*activity\s+(.+)", best_text, re.IGNORECASE)
    major_activity = act_m.group(1).strip() if act_m else None

    city_m = re.search(r"City\s+(.+)", best_text, re.IGNORECASE)
    city = city_m.group(1).strip() if city_m else None

    state_m = re.search(r"State\s+(.+)", best_text, re.IGNORECASE)
    state = state_m.group(1).strip() if state_m else None

    date_m = re.search(r"Date\s+of\s+registration\s+(\d{4}-\d{2}-\d{2})", best_text, re.IGNORECASE)
    date_of_registration = date_m.group(1) if date_m else None

    return {
        "doc_type": "udyam_certificate",
        "raw_udyam": best_udyam,
        "corrected_udyam": best_corr or best_udyam,
        "registry_record": best_record,
        "ocr_note": best_note,
        "enterprise_name": enterprise_name,
        "major_activity": major_activity,
        "city": city,
        "state": state,
        "date_of_registration": date_of_registration,
        "ocr_success": best_udyam is not None,
    }


def extract_signatory_id_fields(img: np.ndarray) -> Dict[str, Any]:
    """Extract fields from Authorised Signatory ID."""
    if img is None or not isinstance(img, np.ndarray) or img.size == 0:
        return {
            "doc_type": "signatory_id",
            "signatory_name": None,
            "designation": None,
            "business_name": None,
            "id_number": None,
            "valid_till": None,
            "ocr_success": False,
        }
    text = pytesseract.image_to_string(deskew_image(img), config="--psm 6")
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    signatory_name = None
    designation = None
    business_name = None
    id_number = None
    valid_till = None

    for i, line in enumerate(lines):
        if line.lower() == "name" and i + 1 < len(lines):
            signatory_name = lines[i + 1]
        elif line.lower() == "designation" and i + 1 < len(lines):
            designation = lines[i + 1]
        elif "business" in line.lower() and i + 1 < len(lines):
            business_name = lines[i + 1]
        elif "id no" in line.lower() and i + 1 < len(lines):
            id_m = re.search(r"(SYN-ID-\d{6})", lines[i + 1])
            if id_m:
                id_number = id_m.group(1)
        elif "valid till" in line.lower() and i + 1 < len(lines):
            date_m = re.search(r"(\d{4}-\d{2}-\d{2})", lines[i + 1])
            if date_m:
                valid_till = date_m.group(1)

    if not id_number:
        id_m = re.search(r"(SYN-ID-\d{6})", text)
        if id_m:
            id_number = id_m.group(1)

    if not valid_till:
        date_m = re.search(r"(\d{4}-\d{2}-\d{2})", text)
        if date_m:
            valid_till = date_m.group(1)

    return {
        "doc_type": "signatory_id",
        "signatory_name": signatory_name,
        "designation": designation,
        "business_name": business_name,
        "id_number": id_number,
        "valid_till": valid_till,
        "ocr_success": signatory_name is not None and valid_till is not None,
    }


def extract_address_proof_fields(img: np.ndarray) -> Dict[str, Any]:
    """
    Extract fields from Utility Electricity Bill Address Proof.
    Handles two-block header/values layout and line-wrapped PIN codes.
    """
    if img is None or not isinstance(img, np.ndarray) or img.size == 0:
        return {
            "doc_type": "address_proof",
            "consumer_no": None,
            "billed_to": None,
            "supply_address": None,
            "bill_date": None,
            "ocr_success": False,
        }
    text = pytesseract.image_to_string(deskew_image(img))
    # Normalize broken hyphenations e.g. '75\n2083' -> '752083'
    clean_text = re.sub(r"-\s*(\d{2})\s*\n\s*(\d{4})", r"-\1\2", text)
    clean_text = re.sub(r"-\s*\n\s*", "-", clean_text)
    
    lines = [l.strip() for l in clean_text.splitlines() if l.strip()]

    consumer_no = None
    billed_to = None
    supply_address = None
    bill_date = None

    # Locate 10-digit consumer number
    c_idx = -1
    for idx, l in enumerate(lines):
        if re.search(r"\b\d{10}\b", l):
            c_idx = idx
            consumer_no = re.search(r"\b\d{10}\b", l).group(0)
            break

    # Locate bill date
    d_idx = -1
    for idx, l in enumerate(lines):
        m = re.search(r"(202\d-\d{2}-\d{2})", l)
        if m:
            d_idx = idx
            bill_date = m.group(1)
            break

    if not bill_date:
        date_all = re.search(r"(202\d-\d{2}-\d{2})", clean_text)
        if date_all:
            bill_date = date_all.group(1)

    if c_idx != -1 and d_idx != -1 and d_idx > c_idx:
        billed_to = lines[c_idx + 1] if c_idx + 1 < d_idx else ""
        billed_to = re.sub(r"^Billed\s*to\s*", "", billed_to, flags=re.IGNORECASE).strip()
        addr_lines = lines[c_idx + 2:d_idx]
        supply_address = " ".join(addr_lines)
    else:
        # Fallback regex search
        b_m = re.search(r"Billed\s*to\s*(?:Neelgiri|Trinity|Star|Balaji|Saffron|Ganesh|Green|Kaveri|Vindhya|Harmony)?\s*([^\n]+)", clean_text)
        if b_m:
            billed_to = b_m.group(0).replace("Billed to", "").strip()

    # Extract PIN code
    pin_m = re.search(r"\b(\d{6})\b", clean_text)
    pin_code = pin_m.group(1) if pin_m else None

    return {
        "doc_type": "address_proof",
        "consumer_no": consumer_no,
        "billed_to": billed_to,
        "supply_address": supply_address or clean_text,
        "pin_code": pin_code,
        "bill_date": bill_date,
        "ocr_success": billed_to is not None and bill_date is not None,
    }
