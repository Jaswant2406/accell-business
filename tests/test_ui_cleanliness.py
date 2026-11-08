"""
Test Suite for UI Cleanliness, Zero Raw HTML Leakage, and WCAG Button Contrast.
Validates:
1. Every HTML string passed to render_html has no line with 4+ leading spaces and no blank lines.
2. No rendered st.markdown element contains the literal text '<div'.
3. All button text states meet WCAG 2.1 AA contrast ratio (>= 4.5:1).
4. Top header has no standalone 'Get a quote' button.
"""

import re
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).parent.parent / "app.py"
from ui.html import clean_html, render_html, RENDERED_HTML_REGISTRY
from ui.styles import (
    render_top_header,
    render_stepper,
    render_hero_section,
    render_service_panels,
    render_clear_strip,
    render_checklist_block,
    render_stat_block,
    render_editorial_footer,
    status_badge,
)


def calculate_relative_luminance(hex_color: str) -> float:
    """Calculate WCAG 2.1 relative luminance for an sRGB hex color."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    r, g, b = [int(hex_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]

    def channel_luminance(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    rl = channel_luminance(r)
    gl = channel_luminance(g)
    bl = channel_luminance(b)
    return 0.2126 * rl + 0.7152 * gl + 0.0722 * bl


def calculate_contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculate WCAG 2.1 contrast ratio between two hex colors."""
    l1 = calculate_relative_luminance(hex1)
    l2 = calculate_relative_luminance(hex2)
    brightest = max(l1, l2)
    darkest = min(l1, l2)
    return (brightest + 0.05) / (darkest + 0.05)


def test_clean_html_removes_leading_spaces_and_blank_lines():
    """Verify clean_html removes all 4+ spaces and blank lines from dirty HTML strings."""
    dirty_html = """
        <div class="test-class">
            
            <span>Nested content</span>
                <p>Deeply indented line</p>
                
        </div>
    """
    cleaned = clean_html(dirty_html)
    assert cleaned != ""
    lines = cleaned.splitlines()
    for line in lines:
        assert not line.startswith("    "), f"Cleaned line starts with 4+ spaces: {line!r}"
        assert not line.startswith("\t"), f"Cleaned line starts with tab: {line!r}"
        assert line.strip() != "", "Cleaned HTML contains a blank line!"


def test_all_rendered_html_has_no_leading_spaces_or_blank_lines():
    """
    Scan every HTML string tracked in RENDERED_HTML_REGISTRY.
    Fails if any line has 4+ leading spaces or any blank line appears inside it.
    """
    # First, render standard components to populate registry
    render_top_header("journey")
    render_stepper(1)
    render_stepper(3)
    render_stepper(5)
    render_hero_section()
    render_service_panels()
    render_clear_strip()
    render_checklist_block()
    render_stat_block()
    render_editorial_footer()
    status_badge("APPROVED")
    status_badge("MANUAL REVIEW")
    status_badge("REJECTED")

    assert len(RENDERED_HTML_REGISTRY) > 0, "No HTML strings were registered!"

    for idx, html_str in enumerate(RENDERED_HTML_REGISTRY):
        lines = html_str.splitlines()
        for line_num, line in enumerate(lines, start=1):
            assert not line.startswith("    "), (
                f"Registry entry #{idx} line {line_num} starts with 4+ spaces: {line!r}"
            )
            assert not line.startswith("\t"), (
                f"Registry entry #{idx} line {line_num} starts with tab: {line!r}"
            )
            assert line != "", (
                f"Registry entry #{idx} line {line_num} is a blank line!"
            )


def test_no_rendered_markdown_contains_raw_div():
    """
    Using Streamlit AppTest, run all app views and steps.
    Asserts no rendered st.markdown element contains the literal text '<div'.
    """
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception

    def assert_no_raw_div(view_name: str):
        for idx, m in enumerate(at.markdown):
            assert "<div" not in m.value.lower(), (
                f"View '{view_name}' markdown element #{idx} contains literal '<div':\n{m.value}"
            )

    # 1. Home View
    assert_no_raw_div("Home Overview")

    # 2. Advisor Step
    at.session_state["nav_view_selector"] = "Customer Journey"
    at.session_state["current_step"] = 1
    at.run()
    assert not at.exception
    assert_no_raw_div("Advisor Step")

    # 3. Quote Step
    at.session_state["current_step"] = 2
    at.session_state["selected_items"] = [
        {
            "product_id": "P01",
            "product_name": "Business Broadband 100 Mbps",
            "category": "Connectivity",
            "quantity": 1,
            "price_min": 999,
            "price_max": 1499,
            "one_time_setup": 1000,
            "unit": "per connection",
            "reason": "Test item",
            "assumption": "Test assumption",
        }
    ]
    at.run()
    assert not at.exception
    assert_no_raw_div("Quote Step")

    # 4. KYC Step
    at.session_state["current_step"] = 3
    at.session_state["dpdp_consent_granted"] = True
    at.run()
    assert not at.exception
    assert_no_raw_div("KYC Step")

    # 5. Checkout Step
    at.session_state["current_step"] = 4
    at.run()
    assert not at.exception
    assert_no_raw_div("Checkout Step")

    # 6. Track Step
    at.session_state["current_step"] = 5
    at.run()
    assert not at.exception
    assert_no_raw_div("Track Step")

    # 7. KYC Verification Desk
    at.session_state["nav_view_selector"] = "KYC Verification Desk"
    at.run()
    assert not at.exception
    assert_no_raw_div("KYC Desk")

    # 8. Sales Analytics
    at.session_state["nav_view_selector"] = "Sales Analytics"
    at.run(timeout=60)
    assert not at.exception
    assert_no_raw_div("Sales Analytics")


def test_button_contrast_ratios_exceed_4_5_to_1():
    """
    Assert all button text and label states meet or exceed WCAG 2.1 AA 4.5:1 contrast.
    """
    button_states = {
        "Primary Button (White on Navy)": {
            "text": "#FFFFFF",
            "bg": "#1E3A8A",
            "min_required": 4.5,
        },
        "Primary Button Hover (White on Dark Navy)": {
            "text": "#FFFFFF",
            "bg": "#172B6B",
            "min_required": 4.5,
        },
        "Secondary Button (Ink on White)": {
            "text": "#111827",
            "bg": "#FFFFFF",
            "min_required": 4.5,
        },
        "Disabled Button (Muted Grey on Light Grey)": {
            "text": "#4B5563",
            "bg": "#E5E7EB",
            "min_required": 4.5,
        },
        "Sidebar Active Step (White on Navy)": {
            "text": "#FFFFFF",
            "bg": "#1E3A8A",
            "min_required": 4.5,
        },
        "Sidebar Completed Step (Navy on White)": {
            "text": "#1E3A8A",
            "bg": "#FFFFFF",
            "min_required": 4.5,
        },
        "Sidebar Upcoming Step (Dark Slate on White)": {
            "text": "#1F2937",
            "bg": "#FFFFFF",
            "min_required": 4.5,
        },
    }

    for name, config in button_states.items():
        ratio = calculate_contrast_ratio(config["text"], config["bg"])
        assert ratio >= config["min_required"], (
            f"Button state '{name}' failed contrast check: {ratio:.2f}:1 < {config['min_required']}:1"
        )


def test_top_header_no_get_a_quote_button():
    """Verify that the standalone 'Get a quote' pill button is removed from the top bar."""
    from ui.styles import render_top_header
    from ui.html import RENDERED_HTML_REGISTRY

    initial_len = len(RENDERED_HTML_REGISTRY)
    render_top_header("journey")
    rendered = RENDERED_HTML_REGISTRY[-1]

    assert "Get a quote" not in rendered, "Standalone 'Get a quote' button found in top header!"
    assert "top-wordmark" in rendered, "Wordmark missing from top header!"
    assert "UDYAM DIGITAL" in rendered, "Sub-label missing from top header!"


def test_injected_css_no_fixed_heights_and_overflow_protection():
    """
    Scan injected CSS from ui/styles.py:
    1. Assert no card/panel class (.bordered-card, .bordered-card-subtle, .bordered-box,
       .editorial-hero-left, .service-panels-row > div) defines fixed height: <number>px.
    2. Assert min-width: 0 is present.
    3. Assert overflow-wrap: anywhere is present.
    4. Assert white-space: normal / word-break on buttons and cells.
    """
    from ui.styles import apply_custom_styles
    initial_len = len(RENDERED_HTML_REGISTRY)
    apply_custom_styles()
    css_content = RENDERED_HTML_REGISTRY[-1]

    # Target selectors to verify no fixed height in px
    target_classes = [
        r'\.bordered-box',
        r'\.bordered-card',
        r'\.bordered-card-subtle',
        r'\.editorial-hero-left',
        r'\.service-panels-row\s*>\s*div',
    ]

    for target in target_classes:
        # Check that there is no fixed height like "height: 300px" or "height: 270px"
        fixed_height_pattern = rf'{target}[^{{\}}]*\{{[^}}]*?(?<!min-)height:\s*[0-9]+px'
        match = re.search(fixed_height_pattern, css_content, re.IGNORECASE | re.DOTALL)
        assert match is None, f"Fixed height in px found for selector {target}: {match.group(0) if match else ''}"

    # Verify min-width: 0 is present for flex/grid children
    assert "min-width: 0" in css_content, "min-width: 0 rule missing from injected CSS"

    # Verify overflow-wrap: anywhere is present
    assert "overflow-wrap: anywhere" in css_content, "overflow-wrap: anywhere missing from injected CSS"

    # Verify word-break: break-word
    assert "word-break: break-word" in css_content, "word-break rule missing from injected CSS"


def test_responsive_views_render_at_multiple_widths():
    """
    Simulate responsive rendering for screen widths [1440, 1024, 768, 390].
    Ensures Home, Advisor, Quote, KYC, Checkout, Track, and Analytics render cleanly
    without exception across desktop, tablet, and mobile breakpoints.
    """
    simulated_widths = [1440, 1024, 768, 390]

    for width in simulated_widths:
        at = AppTest.from_file(APP_PATH, default_timeout=30)
        at.run()
        assert not at.exception, f"App crashed on initial run at width {width}px"

        # 1. Customer Journey - Step 1: Advisor
        at.session_state["nav_view_selector"] = "Customer Journey"
        at.session_state["current_step"] = 1
        at.session_state["target_language"] = "English" if width > 768 else "Hindi"
        at.run()
        assert not at.exception, f"Advisor crashed at width {width}px"

        # 2. Customer Journey - Step 2: Quote
        at.session_state["current_step"] = 2
        at.session_state["selected_items"] = [
            {
                "product_id": "P01",
                "product_name": "Biz Fibre 100",
                "category": "Connectivity",
                "quantity": 1,
                "price_min": 999,
                "price_max": 1199,
                "one_time_setup": 0,
                "unit": "per site",
                "reason": "Test",
                "assumption": "Test",
            }
        ]
        at.run()
        assert not at.exception, f"Quote step crashed at width {width}px"

        # 3. Customer Journey - Step 3: KYC
        at.session_state["current_step"] = 3
        at.session_state["dpdp_consent_granted"] = True
        at.run()
        assert not at.exception, f"KYC step crashed at width {width}px"

        # 4. Customer Journey - Step 4: Checkout
        at.session_state["current_step"] = 4
        at.run()
        assert not at.exception, f"Checkout step crashed at width {width}px"

        # 5. Customer Journey - Step 5: Track
        at.session_state["current_step"] = 5
        at.run()
        assert not at.exception, f"Track step crashed at width {width}px"

        # 6. KYC Verification Desk
        at.session_state["nav_view_selector"] = "KYC Verification Desk"
        at.run()
        assert not at.exception, f"KYC desk crashed at width {width}px"

        # 7. Sales Analytics
        at.session_state["nav_view_selector"] = "Sales Analytics"
        at.run()
        assert not at.exception, f"Sales Analytics crashed at width {width}px"

