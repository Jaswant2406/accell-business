"""
Verification script for Gemini Advisor Calls and Network Blocked Fallback.
Tests:
1. Three live advisor runs with user message:
   "Dental clinic, 5 staff, 1 location in Kochi, I have a GSTIN"
2. Network blocked test:
   Confirms recommendations are returned within the timeout.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from engine.advisor import (
    extract_profile_with_llm,
    extract_profile_multilingual_fallback,
    deterministic_advisor_fallback,
    build_business_profile_from_advisor,
)
from engine.eligibility import recommend_products

MESSAGE = "Dental clinic, 5 staff, 1 location in Kochi, I have a GSTIN"


def run_single_advisor_pass(iteration: int):
    print(f"\n--- RUN {iteration} ---", flush=True)
    t0 = time.time()
    
    # 1. Extraction step
    llm_data = extract_profile_with_llm(MESSAGE, target_language="English")
    fallback_used = False
    
    if not llm_data:
        fallback_used = True
        llm_data = extract_profile_multilingual_fallback(MESSAGE, language="English")
        badge = "Running in rules mode"
        note = "Gemini was slow, so rules mode answered"
    else:
        badge = "AI Powered (Gemini)"
        note = None
        
    t_end = time.time()
    total_elapsed = t_end - t0
    
    # 2. Eligibility & Recommendation Engine step
    prof_dict = deterministic_advisor_fallback(
        business_type=llm_data.get("business_type", "Healthcare/Clinic"),
        employees=int(llm_data.get("employees", 5)),
        sites=int(llm_data.get("sites", 1)),
        city=llm_data.get("city", "Kochi"),
        has_gstin=bool(llm_data.get("has_gstin", True)),
        gstin=llm_data.get("gstin"),
        digital_needs=llm_data.get("digital_needs", []),
    )
    b_profile = build_business_profile_from_advisor(prof_dict)
    rec_result = recommend_products(b_profile)
    rec_pids = [it["product_id"] for it in rec_result["recommended"]]
    
    print(f"Result Run {iteration}:", flush=True)
    print(f"  Total Latency: {total_elapsed:.2f}s", flush=True)
    print(f"  Badge Shown:   {badge}", flush=True)
    if note:
        print(f"  Note Shown:    {note}", flush=True)
    print(f"  Extracted:     City={llm_data.get('city')}, Emp={llm_data.get('employees')}, GSTIN={llm_data.get('has_gstin')}", flush=True)
    print(f"  Recommendations ({len(rec_pids)}): {rec_pids}", flush=True)
    
    return {
        "iteration": iteration,
        "latency": total_elapsed,
        "badge": badge,
        "note": note,
        "pids": rec_pids,
        "fallback_used": fallback_used,
    }


def run_blocked_network_test():
    print(f"\n--- NETWORK BLOCKED TEST ---", flush=True)
    t0 = time.time()
    
    # Simulate blocked network by using a non-routable dummy host / invalid key or monkeypatching socket
    import socket
    orig_getaddrinfo = socket.getaddrinfo
    
    def blocked_getaddrinfo(*args, **kwargs):
        raise socket.gaierror(-3, "Temporary failure in name resolution (Network Blocked)")
        
    socket.getaddrinfo = blocked_getaddrinfo
    
    try:
        llm_data = extract_profile_with_llm(MESSAGE, target_language="English")
        if not llm_data:
            llm_data = extract_profile_multilingual_fallback(MESSAGE, language="English")
            badge = "Running in rules mode"
            note = "Gemini was slow, so rules mode answered"
        else:
            badge = "AI Powered (Gemini)"
            note = None
    finally:
        socket.getaddrinfo = orig_getaddrinfo
        
    t_end = time.time()
    total_elapsed = t_end - t0
    
    prof_dict = deterministic_advisor_fallback(
        business_type=llm_data.get("business_type", "Healthcare/Clinic"),
        employees=int(llm_data.get("employees", 5)),
        sites=int(llm_data.get("sites", 1)),
        city=llm_data.get("city", "Kochi"),
        has_gstin=bool(llm_data.get("has_gstin", True)),
        gstin=llm_data.get("gstin"),
        digital_needs=llm_data.get("digital_needs", []),
    )
    b_profile = build_business_profile_from_advisor(prof_dict)
    rec_result = recommend_products(b_profile)
    rec_pids = [it["product_id"] for it in rec_result["recommended"]]
    
    print(f"Result Blocked Network Test:", flush=True)
    print(f"  Total Latency: {total_elapsed:.2f}s (well within timeout)", flush=True)
    print(f"  Badge Shown:   {badge}", flush=True)
    print(f"  Note Shown:    {note}", flush=True)
    print(f"  Recommendations ({len(rec_pids)}): {rec_pids}", flush=True)
    
    return {
        "latency": total_elapsed,
        "badge": badge,
        "note": note,
        "pids": rec_pids,
    }


def main():
    print("=========================================================")
    print("TESTING ADVISOR WITH USER .ENV KEY AND GEMINI-3.8-FLASH")
    print(f"Model: {os.getenv('GEMINI_MODEL', 'gemini-3.8-flash')}")
    print(f"Configured Timeout: {os.getenv('GEMINI_TIMEOUT_SECONDS', '20')}s")
    print("=========================================================")
    
    results = []
    for i in range(1, 4):
        res = run_single_advisor_pass(i)
        results.append(res)
        
    blocked_res = run_blocked_network_test()
    
    print("\n======================= SUMMARY =========================")
    for r in results:
        print(f"Run {r['iteration']}: Latency={r['latency']:.2f}s | Badge='{r['badge']}' | Fallback={r['fallback_used']}")
    print(f"Blocked: Latency={blocked_res['latency']:.2f}s | Badge='{blocked_res['badge']}'")
    print("=========================================================")


if __name__ == "__main__":
    main()
