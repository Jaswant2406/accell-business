"""
Accel Business Udyam Digital - Main Streamlit Application
Autonomous End-to-End Enterprise SMB Onboarding
Accel YTL Hackathon 2026, Enterprise Track A
"""

import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

FAVICON_PATH = str(Path(__file__).resolve().parent / "assets" / "favicon.png")

# Streamlit Page Configuration - Clean monochrome favicon, wide layout
st.set_page_config(
    page_title="Accel Business • Udyam Digital",
    page_icon=FAVICON_PATH if os.path.exists(FAVICON_PATH) else None,
    layout="wide",
    initial_sidebar_state="auto",
)

from ui.html import render_html
from ui.styles import (
    apply_custom_styles,
    render_top_header,
    render_stepper,
    render_hero_section,
    render_service_panels,
    render_clear_strip,
    render_checklist_block,
    render_stat_block,
    render_editorial_footer,
    SVG_ICONS,
)
from ui.step_advisor import render_step_advisor
from ui.step_quote import render_step_quote
from ui.step_kyc import render_step_kyc
from ui.step_checkout import render_step_checkout
from engine.pricing import calculate_quote
from ui.step_track import render_step_track
from ui.page_analytics import render_sales_analytics


def init_session():
    """Ensure persistent session state keys across all steps."""
    if "current_step" not in st.session_state:
        st.session_state.current_step = 1
    if "business_profile" not in st.session_state:
        st.session_state.business_profile = None
    if "selected_items" not in st.session_state:
        st.session_state.selected_items = []
    if "current_quote" not in st.session_state:
        st.session_state.current_quote = None
    if "kyc_result" not in st.session_state:
        st.session_state.kyc_result = None
    if "dpdp_consent_granted" not in st.session_state:
        st.session_state.dpdp_consent_granted = False
    if "nav_view_selector" not in st.session_state:
        st.session_state.nav_view_selector = "Home"
    if "ai_mode_toggle" not in st.session_state:
        st.session_state.ai_mode_toggle = False
    if "advisor_input" not in st.session_state:
        st.session_state.advisor_input = {
            "business_name": "Harmony Dental Care",
            "business_type": "Healthcare/Clinic",
            "employees": 5,
            "sites": 1,
            "city": "Bengaluru",
            "current_broadband": "None",
            "has_gstin": True,
            "gstin": "29AABCS1429B1ZB",
            "digital_needs": ["cloud_storage", "voice_lines"],
            "chat_text": "We are a 5-doctor dental and healthcare clinic in Bengaluru operating from 1 premises. We need reliable high-speed broadband for digital X-rays and patient EHR, cloud backup, and fixed voice lines for patient appointments.",
        }


def render_sidebar():
    """Render editorial sidebar with navigation and system diagnostic health."""
    with st.sidebar:
        render_html(
            """
            <div style="padding: 12px 0 16px 0; border-bottom: 1.5px solid var(--ink); margin-bottom: 16px;">
                <div style="font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 1.25rem; color: var(--navy); line-height: 1.1;">
                    Accel Business
                </div>
                <div style="font-family: 'Inter', sans-serif; font-weight: 600; font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: var(--muted); margin-top: 4px;">
                    Udyam Digital • Track A
                </div>
            </div>
            """
        )

        nav_options = [
            "Home",
            "Customer Journey",
            "KYC Verification Desk",
            "Sales Analytics",
        ]

        if st.session_state.get("nav_view_selector") not in nav_options:
            st.session_state["nav_view_selector"] = "Home"

        nav_view = st.radio(
            "Application View:",
            nav_options,
            key="nav_view_selector",
        )

        if "journey" in nav_view.lower():
            render_html(
                """
                <div style="margin-top: 20px; margin-bottom: 10px;">
                    <span class="eyebrow">JOURNEY STAGES</span>
                </div>
                """
            )
            step_names = {
                1: "01 Advisor",
                2: "02 Quote",
                3: "03 KYC Verification",
                4: "04 Checkout",
                5: "05 Activation Track",
            }

            curr = st.session_state.current_step
            btn_css_parts = []
            for s_num in range(1, 6):
                if s_num == curr:
                    # Current step: filled navy #1E3A8A, white text #FFFFFF (10.3:1 contrast)
                    btn_css_parts.append(f"""
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} > div.stButton > button,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button {{
                        background-color: #1E3A8A !important;
                        border: 1.5px solid #1E3A8A !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button *,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button p,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button div,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button span,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button svg {{
                        color: #FFFFFF !important;
                        fill: #FFFFFF !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]) {{
                        font-family: 'Inter', sans-serif !important;
                        font-weight: 600 !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button span.material-symbols-rounded,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button [data-testid="stIconMaterial"] {{
                        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button:hover {{
                        background-color: #172B6B !important;
                        border-color: #172B6B !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button:hover * {{
                        color: #FFFFFF !important;
                        fill: #FFFFFF !important;
                    }}
                    """)
                elif s_num < curr:
                    # Completed step: white background, navy outline 1.5px solid #1E3A8A, navy text #1E3A8A (10.3:1 contrast on white)
                    btn_css_parts.append(f"""
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} > div.stButton > button,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button {{
                        background-color: #FFFFFF !important;
                        border: 1.5px solid #1E3A8A !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button *,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button p,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button div,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button span,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button svg {{
                        color: #1E3A8A !important;
                        fill: #1E3A8A !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]) {{
                        font-family: 'Inter', sans-serif !important;
                        font-weight: 600 !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button span.material-symbols-rounded,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button [data-testid="stIconMaterial"] {{
                        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button:hover {{
                        background-color: #F4F5F7 !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button:hover * {{
                        color: #1E3A8A !important;
                        fill: #1E3A8A !important;
                    }}
                    """)
                else:
                    # Upcoming step: white background, muted outline 1.5px solid #D9DCE1, #111827 text (16.15:1 contrast on white)
                    btn_css_parts.append(f"""
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} > div.stButton > button,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button {{
                        background-color: #FFFFFF !important;
                        border: 1.5px solid #D9DCE1 !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button *,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button p,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button div,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button span,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button svg {{
                        color: #111827 !important;
                        fill: #111827 !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button span:not(.material-symbols-rounded):not([data-testid="stIconMaterial"]) {{
                        font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Arial, sans-serif !important;
                        font-weight: 600 !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button span.material-symbols-rounded,
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button [data-testid="stIconMaterial"] {{
                        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button:hover {{
                        background-color: #F4F5F7 !important;
                        border-color: #94A3B8 !important;
                    }}
                    [data-testid="stSidebar"] div.st-key-nav_step_{s_num} button:hover * {{
                        color: #111827 !important;
                        fill: #111827 !important;
                    }}
                    """)

            render_html(f"<style>{''.join(btn_css_parts)}</style>")

            for s_num, s_name in step_names.items():
                icon_val = ":material/check:" if s_num < curr else None
                if st.button(s_name, key=f"nav_step_{s_num}", icon=icon_val, width="stretch"):
                    st.session_state.current_step = s_num
                    st.rerun()

            if st.session_state.get("selected_items"):
                q_res = calculate_quote(st.session_state.selected_items)
                render_html(
                    f"""
                    <div class="bordered-card-subtle" style="margin-top: 20px; padding: 16px; border: 1.5px solid var(--hairline); border-radius: 12px; background: var(--card); display: flex; flex-direction: column; gap: 8px;">
                        <span class="eyebrow" style="margin-bottom: 2px;">ORDER SUMMARY</span>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13px; color: var(--muted);">Monthly Total:</span>
                            <span style="font-size: 13px; font-weight: 600; color: var(--navy); font-variant-numeric: tabular-nums;">₹{q_res.monthly_subtotal:,}/mo</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13px; color: var(--muted);">One-Time Setup:</span>
                            <span style="font-size: 13px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums;">₹{q_res.one_time_subtotal:,}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 13px; color: var(--muted);">First Month:</span>
                            <span style="font-size: 13px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums;">₹{q_res.first_month_payable:,}</span>
                        </div>
                    </div>
                    """
                )

        render_html(
            """
            <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--hairline);">
                <span class="eyebrow">INTELLIGENCE & DIAGNOSTICS</span>
            </div>
            """
        )

        def _on_ai_mode_toggle_change():
            if st.session_state.get("ai_mode_toggle", False):
                if "gemini_health_cached" not in st.session_state:
                    from engine.advisor import check_gemini_health
                    is_healthy = check_gemini_health(timeout_seconds=4.0)
                    st.session_state["gemini_health_cached"] = is_healthy
                else:
                    is_healthy = st.session_state["gemini_health_cached"]

                if not is_healthy:
                    st.session_state["ai_mode_toggle"] = False
                    st.session_state["gemini_unavailable_note"] = "Gemini unavailable, using rules mode"
                else:
                    st.session_state.pop("gemini_unavailable_note", None)
            else:
                st.session_state.pop("gemini_unavailable_note", None)

        st.toggle("AI mode (Gemini)", key="ai_mode_toggle", on_change=_on_ai_mode_toggle_change)
        if st.session_state.get("gemini_unavailable_note"):
            st.caption(f"⚠️ *{st.session_state['gemini_unavailable_note']}*")
        elif st.session_state.get("ai_mode_toggle", False):
            st.caption("Active: Gemini Flash extraction enabled")
        else:
            st.caption("Default: Rules mode (offline, instant)")

        # Check Tesseract OCR status
        import pytesseract
        tess_status_html = '<span class="badge-approved">Active</span>'
        try:
            v = pytesseract.get_tesseract_version()
        except Exception:
            tess_status_html = '<span class="badge-rejected">Not Configured</span>'

        render_html(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 8px;">
                <span style="font-size: 13px; font-weight: 500; color: var(--ink);">Tesseract OCR</span>
                {tess_status_html}
            </div>
            """
        )

        # Check Gemini API status
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key and gemini_key.strip():
            llm_badge = '<span class="badge-approved">Configured</span>'
        else:
            llm_badge = '<span class="badge-review">Rule-Based</span>'

        render_html(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <span style="font-size: 13px; font-weight: 500; color: var(--ink);">LLM Engine</span>
                {llm_badge}
            </div>
            """
        )

        render_html(
            """
            <div style="font-size: 11px; color: var(--muted); line-height: 1.5; margin-top: 14px;">
                Statutory Reference Date: <b>2026-07-15</b><br/>
                Editorial Bordered Grid Architecture
            </div>
            """
        )

        return nav_view


def render_home_view():
    """Render the editorial landing page with Hero, Service Panels, Checklist, and Stat Block."""
    render_hero_section()

    col_btn, _ = st.columns([0.35, 0.65])
    with col_btn:
        if st.button("Start now ↗", width="stretch", key="home_cta_start"):
            st.session_state["requested_view"] = "Customer Journey"
            st.session_state["requested_step"] = 1
            st.rerun()

    render_html("<br/>")
    render_service_panels()
    render_clear_strip()
    render_checklist_block()
    render_stat_block()


def render_kyc_verification_desk():
    """Operational verification desk for compliance officers to view specimen applicant audits."""
    render_html(
        """
        <div style="margin-bottom: 20px;">
            <span class="eyebrow">COMPLIANCE & AUDIT</span>
            <h2>KYC Verification Desk</h2>
            <p style="font-size: 15px; color: var(--muted);">
                Operational audit console to inspect multi-pass OCR extraction, registry cross-checks, and review logs across specimen applicants K01 through K12.
            </p>
        </div>
        """
    )

    docs_report_path = "docs/kyc_results.md"
    if os.path.exists(docs_report_path):
        with open(docs_report_path, "r", encoding="utf-8") as f:
            content = f.read()
        st.markdown(content)
    else:
        st.warning("docs/kyc_results.md not found. Run scripts/generate_kyc_report.py to generate.")


def main():
    apply_custom_styles()
    init_session()

    # Apply any pending view or step requests before widgets are created
    if "requested_view" in st.session_state:
        req = st.session_state.pop("requested_view")
        for opt in ["Home", "Customer Journey", "KYC Verification Desk", "Sales Analytics"]:
            if opt.lower() in req.lower() or req.lower() in opt.lower():
                st.session_state["nav_view_selector"] = opt
                break
        else:
            st.session_state["nav_view_selector"] = req

    if "journey_step_num" in st.session_state:
        st.session_state["current_step"] = st.session_state.pop("journey_step_num")
    if "requested_step" in st.session_state:
        st.session_state["current_step"] = st.session_state.pop("requested_step")

    raw_nav = render_sidebar()
    active_nav_str = "home"
    if "journey" in raw_nav.lower():
        active_nav_str = "journey"
    elif "kyc" in raw_nav.lower():
        active_nav_str = "kyc"
    elif "analytic" in raw_nav.lower():
        active_nav_str = "analytics"

    render_top_header(active_nav=active_nav_str)

    if active_nav_str == "home":
        render_home_view()
    elif active_nav_str == "journey":
        render_stepper(st.session_state.current_step)
        if st.session_state.current_step == 1:
            render_step_advisor()
        elif st.session_state.current_step == 2:
            render_step_quote()
        elif st.session_state.current_step == 3:
            render_step_kyc()
        elif st.session_state.current_step == 4:
            render_step_checkout()
        elif st.session_state.current_step == 5:
            render_step_track()
    elif active_nav_str == "kyc":
        render_kyc_verification_desk()
    elif active_nav_str == "analytics":
        render_sales_analytics()

    render_editorial_footer()


if __name__ == "__main__":
    main()
