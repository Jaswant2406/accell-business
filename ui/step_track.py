"""
Step 5: Order Activation Tracker.
Tracks enterprise activation lifecycle along the timeline state machine:
Order Placed -> Smart KYC -> Site Survey -> Hardware Installation -> Service Live.
Allows milestone simulation with strict KYC block enforcement.
Editorial bordered grid styling, zero emojis.
"""

import streamlit as st
from engine.orders import advance_order_status, get_order, load_all_orders
from ui.styles import status_badge, SVG_ICONS
from ui.html import render_html


def render_step_track():
    render_html(
        """
        <div style="margin-bottom: 24px;">
            <span class="eyebrow">STEP 05 / PROVISIONING TELEMETRY</span>
            <h2>Order Activation & Service Tracker</h2>
            <p style="font-size: 15px; color: var(--muted); margin: 0;">
                Track the real-time fulfillment of your enterprise digital circuits.
                View engineer site dispatch, fiber termination milestones, and SLA activation status.
            </p>
        </div>
        """
    )

    all_orders = load_all_orders()
    order_ids = list(all_orders.keys())

    # Order ID selector or lookup
    col_sel, col_stat = st.columns([0.65, 0.35])
    with col_sel:
        default_order = st.session_state.get("last_order_id")
        if default_order and default_order in order_ids:
            def_idx = order_ids.index(default_order)
        else:
            def_idx = len(order_ids) - 1 if order_ids else 0
        def_idx = max(0, min(len(order_ids) - 1, def_idx)) if order_ids else 0

        if order_ids:
            active_oid = st.selectbox(
                "Select / Search Order Reference ID:",
                order_ids,
                index=def_idx,
            )
        else:
            st.info("No orders placed yet. Complete steps 1-4 to create your first order.")
            if st.button("Start New Journey"):
                st.session_state.current_step = 1
                st.rerun()
            return

    order = get_order(active_oid)
    if not order:
        st.error("Order record not found.")
        return

    with col_stat:
        st.write("")
        curr_status = order.get("status", "PLACED")
        if curr_status == "ACTIVATED":
            badge_markup = '<span class="badge-approved" style="font-size: 13px; padding: 6px 16px;">Service Live</span>'
        elif curr_status == "INSTALLATION_SCHEDULED":
            badge_markup = '<span class="badge-review" style="font-size: 13px; padding: 6px 16px;">Installation In Progress</span>'
        elif curr_status == "SURVEY_SCHEDULED":
            badge_markup = '<span class="badge-review" style="font-size: 13px; padding: 6px 16px;">Site Survey Scheduled</span>'
        else:
            badge_markup = '<span class="badge-neutral" style="font-size: 13px; padding: 6px 16px;">Order Reserved</span>'

        render_html(f'<div style="text-align: right;">{badge_markup}</div>')

    # Order overview card
    render_html(
        f"""
        <div class="bordered-card" style="padding: 24px; margin-top: 14px; margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
                <div>
                    <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); font-weight: 600;">Subscriber Organization</span><br/>
                    <span style="font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 18px; color: var(--ink);">{order.get('company_name')}</span>
                    <div style="font-size: 13px; color: var(--muted); margin-top: 4px;">Contact: {order.get('contact_person')} ({order.get('phone')})</div>
                </div>
                <div>
                    <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); font-weight: 600;">Location & City</span><br/>
                    <span style="font-family: 'Manrope', sans-serif; font-weight: 600; font-size: 18px; color: var(--ink);">{order.get('city')}</span>
                    <div style="font-size: 13px; color: var(--muted); margin-top: 4px;">Payment: {order.get('payment_method').split('(')[0]}</div>
                </div>
                <div>
                    <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: var(--muted); font-weight: 600;">Target Activation SLA</span><br/>
                    <span style="font-family: 'Inter', sans-serif; font-weight: 600; font-size: 18px; color: var(--navy); font-variant-numeric: tabular-nums;">{order.get('target_activation_date')}</span>
                    <div style="font-size: 13px; color: var(--success-text); margin-top: 4px;">Lead time: {order.get('quote', {}).get('max_install_days')} days</div>
                </div>
            </div>
        </div>
        """
    )

    # State Machine Visual Timeline: Single Self-Contained HTML Block
    render_html(
        """
        <div style="margin-bottom: 14px;">
            <span class="eyebrow">AUTONOMOUS FULFILLMENT TIMELINE</span>
        </div>
        """
    )
    timeline = order.get("timeline", [])
    timeline_steps_html = []

    for idx, event in enumerate(timeline):
        ev_status = event.get("status", "PENDING")
        if ev_status == "COMPLETED":
            dot_color = "var(--navy)"
            dot_text = SVG_ICONS["check"]
            card_bg = "var(--card)"
            border_color = "var(--ink)"
        elif ev_status in ["IN_PROGRESS", "UNDER_REVIEW"]:
            dot_color = "var(--warning-text)"
            dot_text = str(idx + 1)
            card_bg = "var(--warning-bg)"
            border_color = "var(--warning-border)"
        elif ev_status == "REJECTED":
            dot_color = "var(--error-text)"
            dot_text = "!"
            card_bg = "var(--error-bg)"
            border_color = "var(--error-border)"
        else:
            dot_color = "var(--hairline)"
            dot_text = str(idx + 1)
            card_bg = "var(--card)"
            border_color = "var(--hairline)"

        connector = '<div style="width: 1.5px; height: 28px; background: var(--hairline); margin: 4px 0;"></div>' if idx < len(timeline) - 1 else ''

        timeline_steps_html.append(
            f"""
            <div style="display: flex; gap: 16px; align-items: flex-start;">
                <div style="display: flex; flex-direction: column; align-items: center; width: 32px; flex-shrink: 0;">
                    <div style="width: 32px; height: 32px; border-radius: 50%; background: {dot_color}; color: #FFFFFF; display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 13px;">
                        {dot_text}
                    </div>
                    {connector}
                </div>
                <div style="flex: 1; background: {card_bg}; border: 1.5px solid {border_color}; border-radius: 12px; padding: 14px 18px; display: flex; flex-direction: column; gap: 4px; min-width: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-family: 'Manrope', system-ui, sans-serif; font-weight: 700; color: var(--ink); font-size: 15px;">{event.get('step')}</span>
                        <span style="font-family: 'Inter', system-ui, sans-serif; font-size: 12px; color: var(--muted); font-variant-numeric: tabular-nums;">{event.get('date')}</span>
                    </div>
                    <div style="font-size: 13px; line-height: 1.5; color: var(--muted);">
                        {event.get('notes')}
                    </div>
                </div>
            </div>
            """
        )

    render_html(
        f"""
        <div class="bordered-card" style="padding: 24px; margin-bottom: 24px; display: flex; flex-direction: column; gap: 8px;">
            {''.join(timeline_steps_html)}
        </div>
        """
    )

    # Progression Simulation Controls
    render_html("<br/>")
    render_html(
        """
        <div style="margin-bottom: 10px;">
            <span class="eyebrow">DEMO LIFECYCLE SIMULATOR</span>
            <p style="font-size: 13px; color: var(--muted); margin: 0;">
                Advance order milestones to demonstrate fulfillment telemetry without waiting for physical field dispatch.
            </p>
        </div>
        """
    )

    c_sim, c_new, c_json = st.columns([0.4, 0.3, 0.3])
    with c_sim:
        if st.button("Advance to Next Milestone ↗", width="stretch"):
            ok, msg, updated_order = advance_order_status(active_oid)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(f"Fulfillment Blocked: {msg}")

    with c_new:
        if st.button("New Customer Journey", width="stretch"):
            st.session_state.current_step = 1
            st.session_state.selected_items = []
            st.session_state.current_quote = None
            st.session_state.kyc_result = None
            st.session_state.active_order_id = None
            st.session_state.kyc_verified = False
            st.rerun()

    with c_json:
        with st.popover("View Order JSON"):
            st.json(order)
