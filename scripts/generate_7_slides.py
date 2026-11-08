"""
Generate 7-Slide Competition Presentation for YTL Hackathon 2026 - Enterprise Track A.
Project: Udyam Digital (Accel Business).
Produces:
- Udyam_Digital_Final_7_Slides.pptx
- Udyam_Digital_Final_7_Slides.pdf
And renders each slide to PNG for visual inspection.
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# Color Palette Constants
COLOR_NAVY = RGBColor(30, 58, 138)        # #1E3A8A Primary / Headers
COLOR_INK = RGBColor(15, 23, 42)          # #0F172A Headings / Bold text
COLOR_BODY = RGBColor(51, 65, 85)         # #334155 Body text
COLOR_SLATE = RGBColor(100, 116, 139)     # #64748B Secondary / Subtitles
COLOR_CARD_BG = RGBColor(255, 255, 255)   # #FFFFFF Card background
COLOR_BORDER = RGBColor(226, 232, 240)    # #E2E8F0 Subtle border
COLOR_BORDER_STRONG = RGBColor(203, 213, 225) # #CBD5E1
COLOR_RED = RGBColor(220, 38, 38)         # #DC2626 Critical drop / Warning
COLOR_LIGHT_BG = RGBColor(248, 250, 252)  # #F8FAFC Table alt row
COLOR_BLUE_BG = RGBColor(239, 246, 255)   # #EFF6FF Highlight card bg

# Status Pill Colors
PILL_COLORS = {
    "implemented": (RGBColor(236, 253, 245), RGBColor(167, 243, 208), RGBColor(6, 95, 70)),   # Green
    "simulated":   (RGBColor(254, 243, 199), RGBColor(253, 230, 138), RGBColor(146, 64, 14)), # Amber
    "planned":     (RGBColor(238, 242, 255), RGBColor(199, 210, 254), RGBColor(55, 48, 163)), # Purple
    "accent":      (RGBColor(239, 246, 255), RGBColor(147, 197, 253), RGBColor(30, 58, 138)), # Blue
    "alert":       (RGBColor(254, 242, 242), RGBColor(254, 202, 202), RGBColor(220, 38, 38)), # Red
}

TEMPLATE_BG = os.path.abspath("d:/airtel/assets/slide_bg_template.jpg")


def set_slide_background(slide):
    """Sets the official hackathon background template image."""
    slide.shapes.add_picture(TEMPLATE_BG, Inches(0), Inches(0), Inches(10.0), Inches(5.625))


def add_header(slide, eyebrow, headline, subtitle=None):
    """Adds the standard header block for a slide."""
    # Eyebrow
    tb_eye = slide.shapes.add_textbox(Inches(0.65), Inches(0.82), Inches(8.70), Inches(0.20))
    tf_eye = tb_eye.text_frame
    tf_eye.word_wrap = True
    tf_eye.margin_left = tf_eye.margin_right = tf_eye.margin_top = tf_eye.margin_bottom = 0
    p_eye = tf_eye.paragraphs[0]
    p_eye.text = eyebrow.upper()
    p_eye.font.name = "Arial"
    p_eye.font.size = Pt(8.5)
    p_eye.font.bold = True
    p_eye.font.color.rgb = COLOR_NAVY

    # Headline
    tb_head = slide.shapes.add_textbox(Inches(0.65), Inches(1.02), Inches(8.70), Inches(0.34))
    tf_head = tb_head.text_frame
    tf_head.word_wrap = True
    tf_head.margin_left = tf_head.margin_right = tf_head.margin_top = tf_head.margin_bottom = 0
    p_head = tf_head.paragraphs[0]
    p_head.text = headline
    p_head.font.name = "Arial"
    p_head.font.size = Pt(15)
    p_head.font.bold = True
    p_head.font.color.rgb = COLOR_INK

    # Subtitle
    if subtitle:
        tb_sub = slide.shapes.add_textbox(Inches(0.65), Inches(1.36), Inches(8.70), Inches(0.18))
        tf_sub = tb_sub.text_frame
        tf_sub.word_wrap = True
        tf_sub.margin_left = tf_sub.margin_right = tf_sub.margin_top = tf_sub.margin_bottom = 0
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = subtitle
        p_sub.font.name = "Arial"
        p_sub.font.size = Pt(8.0)
        p_sub.font.color.rgb = COLOR_SLATE


def add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER):
    """Draws a neat card container with optional border."""
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_color
    if border_color:
        shape.line.color.rgb = border_color
        shape.line.width = Pt(0.75)
    else:
        shape.line.fill.background()
    return shape


def add_pill(slide, left, top, width, height, text, pill_type="implemented"):
    """Adds a small rounded/clean pill badge."""
    bg_col, border_col, text_col = PILL_COLORS.get(pill_type, PILL_COLORS["accent"])
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = bg_col
    shape.line.color.rgb = border_col
    shape.line.width = Pt(0.75)
    tf = shape.text_frame
    tf.word_wrap = False
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.04)
    tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = PP_ALIGN.CENTER
    p.font.name = "Arial"
    p.font.size = Pt(6.5)
    p.font.bold = True
    p.font.color.rgb = text_col
    return shape


def add_table(slide, left, top, width, height, headers, rows, col_widths, col_align=None, font_size=7.5, pad_y=0.03):
    """Generates a professional data table."""
    num_rows = len(rows) + 1
    num_cols = len(headers)
    table_shape = slide.shapes.add_table(num_rows, num_cols, left, top, width, height)
    table = table_shape.table

    for i, w in enumerate(col_widths):
        table.columns[i].width = w

    # Header Row
    for col_idx, h_text in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_NAVY
        tf = cell.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = Inches(0.05)
        tf.margin_top = tf.margin_bottom = Inches(pad_y)
        p = tf.paragraphs[0]
        p.text = h_text
        p.font.name = "Arial"
        p.font.size = Pt(font_size + 0.3)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        if col_align and col_idx < len(col_align):
            p.alignment = col_align[col_idx]

    # Data Rows
    for row_idx, row_data in enumerate(rows):
        bg = COLOR_LIGHT_BG if (row_idx % 2 == 1) else COLOR_CARD_BG
        for col_idx, val in enumerate(row_data):
            cell = table.cell(row_idx + 1, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = bg
            tf = cell.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.margin_left = tf.margin_right = Inches(0.05)
            tf.margin_top = tf.margin_bottom = Inches(pad_y)
            p = tf.paragraphs[0]
            p.text = str(val)
            p.font.name = "Arial"
            p.font.size = Pt(font_size)
            p.font.color.rgb = COLOR_INK if col_idx == 0 else COLOR_BODY
            if col_idx == 0:
                p.font.bold = True
            if col_align and col_idx < len(col_align):
                p.alignment = col_align[col_idx]

    return table_shape


# ==========================================
# SLIDE BUILDERS
# ==========================================

def build_slide_1(prs):
    """Slide 1: Executive Pitch"""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)

    add_header(
        slide,
        eyebrow="YTL HACKATHON 2026 · ENTERPRISE TRACK A · ACCEL BUSINESS",
        headline="Udyam Digital: Making small businesses go digital in one sitting.",
        subtitle="Autonomous MSME onboarding & service assembly platform for Indian small businesses."
    )

    # Left Column: Strategic Pitch & Proposition
    left_x = Inches(0.65)
    col_w = Inches(4.75)

    # 1. Challenge & Solution Card
    add_card(slide, left_x, Inches(1.55), col_w, Inches(1.50))
    tb = slide.shapes.add_textbox(left_x + Inches(0.12), Inches(1.60), col_w - Inches(0.24), Inches(1.40))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

    p1 = tf.paragraphs[0]
    p1.text = "THE BUSINESS CHALLENGE"
    p1.font.name = "Arial"
    p1.font.size = Pt(8.0)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_RED

    p2 = tf.add_paragraph()
    p2.text = "India's 63M+ MSMEs face a fragmented, slow, multi-vendor onboarding barrier—averaging 17.6 days and 3 status-chase calls per customer across disconnected sales visits and paper KYC."
    p2.font.name = "Arial"
    p2.font.size = Pt(7.8)
    p2.font.color.rgb = COLOR_BODY
    p2.space_after = Pt(6)

    p3 = tf.add_paragraph()
    p3.text = "THE PROPOSED SOLUTION"
    p3.font.name = "Arial"
    p3.font.size = Pt(8.0)
    p3.font.bold = True
    p3.font.color.rgb = COLOR_NAVY

    p4 = tf.add_paragraph()
    p4.text = "A unified, rules-first digital journey that discovers needs in vernacular languages, generates instant binding quotes, verifies KYC in-memory, and provides transparent order tracking—all in under 15 minutes."
    p4.font.name = "Arial"
    p4.font.size = Pt(7.8)
    p4.font.color.rgb = COLOR_BODY

    # 2. Target Customer & Value Proposition Card
    add_card(slide, left_x, Inches(3.15), col_w, Inches(1.15))
    tb2 = slide.shapes.add_textbox(left_x + Inches(0.12), Inches(3.20), col_w - Inches(0.24), Inches(1.05))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_right = tf2.margin_top = tf2.margin_bottom = 0

    p2_1 = tf2.paragraphs[0]
    p2_1.text = "TARGET CUSTOMER & VALUE PROPOSITION"
    p2_1.font.name = "Arial"
    p2_1.font.size = Pt(8.0)
    p2_1.font.bold = True
    p2_1.font.color.rgb = COLOR_INK

    p2_2 = tf2.add_paragraph()
    p2_2.text = "• Target Audience: Indian MSMEs (micro-retail, kiranas, CA offices, clinics, multi-site branches).\n• Core Proposition: Discover, configure, verify, and track business telecom & digital services through one continuous digital sitting—eliminating sales pitches, quotation lag, and paper friction."
    p2_2.font.name = "Arial"
    p2_2.font.size = Pt(7.8)
    p2_2.font.color.rgb = COLOR_BODY

    # 3. Badges Row
    badge_y = Inches(4.42)
    badge_w = Inches(1.12)
    badge_gap = Inches(0.09)
    badges = [
        ("15-MIN ONBOARDING", "accent"),
        ("ZERO PAPERWORK", "implemented"),
        ("RULES-DRIVEN PRICING", "accent"),
        ("DPDP 2023 ALIGNED", "implemented"),
    ]
    for idx, (b_txt, b_type) in enumerate(badges):
        add_pill(slide, left_x + idx * (badge_w + badge_gap), badge_y, badge_w, Inches(0.28), b_txt, b_type)

    # Right Column: Live Prototype Visual
    right_x = Inches(5.55)
    right_w = Inches(3.80)
    add_card(slide, right_x, Inches(1.55), right_w, Inches(3.15), bg_color=COLOR_CARD_BG, border_color=COLOR_BORDER)

    home_img = "d:/airtel/docs/screenshots/restyle_1440_desktop_home.png"
    if os.path.exists(home_img):
        slide.shapes.add_picture(home_img, right_x + Inches(0.10), Inches(1.65), right_w - Inches(0.20), Inches(2.35))

    tb_cap = slide.shapes.add_textbox(right_x + Inches(0.12), Inches(4.08), right_w - Inches(0.24), Inches(0.55))
    tf_cap = tb_cap.text_frame
    tf_cap.word_wrap = True
    tf_cap.margin_left = tf_cap.margin_right = tf_cap.margin_top = tf_cap.margin_bottom = 0
    p_cap1 = tf_cap.paragraphs[0]
    p_cap1.text = "LIVE WORKING STREAMLIT PROTOTYPE"
    p_cap1.font.name = "Arial"
    p_cap1.font.size = Pt(7.5)
    p_cap1.font.bold = True
    p_cap1.font.color.rgb = COLOR_NAVY

    p_cap2 = tf_cap.add_paragraph()
    p_cap2.text = "Interactive 4-stage onboarding: Advisor → Quote → Smart KYC → Live Tracking. Fully operational offline rules engine with 89 automated tests passing."
    p_cap2.font.name = "Arial"
    p_cap2.font.size = Pt(7.0)
    p_cap2.font.color.rgb = COLOR_SLATE


def build_slide_2(prs):
    """Slide 2: The Business Problem & Conversion Funnel"""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)

    add_header(
        slide,
        eyebrow="01 · THE PROBLEM & CONVERSION FUNNEL",
        headline="India's small businesses lose customers between recommendation and activation.",
        subtitle="Evidence from case-study synthetic dataset (smb_leads.csv, N=5,000 leads, Apr–Jun 2026). Figures illustrate operational leakage."
    )

    # Top Funnel Visualization
    funnel_y = Inches(1.55)
    stages = [
        ("1. Total Leads", "5,000", "100%", "Inbound leads", COLOR_NAVY),
        ("2. Contacted", "3,406", "68.1%", "Initial contact", COLOR_NAVY),
        ("3. Needs Assessed", "1,974", "58.0%", "Needs captured", COLOR_NAVY),
        ("4. Quote Accepted", "861", "43.6%", "STEEPEST DROP (-56%)", COLOR_RED),
        ("5. KYC Completed", "588", "68.3%", "Document checks", COLOR_NAVY),
        ("6. Activated", "368", "7.4%", "Final active SMBs", COLOR_NAVY),
    ]

    card_w = Inches(1.38)
    card_gap = Inches(0.08)
    start_x = Inches(0.65)

    for i, (stg_name, count, pct, note, col) in enumerate(stages):
        x = start_x + i * (card_w + card_gap)
        bg = COLOR_BLUE_BG if i == 5 else (COLOR_CARD_BG if i != 3 else RGBColor(254, 242, 242))
        bdr = COLOR_BORDER if i != 3 else RGBColor(254, 202, 202)
        add_card(slide, x, funnel_y, card_w, Inches(1.20), bg_color=bg, border_color=bdr)

        tb = slide.shapes.add_textbox(x + Inches(0.06), funnel_y + Inches(0.06), card_w - Inches(0.12), Inches(1.08))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p0 = tf.paragraphs[0]
        p0.text = stg_name
        p0.font.name = "Arial"
        p0.font.size = Pt(7.0)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_INK

        p1 = tf.add_paragraph()
        p1.text = count
        p1.font.name = "Arial"
        p1.font.size = Pt(13)
        p1.font.bold = True
        p1.font.color.rgb = col

        p2 = tf.add_paragraph()
        p2.text = f"{pct} of stage"
        p2.font.name = "Arial"
        p2.font.size = Pt(7.0)
        p2.font.bold = True
        p2.font.color.rgb = col

        p3 = tf.add_paragraph()
        p3.text = note
        p3.font.name = "Arial"
        p3.font.size = Pt(6.5)
        p3.font.color.rgb = COLOR_SLATE

    # Critical Bottleneck Callout Banner
    bot_y = Inches(2.83)
    add_card(slide, start_x, bot_y, Inches(8.70), Inches(0.40), bg_color=RGBColor(254, 242, 242), border_color=RGBColor(254, 202, 202))
    tb_bot = slide.shapes.add_textbox(start_x + Inches(0.12), bot_y + Inches(0.05), Inches(8.46), Inches(0.30))
    tf_bot = tb_bot.text_frame
    tf_bot.word_wrap = True
    tf_bot.margin_left = tf_bot.margin_right = tf_bot.margin_top = tf_bot.margin_bottom = 0
    p_bot = tf_bot.paragraphs[0]
    p_bot.text = "CRITICAL BOTTLENECK: 56.4% of qualified leads (1,113 businesses) abandon during the 3–5 day delay for manual PDF quotation with opaque product codes. Another 273 qualified quotes drop out during paper-heavy KYC."
    p_bot.font.name = "Arial"
    p_bot.font.size = Pt(7.2)
    p_bot.font.bold = True
    p_bot.font.color.rgb = COLOR_RED

    # Bottom 4 Key Impact Metric Cards
    met_y = Inches(3.32)
    met_h = Inches(1.40)
    met_w = Inches(2.11)
    met_gap = Inches(0.08)

    metrics = [
        ("7.4% CONVERSION", "Overall Lead-to-Activation", "Only 368 of 5,000 leads activate. 92.6% leakage occurs across disconnected sales visits and offline paperwork.", COLOR_RED),
        ("17.6 DAYS LAG", "Lead-to-Activation Cycle", "Average 17.6 days from contact to activation; causes 3 status-chase calls per customer to call centers.", COLOR_INK),
        ("₹15,000 CAC", "Cost per Activated SMB", "Multiple field visits and manual paperwork create high CAC, unviable for micro-SMBs paying ₹2,500/month.", COLOR_INK),
        ("9.6% vs 2.0%", "GSTIN Activation Disparity", "Leads with verifiable GSTIN convert 4.8× higher due to structured verification vs informal unverified shops.", COLOR_NAVY),
    ]

    for j, (num_hdr, lbl, desc, col) in enumerate(metrics):
        mx = start_x + j * (met_w + met_gap)
        add_card(slide, mx, met_y, met_w, met_h)

        tb_m = slide.shapes.add_textbox(mx + Inches(0.10), met_y + Inches(0.08), met_w - Inches(0.20), met_h - Inches(0.16))
        tf_m = tb_m.text_frame
        tf_m.word_wrap = True
        tf_m.margin_left = tf_m.margin_right = tf_m.margin_top = tf_m.margin_bottom = 0

        pm0 = tf_m.paragraphs[0]
        pm0.text = num_hdr
        pm0.font.name = "Arial"
        pm0.font.size = Pt(11)
        pm0.font.bold = True
        pm0.font.color.rgb = col

        pm1 = tf_m.add_paragraph()
        pm1.text = lbl
        pm1.font.name = "Arial"
        pm1.font.size = Pt(7.5)
        pm1.font.bold = True
        pm1.font.color.rgb = COLOR_INK
        pm1.space_after = Pt(3)

        pm2 = tf_m.add_paragraph()
        pm2.text = desc
        pm2.font.name = "Arial"
        pm2.font.size = Pt(7.0)
        pm2.font.color.rgb = COLOR_BODY


def build_slide_3(prs):
    """Slide 3: The Solution and Working Prototype"""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)

    add_header(
        slide,
        eyebrow="02 · THE SOLUTION & WORKING PROTOTYPE",
        headline="One digital journey replaces a fragmented onboarding process.",
        subtitle="Live Streamlit prototype combines discovery, dynamic quoting, smart KYC, and order tracking in one sitting."
    )

    # Before vs After Workflow Comparison Bar
    comp_y = Inches(1.52)
    add_card(slide, Inches(0.65), comp_y, Inches(8.70), Inches(0.48), bg_color=COLOR_BLUE_BG, border_color=RGBColor(147, 197, 253))
    tb_c = slide.shapes.add_textbox(Inches(0.75), comp_y + Inches(0.04), Inches(8.50), Inches(0.40))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    tf_c.margin_left = tf_c.margin_right = tf_c.margin_top = tf_c.margin_bottom = 0

    p_tr = tf_c.paragraphs[0]
    p_tr.text = "TRADITIONAL: Sales visit (3–5d) → Manual quote (2–4d) → Paper KYC (3–5d) → 3× Status calls → 17.6d Activation"
    p_tr.font.name = "Arial"
    p_tr.font.size = Pt(7.2)
    p_tr.font.color.rgb = COLOR_RED

    p_ud = tf_c.add_paragraph()
    p_ud.text = "UDYAM DIGITAL: Digital Advisor (3 min) → Instant Quote (1 min) → Digital Smart KYC (3 min) → Order Tracker (<7d Activation)"
    p_ud.font.name = "Arial"
    p_ud.font.size = Pt(7.2)
    p_ud.font.bold = True
    p_ud.font.color.rgb = COLOR_NAVY

    # 4 Customer Journey Cards with Real Screenshots
    cards_y = Inches(2.08)
    card_w = Inches(2.11)
    card_h = Inches(2.65)
    card_gap = Inches(0.08)
    start_x = Inches(0.65)

    stages = [
        (
            "1. ADVISOR",
            "d:/airtel/assets/slide_crops/crop_advisor.png",
            "Multilingual Needs Discovery",
            "• Natural conversation in EN, HI, TA\n• Sizing & operational inputs\n• Deterministic bundle recommendation\n• Replaces sales pitching"
        ),
        (
            "2. DYNAMIC QUOTE",
            "d:/airtel/assets/slide_crops/crop_quote.png",
            "Transparent Single Bill",
            "• Instant eligibility across 25 products\n• Interactive add-ons & setup fees\n• Fixed contract terms up front\n• Replaces 3-5 day PDF quotes"
        ),
        (
            "3. SMART KYC",
            "d:/airtel/assets/slide_crops/crop_kyc.png",
            "In-Memory Document Checks",
            "• Mandatory DPDP consent screen\n• Local Tesseract OCR (zero cloud upload)\n• GSTIN checksum & mock registry checks\n• Replaces paper document courier"
        ),
        (
            "4. ORDER TRACKER",
            "d:/airtel/assets/slide_crops/crop_track.png",
            "Self-Serve Transparency",
            "• 5-stage provisioning timeline\n• Dynamic expected activation dates\n• Live status reduces call-center chases\n• Replaces 3 status calls/customer"
        ),
    ]

    for k, (step_title, img_path, subtitle, bullet_text) in enumerate(stages):
        cx = start_x + k * (card_w + card_gap)
        add_card(slide, cx, cards_y, card_w, card_h)

        tb_sh = slide.shapes.add_textbox(cx + Inches(0.08), cards_y + Inches(0.06), card_w - Inches(0.16), Inches(0.20))
        tf_sh = tb_sh.text_frame
        tf_sh.word_wrap = True
        tf_sh.margin_left = tf_sh.margin_right = tf_sh.margin_top = tf_sh.margin_bottom = 0
        psh = tf_sh.paragraphs[0]
        psh.text = step_title
        psh.font.name = "Arial"
        psh.font.size = Pt(8.0)
        psh.font.bold = True
        psh.font.color.rgb = COLOR_NAVY

        if os.path.exists(img_path):
            slide.shapes.add_picture(img_path, cx + Inches(0.08), cards_y + Inches(0.28), card_w - Inches(0.16), Inches(1.10))

        tb_tx = slide.shapes.add_textbox(cx + Inches(0.08), cards_y + Inches(1.42), card_w - Inches(0.16), Inches(1.15))
        tf_tx = tb_tx.text_frame
        tf_tx.word_wrap = True
        tf_tx.margin_left = tf_tx.margin_right = tf_tx.margin_top = tf_tx.margin_bottom = 0

        p_sub = tf_tx.paragraphs[0]
        p_sub.text = subtitle
        p_sub.font.name = "Arial"
        p_sub.font.size = Pt(7.2)
        p_sub.font.bold = True
        p_sub.font.color.rgb = COLOR_INK
        p_sub.space_after = Pt(2)

        p_bul = tf_tx.add_paragraph()
        p_bul.text = bullet_text
        p_bul.font.name = "Arial"
        p_bul.font.size = Pt(6.8)
        p_bul.font.color.rgb = COLOR_BODY


def build_slide_4(prs):
    """Slide 4: Solution Architecture and Technical Differentiation"""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)

    add_header(
        slide,
        eyebrow="03 · SOLUTION ARCHITECTURE & TECHNICAL DIFFERENTIATION",
        headline="Rules decide. AI assists. The application remains functional offline.",
        subtitle="Modular Python monolith with a deterministic core, local OCR, optional Gemini LLM, and in-memory verification."
    )

    left_x = Inches(0.65)
    col_w = Inches(4.65)

    # 3 Major Differentiator Cards (Stacked)
    diffs = [
        (
            "1. RULES-FIRST DECISION ARCHITECTURE",
            "CORE DIFFERENTIATOR",
            "implemented",
            "Eligibility, product dependencies, bundle ranking, and pricing are strictly controlled by deterministic Python business rules (engine/rules.py) over product_catalogue.csv (25 products). Zero LLM hallucinations of unfulfillable bundles, incorrect pricing, or invalid SLAs."
        ),
        (
            "2. HYBRID AI & RESILIENT OFFLINE FALLBACK",
            "RELIABILITY",
            "implemented",
            "Google Gemini API optionally assists conversational extraction (sidebar toggle default OFF). Operates over forced IPv4 (0.0.0.0), 10s strict timeout, 0 retries. If unavailable, the platform seamlessly falls back to offline multilingual regex/rule extraction with zero UI interruption."
        ),
        (
            "3. INTEGRATED CUSTOMER JOURNEY MONOLITH",
            "VELOCITY",
            "implemented",
            "Recommendation, quoting, KYC, and order tracking run in one continuous Streamlit session state machine. Replaces fragmented enterprise CRMs, quoting portals, and paper couriers with a unified, self-serve or partner-assisted digital experience."
        ),
    ]

    card_y = Inches(1.52)
    card_h = Inches(0.78)
    card_gap = Inches(0.08)

    for idx, (title, tag, ptype, desc) in enumerate(diffs):
        cy = card_y + idx * (card_h + card_gap)
        add_card(slide, left_x, cy, col_w, card_h)

        add_pill(slide, left_x + col_w - Inches(1.30), cy + Inches(0.06), Inches(1.20), Inches(0.18), tag, ptype)

        tb = slide.shapes.add_textbox(left_x + Inches(0.10), cy + Inches(0.06), col_w - Inches(1.45), card_h - Inches(0.10))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.name = "Arial"
        p0.font.size = Pt(7.5)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_NAVY

        p1 = tf.add_paragraph()
        p1.text = desc
        p1.font.name = "Arial"
        p1.font.size = Pt(6.8)
        p1.font.color.rgb = COLOR_BODY

    # Integration Boundaries & Simulated Components Card
    sim_y = Inches(4.08)
    add_card(slide, left_x, sim_y, col_w, Inches(0.68), bg_color=COLOR_BLUE_BG, border_color=RGBColor(147, 197, 253))
    tb_sim = slide.shapes.add_textbox(left_x + Inches(0.10), sim_y + Inches(0.06), col_w - Inches(0.20), Inches(0.56))
    tf_sim = tb_sim.text_frame
    tf_sim.word_wrap = True
    tf_sim.margin_left = tf_sim.margin_right = tf_sim.margin_top = tf_sim.margin_bottom = 0

    ps0 = tf_sim.paragraphs[0]
    ps0.text = "SYSTEM BOUNDARIES & VERIFIED IMPLEMENTATION STATUS"
    ps0.font.name = "Arial"
    ps0.font.size = Pt(7.2)
    ps0.font.bold = True
    ps0.font.color.rgb = COLOR_INK

    ps1 = tf_sim.add_paragraph()
    ps1.text = "• SIMULATED: GSTN/Udyam registries (mock CSVs + Luhn-mod-36 checksums), e-NACH mandate, telecom BSS.\n• IMPLEMENTED: Localhost Tesseract OCR, in-memory OpenCV decoding, JSON order persistence, 89 test suites."
    ps1.font.name = "Arial"
    ps1.font.size = Pt(6.6)
    ps1.font.color.rgb = COLOR_BODY

    # Right Column: Actual Architecture Diagram
    right_x = Inches(5.45)
    right_w = Inches(3.90)
    add_card(slide, right_x, Inches(1.52), right_w, Inches(3.24))

    arch_img = "d:/airtel/docs/solution_architecture.png"
    if os.path.exists(arch_img):
        slide.shapes.add_picture(arch_img, right_x + Inches(0.35), Inches(1.58), Inches(3.20), Inches(2.80))

    tb_acap = slide.shapes.add_textbox(right_x + Inches(0.10), Inches(4.44), right_w - Inches(0.20), Inches(0.28))
    tf_acap = tb_acap.text_frame
    tf_acap.word_wrap = True
    tf_acap.margin_left = tf_acap.margin_right = tf_acap.margin_top = tf_acap.margin_bottom = 0
    pac = tf_acap.paragraphs[0]
    pac.text = "Verified System Architecture: Streamlit Presentation → Deterministic Engine → Local Tesseract OCR → Optional Gemini IPv4 Transport → Order Persistence."
    pac.font.name = "Arial"
    pac.font.size = Pt(6.3)
    pac.font.color.rgb = COLOR_SLATE


def build_slide_5(prs):
    """Slide 5: Data Privacy, Security and Trust"""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)

    add_header(
        slide,
        eyebrow="04 · DATA PRIVACY, SECURITY & DPDP COMPLIANCE",
        headline="Trust is designed into the onboarding journey.",
        subtitle="Architectural alignment with DPDP Act, 2023 & draft DPDP Rules, 2025. (Internal technical evaluation; not formal legal certification)."
    )

    # 4 Structured Pillar Cards (2x2 Grid)
    grid_x1 = Inches(0.65)
    grid_x2 = Inches(5.05)
    col_w = Inches(4.30)
    row_y1 = Inches(1.55)
    row_y2 = Inches(3.15)
    row_h = Inches(1.50)

    pillars = [
        (
            grid_x1, row_y1,
            "1. PRIVACY BY DESIGN & PURPOSE LIMITATION",
            "IMPLEMENTED", "implemented",
            [
                ("Affirmative Statutory Consent:", "Mandatory consent gate before document submission; details purpose, data categories, and 30-day unactivated purge policy."),
                ("Strict Purpose Limitation:", "Data collected solely for Customer Due Diligence (CDD) under DoT guidelines; zero secondary marketing processing."),
                ("Designated Grievance Redressal:", "Statutory notice displays designated Grievance Officer contact (grievance-officer@accelbusiness.in)."),
            ]
        ),
        (
            grid_x2, row_y1,
            "2. SENSITIVE DATA & LOCAL OCR PROCESSING",
            "IMPLEMENTED", "implemented",
            [
                ("In-Memory Document Decode:", "Uploaded KYC files decoded via OpenCV (np.frombuffer → cv2.imdecode); documents are never written to disk or temp files."),
                ("Localhost Tesseract Execution:", "Character extraction runs entirely on localhost binary; zero document bytes or biometrics sent to cloud vision APIs."),
                ("UI & Audit Token Masking:", "mask_identifier() masks GSTIN, Udyam, and Aadhaar numbers to terminal 4 digits across all logs, views, and order states."),
            ]
        ),
        (
            grid_x1, row_y2,
            "3. APPLICATION SECURITY & GUARDRAILS",
            "IMPLEMENTED", "implemented",
            [
                ("Input Clamping (engine/guardrails.py):", "Strict bounds (employees 1–10k, sites 1–500, budget ≤ ₹10L) prevent buffer overflow and UI crashes."),
                ("File Upload Hardening:", "MIME-type whitelisting (.png, .jpg, .jpeg), 10MB limits, empty-file blocks, and byte-level OpenCV header verification."),
                ("Secret Hygiene & Telemetry Quarantine:", "Secrets isolated in .env and quarantined in .gitignore; Streamlit usage telemetry disabled (gatherUsageStats = false)."),
            ]
        ),
        (
            grid_x2, row_y2,
            "4. EXTERNAL BOUNDARIES & PLANNED ROADMAP",
            "SIMULATED | PLANNED", "simulated",
            [
                ("Gemini Data Boundary [IMPLEMENTED]:", "Transmits plain requirement text only over IPv4; zero documents, PII, or credentials sent to LLM."),
                ("Encryption at Rest [PLANNED]:", "data/orders.json currently stores plaintext JSON; field-level AES-256 encryption planned for production persistence."),
                ("RBAC & Gateways [PLANNED]:", "Role-based access control between subscriber and compliance audit desk; live GSTN/NPCI gateway integrations planned."),
            ]
        ),
    ]

    for gx, gy, title, ptxt, ptype, bullets in pillars:
        add_card(slide, gx, gy, col_w, row_h)

        add_pill(slide, gx + col_w - Inches(1.30), gy + Inches(0.08), Inches(1.22), Inches(0.20), ptxt, ptype)

        tb = slide.shapes.add_textbox(gx + Inches(0.10), gy + Inches(0.08), col_w - Inches(1.40), Inches(0.22))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        p0 = tf.paragraphs[0]
        p0.text = title
        p0.font.name = "Arial"
        p0.font.size = Pt(7.5)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_NAVY

        tb_b = slide.shapes.add_textbox(gx + Inches(0.10), gy + Inches(0.32), col_w - Inches(0.20), row_h - Inches(0.36))
        tf_b = tb_b.text_frame
        tf_b.word_wrap = True
        tf_b.margin_left = tf_b.margin_right = tf_b.margin_top = tf_b.margin_bottom = 0

        for b_idx, (b_hdr, b_desc) in enumerate(bullets):
            p = tf_b.paragraphs[0] if b_idx == 0 else tf_b.add_paragraph()
            p.text = f"• {b_hdr} "
            p.font.name = "Arial"
            p.font.size = Pt(6.8)
            p.font.bold = True
            p.font.color.rgb = COLOR_INK

            run = p.add_run()
            run.text = b_desc
            run.font.name = "Arial"
            run.font.size = Pt(6.8)
            run.font.bold = False
            run.font.color.rgb = COLOR_BODY
            p.space_after = Pt(2)


def build_slide_6(prs):
    """Slide 6: Business Model and Commercial Impact"""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)

    add_header(
        slide,
        eyebrow="05 · COMMERCIAL MODEL & UNIT ECONOMICS",
        headline="Lower acquisition friction. One bill. Recurring business value.",
        subtitle="Standardized bundles capture high-volume MSME segments while digital onboarding cuts acquisition cost by 40%."
    )

    left_x = Inches(0.65)
    left_w = Inches(3.90)

    # 1. Proposed Core Bundles (Left Column)
    bundles = [
        (
            "STARTER BUNDLE — ₹2,500 / month",
            "MICRO RETAIL & SERVICES (55% OF MSME BASE)",
            "• Kiranas, salons, standalone pharmacies, retail counters\n• Broadband for UPI/POS reliability + Business SIM\n• WhatsApp business channel + SMS updates\n• Single bill, one support helpline, modular toggleable add-ons\n• Replaces fragmented consumer SIMs and domestic broadband"
        ),
        (
            "OFFICE BUNDLE — ₹6,900 / month",
            "PROFESSIONAL OFFICES (25% OF MSME BASE)",
            "• CA firms, diagnostic clinics, coaching centres, agencies\n• High-uptime enterprise broadband with guaranteed SLA\n• Cloud corporate email & secure team storage\n• Basic cybersecurity endpoint protection\n• Consolidated monthly corporate invoice & dedicated account support"
        ),
    ]

    by = Inches(1.52)
    bh = Inches(1.42)
    bgap = Inches(0.10)

    for b_idx, (btitle, bsub, bbullets) in enumerate(bundles):
        cy = by + b_idx * (bh + bgap)
        add_card(slide, left_x, cy, left_w, bh)

        tb = slide.shapes.add_textbox(left_x + Inches(0.10), cy + Inches(0.08), left_w - Inches(0.20), bh - Inches(0.14))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0

        p0 = tf.paragraphs[0]
        p0.text = btitle
        p0.font.name = "Arial"
        p0.font.size = Pt(8.2)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_NAVY

        p1 = tf.add_paragraph()
        p1.text = bsub
        p1.font.name = "Arial"
        p1.font.size = Pt(6.8)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_SLATE
        p1.space_after = Pt(2)

        p2 = tf.add_paragraph()
        p2.text = bbullets
        p2.font.name = "Arial"
        p2.font.size = Pt(6.8)
        p2.font.color.rgb = COLOR_BODY

    # Note on catalogue rules
    tb_cnote = slide.shapes.add_textbox(left_x, Inches(4.56), left_w, Inches(0.20))
    tf_cnote = tb_cnote.text_frame
    tf_cnote.word_wrap = True
    tf_cnote.margin_left = tf_cnote.margin_right = tf_cnote.margin_top = tf_cnote.margin_bottom = 0
    pcn = tf_cnote.paragraphs[0]
    pcn.text = "Prices indicative based on product_catalogue.csv; deterministic rules set final price & contract."
    pcn.font.name = "Arial"
    pcn.font.size = Pt(6.5)
    pcn.font.italic = True
    pcn.font.color.rgb = COLOR_SLATE

    # Right Column: Acquisition Opportunity & Payback Table
    right_x = Inches(4.70)
    right_w = Inches(4.65)

    # CAC Comparison Banner
    add_card(slide, right_x, Inches(1.52), right_w, Inches(0.55), bg_color=COLOR_BLUE_BG, border_color=RGBColor(147, 197, 253))
    tb_cac = slide.shapes.add_textbox(right_x + Inches(0.12), Inches(1.55), right_w - Inches(0.24), Inches(0.48))
    tf_cac = tb_cac.text_frame
    tf_cac.word_wrap = True
    tf_cac.margin_left = tf_cac.margin_right = tf_cac.margin_top = tf_cac.margin_bottom = 0

    pc0 = tf_cac.paragraphs[0]
    pc0.text = "ACQUISITION COST OPPORTUNITY: 40% CAC REDUCTION"
    pc0.font.name = "Arial"
    pc0.font.size = Pt(7.5)
    pc0.font.bold = True
    pc0.font.color.rgb = COLOR_NAVY

    pc1 = tf_cac.add_paragraph()
    pc1.text = "Current Baseline CAC: ₹15,000 / active SMB  →  Target Digital CAC: ≤ ₹9,000 (40% saving)"
    pc1.font.name = "Arial"
    pc1.font.size = Pt(6.8)
    pc1.font.color.rgb = COLOR_BODY

    # Revenue-Based Acquisition Payback Table
    tb_hdr = slide.shapes.add_textbox(right_x, Inches(2.14), right_w, Inches(0.16))
    tf_hdr = tb_hdr.text_frame
    tf_hdr.word_wrap = True
    tf_hdr.margin_left = tf_hdr.margin_right = tf_hdr.margin_top = tf_hdr.margin_bottom = 0
    ptb0 = tf_hdr.paragraphs[0]
    ptb0.text = "REVENUE-BASED ACQUISITION PAYBACK (GROSS REVENUE BEFORE OPERATING MARGIN)"
    ptb0.font.name = "Arial"
    ptb0.font.size = Pt(7.0)
    ptb0.font.bold = True
    ptb0.font.color.rgb = COLOR_INK

    table_headers = ["Bundle", "Monthly Price", "Current CAC (₹15k)", "Target CAC (₹9k)", "Payback Speedup"]
    table_rows = [
        ["Starter", "₹2,500 / mo", "6.0 Months", "3.6 Months", "40% Faster"],
        ["Office", "₹6,900 / mo", "2.2 Months", "1.3 Months", "41% Faster"],
    ]
    col_w_list = [Inches(0.85), Inches(0.95), Inches(1.00), Inches(0.95), Inches(0.90)]
    align_list = [PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.CENTER]

    add_table(slide, right_x, Inches(2.32), right_w, Inches(0.65), table_headers, table_rows, col_w_list, align_list, font_size=7.0, pad_y=0.015)

    # Operational Advantage Box (Placed cleanly at 3.50 in with zero overlap)
    add_card(slide, right_x, Inches(3.48), right_w, Inches(1.22))
    tb_op = slide.shapes.add_textbox(right_x + Inches(0.12), Inches(3.52), right_w - Inches(0.24), Inches(1.14))
    tf_op = tb_op.text_frame
    tf_op.word_wrap = True
    tf_op.margin_left = tf_op.margin_right = tf_op.margin_top = tf_op.margin_bottom = 0

    pop0 = tf_op.paragraphs[0]
    pop0.text = "HOW DIGITAL ONBOARDING CUTS OPERATIONAL FRICTION"
    pop0.font.name = "Arial"
    pop0.font.size = Pt(7.5)
    pop0.font.bold = True
    pop0.font.color.rgb = COLOR_NAVY
    pop0.space_after = Pt(2)

    pop1 = tf_op.add_paragraph()
    pop1.text = "• Eliminates Manual Quotation: Instant eligibility and pricing remove the 3–5 day sales drafting bottleneck.\n• Removes Physical KYC Couriers: In-memory OCR and automated checks avoid repeated document pickups.\n• Shifts Field Force to High-Value Deals: Self-serve covers micro-retail and CA offices, letting sales teams focus on multi-site enterprises and manufacturing clients."
    pop1.font.name = "Arial"
    pop1.font.size = Pt(6.8)
    pop1.font.color.rgb = COLOR_BODY


def build_slide_7(prs):
    """Slide 7: Execution Roadmap, KPIs and The Ask"""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide)

    add_header(
        slide,
        eyebrow="06 · EXECUTION ROADMAP, KPIS & THE ASK",
        headline="A measurable three-month pilot can validate the model.",
        subtitle="Clear performance milestones, 3-phase commercial scaling, and an actionable pilot proposal for judging approval."
    )

    # Target Performance KPIs Table (Top) - Compact 5 rows fully visible
    kpi_headers = ["Performance Metric", "Current Baseline (Synthetic Case)", "Target (Proposed Pilot)", "Strategic Commercial Impact"]
    kpi_rows = [
        ["Lead-to-Activation Conversion", "7.4% (368 / 5,000)", "12.0%", "+62% conversion via instant quotes and zero paperwork"],
        ["Activation Lead Time", "17.6 Days", "≤ 7.0 Days", "60% cycle compression from in-memory digital KYC pre-checks"],
        ["Status-Chase Calls / Customer", "3.0 Calls", "≤ 1.0 Call", "Live order tracking eliminates inbound status call overhead"],
        ["Acquisition Cost (CAC)", "₹15,000 / active SMB", "≤ ₹9,000", "40% CAC reduction through self-serve & partner onboarding"],
        ["Six-Month Churn Rate", "Q2 Cohort Baseline", "≤ Baseline", "Single bill transparency and upfront SLA protect retention"],
    ]
    kpi_w = [Inches(1.75), Inches(1.75), Inches(1.20), Inches(4.00)]
    kpi_align = [PP_ALIGN.LEFT, PP_ALIGN.CENTER, PP_ALIGN.CENTER, PP_ALIGN.LEFT]

    add_table(slide, Inches(0.65), Inches(1.50), Inches(8.70), Inches(1.25), kpi_headers, kpi_rows, kpi_w, kpi_align, font_size=6.8, pad_y=0.015)

    # Bottom Split: 3-Phase Rollout (Left) vs The Ask (Right) - Placed below table at 2.92 in
    bot_y = Inches(2.92)
    bot_h = Inches(1.80)

    # Left: 3-Phase Rollout
    left_x = Inches(0.65)
    left_w = Inches(4.35)
    add_card(slide, left_x, bot_y, left_w, bot_h)

    tb_ro = slide.shapes.add_textbox(left_x + Inches(0.12), bot_y + Inches(0.08), left_w - Inches(0.24), bot_h - Inches(0.14))
    tf_ro = tb_ro.text_frame
    tf_ro.word_wrap = True
    tf_ro.margin_left = tf_ro.margin_right = tf_ro.margin_top = tf_ro.margin_bottom = 0

    pro0 = tf_ro.paragraphs[0]
    pro0.text = "PHASED 12-MONTH COMMERCIAL ROLLOUT"
    pro0.font.name = "Arial"
    pro0.font.size = Pt(7.6)
    pro0.font.bold = True
    pro0.font.color.rgb = COLOR_NAVY
    pro0.space_after = Pt(2)

    phases = [
        ("Phase 1: Pilot (0–3 Months)", "Two Tier-1 cities, Micro-retail & Office segments. Shadow advisor with field sales to establish live conversion baseline."),
        ("Phase 2: Scale (3–6 Months)", "Expand to Tier-2 cities, launch local partner-assisted onboarding, and integrate live GSTN/MCA GSP API gateways."),
        ("Phase 3: Expand (6–12 Months)", "Multi-site retail chains, manufacturing IoT tiers, WhatsApp bot onboarding, and automated predictive provisioning."),
    ]
    for ph_title, ph_desc in phases:
        p = tf_ro.add_paragraph()
        p.text = f"• {ph_title}: "
        p.font.name = "Arial"
        p.font.size = Pt(6.6)
        p.font.bold = True
        p.font.color.rgb = COLOR_INK

        run = p.add_run()
        run.text = ph_desc
        run.font.name = "Arial"
        run.font.size = Pt(6.6)
        run.font.bold = False
        run.font.color.rgb = COLOR_BODY
        p.space_after = Pt(2)

    # Right: The Ask & Next Steps
    right_x = Inches(5.10)
    right_w = Inches(4.25)
    add_card(slide, right_x, bot_y, right_w, bot_h, bg_color=COLOR_BLUE_BG, border_color=RGBColor(147, 197, 253))

    tb_ask = slide.shapes.add_textbox(right_x + Inches(0.12), bot_y + Inches(0.08), right_w - Inches(0.24), bot_h - Inches(0.14))
    tf_ask = tb_ask.text_frame
    tf_ask.word_wrap = True
    tf_ask.margin_left = tf_ask.margin_right = tf_ask.margin_top = tf_ask.margin_bottom = 0

    pask0 = tf_ask.paragraphs[0]
    pask0.text = "THE ASK: APPROVE A THREE-MONTH, TWO-CITY PILOT"
    pask0.font.name = "Arial"
    pask0.font.size = Pt(7.8)
    pask0.font.bold = True
    pask0.font.color.rgb = COLOR_NAVY
    pask0.space_after = Pt(2)

    actions = [
        ("1. Validate Advisor with Live SMBs:", "Run 500 live MSME interactions across two test cities to tune multilingual intent recognition."),
        ("2. Establish Verified Baseline:", "Measure empirical conversion, KYC completion, and 6-month retention against traditional manual channels."),
        ("3. Onboard 20 Pilot Partners:", "Equip local IT dealers and kirana aggregators with the partner-assisted mobile onboarding flow."),
    ]
    for a_title, a_desc in actions:
        pa = tf_ask.add_paragraph()
        pa.text = f"✓ {a_title} "
        pa.font.name = "Arial"
        pa.font.size = Pt(6.6)
        pa.font.bold = True
        pa.font.color.rgb = COLOR_INK

        run = pa.add_run()
        run.text = a_desc
        run.font.name = "Arial"
        run.font.size = Pt(6.6)
        run.font.bold = False
        run.font.color.rgb = COLOR_BODY
        pa.space_after = Pt(2)

    # Verified Repository & Test Status footer
    pfoot = tf_ask.add_paragraph()
    pfoot.text = "Repository: https://github.com/Jaswant2406/accell-business  |  Status: 89 Tests Passed (100%)"
    pfoot.font.name = "Arial"
    pfoot.font.size = Pt(6.3)
    pfoot.font.bold = True
    pfoot.font.color.rgb = COLOR_SLATE


def main():
    print("Initializing 7-Slide Presentation Generation...")
    prs = Presentation()
    prs.slide_width = Inches(10.0)
    prs.slide_height = Inches(5.625)

    print("Building Slide 1: Executive Pitch...")
    build_slide_1(prs)

    print("Building Slide 2: The Business Problem...")
    build_slide_2(prs)

    print("Building Slide 3: The Solution and Working Prototype...")
    build_slide_3(prs)

    print("Building Slide 4: Solution Architecture and Technical Differentiation...")
    build_slide_4(prs)

    print("Building Slide 5: Data Privacy, Security and Trust...")
    build_slide_5(prs)

    print("Building Slide 6: Business Model and Commercial Impact...")
    build_slide_6(prs)

    print("Building Slide 7: Execution Roadmap, KPIs and The Ask...")
    build_slide_7(prs)

    pptx_path = os.path.abspath("d:/airtel/Udyam_Digital_Final_7_Slides.pptx")
    prs.save(pptx_path)
    print(f"Saved PPTX successfully: {pptx_path} (Slides: {len(prs.slides)})")

    # Export to PDF via PowerPoint COM
    pdf_path = os.path.abspath("d:/airtel/Udyam_Digital_Final_7_Slides.pdf")
    print(f"Exporting to PDF via PowerPoint COM: {pdf_path}...")
    try:
        import win32com.client
        ppt_app = win32com.client.Dispatch("PowerPoint.Application")
        ppt_pres = ppt_app.Presentations.Open(pptx_path, WithWindow=False)
        ppt_pres.SaveAs(pdf_path, 32) # 32 = ppSaveAsPDF
        ppt_pres.Close()
        ppt_app.Quit()
        print(f"Saved PDF successfully: {pdf_path} (Size: {os.path.getsize(pdf_path):,} bytes)")
    except Exception as e:
        print(f"PowerPoint COM export error: {e}")

    # Render each page to high-res PNG for visual inspection
    print("Rendering slides to PNG via PyMuPDF...")
    import pymupdf
    doc = pymupdf.open(pdf_path)
    print(f"PyMuPDF verification: doc.page_count = {doc.page_count}")
    assert doc.page_count == 7, f"Expected 7 pages, got {doc.page_count}"

    preview_dir = os.path.abspath("d:/airtel/docs/presentation_slides_preview")
    os.makedirs(preview_dir, exist_ok=True)

    for page_idx in range(doc.page_count):
        page = doc[page_idx]
        pix = page.get_pixmap(dpi=200) # High-res 200 DPI
        slide_img_path = os.path.join(preview_dir, f"slide_{page_idx + 1}.png")
        pix.save(slide_img_path)
        print(f"Rendered slide {page_idx + 1}: {slide_img_path} ({pix.width}x{pix.height})")

    print("\nALL 7 SLIDES GENERATED AND VALIDATED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
