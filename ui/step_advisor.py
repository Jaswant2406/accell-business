"""
Step 1: AI Business Advisor.
Collects customer requirements via natural chat / structured controls,
extracts profile attributes via Gemini (or deterministic fallback),
runs the eligibility rules engine, and displays personalized recommendations.
Editorial bordered grid styling, zero emojis.
"""

import streamlit as st
import pandas as pd
from engine.advisor import (
    build_business_profile_from_advisor,
    deterministic_advisor_fallback,
    evaluate_slot_filling,
    extract_profile_multilingual_fallback,
    extract_profile_with_llm,
    SUPPORTED_LANGUAGES,
    EMPLOYEES_MIN,
    EMPLOYEES_MAX,
    SITES_MIN,
    SITES_MAX,
    BUDGET_MIN,
    BUDGET_MAX,
)
from engine.eligibility import recommend_products
from kyc.registry import get_city_tier, get_city_tier_info
from ui.html import render_html
from ui.styles import SVG_ICONS


def render_step_advisor():
    render_html(
        """
        <div style="margin-bottom: 24px;">
            <span class="eyebrow">STEP 01 / PROFILING & ADVISORY</span>
            <h2>AI Business Advisor</h2>
            <p style="font-size: 15px; color: var(--muted); margin: 0;">
                Tell us about your operational footprint, headcount, and technology requirements.
                Our rules engine validates eligibility across 25 catalogue products and curates a personalized package.
            </p>
        </div>
        """
    )

    # Initialize default state if needed
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

    # Input Mode Selection
    mode_options = ["Conversational AI Advisor", "Direct Structured Profiler"]
    if st.session_state.get("advisor_mode_selector") not in mode_options:
        st.session_state["advisor_mode_selector"] = "Conversational AI Advisor"
    mode = st.radio(
        "Advisor Input Mode:",
        mode_options,
        key="advisor_mode_selector",
        horizontal=True,
    )

    col_left, col_right = st.columns([1.1, 0.9])

    with col_left:
        render_html(
            """
            <div style="margin-bottom: 12px;">
                <span class="eyebrow">BUSINESS PROFILE & REQUIREMENTS</span>
            </div>
            """
        )

        val_notes = st.session_state.advisor_input.get("validation_notes", [])
        if val_notes:
            for v_note in val_notes:
                st.info(f"ℹ️ {v_note}")

        if mode == "Conversational AI Advisor":
            col_in_hdr, col_lang = st.columns([0.62, 0.38])
            with col_in_hdr:
                st.caption("Input accepted in English, Hindi (हिंदी), or Tamil (தமிழ்).")
            with col_lang:
                if st.session_state.get("sb_advisor_language") not in SUPPORTED_LANGUAGES:
                    st.session_state["sb_advisor_language"] = st.session_state.get("advisor_language", "English")
                if st.session_state.get("sb_advisor_language") not in SUPPORTED_LANGUAGES:
                    st.session_state["sb_advisor_language"] = "English"
                selected_lang = st.selectbox(
                    "Language / भाषा / மொழி:",
                    SUPPORTED_LANGUAGES,
                    key="sb_advisor_language",
                )
                st.session_state["advisor_language"] = selected_lang

            chat_input = st.text_area(
                "Describe your business, team size, locations, and technology needs:",
                value=st.session_state.advisor_input.get("chat_text", ""),
                height=130,
                placeholder="E.g., We are an auto components factory in Pune with 30 employees across 1 plant. We have GSTIN 27QHJXK0658U1ZL and need a 100 Mbps dedicated leased line and factory CCTV.",
            )

            ai_mode_enabled = bool(st.session_state.get("ai_mode_toggle", False))

            c_btn, c_info = st.columns([0.45, 0.55])
            with c_btn:
                run_ai = st.button("Analyze with AI ↗", width="stretch")
            with c_info:
                if not ai_mode_enabled:
                    st.caption("Mode: **Rules Mode** (AI toggle is OFF)")
                elif not st.session_state.advisor_input.get("is_llm", False):
                    st.caption("Mode: **Running in rules mode** (deterministic engine)")
                    if st.session_state.get("gemini_fallback_note"):
                        st.caption(f"*{st.session_state['gemini_fallback_note']}*")
                else:
                    st.caption("Mode: **AI Powered** (Gemini Flash active)")

            if run_ai and chat_input.strip():
                if ai_mode_enabled:
                    with st.spinner("Asking Gemini..."):
                        llm_data = extract_profile_with_llm(chat_input, target_language=selected_lang)
                        if not llm_data:
                            llm_data = extract_profile_multilingual_fallback(chat_input, language=selected_lang)
                            st.session_state["gemini_fallback_note"] = "Gemini was slow, so rules mode answered"
                            st.info("Gemini was slow, so rules mode answered")
                        else:
                            st.session_state.pop("gemini_fallback_note", None)
                            st.success("Requirements parsed successfully.")
                else:
                    # Straight to rules mode with no spinner delay
                    llm_data = extract_profile_multilingual_fallback(chat_input, language=selected_lang)
                    st.session_state.pop("gemini_fallback_note", None)
                    st.success("Requirements parsed instantly via rules engine.")

                st.session_state["raw_extracted_profile"] = llm_data
                city_extracted = llm_data.get("city", "Mumbai")
                if city_extracted == "Unknown":
                    city_extracted = "Mumbai"

                cur_emp = int(llm_data.get("employees", 1))
                clamped_emp = max(EMPLOYEES_MIN, min(EMPLOYEES_MAX, cur_emp))

                cur_sites = int(llm_data.get("sites", 1))
                clamped_sites = max(SITES_MIN, min(SITES_MAX, cur_sites))

                st.session_state.advisor_input.update({
                    "business_type": llm_data.get("business_type", "Retail/Kirana"),
                    "employees": clamped_emp,
                    "sites": clamped_sites,
                    "city": city_extracted,
                    "current_broadband": llm_data.get("current_broadband", "None"),
                    "has_gstin": bool(llm_data.get("has_gstin", True)),
                    "gstin": llm_data.get("gstin"),
                    "digital_needs": llm_data.get("digital_needs", []),
                    "chat_text": chat_input,
                    "explanation": llm_data.get("explanation"),
                    "is_llm": llm_data.get("is_llm", False),
                    "mode_note": llm_data.get("mode_note", "Running in rules mode"),
                    "budget": llm_data.get("budget"),
                    "validation_notes": llm_data.get("validation_notes", []),
                })
                if llm_data.get("budget") is not None:
                    clamped_b = max(BUDGET_MIN, min(BUDGET_MAX, int(llm_data["budget"])))
                    st.session_state["last_budget_entered"] = clamped_b
                    st.session_state["input_budget_ceiling"] = clamped_b

                # Sync need_* checkbox keys in session_state
                for k in ["cloud_storage", "surveillance_cctv", "voice_lines", "dedicated_ip", "fleet_tracking", "conference_room", "cybersecurity"]:
                    st.session_state[f"need_{k}"] = k in llm_data.get("digital_needs", [])
                st.rerun()

            # Slot Filling & Ambiguity Confirmation
            raw_prof = st.session_state.get("raw_extracted_profile")
            if raw_prof:
                slot_info = evaluate_slot_filling(raw_prof, language=selected_lang)
                if not slot_info["is_complete"]:
                    if slot_info.get("confirmation_prompt"):
                        render_html(
                            f"""
                            <div class="bordered-card-subtle" style="margin-top: 12px; padding: 14px 18px; border-left: 3px solid var(--warning-border);">
                                <div style="font-weight: 600; font-size: 13px; color: var(--warning-text); margin-bottom: 4px;">Ambiguous Value Confirmation:</div>
                                <div style="font-size: 13px; color: var(--ink);">{slot_info['confirmation_prompt']}</div>
                            </div>
                            """
                        )
                        c_conf_in, c_conf_btn = st.columns([0.7, 0.3])
                        with c_conf_in:
                            conf_val = st.text_input("Confirm Headcount / Value:", key="input_confirm_val")
                        with c_conf_btn:
                            if st.button("Confirm ↗", key="btn_confirm_slot", width="stretch"):
                                if conf_val.strip():
                                    if slot_info["ambiguous_slot"] == "employees":
                                        try:
                                            parsed_e = int(conf_val.replace(',', ''))
                                            clamped_e = max(EMPLOYEES_MIN, min(EMPLOYEES_MAX, parsed_e))
                                            st.session_state.advisor_input["employees"] = clamped_e
                                            raw_prof["employees"] = clamped_e
                                        except (ValueError, TypeError):
                                            pass
                                        raw_prof["is_ambiguous_employees"] = False
                                    elif slot_info["ambiguous_slot"] == "city":
                                        st.session_state.advisor_input["city"] = conf_val.strip()
                                        raw_prof["is_ambiguous_city"] = False
                                    st.rerun()
                    elif slot_info.get("next_question"):
                        render_html(
                            f"""
                            <div class="bordered-card-subtle" style="margin-top: 12px; padding: 14px 18px; border-left: 3px solid var(--navy);">
                                <div style="font-weight: 600; font-size: 13px; color: var(--navy); margin-bottom: 4px;">Advisor Follow-Up Question:</div>
                                <div style="font-size: 14px; color: var(--ink); font-weight: 500;">{slot_info['next_question']}</div>
                            </div>
                            """
                        )
                        c_ans_in, c_ans_btn = st.columns([0.75, 0.25])
                        with c_ans_in:
                            ans_val = st.text_input("Your Answer:", key="input_slot_ans")
                        with c_ans_btn:
                            if st.button("Submit ↗", key="btn_submit_slot", width="stretch"):
                                if ans_val.strip():
                                    slot_key = slot_info["next_missing_slot"]
                                    if slot_key == "employees":
                                        try:
                                            parsed_e = int(ans_val.replace(',', ''))
                                            clamped_e = max(EMPLOYEES_MIN, min(EMPLOYEES_MAX, parsed_e))
                                            st.session_state.advisor_input["employees"] = clamped_e
                                            raw_prof["employees"] = clamped_e
                                            raw_prof["employees_missing"] = False
                                        except (ValueError, TypeError):
                                            pass
                                    elif slot_key == "sites":
                                        try:
                                            parsed_s = int(ans_val.replace(',', ''))
                                            clamped_s = max(SITES_MIN, min(SITES_MAX, parsed_s))
                                            st.session_state.advisor_input["sites"] = clamped_s
                                            raw_prof["sites"] = clamped_s
                                            raw_prof["sites_missing"] = False
                                        except (ValueError, TypeError):
                                            pass
                                    elif slot_key == "city":
                                        st.session_state.advisor_input["city"] = ans_val.strip()
                                        raw_prof["city"] = ans_val.strip()
                                    elif slot_key == "has_gstin":
                                        has_g = any(y in ans_val.lower() for y in ["yes", "haan", "ha", "ஆம்", "true"])
                                        st.session_state.advisor_input["has_gstin"] = has_g
                                        raw_prof["gstin_missing"] = False
                                        raw_prof["has_gstin"] = has_g
                                    elif slot_key == "business_type":
                                        st.session_state.advisor_input["business_type"] = ans_val.strip()
                                        raw_prof["business_type"] = ans_val.strip()
                                    st.rerun()

        # Structured controls (always visible and editable to refine)
        with st.expander("Review and Adjust Profile Details", expanded=(mode == "Direct Structured Profiler")):
            c1, c2 = st.columns(2)
            with c1:
                b_name = st.text_input("Enterprise Name:", value=st.session_state.advisor_input.get("business_name", ""))
                b_options = [
                    "Healthcare/Clinic", "Retail/Kirana", "Restaurant/Food", "Manufacturing",
                    "Professional Services", "IT/Tech", "Salon/Beauty", "Logistics/Transport", "Other"
                ]
                cur_btype = st.session_state.advisor_input.get("business_type")
                if cur_btype not in b_options:
                    cur_btype = "Other" if cur_btype else "Healthcare/Clinic"
                    st.session_state.advisor_input["business_type"] = cur_btype
                b_type = st.selectbox(
                    "Business Sector:",
                    b_options,
                    index=b_options.index(cur_btype),
                )

                cur_emp = int(st.session_state.advisor_input.get("employees", 5))
                clamped_emp = max(EMPLOYEES_MIN, min(EMPLOYEES_MAX, cur_emp))
                if clamped_emp != cur_emp:
                    st.session_state.advisor_input["employees"] = clamped_emp

                cur_sites = int(st.session_state.advisor_input.get("sites", 1))
                clamped_sites = max(SITES_MIN, min(SITES_MAX, cur_sites))
                if clamped_sites != cur_sites:
                    st.session_state.advisor_input["sites"] = clamped_sites

                emp = st.number_input(
                    "Number of Employees / Staff:",
                    min_value=EMPLOYEES_MIN,
                    max_value=EMPLOYEES_MAX,
                    value=clamped_emp,
                )
                sites = st.number_input(
                    "Number of Operational Sites:",
                    min_value=SITES_MIN,
                    max_value=SITES_MAX,
                    value=clamped_sites,
                )

            with c2:
                city = st.text_input("Primary City:", value=st.session_state.advisor_input.get("city", "Bengaluru"))
                tier, is_known = get_city_tier_info(city)
                if not is_known and city and city.strip():
                    st.warning("We couldn't confirm your city tier, assuming Tier 2.")
                else:
                    st.caption(f"Location Classification: **Tier {tier} City** (derived from SMB registry)")

                bb_options = ["None", "Basic DSL/Cable", "Fiber", "Mobile Hotspot", "Leased Line"]
                cur_bb = st.session_state.advisor_input.get("current_broadband")
                if cur_bb not in bb_options:
                    cur_bb = "None"
                    st.session_state.advisor_input["current_broadband"] = cur_bb
                curr_bb = st.selectbox(
                    "Current Internet Connection:",
                    bb_options,
                    index=bb_options.index(cur_bb),
                )
                has_gst = st.checkbox("Business has GSTIN", value=bool(st.session_state.advisor_input.get("has_gstin", True)))
                gst_num = st.text_input("GSTIN (15 characters):", value=st.session_state.advisor_input.get("gstin", "") or "") if has_gst else ""
                if has_gst and (not gst_num or not gst_num.strip()):
                    st.info("Please provide your 15-character GSTIN before GSTIN-exclusive products can be activated (the number will be verified at KYC).")

            st.markdown("**Digital & Cloud Solutions Required:**")
            d_options = {
                "cloud_storage": "Cloud Backup & Storage",
                "surveillance_cctv": "Surveillance / CCTV Security",
                "voice_lines": "Fixed Business Voice Lines",
                "dedicated_ip": "Static / Dedicated IP",
                "fleet_tracking": "Vehicle / Fleet Tracking",
                "conference_room": "Smart Meeting / Video Conf",
                "cybersecurity": "Managed Antivirus & DNS Security",
            }
            selected_needs = []
            curr_needs = st.session_state.advisor_input.get("digital_needs", [])
            cols_d = st.columns(3)
            for i, (k, label) in enumerate(d_options.items()):
                col_box = cols_d[i % 3]
                need_key = f"need_{k}"
                if need_key not in st.session_state:
                    st.session_state[need_key] = k in curr_needs
                if col_box.checkbox(label, key=need_key):
                    selected_needs.append(k)

            # Update session state with refined values
            st.session_state.advisor_input.update({
                "business_name": b_name,
                "business_type": b_type,
                "employees": emp,
                "sites": sites,
                "city": city,
                "current_broadband": curr_bb,
                "has_gstin": has_gst,
                "gstin": gst_num if has_gst else None,
                "digital_needs": selected_needs,
            })

    # Run deterministic rules engine
    prof_dict = deterministic_advisor_fallback(
        business_type=st.session_state.advisor_input["business_type"],
        employees=st.session_state.advisor_input["employees"],
        sites=st.session_state.advisor_input["sites"],
        city=st.session_state.advisor_input["city"],
        has_gstin=st.session_state.advisor_input["has_gstin"],
        gstin=st.session_state.advisor_input["gstin"],
        current_broadband=st.session_state.advisor_input["current_broadband"],
        digital_needs=st.session_state.advisor_input["digital_needs"],
        budget=st.session_state.advisor_input.get("budget"),
    )
    prof_dict["business_name"] = st.session_state.advisor_input.get("business_name", "")
    prof_dict["budget"] = st.session_state.advisor_input.get("budget")
    business_profile = build_business_profile_from_advisor(prof_dict)

    # Store profile in session
    st.session_state.business_profile = business_profile

    # Execute eligibility engine
    rec_engine_result = recommend_products(business_profile)
    recommended_items = rec_engine_result["recommended"]
    catalogue_status = rec_engine_result["catalogue_status"]

    with col_right:
        is_llm = st.session_state.advisor_input.get("is_llm", False)
        fallback_note = st.session_state.get("gemini_fallback_note")
        mode_badge = (
            '<span class="badge-approved" style="font-size: 11px; padding: 2px 8px;">AI Powered (Gemini)</span>'
            if is_llm
            else '<span class="badge-review" style="font-size: 11px; padding: 2px 8px;">Running in rules mode</span>'
        )
        fallback_html = ""
        if fallback_note and not is_llm:
            fallback_html = f'<div style="font-size: 12px; color: var(--muted); font-style: italic; margin-top: 4px;">{fallback_note}</div>'

        render_html(
            f"""
            <div style="margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="eyebrow">CURATED RECOMMENDATION</span>
                    {mode_badge}
                </div>
                {fallback_html}
            </div>
            """
        )

        # Display rationale banner
        rationale_text = st.session_state.advisor_input.get("explanation") or prof_dict["explanation"]
        render_html(
            f"""
            <div class="bordered-card-subtle" style="border-left: 4px solid var(--navy); margin-bottom: 16px;">
                <div style="font-weight: 600; font-size: 13px; color: var(--navy); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">
                    Strategic Rationale
                </div>
                <div style="font-size: 14px; color: var(--ink); line-height: 1.5;">
                    {rationale_text}
                </div>
            </div>
            """
        )

        if rec_engine_result.get("city_tier_disclosure"):
            st.info(rec_engine_result["city_tier_disclosure"])
        if rec_engine_result.get("gstin_disclosure"):
            st.warning(rec_engine_result["gstin_disclosure"])
        if rec_engine_result.get("static_ip_disclosure"):
            st.info(rec_engine_result["static_ip_disclosure"])

        # Summary of recommended items
        st.markdown(f"**{len(recommended_items)} Products Pre-Selected for Your Profile:**")

        total_monthly_est = 0
        total_setup_est = 0

        for it in recommended_items:
            total_monthly_est += it["price_min"] * it["quantity"]
            total_setup_est += it["one_time_setup"] * it["quantity"]

            render_html(
                f"""
                <div class="bordered-card-subtle" style="margin-bottom: 10px; padding: 14px 18px;">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <span style="font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 15px; color: var(--ink);">{it['product_name']}</span>
                        <span style="font-family: 'Inter', sans-serif; font-weight: 600; font-size: 16px; color: var(--navy); font-variant-numeric: tabular-nums;">
                            ₹{it['price_min']:,} <span style="font-size: 12px; color: var(--muted); font-weight: 400;">/mo</span>
                        </span>
                    </div>
                    <div style="font-size: 13px; color: var(--muted); margin-top: 4px;">
                        Category: <b style="color: var(--ink);">{it['category']}</b> • Qty: <b style="color: var(--ink);">{it['quantity']} {it['unit']}</b> (Setup: ₹{it['one_time_setup']:,})
                    </div>
                    <div style="font-size: 12px; color: var(--navy); margin-top: 6px; display: flex; align-items: center; gap: 6px;">
                        {SVG_ICONS['check']} <span>{it['reason']} ({it.get('assumption', '')})</span>
                    </div>
                </div>
                """
            )

        render_html(
            f"""
            <div class="bordered-card" style="padding: 18px 24px; margin-top: 16px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); font-weight: 600;">Estimated Monthly</span><br/>
                    <span style="font-family: 'Inter', sans-serif; font-size: 26px; font-weight: 600; color: var(--navy); font-variant-numeric: tabular-nums;">₹{total_monthly_est:,}</span>
                    <span style="font-size: 13px; color: var(--muted);">/month</span>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); font-weight: 600;">One-Time Setup</span><br/>
                    <span style="font-family: 'Inter', sans-serif; font-size: 20px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums;">₹{total_setup_est:,}</span>
                </div>
            </div>
            """
        )

        render_html("<br/>")
        if st.button("Proceed to Quote Configuration ↗", width="stretch"):
            st.session_state.selected_items = recommended_items
            st.session_state.current_step = 2
            st.rerun()

    # Alternative connectivity & optional add-ons expandable sections
    alternatives = rec_engine_result.get("alternatives", [])
    optional_addons = rec_engine_result.get("optional_addons", [])

    if alternatives:
        with st.expander(f"View Alternative Connectivity Plans ({len(alternatives)} plans)"):
            st.caption("Other eligible primary connectivity plans (not added to your bundle total):")
            alt_rows = []
            for alt in alternatives:
                alt_rows.append({
                    "Product Code": alt["product_id"],
                    "Product Name": alt["product_name"],
                    "Category": alt["category"],
                    "Price": f"₹{alt['price_min']:,} /mo",
                    "Details": alt["reason"],
                })
            st.dataframe(pd.DataFrame(alt_rows), width="stretch", hide_index=True)

    if optional_addons:
        with st.expander(f"View Optional Business Add-ons ({len(optional_addons)} services)"):
            st.caption("Eligible solutions matching your business tier available as add-ons (not in bundle total):")
            addon_rows = []
            for add in optional_addons:
                addon_rows.append({
                    "Product Code": add["product_id"],
                    "Product Name": add["product_name"],
                    "Category": add["category"],
                    "Price": f"₹{add['price_min']:,} /mo",
                    "Unit": add["unit"],
                    "Details": add["reason"],
                })
            st.dataframe(pd.DataFrame(addon_rows), width="stretch", hide_index=True)

    # Ineligible products expandable section
    render_html("<br/>")
    with st.expander(f"View Ineligible Catalogue Products ({len(catalogue_status) - len(recommended_items)} items)"):
        st.caption("Transparent multi-criteria reasons explaining why certain products were filtered out for this profile:")
        inel_rows = []
        for pid, info in catalogue_status.items():
            if not info["eligible"]:
                inel_rows.append({
                    "Product Code": pid,
                    "Product Name": info["product_name"],
                    "Category": info["category"],
                    "Starting Price": f"₹{info['price_min']:,}",
                    "Exact Ineligibility Reason": info["reason"],
                    "What would unlock this": info.get("unlock_requirement", "N/A"),
                })
        if inel_rows:
            st.dataframe(pd.DataFrame(inel_rows), width="stretch", hide_index=True)
        else:
            st.write("All catalogue items meet eligibility criteria.")
