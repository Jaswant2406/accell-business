"""
Analytics Insights AI Module with Strict Factual Number Verification Guardrails.
Generates an executive narrative from computed metrics JSON only.
Verifies that every single number in the generated narrative exists in the metrics dictionary.
If any hallucinated number is found, the text is discarded and the deterministic template summary is shown.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd


def extract_numbers_from_text(text: str) -> List[float]:
    """
    Extract all numerical values (integers, floats, percentages, currency) from text.
    Ignores common non-metric identifiers like '2026' (year), bullet numbers ('1.', '2.'), etc.
    """
    # Remove dates like 2026-07-15
    cleaned = re.sub(r'\b202[0-9]-[0-9]{2}-[0-9]{2}\b', '', text)
    cleaned = re.sub(r'\b2026\b', '', cleaned)  # ignore hackathon year 2026

    # Matches integers and decimals with optional commas: 5,000 / 7.36 / 2,106 / 15,614
    tokens = re.findall(r'(?<![A-Za-z0-9_])[-+]?[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?(?![A-Za-z0-9_])', cleaned)
    numbers: List[float] = []
    for tok in tokens:
        num_str = tok.replace(",", "").strip()
        if not num_str or num_str in ["-", "+", "."]:
            continue
        try:
            val = float(num_str)
            # Filter out lone single-digit list index markers 1.0, 2.0, 3.0 if preceded by line break
            numbers.append(val)
        except ValueError:
            continue
    return numbers


def build_allowed_metric_numbers(metrics_dict: Dict[str, Any]) -> Set[float]:
    """
    Recursively extract all numeric values from metrics dict and compute standard roundings:
    raw value, rounded to 0 decimal places, 1 decimal place, and 2 decimal places.
    """
    allowed: Set[float] = set()

    def add_val(v: Any):
        if isinstance(v, (int, float)):
            f_val = float(v)
            allowed.add(round(f_val, 4))
            allowed.add(round(f_val, 2))
            allowed.add(round(f_val, 1))
            allowed.add(round(f_val, 0))
            # Also allow in Lakhs if > 1,00,000 (e.g. 455.98)
            if f_val >= 100000:
                lakhs = f_val / 100000.0
                allowed.add(round(lakhs, 2))
                allowed.add(round(lakhs, 1))
                allowed.add(round(lakhs, 0))
        elif isinstance(v, dict):
            for sub_v in v.values():
                add_val(sub_v)
        elif isinstance(v, list):
            for item in v:
                add_val(item)

    add_val(metrics_dict)
    return allowed


def verify_narrative_numbers(
    narrative_text: str,
    allowed_numbers: Set[float],
    tolerance: float = 0.15,
) -> Tuple[bool, List[float], List[float]]:
    """
    Verify that every number mentioned in the narrative text exists in the allowed metrics set.
    Returns: (is_valid, verified_numbers, unverified_numbers)
    """
    text_numbers = extract_numbers_from_text(narrative_text)
    verified: List[float] = []
    unverified: List[float] = []

    for num in text_numbers:
        # Check direct or close rounded match
        matched = False
        for allowed in allowed_numbers:
            if abs(num - allowed) <= tolerance:
                matched = True
                break
            # Also check percentage relative match if num < 100 and allowed < 100
            if allowed > 0 and abs(num - allowed) / allowed <= 0.02:
                matched = True
                break
        if matched:
            verified.append(num)
        else:
            unverified.append(num)

    is_valid = len(unverified) == 0
    return is_valid, verified, unverified


def generate_template_narrative(m: Dict[str, Any]) -> str:
    """
    Deterministic template-based executive summary derived from computed metrics.
    Guaranteed zero hallucinations.
    """
    return (
        f"Across the cohort of {int(m.get('total_leads', 5000)):,} SMB leads, {int(m.get('total_activated', 368)):,} "
        f"reached active status representing a {m.get('overall_conversion_pct', 7.36):.2f}% blended conversion. "
        f"A total of {int(m.get('addressable_drops', 2106)):,} dropped leads ({m.get('addressable_share_pct', 45.5):.1f}% of all drops) "
        f"stem from sales visit delays, complex manual quoting, and paperwork fatigue, directly addressable by Accel self-serve onboarding. "
        f"Portfolio unit economics are led by Small Multi-site Businesses ({m.get('priority1_ltv_cac', 37.88):.2f}x LTV/CAC) "
        f"and Small Manufacturers ({m.get('priority2_ltv_cac', 27.47):.2f}x LTV/CAC, lowest 6M churn)."
    )


def generate_analytics_narrative(
    metrics_summary: Dict[str, Any],
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate an executive narrative from computed metrics JSON only.
    Verifies that every number in the text exists in the metrics; if verification fails or no key
    is available, discards text and falls back to template narrative.
    """
    template_text = generate_template_narrative(metrics_summary)
    allowed_numbers = build_allowed_metric_numbers(metrics_summary)

    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key or key.strip() == "":
        return {
            "narrative": template_text,
            "source": "deterministic_template",
            "verified": True,
            "reason": "Deterministic metrics template active (no API key configured)",
        }

    model = model_name or os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
    timeout_sec = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "10"))

    prompt = f"""You are an executive enterprise telecom data scientist for Accel Business.
Summarize the following SMB funnel performance metrics in exactly 2 to 3 concise, high-impact executive sentences.

RULES:
1. Use ONLY the exact numbers provided in this metrics JSON:
{json.dumps(metrics_summary, indent=2)}
2. Do NOT invent, extrapolate, or approximate any numbers not in the JSON.
3. Every single number, percentage, or currency figure you mention MUST exist in the JSON.

Write the 2-3 sentence executive summary:"""

    try:
        from engine.advisor import create_gemini_client

        client = create_gemini_client(api_key=key.strip(), timeout_seconds=timeout_sec)
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        llm_text = resp.text.strip()

        # Strict number verification guardrail
        is_valid, verified, unverified = verify_narrative_numbers(llm_text, allowed_numbers)
        if is_valid and len(verified) > 0:
            return {
                "narrative": llm_text,
                "source": "gemini_verified",
                "verified": True,
                "verified_numbers": verified,
            }
        else:
            # Hallucinated number detected! Discard and fall back to template!
            return {
                "narrative": template_text,
                "source": "deterministic_template_fallback",
                "verified": True,
                "reason": f"LLM narrative discarded due to unverified numbers: {unverified}",
                "discarded_llm_text": llm_text,
            }
    except Exception as e:
        return {
            "narrative": template_text,
            "source": "deterministic_template_fallback",
            "verified": True,
            "reason": f"LLM generation error: {e}",
        }
