import os
import sys
import time
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

import google.genai as genai
from google.genai import types
from google.genai import errors as genai_errors
import httpx2

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("ERROR: GEMINI_API_KEY is not set.")
    sys.exit(1)

MODELS_TO_TEST = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-omni-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-image",
    "gemini-3.1-flash-lite-image",
    "gemini-2.5-flash-image",
]

def run_single_call(client, model: str, prompt: str = "Reply with OK", timeout: float = 10.0):
    t0 = time.time()
    def _call():
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
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
        return False, elapsed, f"Timeout (> {timeout:.0f}s)"
    except genai_errors.APIError as e:
        elapsed = time.time() - t0
        msg = f"{e.code} {e.message}" if hasattr(e, 'code') else str(e)
        if len(msg) > 40:
            msg = msg[:37] + "..."
        return False, elapsed, msg
    except Exception as e:
        elapsed = time.time() - t0
        msg = str(e)
        if len(msg) > 40:
            msg = msg[:37] + "..."
        return False, elapsed, msg

def main():
    print("=" * 80)
    print("PART 1: Benchmarking All Flash/Lite Models (3 runs each, 10s timeout, Default Client)")
    print("=" * 80)

    client_default = genai.Client(
        api_key=API_KEY,
        http_options=types.HttpOptions(timeout=10000)
    )

    results = []
    for model in MODELS_TO_TEST:
        print(f"Testing {model}...", flush=True)
        runs = []
        errors = []
        for r in range(1, 4):
            time.sleep(0.5)  # brief pause to avoid instant burst rate-limits
            success, elapsed, output_or_err = run_single_call(client_default, model, timeout=10.0)
            runs.append((success, elapsed, output_or_err))
            if not success:
                errors.append(output_or_err)
            print(f"  Run {r}: {'PASS' if success else 'FAIL'} in {elapsed:.2f}s - {output_or_err}", flush=True)

        passed_runs = [r[1] for r in runs if r[0]]
        avg_lat = sum(passed_runs) / len(passed_runs) if passed_runs else None
        results.append({
            "model": model,
            "runs": runs,
            "avg": avg_lat,
            "pass_count": len(passed_runs),
            "errors": list(set(errors)),
        })

    print("\n" + "=" * 80)
    print("PART 1 SUMMARY TABLE")
    print("=" * 80)
    header = f"{'Model':<28} | {'Run 1':<8} | {'Run 2':<8} | {'Run 3':<8} | {'Avg Latency':<11} | {'Status / Errors'}"
    print(header)
    print("-" * len(header))
    for res in results:
        r_strs = []
        for s, el, _ in res["runs"]:
            if s:
                r_strs.append(f"{el:.2f}s")
            else:
                r_strs.append(f"ERR({el:.1f}s)")
        avg_str = f"{res['avg']:.2f}s" if res["avg"] is not None else "N/A"
        err_str = ", ".join(res["errors"]) if res["errors"] else "OK (3/3 PASS)"
        print(f"{res['model']:<28} | {r_strs[0]:<8} | {r_strs[1]:<8} | {r_strs[2]:<8} | {avg_str:<11} | {err_str}")

if __name__ == "__main__":
    main()
