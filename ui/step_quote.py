"""
Step 2: Quote & Customization.
Allows the customer to review, add, remove, and adjust quantities for their bundle.
Prices strictly come from product_catalogue.csv.
Dynamically re-evaluates dependency graph and minimum contract duration.
Editorial bordered grid styling, zero emojis.
"""

import streamlit as st
import pandas as pd
from engine.pricing import (
    calculate_quote,
    remove_product_with_dependency_check,
    validate_quote_dependencies,
)
from engine.budget_fit import fit_bundle_to_budget
from kyc.registry import load_catalogue
from ui.styles import SVG_ICONS
from ui.html import render_html


def render_step_quote():
    render_html(
        """
        <div style="margin-bottom: 24px;">
            <span class="eyebrow">STEP 02 / BUNDLE CONFIGURATION</span>
            <h2>Solution Quote & Customization</h2>
            <p style="font-size: 15px; color: var(--muted); margin: 0;">
                Fine-tune your customized business bundle. You can adjust quantities, add complementary
                services, or select your preferred contract commitment. All pricing strictly references the official catalogue.
            </p>
        </div>
        """
    )

    if "selected_items" not in st.session_state or not st.session_state.selected_items:
        st.warning("No products selected yet. Returning to Advisor...")
        if st.button("Back to Advisor"):
            st.session_state.current_step = 1
            st.rerun()
        return

    df_cat = load_catalogue().set_index("product_id")
    selected_items = st.session_state.selected_items

    # 1. Dependency Validation Check
    is_valid_dep, dep_issues = validate_quote_dependencies([it["product_id"] for it in selected_items])
    if not is_valid_dep:
        for iss in dep_issues:
            st.error(f"Dependency Constraint: {iss}")

    col_main, col_summary = st.columns([1.25, 0.75])

    with col_main:
        # Fit My Budget section
        with st.expander("Fit My Budget: Algorithmic Optimization", expanded=False):
            st.markdown(
                "Enter your target monthly ceiling. Our optimizer selects the highest-utility combination "
                "of base connectivity and digital add-ons that fits your budget, strictly respecting catalogue rules and dependencies."
            )
            c_bg1, c_bg2 = st.columns([0.65, 0.35])
            with c_bg1:
                last_b = st.session_state.get("last_budget_entered", 3000)
                cur_b = st.session_state.get("input_budget_ceiling", last_b)
                try:
                    cur_b = int(cur_b)
                except (TypeError, ValueError):
                    cur_b = 3000
                clamped_b = max(0, min(1000000, cur_b))
                st.session_state["input_budget_ceiling"] = clamped_b
                st.session_state["last_budget_entered"] = clamped_b

                user_budget = st.number_input(
                    "Monthly Budget Ceiling (₹/month):",
                    min_value=0,
                    max_value=1000000,
                    step=500,
                    key="input_budget_ceiling",
                )
            with c_bg2:
                st.write("")
                btn_fit = st.button("Optimize Bundle ↗", key="btn_run_budget_fit", width="stretch")

            if btn_fit:
                profile = st.session_state.get("business_profile")
                if profile:
                    fit_res = fit_bundle_to_budget(profile, monthly_budget=int(user_budget))
                    if fit_res.selected_items:
                        st.session_state.selected_items = fit_res.selected_items
                        st.session_state.last_budget_entered = user_budget
                        st.session_state.budget_fit_result = fit_res.to_dict()
                        st.success(fit_res.explanation)
                        st.rerun()
                    else:
                        st.error(fit_res.explanation)
                else:
                    st.warning("Profile not initialized. Please complete Step 1 first.")

            if "budget_fit_result" in st.session_state and st.session_state.budget_fit_result:
                bfr = st.session_state.budget_fit_result
                st.markdown(
                    f"**Allocation:** ₹{bfr['total_monthly_cost']:,}/mo utilized out of ₹{bfr['monthly_budget']:,}/mo "
                    f"(Surplus: ₹{bfr['remaining_budget']:,}/mo)"
                )
                if bfr.get("dropped_items"):
                    st.markdown("**Products Excluded to Respect Budget:**")
                    for d in bfr["dropped_items"][:5]:
                        st.caption(f"• **{d['product_name']}** (₹{d['monthly_cost']:,}/mo): {d['reason']}")

        render_html(
            """
            <div style="margin-top: 20px; margin-bottom: 12px;">
                <span class="eyebrow">SELECTED BUNDLE LINE ITEMS</span>
            </div>
            """
        )

        # Pre-clamp session state quantities for all selected items
        for item in selected_items:
            pid = item["product_id"]
            qty_key = f"qty_{pid}"
            raw_qty = st.session_state.get(qty_key, item.get("quantity", 1))
            try:
                q_val = int(raw_qty)
            except (TypeError, ValueError):
                q_val = 1
            clamped_qty = max(1, min(10000, q_val))
            st.session_state[qty_key] = clamped_qty
            item["quantity"] = clamped_qty

        # Display each line item as a Single Card with visible quantity stepper and remove button
        items_to_remove = []
        for idx, item in enumerate(selected_items):
            pid = item["product_id"]
            if pid not in df_cat.index:
                continue
            cat_row = df_cat.loc[pid]
            item_qty = item.get("quantity", 1)
            monthly_line = int(cat_row["price_min_inr_per_month"]) * item_qty
            setup_unit = int(cat_row["one_time_setup_inr"])
            setup_line = setup_unit * item_qty

            # Requirement tags only when they apply
            req_tags = []
            if str(cat_row["requires_gstin"]).strip().upper() == "Y":
                req_tags.append('<span class="status-badge" style="background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; font-size: 11px; padding: 2px 8px; border-radius: 9999px; font-weight: 600;">GSTIN Required</span>')
            if int(cat_row["min_employees"]) > 1:
                req_tags.append(f'<span class="status-badge" style="background: var(--page); color: var(--navy); border: 1px solid var(--hairline); font-size: 11px; padding: 2px 8px; border-radius: 9999px; font-weight: 600;">Min {int(cat_row["min_employees"])} Employees</span>')
            if int(cat_row["min_sites"]) > 1:
                req_tags.append(f'<span class="status-badge" style="background: var(--page); color: var(--navy); border: 1px solid var(--hairline); font-size: 11px; padding: 2px 8px; border-radius: 9999px; font-weight: 600;">Min {int(cat_row["min_sites"])} Sites</span>')
            tags_html = " ".join(req_tags)

            setup_detail = f"₹{setup_line:,}"
            if setup_unit > 0:
                setup_detail += f" <span style=\"font-size: 11px;\">(₹{setup_unit:,} × {item_qty})</span>"

            with st.container(border=True):
                render_html(
                    f"""
                    <div class="quote-item-card" style="display: flex; flex-direction: column; gap: 10px; width: 100%;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px;">
                            <div style="min-width: 0;">
                                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                                    <span style="font-family: 'Manrope', system-ui, sans-serif; font-weight: 700; font-size: 18px; line-height: 1.25; color: var(--ink);">{cat_row['product_name']}</span>
                                    <span style="font-family: 'Inter', sans-serif; font-size: 11px; background: var(--page); border: 1px solid var(--hairline); color: var(--navy); padding: 2px 8px; border-radius: 4px; font-weight: 600;">{pid}</span>
                                    <span style="font-family: 'Inter', sans-serif; font-size: 11px; color: var(--muted); background: var(--page); padding: 2px 8px; border-radius: 4px;">{cat_row['category']}</span>
                                </div>
                                <div style="font-size: 14px; line-height: 24.5px; color: var(--muted); margin-top: 6px; overflow-wrap: anywhere; word-break: break-word;">{cat_row['description']}</div>
                            </div>
                            <div style="text-align: right; flex-shrink: 0;">
                                <div style="font-family: 'Inter', sans-serif; font-weight: 600; font-size: 20px; color: var(--navy); font-variant-numeric: tabular-nums;">₹{monthly_line:,}<span style="font-size: 13px; font-weight: 400; color: var(--muted);">/mo</span></div>
                                <div style="font-size: 12px; color: var(--muted); margin-top: 2px; font-variant-numeric: tabular-nums;">₹{int(cat_row['price_min_inr_per_month']):,} × {item_qty} {cat_row['unit']}</div>
                            </div>
                        </div>
                        <div class="hairline-divider" style="margin: 2px 0;"></div>
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; font-size: 13px; color: var(--muted);">
                            <div>Commitment: <b style="color: var(--ink); font-variant-numeric: tabular-nums;">{cat_row['min_contract_months']} Months min</b></div>
                            <div>Typical Install: <b style="color: var(--ink); font-variant-numeric: tabular-nums;">{cat_row['typical_install_days']} Business Days</b></div>
                            <div>One-Time Setup: <b style="color: var(--ink); font-variant-numeric: tabular-nums;">{setup_detail}</b></div>
                            {f'<div>{tags_html}</div>' if tags_html else ''}
                        </div>
                    </div>
                    """
                )

                # Direct Controls on Card: Quantity Stepper & Remove Button
                c_q, c_del = st.columns([0.65, 0.35])
                with c_q:
                    new_qty = st.number_input(
                        f"Quantity ({cat_row['unit']}):",
                        min_value=1,
                        max_value=10000,
                        value=item_qty,
                        key=f"qty_{pid}",
                    )
                    if new_qty != item_qty:
                        item["quantity"] = new_qty
                        st.rerun()
                with c_del:
                    render_html('<div style="font-size: 13px; font-weight: 500; color: transparent; user-select: none; margin-bottom: 4px;">Action</div>')
                    if st.button("Remove Item", key=f"del_{pid}", width="stretch", help=f"Remove {cat_row['product_name']} from quote"):
                        items_to_remove.append(pid)

        # Handle removals
        if items_to_remove:
            for r_pid in items_to_remove:
                st.session_state.pop(f"qty_{r_pid}", None)
                rem_items, rem_warns = remove_product_with_dependency_check(
                    st.session_state.selected_items, r_pid
                )
                st.session_state.selected_items = rem_items
                for w in rem_warns:
                    st.warning(f"Dependency note: {w}")
            st.rerun()

        render_html("<br/>")
        # Add Product Section
        with st.expander("Add Complementary Product from Catalogue"):
            curr_pids = {it["product_id"] for it in selected_items}
            addable_pids = [pid for pid in df_cat.index if pid not in curr_pids]

            if addable_pids:
                choice = st.selectbox(
                    "Choose product to add:",
                    addable_pids,
                    format_func=lambda x: f"{x} - {df_cat.loc[x]['product_name']} (₹{df_cat.loc[x]['price_min_inr_per_month']:,}/mo)",
                )
                if st.button("Add to Quote ↗", key="btn_add_prod"):
                    crow = df_cat.loc[choice]
                    st.session_state.selected_items.append({
                        "product_id": choice,
                        "product_name": crow["product_name"],
                        "category": crow["category"],
                        "quantity": 1,
                        "price_min": int(crow["price_min_inr_per_month"]),
                        "price_max": int(crow["price_max_inr_per_month"]),
                        "one_time_setup": int(crow["one_time_setup_inr"]),
                        "unit": crow["unit"],
                        "reason": "Manually added by customer",
                        "assumption": "Added to customized bundle",
                    })
                    st.rerun()
            else:
                st.write("All catalogue products are currently included.")

    # Calculate Official Quote
    min_req_months = max([int(df_cat.loc[it["product_id"]]["min_contract_months"]) for it in st.session_state.selected_items], default=1)

    with col_summary:
        render_html(
            """
            <div style="margin-bottom: 12px;">
                <span class="eyebrow">OFFICIAL QUOTE SUMMARY</span>
            </div>
            """
        )

        # Contract commitment selector
        contract_options = [m for m in [1, 3, 6, 12, 24, 36] if m >= min_req_months]
        if not contract_options:
            contract_options = [min_req_months]

        default_idx = contract_options.index(12) if 12 in contract_options else 0
        default_idx = max(0, min(len(contract_options) - 1, default_idx))
        selected_contract = st.selectbox(
            "Contract Commitment Term:",
            contract_options,
            index=default_idx,
            format_func=lambda x: f"{x} Months commitment",
        )

        quote = calculate_quote(st.session_state.selected_items, contract_months=selected_contract)
        st.session_state.current_quote = quote.to_dict()

        # Display Summary Card: Single Self-Contained HTML Block
        render_html(
            f"""
            <div class="bordered-card" style="display: flex; flex-direction: column; gap: 12px; box-sizing: border-box; padding: 24px; border: 1.5px solid var(--ink); border-radius: 16px; background: var(--card);">
                <div>
                    <span style="font-family: 'Inter', system-ui, sans-serif; font-size: 12px; text-transform: uppercase; letter-spacing: 0.14em; color: var(--navy); font-weight: 600;">Monthly Recurring Total</span><br/>
                    <div style="font-family: 'Inter', system-ui, sans-serif; font-size: 32px; font-weight: 600; color: var(--navy); font-variant-numeric: tabular-nums; margin-top: 4px;">
                        ₹{quote.monthly_subtotal:,}
                        <span style="font-size: 14px; font-weight: 400; color: var(--muted);">/mo + taxes</span>
                    </div>
                </div>

                <div class="hairline-divider" style="margin: 4px 0;"></div>

                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 14px; color: var(--muted);">One-Time Setup Total:</span>
                    <span style="font-family: 'Inter', system-ui, sans-serif; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums;">₹{quote.one_time_subtotal:,}</span>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 14px; color: var(--muted);">Contract Duration:</span>
                    <span style="font-family: 'Inter', system-ui, sans-serif; font-weight: 600; color: var(--ink);">{quote.contract_months} Months</span>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 14px; color: var(--muted);">Max Installation Turnaround:</span>
                    <span style="font-family: 'Inter', system-ui, sans-serif; font-weight: 600; color: var(--navy);">{quote.max_install_days} Business Days</span>
                </div>

                <div class="bordered-card-subtle" style="padding: 16px; margin-top: 6px; border-radius: 12px; background: var(--page); border: 1px solid var(--hairline); display: flex; flex-direction: column; gap: 4px;">
                    <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); font-weight: 600;">First-Month Total Payable:</div>
                    <div style="font-family: 'Inter', system-ui, sans-serif; font-size: 22px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums;">₹{quote.first_month_payable:,}</div>
                    <div style="font-size: 12px; color: var(--muted);">Includes 1st month subscription + 100% one-time setup fees</div>
                </div>
            </div>
            """
        )

        if quote.warnings:
            for w in quote.warnings:
                st.warning(f"Note: {w}")

        render_html("<br/>")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Back to Advisor", width="stretch"):
                st.session_state.current_step = 1
                st.rerun()
        with col_b2:
            if st.button("Accept & Proceed to KYC ↗", width="stretch", disabled=not is_valid_dep):
                st.session_state.current_step = 3
                st.rerun()
