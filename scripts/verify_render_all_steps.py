"""
Script to verify that every step and view in app.py actually renders
with detailed proof of rendered UI components and contents.
"""

import sys
from pathlib import Path
import urllib.request
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def main():
    print("=" * 70)
    print("1. PROBING LIVE STREAMLIT SERVER (http://localhost:8501)")
    print("=" * 70)
    try:
        req = urllib.request.Request("http://localhost:8501", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode("utf-8")
            print(f"HTTP Status: {resp.status}")
            print(f"HTML Payload Size: {len(html)} bytes")
            assert "<title>Streamlit</title>" in html
            print("Verified: Base HTML contains '<title>Streamlit</title>'")
            assert 'id="root"' in html
            print("Verified: Client container <div id='root'> mounted successfully")
    except Exception as e:
        print(f"Error connecting to live server: {e}")

    print("\n" + "=" * 70)
    print("2. PROVING EVERY STEP RENDERS VIA STREAMLIT TESTING ENGINE")
    print("=" * 70)

    # Step 1: Advisor
    at = AppTest.from_file(APP_PATH, default_timeout=25)
    at.run()
    assert len(at.exception) == 0
    at.session_state["current_step"] = 1
    at.run()
    assert len(at.exception) == 0
    md_texts = [m.value for m in at.markdown]
    print("[STEP 1: ADVISOR] RENDER VERIFIED:")
    print(f" - Title: {[t for t in md_texts if 'Step 1' in t][0]}")
    print(f" - Radio options: {[r.value for r in at.radio]}")
    print(f" - Text inputs: {[ti.label for ti in at.text_input]}")
    print(f" - Number inputs: {[ni.label for ni in at.number_input]}")
    print(f" - Buttons: {[b.label for b in at.button]}")
    assert any("Step 1: AI Business Advisor" in t for t in md_texts)
    assert any("Recommended Solution Bundle" in t for t in md_texts)

    # Step 2: Quote
    at.session_state["current_step"] = 2
    at.session_state["selected_items"] = [
        {
            "product_id": "P01",
            "product_name": "Biz Fibre 100 Mbps",
            "category": "Broadband",
            "quantity": 1,
            "price_min": 999,
            "price_max": 1499,
            "one_time_setup": 1500,
            "unit": "per site",
            "min_contract_months": 12,
            "typical_install_days": 3,
            "reason": "Base connectivity",
            "assumption": "1 site",
        }
    ]
    at.run()
    assert len(at.exception) == 0
    md_texts_2 = [m.value for m in at.markdown]
    print("\n[STEP 2: QUOTE] RENDER VERIFIED:")
    print(f" - Title: {[t for t in md_texts_2 if 'Step 2' in t][0]}")
    print(f" - Line item quantities: {[ni.label for ni in at.number_input]}")
    print(f" - Contract options: {[sb.label for sb in at.selectbox]}")
    print(f" - Buttons: {[b.label for b in at.button]}")
    assert any("Step 2: Solution Quote & Customization" in t for t in md_texts_2)
    assert any("Official Quote Summary" in t for t in md_texts_2)

    # Step 3: KYC
    at.session_state["current_step"] = 3
    at.session_state["dpdp_consent_granted"] = True
    at.run()
    assert len(at.exception) == 0
    md_texts_3 = [m.value for m in at.markdown]
    print("\n[STEP 3: SMART KYC] RENDER VERIFIED:")
    print(f" - Title: {[t for t in md_texts_3 if 'Step 3' in t][0]}")
    print(f" - Demo selector: {[sb.label for sb in at.selectbox]}")
    print(f" - Checkboxes: {[cb.label for cb in at.checkbox]}")
    print(f" - Verification button: {[b.label for b in at.button]}")
    assert any("Step 3: Smart Digital KYC Verification" in t for t in md_texts_3)
    assert any("DPDP" in t for t in md_texts_3)

    # Step 4: Checkout
    at.session_state["current_step"] = 4
    at.session_state["current_quote"] = {
        "monthly_subtotal": 999,
        "one_time_subtotal": 1500,
        "first_month_payable": 2499,
        "contract_months": 12,
        "max_install_days": 3,
        "items": [{"product_name": "Biz Fibre 100 Mbps", "monthly_amount": 999}],
    }
    at.run()
    assert len(at.exception) == 0
    md_texts_4 = [m.value for m in at.markdown]
    print("\n[STEP 4: CHECKOUT] RENDER VERIFIED:")
    print(f" - Title: {[t for t in md_texts_4 if 'Step 4' in t][0]}")
    print(f" - Subscriber text inputs: {[ti.label for ti in at.text_input]}")
    print(f" - Payment mandate options: {[r.label for r in at.radio]}")
    print(f" - Confirm button: {[b.label for b in at.button]}")
    assert any("Step 4: Checkout & Service Authorization" in t for t in md_texts_4)

    # Step 5: Track
    at.session_state["current_step"] = 5
    at.session_state["last_order_id"] = "AB-2026-94317"
    at.run()
    assert len(at.exception) == 0
    md_texts_5 = [m.value for m in at.markdown]
    print("\n[STEP 5: TRACK] RENDER VERIFIED:")
    print(f" - Title: {[t for t in md_texts_5 if 'Step 5' in t][0]}")
    print(f" - Order selector: {[sb.label for sb in at.selectbox]}")
    print(f" - Simulator buttons: {[b.label for b in at.button]}")
    assert any("Step 5: Order Activation & Service Tracker" in t for t in md_texts_5)
    assert any("Autonomous Fulfillment Timeline" in t for t in md_texts_5)

    # KYC Desk
    at.session_state["nav_view_selector"] = "🔍 KYC Verification Desk"
    at.run()
    assert len(at.exception) == 0
    md_texts_k = [m.value for m in at.markdown]
    print("\n[VIEW: KYC VERIFICATION DESK] RENDER VERIFIED:")
    print(f" - Title: {[t for t in md_texts_k if 'KYC Verification Desk' in t][0]}")
    assert any("KYC Verification Desk" in t for t in md_texts_k)

    # Sales Analytics
    at.session_state["nav_view_selector"] = "📊 Sales Analytics"
    at.run()
    assert len(at.exception) == 0
    md_texts_sa = [m.value for m in at.markdown]
    print("\n[VIEW: SALES ANALYTICS] RENDER VERIFIED:")
    print(f" - Title: {[t for t in md_texts_sa if 'Sales & Funnel Performance Analytics' in t][0]}")
    print(f" - Dataframes rendered: {len(at.dataframe)}")
    print(f" - Metrics rendered: {[me.label for me in at.metric]}")
    assert any("Sales & Funnel Performance Analytics" in t for t in md_texts_sa)
    assert len(at.dataframe) >= 3

    print("\n" + "=" * 70)
    print("ALL 5 JOURNEY STEPS + 2 OPS/ANALYTICS VIEWS RENDERED WITH ZERO ERRORS!")
    print("=" * 70)


if __name__ == "__main__":
    main()
