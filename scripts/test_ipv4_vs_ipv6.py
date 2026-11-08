import os
import sys
import time
import socket
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

import google.genai as genai
from google.genai import types
from google.genai import errors as genai_errors
import httpx2

API_KEY = os.getenv("GEMINI_API_KEY")

def make_default_client():
    return genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(timeout=10000)
    )

def make_ipv4_transport_client():
    transport = httpx2.HTTPTransport(local_address="0.0.0.0")
    return genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(
            timeout=10000,
            client_args={"transport": transport}
        )
    )

def run_single(client, model: str, timeout: float = 10.0):
    t0 = time.time()
    def _call():
        resp = client.models.generate_content(
            model=model,
            contents="Reply with OK",
            config=types.GenerateContentConfig(
                max_output_tokens=10,
                temperature=0.0,
            ),
        )
        return resp.text

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            fut = executor.submit(_call)
            text = fut.result(timeout=timeout)
            elapsed = time.time() - t0
            return True, elapsed, (text or "").strip()
    except concurrent.futures.TimeoutError:
        elapsed = time.time() - t0
        return False, elapsed, f"Timeout ({elapsed:.1f}s)"
    except genai_errors.APIError as e:
        elapsed = time.time() - t0
        msg = f"{e.code} {e.message}" if hasattr(e, 'code') else str(e)
        if len(msg) > 35:
            msg = msg[:32] + "..."
        return False, elapsed, msg
    except Exception as e:
        elapsed = time.time() - t0
        msg = str(e)
        if len(msg) > 35:
            msg = msg[:32] + "..."
        return False, elapsed, msg

def benchmark_scenario(model_name: str, num_runs: int = 5):
    print(f"\n=======================================================")
    print(f"Testing {model_name}: Default (IPv6) vs Forced IPv4")
    print(f"=======================================================")
    
    # 1. Default (IPv6)
    print("\n--- Running Default (IPv6) ---")
    client_def = make_default_client()
    def_results = []
    for i in range(1, num_runs + 1):
        time.sleep(0.5)
        ok, elapsed, out = run_single(client_def, model_name)
        def_results.append((ok, elapsed, out))
        print(f"  Default Run {i}: {'PASS' if ok else 'FAIL'} in {elapsed:.3f}s - {out}")

    # 2. Forced IPv4 via transport
    print("\n--- Running Forced IPv4 (local_address='0.0.0.0') ---")
    client_v4 = make_ipv4_transport_client()
    v4_results = []
    for i in range(1, num_runs + 1):
        time.sleep(0.5)
        ok, elapsed, out = run_single(client_v4, model_name)
        v4_results.append((ok, elapsed, out))
        print(f"  Forced IPv4 Run {i}: {'PASS' if ok else 'FAIL'} in {elapsed:.3f}s - {out}")

    # Analysis
    def_pass = [r[1] for r in def_results if r[0]]
    v4_pass = [r[1] for r in v4_results if r[0]]
    
    def_avg = sum(def_pass) / len(def_pass) if def_pass else 0.0
    v4_avg = sum(v4_pass) / len(v4_pass) if v4_pass else 0.0
    
    print("\n" + "-" * 55)
    print(f"Result for {model_name}:")
    print(f"  Default (IPv6): {len(def_pass)}/{num_runs} passed. Avg (passed): {def_avg:.3f}s")
    print(f"  Forced IPv4:    {len(v4_pass)}/{num_runs} passed. Avg (passed): {v4_avg:.3f}s")
    if v4_avg > 0 and def_avg > 0:
        diff = ((def_avg - v4_avg) / def_avg) * 100
        faster = "IPv4" if v4_avg < def_avg else "Default (IPv6)"
        print(f"  Comparison: {faster} is faster by {abs(diff):.1f}%")
    print("-" * 55)
    return {
        "model": model_name,
        "def_results": def_results,
        "v4_results": v4_results,
        "def_avg": def_avg,
        "v4_avg": v4_avg,
        "def_pass_count": len(def_pass),
        "v4_pass_count": len(v4_pass),
    }

if __name__ == "__main__":
    res_35 = benchmark_scenario("gemini-3.5-flash", num_runs=5)
    res_31 = benchmark_scenario("gemini-3.1-flash-lite", num_runs=5)
