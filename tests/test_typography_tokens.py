"""
Test Suite for Typography, Design Tokens, Contrast Compliance, and Overlap Prevention.
Validates:
1. Exact design tokens: --ink #111827, --navy #1E3A8A, --muted #616B7A, --page #F4F5F7,
   --card #FFFFFF, --sky #93C5FD, --sand #E8DFCB, --hairline #D9DCE1.
2. Single Google Fonts @import with Manrope (500,600,700,800) and Inter (400,500,600).
3. Typography hierarchy:
   - Hero headline: Manrope 800, clamp(40px, 5.2vw, 70px), line-height 1.04, -0.04em, #111827.
   - Section headings: Manrope 800, clamp(28px, 3.4vw, 44px), line-height 1.1.
   - Card titles: Manrope 700, 20px, line-height 1.25.
   - Body text: Inter 400, 14px, line-height 24.5px, color --muted.
   - Small text / captions: Inter 400, 13px, line-height 1.5.
   - Eyebrow labels: Inter 600, 12px, uppercase, 0.14em, --navy.
   - Buttons and nav: Inter 600, 14px.
   - Tabular numbers & prices: Inter 600, tabular-nums.
4. Overlap prevention:
   - Every card/panel has display: flex/grid, gap: 12px+, box-sizing: border-box, padding 24px (16px mobile).
   - No negative margins in CSS.
   - No position: absolute on text elements.
   - Zero use of --muted on sand and sky panels.
"""

import re
import pytest
from ui.styles import (
    apply_custom_styles,
    render_hero_section,
    render_service_panels,
    render_stat_block,
    render_checklist_block,
    render_clear_strip,
)
from ui.html import RENDERED_HTML_REGISTRY


@pytest.fixture(scope="module")
def injected_css():
    """Retrieve injected CSS string from apply_custom_styles."""
    apply_custom_styles()
    return RENDERED_HTML_REGISTRY[-1]


def test_design_tokens_exact_hex_values(injected_css):
    """Assert all tokens strictly match reference values in :root."""
    expected_tokens = {
        "--ink": "#111827",
        "--navy": "#1E3A8A",
        "--muted": "#616B7A",
        "--page": "#F4F5F7",
        "--card": "#FFFFFF",
        "--sky": "#93C5FD",
        "--sand": "#E8DFCB",
        "--hairline": "#D9DCE1",
    }
    for token, hex_val in expected_tokens.items():
        pattern = rf"{token}\s*:\s*{hex_val}\s*;"
        assert re.search(pattern, injected_css, re.IGNORECASE) is not None, (
            f"Token '{token}' does not match expected '{hex_val}' in injected CSS"
        )


def test_single_google_fonts_import_weights(injected_css):
    """Assert single Google Fonts import loads required weights for Manrope & Inter."""
    import_match = re.search(r"@import\s+url\(['\"]([^'\"]+)['\"]\);", injected_css)
    assert import_match is not None, "@import rule for fonts not found in CSS"
    font_url = import_match.group(1)
    assert "family=Inter:wght@400;500;600" in font_url
    assert "family=Manrope:wght@500;600;700;800" in font_url


def test_hero_headline_typography(injected_css):
    """Assert hero headline specifies Manrope 800, clamp(40px, 5.2vw, 70px), and line-height 1.04."""
    hero_pattern = r"\.hero-headline\s*\{([^}]+)\}"
    match = re.search(hero_pattern, injected_css, re.DOTALL)
    assert match is not None, ".hero-headline class rule missing from CSS"
    rules = match.group(1)

    assert "font-family: 'Manrope'" in rules or 'font-family: "Manrope"' in rules or "Manrope" in rules
    assert "font-weight: 800" in rules
    assert "clamp(40px, 5.2vw, 70px)" in rules
    assert "line-height: 1.04" in rules
    assert "letter-spacing: -0.04em" in rules
    assert "var(--ink)" in rules or "#111827" in rules


def test_section_headings_and_card_titles_typography(injected_css):
    """Assert section headings and card titles follow Manrope 800 and 700 with fluid scales."""
    # h1 section headings
    h1_pattern = r"h1,\s*\[data-testid=\"stMarkdownContainer\"\]\s*h1\s*\{([^}]+)\}"
    h1_match = re.search(h1_pattern, injected_css, re.DOTALL)
    assert h1_match is not None
    h1_rules = h1_match.group(1)
    assert "font-weight: 800" in h1_rules
    assert "clamp(28px, 3.4vw, 44px)" in h1_rules
    assert "line-height: 1.1" in h1_rules

    # Card titles
    card_title_pattern = r"h3,\s*\[data-testid=\"stMarkdownContainer\"\]\s*h3,\s*\.card-title\s*\{([^}]+)\}"
    card_title_match = re.search(card_title_pattern, injected_css, re.DOTALL)
    assert card_title_match is not None
    ct_rules = card_title_match.group(1)
    assert "font-weight: 700" in ct_rules
    assert "font-size: 20px" in ct_rules
    assert "line-height: 1.25" in ct_rules


def test_body_text_and_captions_typography(injected_css):
    """Assert body text is Inter 400, 14px, line-height 24.5px; captions are 13px / 1.5."""
    body_pattern = r"p,\s*label,\s*li,\s*\[data-testid=\"stMarkdownContainer\"\]\s*p[^\{]*\{([^}]+)\}"
    body_match = re.search(body_pattern, injected_css, re.DOTALL)
    assert body_match is not None
    b_rules = body_match.group(1)
    assert "font-weight: 400" in b_rules
    assert "font-size: 14px" in b_rules
    assert "line-height: 24.5px" in b_rules
    assert "var(--muted)" in b_rules

    # Captions
    caption_pattern = r"\.caption,\s*small,\s*\[data-testid=\"stCaptionContainer\"\]\s*p[^\{]*\{([^}]+)\}"
    caption_match = re.search(caption_pattern, injected_css, re.DOTALL)
    assert caption_match is not None
    c_rules = caption_match.group(1)
    assert "font-weight: 400" in c_rules
    assert "font-size: 13px" in c_rules
    assert "line-height: 1.5" in c_rules


def test_eyebrow_and_button_typography(injected_css):
    """Assert eyebrow is Inter 600, 12px uppercase, 0.14em, and buttons are Inter 600, 14px."""
    eyebrow_pattern = r"\.eyebrow\s*\{([^}]+)\}"
    eyebrow_match = re.search(eyebrow_pattern, injected_css, re.DOTALL)
    assert eyebrow_match is not None
    e_rules = eyebrow_match.group(1)
    assert "font-weight: 600" in e_rules
    assert "font-size: 12px" in e_rules
    assert "text-transform: uppercase" in e_rules
    assert "letter-spacing: 0.14em" in e_rules
    assert "var(--navy)" in e_rules

    btn_pattern = r"div\.stButton\s*>\s*button[^\{]*\{([^}]+)\}"
    btn_match = re.search(btn_pattern, injected_css, re.DOTALL)
    assert btn_match is not None
    btn_rules = btn_match.group(1)
    assert "font-weight: 600" in btn_rules
    assert "font-size: 14px" in btn_rules


def test_cards_flex_gap_padding_and_no_negative_margins(injected_css):
    """
    Assert cards define:
    1. display: flex with flex-direction: column and gap: 12px+ (or grid).
    2. box-sizing: border-box and padding: 24px (16px on mobile).
    3. Zero negative margins in CSS.
    """
    card_pattern = r"\.bordered-box,\s*\.bordered-card,\s*\.bordered-card-subtle\s*\{([^}]+)\}"
    card_match = re.search(card_pattern, injected_css, re.DOTALL)
    assert card_match is not None
    c_rules = card_match.group(1)
    assert "display: flex" in c_rules
    assert "flex-direction: column" in c_rules
    assert "gap: 12px" in c_rules
    assert "box-sizing: border-box" in c_rules
    assert "padding: 24px" in c_rules

    # Assert no negative margins anywhere in the entire injected CSS
    neg_margin_pattern = r"margin(-[a-z]+)?:\s*-\s*[0-9]+px"
    neg_matches = re.findall(neg_margin_pattern, injected_css, re.IGNORECASE)
    assert len(neg_matches) == 0, f"Found negative margins in CSS: {neg_matches}"


def test_no_position_absolute_on_text_elements(injected_css):
    """Assert no text container selector has position: absolute in CSS."""
    text_selectors = [
        r"p\b",
        r"span\b",
        r"h1\b",
        r"h2\b",
        r"h3\b",
        r"h4\b",
        r"\.bordered-card\b",
        r"\.bordered-box\b",
        r"\.hero-headline\b",
        r"\.eyebrow\b",
    ]
    for sel in text_selectors:
        pattern = rf"{sel}[^{{\}}]*\{{[^}}]*?position:\s*absolute"
        match = re.search(pattern, injected_css, re.IGNORECASE | re.DOTALL)
        assert match is None, f"Selector {sel} has position: absolute in CSS: {match.group(0) if match else ''}"


def test_sand_and_sky_panels_never_use_muted_for_high_contrast():
    """
    Assert that neither the sky panel nor the sand panel in render_hero_section
    and render_service_panels use --muted or #616B7A (ensuring >= 4.5:1 contrast).
    """
    # 1. Hero right panel (Sky background)
    render_hero_section()
    hero_html = RENDERED_HTML_REGISTRY[-1]
    # Find the sky panel div
    sky_match = re.search(r'<div\s+style="background:\s*var\(--sky\);[^"]*">(.*?)</div>\s*</div>\s*</div>', hero_html, re.DOTALL)
    assert sky_match is not None
    sky_content = sky_match.group(1)
    assert "var(--muted)" not in sky_content, "Hero sky panel contains var(--muted)!"
    assert "#616B7A" not in sky_content, "Hero sky panel contains #616B7A!"

    # 2. Service panels (Navy, Sky, Sand)
    render_service_panels()
    panels_html = RENDERED_HTML_REGISTRY[-1]

    # Find the sand panel
    sand_match = re.search(r'<div\s+style="background:\s*var\(--sand\);[^"]*">(.*?)</div>\s*</div>\s*</div>', panels_html, re.DOTALL)
    assert sand_match is not None
    sand_content = sand_match.group(1)
    assert "var(--muted)" not in sand_content, "Service panel 3 (Sand) contains var(--muted)!"
    assert "#616B7A" not in sand_content, "Service panel 3 (Sand) contains #616B7A!"
