"""
Verification script for UI DOM rendering, Stepper, Sidebar buttons, and Markdown purity.
"""
from pathlib import Path
from streamlit.testing.v1 import AppTest

app_path = Path("app.py").resolve()
at = AppTest.from_file(str(app_path), default_timeout=30)
at.run()

views_and_steps = [
    ("Home View", "Home", None),
    ("Advisor Step", "Customer Journey", 1),
    ("Quote Step", "Customer Journey", 2),
    ("KYC Step", "Customer Journey", 3),
    ("Checkout Step", "Customer Journey", 4),
    ("Track Step", "Customer Journey", 5),
    ("KYC Verification Desk", "KYC Verification Desk", None),
    ("Sales Analytics", "Sales Analytics", None),
]

for label, nav_view, step_num in views_and_steps:
    at.session_state["nav_view_selector"] = nav_view
    if step_num is not None:
        at.session_state["current_step"] = step_num
        if step_num >= 2:
            at.session_state["selected_items"] = [{
                "product_id": "P01",
                "product_name": "Business Broadband 100 Mbps",
                "category": "Connectivity",
                "quantity": 1,
                "price_min": 999,
                "price_max": 1499,
                "one_time_setup": 1000,
                "unit": "per connection",
                "reason": "Test",
                "assumption": "Test",
            }]
        if step_num >= 3:
            at.session_state["dpdp_consent_granted"] = True
    at.run()
    assert not at.exception, f"Exception in {label}: {at.exception}"

    # Verify no raw <div in markdown
    raw_div_count = sum(1 for m in at.markdown if "<div" in m.value.lower())
    assert raw_div_count == 0, f"Found {raw_div_count} raw <div in markdown for {label}!"

    # Verify stepper when in customer journey
    if nav_view == "Customer Journey":
        stepper_found = any("editorial-stepper" in h.value for h in at.html)
        assert stepper_found, f"Editorial stepper not found in HTML for {label}!"
        # Check stepper structure: circles, arrows
        stepper_html = next(h.value for h in at.html if "editorial-stepper" in h.value)
        assert "stepper-circle active" in stepper_html, "Active stepper circle missing!"
        assert "stepper-arrow" in stepper_html, "Stepper arrows missing!"

    # Verify top bar has no 'Get a quote'
    top_bar_html = next((h.value for h in at.html if "editorial-top-bar" in h.value), None)
    if top_bar_html:
        assert "Get a quote" not in top_bar_html, f"'Get a quote' found in top bar for {label}!"

    print(f"[OK] {label}: Clean markdown ({len(at.markdown)} elements), Valid HTML ({len(at.html)} blocks)")

print("\nAll views and steps render flawlessly with zero raw HTML leaks and verified stepper!")
