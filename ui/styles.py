"""
Editorial 'Bordered Grid' Design System for Accel Business Udyam Digital.
Inspired by modern editorial grid aesthetics (Lexa template).
Zero emojis. Strict typography and palette compliance:
- Palette: --ink #111827, --navy #1E3A8A, --sky #93C5FD, --sand #E8DFCB, --page #F4F5F7, --card #FFFFFF, --muted #616B7A, --hairline #D9DCE1.
- Typography: Manrope (headings), Inter (body, buttons, tabular-nums).
- Layout: 1.5px solid --ink borders, 20px radius containers, no drop shadows, clean hairlines.
- Bulletproof HTML rendering via ui.html.render_html (no markdown code-block bleeding).
"""

from typing import Optional
from ui.html import render_html

# Inline SVG Icon Library (monochrome, line stroke, consistent 1.8 - 2.2 stroke width)
SVG_ICONS = {
    "arrow_diag": """<svg class="icon-inline" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7M7 7h10v10"/></svg>""",
    "arrow_right": """<svg class="icon-inline" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>""",
    "check": """<svg class="icon-inline" viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>""",
    "check_circle": """<svg class="icon-inline" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>""",
    "shield": """<svg class="icon-inline" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>""",
    "file_text": """<svg class="icon-inline" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>""",
    "cpu": """<svg class="icon-inline" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>""",
    "activity": """<svg class="icon-inline" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>""",
    "layers": """<svg class="icon-inline" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>""",
    "sparkles": """<svg class="icon-inline" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v3m0 12v3m9-9h-3M6 12H3m15.364-6.364l-2.121 2.121M8.757 15.243l-2.121 2.121m12.728 0l-2.121-2.121M8.757 8.757L6.636 6.636"></path></svg>""",
}


def apply_custom_styles():
    """Inject editorial bordered grid CSS styles and Google Fonts."""
    css = """
    <style>
    /* Google Fonts: Single @import with Manrope (500,600,700,800) and Inter (400,500,600) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    :root {
        --ink: #111827;
        --navy: #1E3A8A;
        --navy-hover: #172B6B;
        --sky: #93C5FD;
        --sand: #E8DFCB;
        --page: #F4F5F7;
        --card: #FFFFFF;
        --muted: #616B7A;
        --hairline: #D9DCE1;
        --success-text: #166534;
        --success-bg: #DCFCE7;
        --success-border: #86EFAC;
        --warning-text: #92400E;
        --warning-bg: #FEF3C7;
        --warning-border: #FCD34D;
        --error-text: #991B1B;
        --error-bg: #FEE2E2;
        --error-border: #FCA5A5;
    }

    /* Hide Streamlit default chrome */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    footer {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden !important;
    }

    /* Page Canvas */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: var(--page) !important;
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        color: var(--muted) !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        overflow-x: hidden !important;
    }

    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 4rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 1240px !important;
    }

    /* Hero headline: Manrope 800, clamp(40px, 5.2vw, 70px), line-height 1.04 (72.8px), color #111827, letter-spacing -0.04em */
    .hero-headline {
        font-family: 'Manrope', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 800 !important;
        font-size: clamp(40px, 5.2vw, 70px) !important;
        line-height: 1.04 !important;
        letter-spacing: -0.04em !important;
        color: var(--ink) !important;
        margin: 16px 0 20px 0 !important;
        overflow-wrap: normal !important;
        word-break: normal !important;
        hyphens: none !important;
        -webkit-hyphens: none !important;
    }

    /* Section Headings: Manrope 800, clamp(28px, 3.4vw, 44px), line-height 1.1 */
    h1, [data-testid="stMarkdownContainer"] h1 {
        font-family: 'Manrope', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 800 !important;
        font-size: clamp(28px, 3.4vw, 44px) !important;
        line-height: 1.1 !important;
        letter-spacing: -0.03em !important;
        color: var(--ink) !important;
        margin-top: 0 !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
    }

    h2, [data-testid="stMarkdownContainer"] h2 {
        font-family: 'Manrope', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 800 !important;
        font-size: clamp(24px, 3.0vw, 36px) !important;
        line-height: 1.15 !important;
        letter-spacing: -0.03em !important;
        color: var(--ink) !important;
        margin-top: 0 !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
    }

    /* Card Titles: Manrope 700, 20px, line-height 1.25 */
    h3, [data-testid="stMarkdownContainer"] h3, .card-title {
        font-family: 'Manrope', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 700 !important;
        font-size: 20px !important;
        line-height: 1.25 !important;
        letter-spacing: -0.02em !important;
        color: var(--ink) !important;
        margin-top: 0 !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
    }

    h4, h5, h6,
    [data-testid="stMarkdownContainer"] h4,
    [data-testid="stMarkdownContainer"] h5,
    [data-testid="stMarkdownContainer"] h6 {
        font-family: 'Manrope', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        line-height: 1.3 !important;
        color: var(--ink) !important;
        margin-top: 0 !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
    }

    /* Body Text: Inter 400, 14px, line-height 24.5px (1.75), color --muted */
    p, label, li, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span:not([class*="material-"]):not([data-testid*="Icon"]) {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 400 !important;
        font-size: 14px !important;
        line-height: 24.5px !important;
        color: var(--muted);
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        hyphens: auto;
    }

    /* Small text / captions: Inter 400, 13px, line-height 1.5 */
    .caption, small, [data-testid="stCaptionContainer"] p, [data-testid="stCaptionContainer"] span {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 400 !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
        color: var(--muted) !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
    }

    /* Icon Font Protection: ensure Material Symbols and Streamlit UI icons ALWAYS render as glyphs */
    .material-symbols-rounded,
    .material-symbols-outlined,
    .material-symbols-sharp,
    .material-icons,
    [data-testid="stIconMaterial"],
    span[data-testid*="Icon"],
    div[data-testid*="Icon"],
    [data-testid="stExpander"] summary span:first-child,
    [data-testid="stExpander"] summary svg,
    div[data-testid="stFileUploader"] svg,
    div[data-testid="stFileUploader"] span[data-testid*="Icon"],
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="stSidebarCollapseButton"] svg {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
        font-style: normal !important;
        font-weight: normal !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        word-wrap: normal !important;
        white-space: nowrap !important;
        direction: ltr !important;
        -webkit-font-smoothing: antialiased !important;
        text-rendering: optimizeLegibility !important;
        -moz-osx-font-smoothing: grayscale !important;
        font-feature-settings: 'liga' 1 !important;
    }

    /* Eyebrow Label: Inter 600, 12px, uppercase, letter-spacing 0.14em, --navy */
    .eyebrow {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 600 !important;
        font-size: 12px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.14em !important;
        color: var(--navy) !important;
        margin-bottom: 8px !important;
        display: inline-block !important;
    }

    /* Tabular numbers for prices, metrics and data tables: Inter 600 */
    .tabular-num, td, th, [data-testid="stMetricValue"] {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 600 !important;
        font-variant-numeric: tabular-nums !important;
        font-feature-settings: "tnum" 1 !important;
    }

    /* ============================================================
       BUTTON STYLING (Strict 4.5:1 Contrast, High Specificity)
       ============================================================ */
    /* Universal Button Shape & Typography: Inter 600, 14px, Wrap labels, min-height 44px, no overlap */
    div.stButton > button,
    div[data-testid="stFileUploader"] button,
    button[data-testid="baseButton-primary"],
    button[data-testid="baseButton-secondary"],
    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-secondary"],
    button[kind="primary"],
    button[kind="secondary"],
    .stDownloadButton > button,
    .stLinkButton > a {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        border-radius: 9999px !important;
        min-height: 44px !important;
        height: auto !important;
        padding: 10px 22px !important;
        box-shadow: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px !important;
        white-space: normal !important;
        word-break: break-word !important;
        overflow-wrap: anywhere !important;
        text-align: center !important;
        line-height: 1.4 !important;
        transition: background-color 0.15s ease, border-color 0.15s ease !important;
        cursor: pointer !important;
        opacity: 1 !important;
    }

    /* Primary Buttons: Background #1E3A8A */
    div.stButton > button,
    div.stButton > button:first-child,
    div[data-testid="stFileUploader"] button,
    button[data-testid="baseButton-primary"],
    button[data-testid="stBaseButton-primary"],
    button[kind="primary"],
    .stDownloadButton > button {
        background-color: var(--navy) !important;
        border: 1.5px solid var(--navy) !important;
    }

    /* Pierce nested button children so label/icon is pure #FFFFFF (10.3:1 contrast) */
    div.stButton > button,
    div.stButton > button *,
    div[data-testid="stFileUploader"] button,
    div[data-testid="stFileUploader"] button *,
    button[data-testid="baseButton-primary"],
    button[data-testid="baseButton-primary"] *,
    button[data-testid="stBaseButton-primary"],
    button[data-testid="stBaseButton-primary"] *,
    button[kind="primary"],
    button[kind="primary"] *,
    .stDownloadButton > button * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }

    div.stButton > button p,
    div.stButton > button div,
    div.stButton > button span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]),
    div[data-testid="stFileUploader"] button span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]),
    button[data-testid="baseButton-primary"] p,
    button[data-testid="baseButton-primary"] span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]),
    button[data-testid="stBaseButton-primary"] p,
    button[data-testid="stBaseButton-primary"] span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]),
    button[kind="primary"] p,
    button[kind="primary"] span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]),
    .stDownloadButton > button span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]) {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }

    /* Icon font explicitly preserved inside buttons */
    div.stButton > button span.material-symbols-rounded,
    div.stButton > button [data-testid="stIconMaterial"],
    button [data-testid="stIconMaterial"],
    button span.material-symbols-rounded {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
        font-weight: normal !important;
        line-height: 1 !important;
    }

    /* Hover & Focus: Background #172B6B (13.5:1 contrast) */
    div.stButton > button:hover,
    div.stButton > button:focus,
    div[data-testid="stFileUploader"] button:hover,
    div[data-testid="stFileUploader"] button:focus,
    button[kind="primary"]:hover,
    button[kind="primary"]:focus,
    button[data-testid="baseButton-primary"]:hover,
    button[data-testid="stBaseButton-primary"]:hover {
        background-color: var(--navy-hover) !important;
        border-color: var(--navy-hover) !important;
    }
    div.stButton > button:hover *,
    div.stButton > button:focus *,
    div[data-testid="stFileUploader"] button:hover *,
    div[data-testid="stFileUploader"] button:focus *,
    button[kind="primary"]:hover *,
    button[kind="primary"]:focus *,
    button[data-testid="baseButton-primary"]:hover *,
    button[data-testid="stBaseButton-primary"]:hover * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }

    /* Secondary Buttons: Background #FFFFFF, Border 1.5px #111827, Text #111827 (16.15:1 contrast) */
    button[kind="secondary"],
    button[data-testid="baseButton-secondary"],
    button[data-testid="stBaseButton-secondary"] {
        background-color: #FFFFFF !important;
        border: 1.5px solid var(--ink) !important;
    }
    button[kind="secondary"],
    button[kind="secondary"] *,
    button[data-testid="baseButton-secondary"],
    button[data-testid="baseButton-secondary"] *,
    button[data-testid="stBaseButton-secondary"],
    button[data-testid="stBaseButton-secondary"] * {
        color: var(--ink) !important;
        fill: var(--ink) !important;
    }
    button[kind="secondary"] p,
    button[kind="secondary"] span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]),
    button[data-testid="baseButton-secondary"] p,
    button[data-testid="baseButton-secondary"] span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]),
    button[data-testid="stBaseButton-secondary"] p,
    button[data-testid="stBaseButton-secondary"] span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]) {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    button[kind="secondary"] span.material-symbols-rounded,
    button[kind="secondary"] [data-testid="stIconMaterial"],
    button[data-testid="baseButton-secondary"] [data-testid="stIconMaterial"],
    button[data-testid="stBaseButton-secondary"] [data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
        font-weight: normal !important;
    }
    button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover,
    button[data-testid="stBaseButton-secondary"]:hover {
        background-color: var(--page) !important;
        border-color: var(--ink) !important;
    }

    /* Disabled State: Background #E5E7EB, Label #4B5563 (4.94:1 contrast, no opacity wash) */
    div.stButton > button:disabled,
    div.stButton > button[disabled],
    button[disabled],
    div[data-testid="stFileUploader"] button:disabled {
        background-color: #E5E7EB !important;
        border-color: #E5E7EB !important;
        cursor: not-allowed !important;
        opacity: 1 !important;
    }
    div.stButton > button:disabled *,
    div.stButton > button[disabled] *,
    button[disabled] *,
    div[data-testid="stFileUploader"] button:disabled * {
        color: #4B5563 !important;
        fill: #4B5563 !important;
        opacity: 1 !important;
    }

    /* Inputs, Selectboxes, Textareas: 1.5px ink border, 12px radius, no shadow */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div,
    div[data-baseweb="textarea"] > div,
    input, textarea, select {
        border: 1.5px solid var(--ink) !important;
        border-radius: 12px !important;
        background-color: var(--card) !important;
        color: var(--ink) !important;
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-size: 14px !important;
        box-shadow: none !important;
    }
    div[data-baseweb="input"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within,
    div[data-baseweb="textarea"] > div:focus-within {
        border-color: var(--navy) !important;
        box-shadow: 0 0 0 2px rgba(30, 58, 138, 0.25) !important;
    }

    /* Streamlit Cards and Bordered Boxes: 1.5px solid ink border, no shadows, flex column, gap 12px, padding 24px, auto height, no overflow */
    .bordered-box,
    .bordered-card,
    .bordered-card-subtle {
        background: var(--card);
        border: 1.5px solid var(--ink);
        box-shadow: none !important;
        box-sizing: border-box !important;
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 24px;
        min-width: 0 !important;
        height: auto !important;
        min-height: auto !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        hyphens: auto;
    }
    .bordered-box {
        border-radius: 20px;
        margin-bottom: 24px;
        overflow: hidden;
    }
    .bordered-card {
        border-radius: 16px;
        margin-bottom: 20px;
    }
    .bordered-card-subtle {
        background: #FAFAFA;
        border-radius: 14px;
        margin-bottom: 16px;
    }

    /* Container wrappers in Streamlit */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        border: 1.5px solid var(--hairline) !important;
        border-radius: 16px !important;
        background: var(--card) !important;
        padding: 24px !important;
        margin-bottom: 16px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 12px !important;
        box-sizing: border-box !important;
        box-shadow: none !important;
    }

    /* Flex and Grid Containers: min-width: 0 on children, wrap as needed */
    div[data-testid="column"],
    .editorial-hero-grid,
    .service-panels-row,
    .stat-block-grid,
    .checklist-grid,
    .grid-auto-fit-260 {
        min-width: 0 !important;
        box-sizing: border-box !important;
        height: auto !important;
    }

    div[data-testid="column"] > *,
    .editorial-hero-grid > *,
    .service-panels-row > *,
    .stat-block-grid > *,
    .checklist-grid > *,
    .grid-auto-fit-260 > *,
    .bordered-card *,
    .bordered-card-subtle *,
    .bordered-box * {
        min-width: 0 !important;
        box-sizing: border-box !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
    }

    /* Grid standard: repeat(auto-fit, minmax(260px, 1fr)) with 24px gap; equal-height cards */
    .grid-auto-fit-260 {
        display: grid !important;
        grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)) !important;
        gap: 24px !important;
        align-items: stretch !important;
    }

    /* Section divider lines */
    .box-divider {
        border-top: 1.5px solid var(--ink);
        margin: 0;
        padding: 0;
    }
    .hairline-divider {
        border-top: 1px solid var(--hairline);
        margin: 16px 0;
    }

    /* Top Bar: Editorial Header */
    .editorial-top-bar {
        background: var(--card);
        border: 1.5px solid var(--ink);
        border-radius: 16px;
        padding: 14px 24px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: none !important;
    }
    .top-logo-group {
        display: flex;
        flex-direction: column;
        text-decoration: none;
    }
    .top-wordmark {
        font-family: 'Manrope', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif;
        font-weight: 700;
        font-size: 1.35rem;
        letter-spacing: -0.03em;
        color: var(--navy);
        line-height: 1.1;
    }
    .top-sublabel {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif;
        font-weight: 600;
        font-size: 10px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--muted);
        margin-top: 2px;
    }
    .top-nav-links {
        display: flex;
        align-items: center;
        gap: 24px;
    }
    .top-nav-link {
        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif;
        font-weight: 600;
        font-size: 14px;
        color: var(--muted);
        text-decoration: none;
        transition: color 0.15s ease;
    }
    .top-nav-link:hover, .top-nav-link.active {
        color: var(--ink);
        font-weight: 600;
    }

    /* Stepper: Numbered circles joined by thin arrows */
    .editorial-stepper {
        background: var(--card);
        border: 1.5px solid var(--ink);
        border-radius: 16px;
        padding: 14px 20px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: none !important;
    }
    .stepper-step {
        display: flex;
        align-items: center;
        gap: 10px;
        text-decoration: none;
    }
    .stepper-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 13px;
        transition: all 0.15s ease;
    }
    .stepper-circle.active {
        background: var(--navy);
        color: #FFFFFF;
        border: 1.5px solid var(--navy);
    }
    .stepper-circle.completed {
        background: var(--card);
        color: var(--navy);
        border: 1.5px solid var(--navy);
    }
    .stepper-circle.upcoming {
        background: var(--card);
        color: var(--muted);
        border: 1.5px solid var(--hairline);
    }
    .stepper-label {
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        font-weight: 500;
        color: var(--muted);
    }
    .stepper-label.active {
        font-weight: 600;
        color: var(--ink);
    }
    .stepper-label.completed {
        font-weight: 500;
        color: var(--ink);
    }
    .stepper-arrow {
        color: var(--hairline);
        display: flex;
        align-items: center;
        padding: 0 4px;
    }

    /* Status Badges: Text pills with strict contrast */
    .badge-approved {
        background-color: var(--success-bg);
        color: var(--success-text);
        border: 1px solid var(--success-border);
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 12px;
        padding: 4px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        letter-spacing: 0.02em;
    }
    .badge-review {
        background-color: var(--warning-bg);
        color: var(--warning-text);
        border: 1px solid var(--warning-border);
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 12px;
        padding: 4px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        letter-spacing: 0.02em;
    }
    .badge-rejected {
        background-color: var(--error-bg);
        color: var(--error-text);
        border: 1px solid var(--error-border);
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 12px;
        padding: 4px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
        letter-spacing: 0.02em;
    }
    .badge-neutral {
        background-color: var(--page);
        color: var(--ink);
        border: 1px solid var(--hairline);
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        font-size: 12px;
        padding: 4px 12px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }

    /* Expanders: 1.5px solid ink border */
    [data-testid="stExpander"] {
        border: 1.5px solid var(--ink) !important;
        border-radius: 14px !important;
        background: var(--card) !important;
        box-shadow: none !important;
        margin-bottom: 16px !important;
        overflow: hidden !important;
    }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]) {
        font-family: 'Manrope', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        color: var(--ink) !important;
        background-color: var(--card) !important;
        padding: 6px 0 !important;
    }

    /* Slider: ensure slider min/max labels are #111827 (16:1 contrast on page), and thumb value is #FFFFFF (10.3:1 on navy) */
    div[data-testid="stSlider"] div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stSlider"] div[data-testid="stMarkdownContainer"] span {
        color: var(--ink) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
    }
    div[data-testid="stSlider"] [data-testid="stSliderThumbValue"] div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stSlider"] [data-testid="stSliderThumbValue"] p,
    div[data-testid="stSlider"] [data-testid="stSliderThumbValue"] div,
    div[data-testid="stSlider"] [data-testid="stSliderThumbValue"] span,
    div[data-testid="stSlider"] [data-testid="stSliderThumbValue"] *,
    [data-testid="stSliderThumbValue"] p,
    [data-testid="stSliderThumbValue"] span,
    [data-testid="stSliderThumbValue"] *,
    div[role="slider"] div,
    div[role="slider"] p {
        color: #FFFFFF !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }

    /* Table & Dataframe styling: scrollable container, wrapped cells, right-aligned numbers */
    [data-testid="stDataFrame"], table {
        border: 1.5px solid var(--ink) !important;
        border-radius: 12px !important;
        overflow-x: auto !important;
        max-width: 100% !important;
        font-family: 'Inter', sans-serif !important;
    }
    th {
        background-color: #F8FAFC !important;
        color: var(--muted) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 11px !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        border-bottom: 1px solid var(--hairline) !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        line-height: 1.4 !important;
    }
    td {
        border-bottom: 1px solid var(--hairline) !important;
        color: var(--ink) !important;
        font-size: 14px !important;
        white-space: normal !important;
        overflow-wrap: anywhere !important;
        word-break: break-word !important;
        line-height: 1.45 !important;
    }

    /* Inline Icons */
    .icon-inline {
        vertical-align: -2px;
        display: inline-block;
    }

    /* Mobile media query (< 768px): stacks to 1 column, consistent 16px padding */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 12px !important;
            padding-right: 12px !important;
        }
        .bordered-card,
        .bordered-card-subtle,
        .bordered-box,
        div[data-testid="stVerticalBlockBorderWrapper"] > div {
            padding: 16px !important;
        }
        .editorial-hero-grid {
            grid-template-columns: 1fr !important;
            gap: 16px !important;
            height: auto !important;
            min-height: auto !important;
        }
        .editorial-hero-left {
            padding: 24px 16px !important;
            border-right: none !important;
            border-bottom: 1.5px solid var(--ink) !important;
            height: auto !important;
            min-height: auto !important;
        }
        .service-panels-row {
            grid-template-columns: 1fr !important;
            gap: 16px !important;
            height: auto !important;
            min-height: auto !important;
        }
        .service-panels-row > div {
            border-right: none !important;
            border-bottom: 1.5px solid var(--ink) !important;
            padding: 24px 16px !important;
            height: auto !important;
            min-height: auto !important;
        }
        .stat-block-grid {
            grid-template-columns: 1fr !important;
            gap: 16px !important;
            height: auto !important;
            min-height: auto !important;
        }
        .editorial-stepper {
            overflow-x: auto !important;
            gap: 8px !important;
            padding: 10px 14px !important;
        }
        .stepper-label {
            display: none !important;
        }
        .checklist-grid {
            grid-template-columns: 1fr !important;
            height: auto !important;
            min-height: auto !important;
        }
        .checklist-grid > div:first-child {
            border-right: none !important;
            border-bottom: 1.5px solid var(--ink) !important;
            padding: 24px 16px !important;
        }
        .checklist-grid > div:last-child {
            padding: 20px 16px !important;
        }
        .top-nav-links {
            display: none !important;
        }
    }
    </style>
    """
    render_html(css)


def render_top_header(active_nav: str = "journey"):
    """
    Render editorial top bar: text logo Accel Business (navy), sub-label UDYAM DIGITAL,
    and nav links in muted. Removed standalone 'Get a quote' button.
    """
    html = f"""
    <div class="editorial-top-bar">
        <div class="top-logo-group">
            <span class="top-wordmark">Accel Business</span>
            <span class="top-sublabel">UDYAM DIGITAL</span>
        </div>
        <div class="top-nav-links">
            <span class="top-nav-link {'active' if active_nav == 'home' else ''}">Platform</span>
            <span class="top-nav-link {'active' if active_nav == 'journey' else ''}">Onboarding</span>
            <span class="top-nav-link {'active' if active_nav == 'kyc' else ''}">KYC Audit</span>
            <span class="top-nav-link {'active' if active_nav == 'analytics' else ''}">Analytics</span>
        </div>
    </div>
    """
    render_html(html)


def render_stepper(current_step: int):
    """
    Render editorial stepper:
    01 Advisor, 02 Quote, 03 KYC, 04 Checkout, 05 Track joined by thin arrows.
    Filled navy circle for active, outlined navy with check icon for completed, muted outline for upcoming.
    """
    steps = [
        (1, "01", "Advisor"),
        (2, "02", "Quote"),
        (3, "03", "KYC"),
        (4, "04", "Checkout"),
        (5, "05", "Track"),
    ]

    parts = ['<div class="editorial-stepper">']
    for idx, (step_num, num_str, label) in enumerate(steps):
        if step_num < current_step:
            circle_cls = "completed"
            label_cls = "completed"
            content = SVG_ICONS["check"]
        elif step_num == current_step:
            circle_cls = "active"
            label_cls = "active"
            content = num_str
        else:
            circle_cls = "upcoming"
            label_cls = ""
            content = num_str

        parts.append(
            f'<div class="stepper-step">'
            f'<div class="stepper-circle {circle_cls}">{content}</div>'
            f'<span class="stepper-label {label_cls}">{label}</span>'
            f'</div>'
        )

        if idx < len(steps) - 1:
            parts.append(
                f'<div class="stepper-arrow">{SVG_ICONS["arrow_right"]}</div>'
            )

    parts.append("</div>")
    render_html("".join(parts))


def render_hero_section():
    """
    Render 2-column bordered split hero (home view).
    Left white panel: eyebrow 'INDIA'S SMALL BUSINESSES. ONE PLATFORM.',
    headline with fluid clamp 'Your business.' / 'Digital in one sitting.' / 'No salesperson.' (last line navy),
    short paragraph.
    Right --sky panel: eyebrow with line icon, 2-line navy headline, caption, arrow at bottom right.
    """
    html = f"""
    <div class="bordered-box" style="margin-bottom: 24px; padding: 0;">
        <div class="editorial-hero-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); min-height: auto; height: auto; align-items: stretch;">
            <div class="editorial-hero-left" style="background: var(--card); padding: clamp(20px, 3.2vw, 40px); display: flex; flex-direction: column; justify-content: space-between; border-right: 1.5px solid var(--ink); min-height: auto; height: auto;">
                <div>
                    <span class="eyebrow">India's small businesses. One platform.</span>
                    <h1 class="hero-headline">
                        Your business.<br/>
                        Digital in one sitting.<br/>
                        <span style="color: var(--navy) !important;">No salesperson.</span>
                    </h1>
                    <p style="font-size: 14px; line-height: 24.5px; color: var(--muted); max-width: 480px; margin: 0; overflow-wrap: anywhere; word-break: break-word;">
                        Live catalogue pricing, instant statutory eligibility, automated GST and Udyam OCR verification, and simulated circuit provisioning.
                    </p>
                </div>
            </div>
            <div style="background: var(--sky); padding: clamp(24px, 4vw, 44px); display: flex; flex-direction: column; justify-content: space-between; min-height: auto; height: auto;">
                <div>
                    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                        {SVG_ICONS['cpu']}
                        <span style="font-family: 'Inter', sans-serif; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.14em; color: var(--navy);">
                            DETERMINISTIC TELECOM ARCHITECTURE
                        </span>
                    </div>
                    <h2 style="font-family: 'Manrope', sans-serif; font-size: clamp(24px, 3.2vw, 32px); font-weight: 800; line-height: 1.15; letter-spacing: -0.03em; color: var(--navy); margin-bottom: 16px; overflow-wrap: anywhere;">
                        Zero field-agent delays.<br/>
                        Full statutory compliance.
                    </h2>
                    <p style="font-size: 14px; line-height: 24.5px; color: var(--ink) !important; margin: 0; overflow-wrap: anywhere;">
                        Engineered under DPDP Act 2023 with cryptographic checksum cross-checks against MCA, GSTN, and MSME registries.
                    </p>
                </div>
                <div style="display: flex; justify-content: flex-end; color: var(--navy); margin-top: 24px;">
                    {SVG_ICONS['arrow_diag']}
                </div>
            </div>
        </div>
    </div>
    """
    render_html(html)


def render_service_panels():
    """
    Three service panels in a row, flush with 1.5px borders:
    Panel 1: --navy (white text)
    Panel 2: --sky (navy text)
    Panel 3: --sand (ink text)
    Each has tiny '01 / ...' eyebrow, line icon top right, bold title, short description,
    hairline divider, small tags at bottom left, diagonal arrow bottom right.
    """
    html = f"""
    <div class="bordered-box" style="margin-bottom: 24px; padding: 0;">
        <div class="service-panels-row" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); min-height: auto; height: auto; align-items: stretch;">
            <div style="background: var(--navy); color: #FFFFFF; padding: clamp(20px, 3vw, 32px); display: flex; flex-direction: column; justify-content: space-between; border-right: 1.5px solid var(--ink); min-height: auto; height: auto;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                        <span style="font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; letter-spacing: 0.14em; color: var(--sky);">01 / ADVISORY</span>
                        <span style="color: var(--sky);">{SVG_ICONS['cpu']}</span>
                    </div>
                    <h3 class="card-title" style="color: #FFFFFF !important; margin-bottom: 10px; overflow-wrap: anywhere;">AI Business Advisor</h3>
                    <p style="font-size: 14px; line-height: 24.5px; color: #FFFFFF !important; opacity: 0.95; margin: 0; overflow-wrap: anywhere;">
                        Natural language requirements profiling powered by Gemini Flash with deterministic fallback.
                    </p>
                </div>
                <div>
                    <div style="border-top: 1px solid rgba(255, 255, 255, 0.25); margin: 18px 0 14px 0;"></div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; color: var(--sky);">Rules Engine • Needs Mapping</span>
                        <span style="color: #FFFFFF;">{SVG_ICONS['arrow_diag']}</span>
                    </div>
                </div>
            </div>

            <div style="background: var(--sky); color: var(--navy); padding: clamp(20px, 3vw, 32px); display: flex; flex-direction: column; justify-content: space-between; border-right: 1.5px solid var(--ink); min-height: auto; height: auto;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                        <span style="font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; letter-spacing: 0.14em; color: var(--navy);">02 / PRICING</span>
                        <span style="color: var(--navy);">{SVG_ICONS['layers']}</span>
                    </div>
                    <h3 class="card-title" style="color: var(--navy) !important; margin-bottom: 10px; overflow-wrap: anywhere;">Exact Solution Quote</h3>
                    <p style="font-size: 14px; line-height: 24.5px; color: var(--ink) !important; margin: 0; overflow-wrap: anywhere;">
                        Instant catalogue pricing, contract terms, dependency validation, and algorithmic budget fit optimizer.
                    </p>
                </div>
                <div>
                    <div style="border-top: 1px solid rgba(30, 58, 138, 0.25); margin: 18px 0 14px 0;"></div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; color: var(--navy);">25 Products • Zero Hidden Fees</span>
                        <span style="color: var(--navy);">{SVG_ICONS['arrow_diag']}</span>
                    </div>
                </div>
            </div>

            <div style="background: var(--sand); color: var(--ink); padding: clamp(20px, 3vw, 32px); display: flex; flex-direction: column; justify-content: space-between; min-height: auto; height: auto;">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
                        <span style="font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; letter-spacing: 0.14em; color: var(--navy);">03 / STATUTORY</span>
                        <span style="color: var(--navy);">{SVG_ICONS['shield']}</span>
                    </div>
                    <h3 class="card-title" style="color: var(--ink) !important; margin-bottom: 10px; overflow-wrap: anywhere;">Smart KYC & Tracking</h3>
                    <p style="font-size: 14px; line-height: 24.5px; color: var(--ink) !important; margin: 0; overflow-wrap: anywhere;">
                        Automated multi-pass OCR extraction, 8 statutory compliance cross-checks, and live circuit telemetry.
                    </p>
                </div>
                <div>
                    <div style="border-top: 1px solid rgba(17, 24, 39, 0.2); margin: 18px 0 14px 0;"></div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; color: var(--navy);">DPDP Consent • 5-Stage SLA</span>
                        <span style="color: var(--ink);">{SVG_ICONS['arrow_diag']}</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    """
    render_html(html)


def render_clear_strip():
    """
    'Clear from the start' strip: three numbered outlined circles 01, 02, 03 connected by thin arrows.
    """
    html = f"""
    <div class="bordered-card" style="padding: 24px 32px; margin-bottom: 24px;">
        <div style="margin-bottom: 16px;">
            <span class="eyebrow">HOW IT WORKS</span>
            <h3 class="card-title" style="font-size: 20px; margin: 0;">Clear from the start.</h3>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="width: 36px; height: 36px; border-radius: 50%; border: 1.5px solid var(--ink); display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 13px; color: var(--ink);">01</div>
                <div>
                    <div style="font-weight: 600; font-size: 14px; color: var(--ink);">Tell us what you run</div>
                    <div style="font-size: 13px; color: var(--muted);">Team size, premises, sector, and digital needs</div>
                </div>
            </div>
            <div style="color: var(--hairline);">{SVG_ICONS['arrow_right']}</div>
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="width: 36px; height: 36px; border-radius: 50%; border: 1.5px solid var(--ink); display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 13px; color: var(--ink);">02</div>
                <div>
                    <div style="font-weight: 600; font-size: 14px; color: var(--ink);">Get an unbundled quote</div>
                    <div style="font-size: 13px; color: var(--muted);">Itemized catalogue lines with transparent budget control</div>
                </div>
            </div>
            <div style="color: var(--hairline);">{SVG_ICONS['arrow_right']}</div>
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="width: 36px; height: 36px; border-radius: 50%; border: 1.5px solid var(--ink); display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 13px; color: var(--ink);">03</div>
                <div>
                    <div style="font-weight: 600; font-size: 14px; color: var(--ink);">Verify and activate</div>
                    <div style="font-size: 13px; color: var(--muted);">Direct registry checks and live circuit installation</div>
                </div>
            </div>
        </div>
    </div>
    """
    render_html(html)


def render_checklist_block():
    """
    Checklist block: left side eyebrow plus big headline with second line in navy;
    right side rows with circular check icon (alternating --sky and --sand circles),
    bold title, muted description, hairline dividers.
    """
    items = [
        ("Rules-based recommendations", "Deterministic eligibility matching based on city tier, team headcount, and premise dependencies."),
        ("Registry-checked KYC", "Automated cross-verification against live GSTIN checksum and Udyam enterprise registries."),
        ("Consent first (DPDP Act)", "Granular digital consent barrier with automatic 30-day purge policy for unapproved records."),
        ("Live order tracking", "Transparent 5-stage activation timeline with simulated dispatch, engineer assignment, and circuit testing."),
    ]

    right_rows = []
    for idx, (title, desc) in enumerate(items):
        bg_color = "var(--sky)" if idx % 2 == 0 else "var(--sand)"
        icon_color = "var(--navy)" if idx % 2 == 0 else "var(--ink)"
        border_line = "" if idx == len(items) - 1 else '<div class="hairline-divider" style="margin: 14px 0;"></div>'

        right_rows.append(f"""
        <div style="display: flex; align-items: flex-start; gap: 14px;">
            <div style="width: 28px; height: 28px; border-radius: 50%; background: {bg_color}; color: {icon_color}; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;">
                {SVG_ICONS['check']}
            </div>
            <div>
                <div style="font-weight: 700; font-size: 15px; color: var(--ink); overflow-wrap: anywhere;">{title}</div>
                <div style="font-size: 13px; line-height: 1.5; color: var(--muted); margin-top: 2px; overflow-wrap: anywhere;">{desc}</div>
            </div>
        </div>
        {border_line}
        """)

    html = f"""
    <div class="bordered-box" style="margin-bottom: 24px; padding: 0;">
        <div class="checklist-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); min-height: auto; height: auto; align-items: stretch;">
            <div style="padding: clamp(24px, 4vw, 40px); background: var(--card); border-right: 1.5px solid var(--ink); display: flex; flex-direction: column; justify-content: center; min-height: auto; height: auto;">
                <span class="eyebrow">COMPLIANCE & GOVERNANCE</span>
                <h2 style="font-size: clamp(24px, 4vw, 36px); line-height: 1.1; margin-top: 12px; overflow-wrap: anywhere;">
                    Statutory rigor.<br/>
                    <span style="color: var(--navy);">Zero sales friction.</span>
                </h2>
                <p style="font-size: 14px; line-height: 24.5px; color: var(--muted); margin-top: 14px; overflow-wrap: anywhere;">
                    Every check and calculation is auditable. No manual salesperson bias, no hidden commissions, and no document storage outside strict DPDP rules.
                </p>
            </div>
            <div style="padding: clamp(20px, 3.5vw, 36px); background: var(--card); min-height: auto; height: auto;">
                {''.join(right_rows)}
            </div>
        </div>
    </div>
    """
    render_html(html)


def render_stat_block():
    """
    Stat block on a --sand background: huge navy number ('25') with small line icon,
    a headline, and a responsive link list with hairline underlines and diagonal arrows.
    """
    html = f"""
    <div class="bordered-box" style="background: var(--sand); margin-bottom: 28px; padding: 0;">
        <div style="padding: 32px 24px; min-height: auto; height: auto;">
            <div style="display: flex; align-items: baseline; gap: 16px; margin-bottom: 12px;">
                <span style="font-family: 'Manrope', sans-serif; font-weight: 800; font-size: clamp(52px, 8vw, 80px); line-height: 0.95; color: var(--navy); letter-spacing: -0.04em;">25</span>
                <div style="color: var(--navy);">{SVG_ICONS['layers']}</div>
            </div>
            <h3 class="card-title" style="font-size: clamp(18px, 2.5vw, 22px); color: var(--ink); max-width: 680px; margin-bottom: 24px; overflow-wrap: anywhere;">
                Commercial-grade enterprise connectivity, cloud voice, and digital solutions in our unbundled catalogue.
            </h3>

            <div class="stat-block-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; border-top: 1.5px solid var(--ink); padding-top: 20px; min-height: auto; height: auto;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(17, 24, 39, 0.25); padding-bottom: 8px;">
                    <span style="font-weight: 600; font-size: 14px; color: var(--ink); overflow-wrap: anywhere;">Fiber & Leased Lines</span>
                    <span style="color: var(--navy);">{SVG_ICONS['arrow_diag']}</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(17, 24, 39, 0.25); padding-bottom: 8px;">
                    <span style="font-weight: 600; font-size: 14px; color: var(--ink); overflow-wrap: anywhere;">Cloud Voice & SIP Trunks</span>
                    <span style="color: var(--navy);">{SVG_ICONS['arrow_diag']}</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(17, 24, 39, 0.25); padding-bottom: 8px;">
                    <span style="font-weight: 600; font-size: 14px; color: var(--ink); overflow-wrap: anywhere;">Cyber Security & IoT</span>
                    <span style="color: var(--navy);">{SVG_ICONS['arrow_diag']}</span>
                </div>
            </div>
        </div>
    </div>
    """
    render_html(html)


def render_editorial_footer():
    """Footer line in small muted text."""
    html = """
    <div style="border-top: 1.5px solid var(--ink); padding-top: 20px; margin-top: 36px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
        <span style="font-family: 'Inter', sans-serif; font-size: 12px; color: var(--muted);">
            Accel Business Udyam Digital • Autonomous Enterprise SMB Onboarding • Reference Date: 2026-07-15
        </span>
        <span style="font-family: 'Inter', sans-serif; font-size: 12px; color: var(--muted);">
            Enterprise Track A • DPDP Act 2023 Compliant
        </span>
    </div>
    """
    render_html(html)


def status_badge(decision: str) -> str:
    """Return clean HTML status badge pill with zero emojis."""
    clean = decision.upper().strip()
    if "APPROV" in clean or clean == "PASSED":
        return '<span class="badge-approved">Approved</span>'
    elif "MANUAL" in clean or "REVIEW" in clean:
        return '<span class="badge-review">Manual Review</span>'
    elif "REJECT" in clean or "FAILED" in clean:
        return '<span class="badge-rejected">Rejected</span>'
    return f'<span class="badge-neutral">{decision}</span>'
