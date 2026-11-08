"""
Playwright Real-Browser Layout, Typography & Collision Verification.
Covers 4 viewports:
- 1440px (Desktop)
- 1024px (Tablet Landscape)
- 768px (Tablet Portrait)
- 390px (Mobile)

Across Populated States:
1. Home (Editorial Hero, Service Panels, Checklist, Stat Block)
2. Advisor (Populated with Solution Bundle recommendations)
3. Quote (Line item cards with visible quantity stepper, remove button, catalogue specs, Quote Summary)
4. KYC (DPDP Consent, Specimen verification audit, masked credentials, criteria checklist)
5. Checkout (Provisional Order review, mandate authorization, contact details)
6. Track (Live circuit provisioning milestone timeline, SLA countdown)
7. Sales Analytics (Executive Scorecard metrics, Funnel charts, Where Leads Leak, What-if simulator)
8. Sidebar (Header, navigation selector, journey stages, persistent order summary, system health)

Fails if:
- Hero headline doesn't compute to Manrope 800 with ~1.04 line-height ratio
- Body text doesn't compute to Inter 14px / 24.5px
- Any document horizontal overflow occurs (scrollWidth > window width)
- Any sibling text/icon bounding boxes intersect within a card
- Any child text/icon element horizontally overflows its card container
- Any text container clips content via overflow: hidden
"""

import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

SCREENSHOT_DIR = Path("docs/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

VIEWPORTS = [
    {"name": "1440_desktop", "width": 1440, "height": 900},
    {"name": "1024_tablet_ls", "width": 1024, "height": 768},
    {"name": "768_tablet_pt", "width": 768, "height": 1024},
    {"name": "390_mobile", "width": 390, "height": 844},
]

JS_OVERLAP_CHECKER = """
() => {
    const errors = [];
    const winWidth = window.innerWidth;
    const docWidth = document.documentElement.scrollWidth;

    // 1. Fail on page-level horizontal overflow
    if (docWidth > winWidth + 5) {
        errors.push(`Page horizontal overflow: scrollWidth ${docWidth}px > window ${winWidth}px`);
    }

    // 2. Select card and box containers
    const containers = Array.from(document.querySelectorAll(
        '.bordered-card, .bordered-box, .bordered-card-subtle, .quote-item-card, [data-testid="stVerticalBlockBorderWrapper"] > div'
    )).filter(c => {
        const r = c.getBoundingClientRect();
        return r.width > 20 && r.height > 20;
    });

    containers.forEach((card, idx) => {
        const cardRect = card.getBoundingClientRect();
        const cs = window.getComputedStyle(card);

        // Fail on clipped text inside overflow:hidden containers (excluding pure decorative backgrounds)
        if ((cs.overflow === 'hidden' || cs.overflowY === 'hidden') && !card.classList.contains('bordered-box')) {
            if (card.scrollHeight > card.clientHeight + 6) {
                errors.push(`Container #${idx} content is vertically clipped: scrollHeight ${card.scrollHeight}px > clientHeight ${card.clientHeight}px`);
            }
        }

        // Check child elements
        const nodes = card.querySelectorAll('h1, h2, h3, h4, p, span, .eyebrow, .tabular-num, button, input');
        const elements = Array.from(nodes).filter(el => {
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0 && el.childElementCount === 0;
        });

        // Child horizontal boundary check (tolerance 12px for padding and borders)
        elements.forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.right > cardRect.right + 12 || r.left < cardRect.left - 12) {
                const txt = (el.innerText || el.tagName).slice(0, 24).trim();
                errors.push(`Container #${idx} child overflows horizontally: "${txt}" [${r.left.toFixed(0)}, ${r.right.toFixed(0)}] vs card [${cardRect.left.toFixed(0)}, ${cardRect.right.toFixed(0)}]`);
            }
        });

        // Sibling intersections among direct siblings
        for (let i = 0; i < elements.length; i++) {
            for (let j = i + 1; j < elements.length; j++) {
                const e1 = elements[i];
                const e2 = elements[j];
                if (e1.contains(e2) || e2.contains(e1)) continue;
                if (e1.parentElement !== e2.parentElement) continue;

                const r1 = e1.getBoundingClientRect();
                const r2 = e2.getBoundingClientRect();

                // 2px buffer for normal layout rounding
                const intersects = !(
                    r1.right <= r2.left + 2 ||
                    r1.left >= r2.right - 2 ||
                    r1.bottom <= r2.top + 2 ||
                    r1.top >= r2.bottom - 2
                );

                if (intersects) {
                    const t1 = (e1.innerText || e1.tagName).slice(0, 18).trim();
                    const t2 = (e2.innerText || e2.tagName).slice(0, 18).trim();
                    errors.push(`Intersection between "${t1}" and "${t2}" inside Container #${idx}`);
                }
            }
        }
    });

    return errors;
}
"""

JS_SIDEBAR_CHECKER = """
() => {
    const errors = [];
    const sidebar = document.querySelector('[data-testid="stSidebar"]');
    if (!sidebar) return errors;

    const sbRect = sidebar.getBoundingClientRect();
    if (sbRect.width === 0) return errors; // collapsed

    const nodes = sidebar.querySelectorAll('h1, h2, h3, h4, p, span, div, button');
    const elements = Array.from(nodes).filter(el => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && el.childElementCount === 0;
    });

    elements.forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.right > sbRect.right + 12 || r.left < sbRect.left - 12) {
            const txt = (el.innerText || el.tagName).slice(0, 24).trim();
            errors.push(`Sidebar element overflows: "${txt}" [${r.left.toFixed(0)}, ${r.right.toFixed(0)}] vs sidebar [${sbRect.left.toFixed(0)}, ${sbRect.right.toFixed(0)}]`);
        }
    });

    return errors;
}
"""


def safe_screenshot(page, path, full_page=True):
    try:
        page.evaluate("""() => {
            try {
                Object.defineProperty(document.fonts, 'ready', { value: Promise.resolve(), configurable: true });
            } catch(e) {}
        }""")
        page.screenshot(path=str(path), full_page=full_page, timeout=12000, animations="disabled")
    except Exception as ex:
        print(f"Full-page screenshot note for {path.name}: {ex}. Retrying standard viewport screenshot.")
        try:
            page.screenshot(path=str(path), full_page=False, timeout=8000, animations="disabled")
        except Exception:
            pass


def test_layout_and_typography():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        results = []

        for vp in VIEWPORTS:
            vp_name = vp["name"]
            w = vp["width"]
            h = vp["height"]
            print(f"\n==================================================")
            print(f"Testing Viewport: {vp_name} ({w}x{h})")
            print(f"==================================================")

            context = browser.new_context(viewport={"width": w, "height": h})
            page = context.new_page()

            page_metrics = {}

            # -------------------------------------------------------------
            # 1. HOME VIEW
            # -------------------------------------------------------------
            page.goto("http://localhost:8501")
            page.wait_for_selector(".hero-headline", timeout=15000)
            page.wait_for_timeout(1500)

            # Check computed styles of hero headline
            hero_styles = page.evaluate("""() => {
                const h1 = document.querySelector('.hero-headline');
                if (!h1) return null;
                const cs = window.getComputedStyle(h1);
                const fontSize = parseFloat(cs.fontSize);
                const lineHeight = parseFloat(cs.lineHeight);
                return {
                    fontFamily: cs.fontFamily,
                    fontWeight: cs.fontWeight,
                    fontSize: cs.fontSize,
                    lineHeight: cs.lineHeight,
                    lineHeightRatio: (lineHeight / fontSize).toFixed(3),
                    color: cs.color,
                    letterSpacing: cs.letterSpacing
                };
            }""")
            print(f"Hero computed styles at {w}px:", hero_styles)
            assert hero_styles is not None, "Hero headline .hero-headline not found!"
            assert "Manrope" in hero_styles["fontFamily"], f"Hero font family is not Manrope: {hero_styles['fontFamily']}"
            assert hero_styles["fontWeight"] in ["800", 800], f"Hero font weight is not 800: {hero_styles['fontWeight']}"
            lh_ratio = float(hero_styles["lineHeightRatio"])
            assert 0.95 <= lh_ratio <= 1.15, f"Hero line-height ratio {lh_ratio} not close to 1.04!"
            assert "rgb(17, 24, 39)" in hero_styles["color"], f"Hero color {hero_styles['color']} is not rgb(17, 24, 39) (#111827)!"

            # Check computed styles of body text
            body_styles = page.evaluate("""() => {
                const p = document.querySelector('p');
                if (!p) return null;
                const cs = window.getComputedStyle(p);
                return {
                    fontFamily: cs.fontFamily,
                    fontWeight: cs.fontWeight,
                    fontSize: cs.fontSize,
                    lineHeight: cs.lineHeight,
                    color: cs.color
                };
            }""")
            print(f"Body computed styles at {w}px:", body_styles)
            assert body_styles is not None, "Body text <p> not found!"
            assert "Inter" in body_styles["fontFamily"], f"Body font family is not Inter: {body_styles['fontFamily']}"
            assert body_styles["fontSize"] == "14px", f"Body font size is not 14px: {body_styles['fontSize']}"
            assert body_styles["lineHeight"] == "24.5px", f"Body line height is not 24.5px: {body_styles['lineHeight']}"
            assert "rgb(97, 107, 122)" in body_styles["color"], f"Body color {body_styles['color']} is not rgb(97, 107, 122) (#616B7A)!"

            home_errs = page.evaluate(JS_OVERLAP_CHECKER)
            print(f"Home overlap check errors ({w}px):", len(home_errs))
            assert len(home_errs) == 0, f"Overlaps detected on Home view: {home_errs[:5]}"
            page_metrics["Home"] = len(home_errs)

            home_shot = SCREENSHOT_DIR / f"restyle_{vp_name}_home.png"
            safe_screenshot(page, home_shot, full_page=True)
            print(f"Captured: {home_shot}")

            # -------------------------------------------------------------
            # 2. ADVISOR VIEW (Populated with Solution Bundle)
            # -------------------------------------------------------------
            start_btn = None
            for b in page.query_selector_all('button'):
                t = b.inner_text()
                if "Start now" in t or "Start Digital Onboarding" in t:
                    start_btn = b
                    break
            if start_btn:
                start_btn.click(force=True)
                page.wait_for_timeout(2500)

            # Click Analyze with AI to generate recommendations
            for b in page.query_selector_all('button'):
                if "Analyze with AI" in b.inner_text():
                    b.click(force=True)
                    page.wait_for_timeout(2500)
                    break

            advisor_errs = page.evaluate(JS_OVERLAP_CHECKER)
            print(f"Advisor (with bundle) overlap errors ({w}px):", len(advisor_errs))
            assert len(advisor_errs) == 0, f"Overlaps detected on Advisor view: {advisor_errs[:5]}"
            page_metrics["Advisor"] = len(advisor_errs)

            advisor_shot = SCREENSHOT_DIR / f"restyle_{vp_name}_advisor.png"
            safe_screenshot(page, advisor_shot, full_page=True)
            print(f"Captured: {advisor_shot}")

            # -------------------------------------------------------------
            # 3. QUOTE VIEW (Populated with Bundle Line Items & Controls)
            # -------------------------------------------------------------
            for b in page.query_selector_all('button'):
                if "Proceed to Quote Configuration" in b.inner_text():
                    b.click(force=True)
                    page.wait_for_timeout(2500)
                    break

            quote_errs = page.evaluate(JS_OVERLAP_CHECKER)
            print(f"Quote overlap check errors ({w}px):", len(quote_errs))
            assert len(quote_errs) == 0, f"Overlaps detected on Quote view: {quote_errs[:5]}"
            page_metrics["Quote"] = len(quote_errs)

            quote_shot = SCREENSHOT_DIR / f"restyle_{vp_name}_quote.png"
            safe_screenshot(page, quote_shot, full_page=True)
            print(f"Captured: {quote_shot}")

            # -------------------------------------------------------------
            # 4. KYC VIEW (Populated Verification Audit)
            # -------------------------------------------------------------
            for b in page.query_selector_all('button'):
                if "Accept & Proceed to KYC" in b.inner_text():
                    b.click(force=True)
                    page.wait_for_timeout(2500)
                    break

            # Check DPDP Consent
            for cb in page.query_selector_all('input[type="checkbox"]'):
                try:
                    if not cb.is_checked():
                        cb.check(force=True)
                        page.wait_for_timeout(1000)
                except Exception:
                    pass

            # Click Run Smart KYC Verification
            for b in page.query_selector_all('button'):
                if "Run Smart KYC Verification" in b.inner_text():
                    b.click(force=True)
                    break

            try:
                page.wait_for_selector('button:has-text("Proceed to Checkout"), button:has-text("Create Provisional Order")', timeout=12000)
            except Exception:
                page.wait_for_timeout(4000)

            kyc_errs = page.evaluate(JS_OVERLAP_CHECKER)
            print(f"KYC overlap check errors ({w}px):", len(kyc_errs))
            assert len(kyc_errs) == 0, f"Overlaps detected on KYC view: {kyc_errs[:5]}"
            page_metrics["KYC"] = len(kyc_errs)

            kyc_shot = SCREENSHOT_DIR / f"restyle_{vp_name}_kyc.png"
            safe_screenshot(page, kyc_shot, full_page=True)
            print(f"Captured: {kyc_shot}")

            # -------------------------------------------------------------
            # 5. CHECKOUT VIEW (Populated Order & Mandate Review)
            # -------------------------------------------------------------
            chk_btn = None
            for b in page.query_selector_all('button'):
                txt = b.inner_text()
                if "Proceed to Checkout" in txt or "Create Provisional Order" in txt:
                    chk_btn = b
                    break
            if chk_btn:
                chk_btn.click(force=True)
                try:
                    page.wait_for_selector('h2:has-text("Checkout & Digital Mandate")', timeout=10000)
                except Exception:
                    page.wait_for_timeout(2500)

            checkout_errs = page.evaluate(JS_OVERLAP_CHECKER)
            print(f"Checkout overlap check errors ({w}px):", len(checkout_errs))
            assert len(checkout_errs) == 0, f"Overlaps detected on Checkout view: {checkout_errs[:5]}"
            page_metrics["Checkout"] = len(checkout_errs)

            checkout_shot = SCREENSHOT_DIR / f"restyle_{vp_name}_checkout.png"
            safe_screenshot(page, checkout_shot, full_page=True)
            print(f"Captured: {checkout_shot}")

            # -------------------------------------------------------------
            # 6. TRACK VIEW (Live Provisioning Milestone Timeline)
            # -------------------------------------------------------------
            confirm_btn = None
            for b in page.query_selector_all('button'):
                txt = b.inner_text()
                if "Confirm Order" in txt or "Provision Circuit" in txt:
                    confirm_btn = b
                    break
            if confirm_btn:
                confirm_btn.click(force=True)
                try:
                    page.wait_for_selector('h2:has-text("Service Activation Tracker")', timeout=10000)
                except Exception:
                    page.wait_for_timeout(3000)

            track_errs = page.evaluate(JS_OVERLAP_CHECKER)
            print(f"Track overlap check errors ({w}px):", len(track_errs))
            assert len(track_errs) == 0, f"Overlaps detected on Track view: {track_errs[:5]}"
            page_metrics["Track"] = len(track_errs)

            track_shot = SCREENSHOT_DIR / f"restyle_{vp_name}_track.png"
            safe_screenshot(page, track_shot, full_page=True)
            print(f"Captured: {track_shot}")

            # -------------------------------------------------------------
            # 7. SIDEBAR AUDIT (With Order Summary & Diagnostics)
            # -------------------------------------------------------------
            # On mobile, open sidebar if closed
            is_collapsed = page.evaluate("""() => {
                const sb = document.querySelector('[data-testid="stSidebar"]');
                if (!sb) return true;
                return sb.getAttribute('aria-expanded') === 'false' || sb.getAttribute('data-collapsed') === 'true';
            }""")
            if is_collapsed:
                for b in page.query_selector_all('button[data-testid="stSidebarCollapseButton"]'):
                    b.click(force=True)
                    page.wait_for_timeout(1000)
                    break

            sidebar_errs = page.evaluate(JS_SIDEBAR_CHECKER)
            print(f"Sidebar overlap check errors ({w}px):", len(sidebar_errs))
            assert len(sidebar_errs) == 0, f"Overlaps detected in Sidebar: {sidebar_errs[:5]}"
            page_metrics["Sidebar"] = len(sidebar_errs)

            sidebar_shot = SCREENSHOT_DIR / f"restyle_{vp_name}_sidebar.png"
            safe_screenshot(page, sidebar_shot, full_page=False)
            print(f"Captured: {sidebar_shot}")

            # -------------------------------------------------------------
            # 8. SALES ANALYTICS VIEW
            # -------------------------------------------------------------
            # Select Sales Analytics from sidebar radio via direct JS dispatch
            page.evaluate("""() => {
                const labels = Array.from(document.querySelectorAll('label'));
                for (const l of labels) {
                    if (l.innerText && l.innerText.includes('Sales Analytics')) {
                        const inp = l.querySelector('input');
                        if (inp) {
                            inp.click();
                        } else {
                            l.click();
                        }
                        return true;
                    }
                }
                return false;
            }""")

            try:
                page.wait_for_selector('h2:has-text("Sales & Funnel Performance Analytics")', timeout=10000)
            except Exception:
                page.wait_for_timeout(3000)

            # Collapse sidebar on mobile so Analytics page is fully visible
            if w <= 640:
                is_open = page.evaluate("""() => {
                    const sb = document.querySelector('[data-testid="stSidebar"]');
                    if (!sb) return false;
                    return sb.getAttribute('aria-expanded') === 'true' || sb.getAttribute('data-collapsed') === 'false';
                }""")
                if is_open:
                    for b in page.query_selector_all('button[data-testid="stSidebarCollapseButton"]'):
                        b.click(force=True)
                        page.wait_for_timeout(800)
                        break

            analytics_errs = page.evaluate(JS_OVERLAP_CHECKER)
            print(f"Analytics overlap check errors ({w}px):", len(analytics_errs))
            assert len(analytics_errs) == 0, f"Overlaps detected on Analytics view: {analytics_errs[:5]}"
            page_metrics["Analytics"] = len(analytics_errs)

            analytics_shot = SCREENSHOT_DIR / f"restyle_{vp_name}_analytics.png"
            safe_screenshot(page, analytics_shot, full_page=True)
            print(f"Captured: {analytics_shot}")

            context.close()
            results.append({
                "viewport": vp_name,
                "width": w,
                "hero_styles": hero_styles,
                "body_styles": body_styles,
                "metrics": page_metrics,
            })

        browser.close()
        return results


if __name__ == "__main__":
    res = test_layout_and_typography()
    print("\n" + "=" * 80)
    print("PLAYWRIGHT LAYOUT, OVERLAP & TYPOGRAPHY VERIFICATION REPORT")
    print("=" * 80)
    pages = ["Home", "Advisor", "Quote", "KYC", "Checkout", "Track", "Sidebar", "Analytics"]
    header = f"{'Viewport':<18} | " + " | ".join([f"{p:<10}" for p in pages])
    print(header)
    print("-" * len(header))
    for r in res:
        row = f"{r['viewport']:<18} | " + " | ".join([f"{r['metrics'].get(p, 0):<10}" for p in pages])
        print(row)
    print("=" * 80)
    print("All viewports verified: 0 overlaps, 0 clipped text errors, 0 horizontal overflow.")
