"""
Step 4: Mock Checkout & Order Confirmation.
Displays order summary, customer contact collection, simulated mandate payment,
generates unique Order ID, and persists to local JSON store.
Editorial bordered grid styling, zero emojis.
"""

import streamlit as st
from engine.orders import create_new_order_record
from ui.styles import status_badge, SVG_ICONS
from ui.html import render_html


def render_step_checkout():
    render_html(
        """
        <div style="margin-bottom: 24px;">
            <span class="eyebrow">STEP 04 / SERVICE AUTHORIZATION</span>
            <h2>Checkout & Digital Mandate</h2>
            <p style="font-size: 15px; color: var(--muted); margin: 0;">
                Review your corporate subscription details, authorize the recurring digital mandate,
                and generate your official Accel Business service activation order.
            </p>
        </div>
        """
    )

    quote = st.session_state.get("current_quote")
    if not quote:
        st.warning("No quote found in session. Please start from the Quote stage.")
        if st.button("Go to Quote"):
            st.session_state.current_step = 2
            st.rerun()
        return

    profile = st.session_state.get("business_profile")
    kyc_res = st.session_state.get("kyc_result")
    kyc_decision = kyc_res.decision if kyc_res else "PENDING"

    col_details, col_order = st.columns([1.1, 0.9])

    with col_details:
        render_html(
            """
            <div style="margin-bottom: 12px;">
                <span class="eyebrow">SUBSCRIBER & MANDATE DETAILS</span>
            </div>
            """
        )

        c1, c2 = st.columns(2)
        with c1:
            comp_name = st.text_input(
                "Company / Legal Enterprise Name:",
                value=profile.business_name if (profile and profile.business_name) else "Harmony Dental Care",
            )
            contact_person = st.text_input("Authorized Signatory Name:", value="Joseph Shah")
        with c2:
            phone = st.text_input("Registered Mobile Number:", value="+91 98765 43210")
            email = st.text_input("Official Billing Email:", value="admin@harmonydental.in")

        city = profile.city if profile else "Bengaluru"
        st.caption(f"Service Installation City: **{city}**")

        render_html("<br/>")
        render_html(
            """
            <div style="margin-bottom: 12px;">
                <span class="eyebrow">RECURRING AUTO-DEBIT MECHANISM</span>
            </div>
            """
        )
        pay_methods = [
            "Corporate NetBanking (e-NACH Recurring Mandate)",
            "UPI AutoPay (Business Mandate up to ₹1,00,000)",
            "Corporate Credit Card / Standing Instruction",
        ]
        if st.session_state.get("checkout_pay_method") not in pay_methods:
            st.session_state["checkout_pay_method"] = pay_methods[0]

        pay_method = st.radio(
            "Select Auto-Debit Mandate Mechanism:",
            pay_methods,
            key="checkout_pay_method",
        )

        render_html(
            f"""
            <div class="bordered-card-subtle" style="margin-top: 14px; margin-bottom: 16px;">
                <div style="font-weight: 600; font-size: 13px; color: var(--navy); margin-bottom: 4px;">
                    Zero-Cost Mandate Registration Notice
                </div>
                <div style="font-size: 13px; color: var(--muted); line-height: 1.5;">
                    No immediate deduction occurs today. First month invoice (₹{quote['first_month_payable']:,})
                    will be processed strictly upon successful physical fiber termination & SLA handshake.
                </div>
            </div>
            """
        )

        if "cb_auth_mandate" not in st.session_state:
            st.session_state["cb_auth_mandate"] = True
        auth_cb = st.checkbox(
            "I hereby authorize Accel Business Ltd to initiate monthly recurring debit for the contracted enterprise services.",
            key="cb_auth_mandate",
        )

    with col_order:
        render_html(
            """
            <div style="margin-bottom: 12px;">
                <span class="eyebrow">ORDER SUMMARY</span>
            </div>
            """
        )

        badge_html = status_badge(kyc_decision)

        render_html(
            f"""
            <div class="bordered-card" style="padding: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <span style="font-family: 'Manrope', sans-serif; font-size: 16px; font-weight: 600; color: var(--ink);">Compliance Status</span>
                    {badge_html}
                </div>

                <div class="hairline-divider"></div>

                <div style="margin-bottom: 12px;">
                    <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); font-weight: 600;">Included Products</div>
                    <div style="font-size: 14px; font-weight: 500; color: var(--ink); margin-top: 4px;">
                        {', '.join([it['product_name'] for it in quote['items']])}
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 14px; color: var(--muted);">Monthly Subscription:</span>
                    <span style="font-weight: 600; color: var(--navy); font-variant-numeric: tabular-nums;">₹{quote['monthly_subtotal']:,} /mo</span>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <span style="font-size: 14px; color: var(--muted);">One-Time Setup:</span>
                    <span style="font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums;">₹{quote['one_time_subtotal']:,}</span>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <span style="font-size: 14px; color: var(--muted);">Contract Commitment:</span>
                    <span style="font-weight: 600; color: var(--ink);">{quote['contract_months']} Months</span>
                </div>

                <div class="bordered-card-subtle" style="padding: 14px; margin-top: 12px;">
                    <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); font-weight: 600;">First-Month Total Authorized:</div>
                    <div style="font-family: 'Inter', sans-serif; font-size: 24px; font-weight: 600; color: var(--ink); font-variant-numeric: tabular-nums; margin-top: 2px;">₹{quote['first_month_payable']:,}</div>
                    <div style="font-size: 11px; color: var(--muted); margin-top: 2px;">Activation SLA: Within {quote['max_install_days']} business days</div>
                </div>
            </div>
            """
        )

        render_html("<br/>")
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("Back to KYC", width="stretch"):
                st.session_state.current_step = 3
                st.rerun()
        with col_b2:
            confirm_btn = st.button("Confirm Order ↗", width="stretch", disabled=not auth_cb)

        if confirm_btn:
            with st.spinner("Processing digital mandate and securing order reservation..."):
                kyc_dict = {
                    "decision": kyc_decision,
                    "reasons": kyc_res.summary_reasons if kyc_res else [],
                }
                new_order = create_new_order_record(
                    company_name=comp_name,
                    contact_person=contact_person,
                    phone=phone,
                    email=email,
                    city=city,
                    quote_data=quote,
                    kyc_result_data=kyc_dict,
                    payment_method=pay_method,
                )
                st.session_state.last_order_id = new_order["order_id"]
                st.session_state.current_step = 5
                st.success(f"Order {new_order['order_id']} placed successfully.")
                st.rerun()
