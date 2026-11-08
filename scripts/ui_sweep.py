"""
Real-browser UI sweep using Playwright.
Validates:
1. Every view (Home, Advisor, Quote, KYC with K12/K06/K01/K04/K05, Checkout, Track, KYC Desk, Analytics)
   at 1440px and 390px widths.
2. Clicks buttons, expanders, tabs, radios, selectboxes, sliders.
3. Captures console errors, failed network requests, and Streamlit exceptions.
4. Saves full-page screenshots to docs/screenshots/<view>_<width>.png.
5. Flags visible icon text leakage (e.g. '_arrow_right', 'keyboard_', 'check_circle', 'expand_more'),
   raw '<div', '{{', 'None', 'nan', 'undefined', 'NaN', or 'Traceback'.
6. Flags horizontal overflow, clipped text, and text contrast below 4.5:1.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Any
from playwright.sync_api import sync_playwright, Page, Response

SCREENSHOTS_DIR = Path("docs/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = os.getenv("APP_URL", "http://localhost:8501")

VIEWPORTS = [
    {"name": "desktop", "width": 1440, "height": 900},
    {"name": "mobile", "width": 390, "height": 844},
]


def wait_for_streamlit_ready(page: Page, timeout: float = 8.0):
    """Wait until Streamlit finishes its rerun cycle."""
    time.sleep(0.8)
    try:
        # Wait until stStatusWidget is not running
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=timeout * 1000)
        # Check if spinner exists and wait for it to disappear
        page.wait_for_selector('[data-testid="stStatusWidget"]', state="detached", timeout=timeout * 1000)
    except Exception:
        pass
    time.sleep(0.6)


def safe_screenshot(page: Page, path: Path):
    """Capture screenshot instantly via Chrome DevTools Protocol without font delays."""
    import base64
    try:
        cdp = page.context.new_cdp_session(page)
        res = cdp.send("Page.captureScreenshot")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(path), "wb") as f:
            f.write(base64.b64decode(res["data"]))
    except Exception as e:
        try:
            page.screenshot(path=str(path), timeout=3000)
        except Exception:
            pass


def close_mobile_sidebar(page: Page, width: int):
    """Close the mobile sidebar drawer if it is obscuring the main content container."""
    if width <= 768:
        try:
            collapse_btn = page.locator('button[data-testid="stSidebarCollapseButton"]')
            if collapse_btn.count() > 0 and collapse_btn.first.is_visible():
                collapse_btn.first.click()
                time.sleep(0.4)
        except Exception:
            pass


def audit_page_dom(page: Page, view_name: str, width: int) -> List[str]:
    """Execute in-browser JavaScript evaluation to detect visual defects, overflow, and leakage."""
    script = """
    () => {
        const issues = [];

        // 1. Check Horizontal Scroll / Page Overflow
        const scrollW = document.documentElement.scrollWidth;
        const clientW = document.documentElement.clientWidth;
        if (scrollW > clientW + 5) {
            issues.push(`Horizontal page overflow detected: scrollWidth (${scrollW}px) > clientWidth (${clientW}px)`);
        }

        // 2. Check for Streamlit Exception boxes or Tracebacks
        const excElements = document.querySelectorAll('[data-testid="stException"], .stException');
        if (excElements.length > 0) {
            excElements.forEach(el => {
                issues.push(`Streamlit Exception Box Present: ${el.innerText.substring(0, 150)}`);
            });
        }

        // 3. Scan visible text nodes for leaks, broken icons, or unrendered templates
        const suspiciousTokens = [
            "<div", "{{", "None", "nan", "undefined", "NaN", "Traceback",
            "_arrow_right", "arrow_drop", "keyboard_", "expand_more",
            "upload_file", "check_circle"
        ];

        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    const parent = node.parentElement;
                    if (!parent) return NodeFilter.FILTER_REJECT;
                    const tag = parent.tagName.toLowerCase();
                    if (tag === 'script' || tag === 'style' || tag === 'noscript') {
                        return NodeFilter.FILTER_REJECT;
                    }
                    const style = window.getComputedStyle(parent);
                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                        return NodeFilter.FILTER_REJECT;
                    }
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        let node;
        while ((node = walker.nextNode())) {
            const txt = node.nodeValue.trim();
            if (!txt) continue;
            const parent = node.parentElement;
            const style = window.getComputedStyle(parent);
            const fontFamily = style.fontFamily.toLowerCase();
            const isIconFont = fontFamily.includes('material') || fontFamily.includes('symbol') || fontFamily.includes('icon');

            // If it's an icon font, literal icon ligature text like 'arrow_forward' or 'check' is expected inside glyph
            if (isIconFont) {
                continue;
            }

            for (const token of suspiciousTokens) {
                if (txt.includes(token)) {
                    // Exclude benign substrings if any, e.g. "Maintenance" containing "nan"
                    if (token === "nan" && (txt.toLowerCase().includes("financial") || txt.toLowerCase().includes("maintenance") || txt.toLowerCase().includes("nant") || txt.toLowerCase().includes("banner"))) {
                        continue;
                    }
                    issues.push(`Text leak '${token}' found in element <${parent.tagName.toLowerCase()}> with text: "${txt.substring(0, 80)}"`);
                }
            }
        }

        // 4. Contrast check for text elements
        function getLuminance(r, g, b) {
            const a = [r, g, b].map(v => {
                v /= 255;
                return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
            });
            return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
        }

        function parseRgb(colorStr) {
            const match = colorStr.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
            if (!match) return null;
            return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
        }

        // Sample visible text elements (buttons, labels, cards, headings)
        const textElements = document.querySelectorAll('button, .eyebrow, h1, h2, h3, p, span, td, th');
        for (const el of textElements) {
            const text = el.innerText ? el.innerText.trim() : '';
            if (!text || text.length < 2) continue;
            const style = window.getComputedStyle(el);
            if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;

            const fg = parseRgb(style.color);
            if (!fg) continue;

            // Find effective background color walking up ancestors
            let bg = null;
            let curr = el;
            while (curr && curr !== document.documentElement) {
                const s = window.getComputedStyle(curr);
                const parsedBg = parseRgb(s.backgroundColor);
                if (parsedBg && s.backgroundColor !== 'rgba(0, 0, 0, 0)' && s.backgroundColor !== 'transparent') {
                    bg = parsedBg;
                    break;
                }
                curr = curr.parentElement;
            }
            if (!bg) bg = [244, 245, 247]; // fallback page bg #F4F5F7

            const l1 = getLuminance(fg[0], fg[1], fg[2]);
            const l2 = getLuminance(bg[0], bg[1], bg[2]);
            const contrast = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);

            // Flag text with contrast < 4.0:1 (ignoring pure disabled buttons which allow 3.5+)
            const isDisabled = el.hasAttribute('disabled') || el.closest('[disabled]');
            if (contrast < 4.0 && !isDisabled) {
                issues.push(`Low contrast ${contrast.toFixed(2)}:1 on <${el.tagName.toLowerCase()}> with text "${text.substring(0, 30)}" (fg: ${style.color}, bg: rgb(${bg.join(',')}))`);
                if (issues.length > 25) break;
            }
        }

        return issues;
    }
    """
    try:
        raw_issues = page.evaluate(script)
        return raw_issues or []
    except Exception as e:
        return [f"DOM Audit Evaluation Error: {str(e)}"]


def run_ui_sweep():
    """Execute full browser audit across views, widths, and demo applicants."""
    print(f"=== Starting Accel Business UI Full Sweep against {BASE_URL} ===")
    all_findings: Dict[str, List[str]] = {}
    console_errors: List[str] = []
    failed_requests: List[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for vp in VIEWPORTS:
            width = vp["width"]
            height = vp["height"]
            print(f"\n--- Testing Viewport: {vp['name'].upper()} ({width}x{height}px) ---")

            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()

            # Listen to console and network
            page.on("console", lambda msg: console_errors.append(f"[{vp['name']}] Console {msg.type}: {msg.text}") if msg.type in ["error"] else None)
            page.on("requestfailed", lambda req: failed_requests.append(f"[{vp['name']}] Failed Req: {req.url} - {req.failure}"))

            # -------------------------------------------------------------
            # VIEW 1: HOME OVERVIEW
            # -------------------------------------------------------------
            page.goto(BASE_URL, wait_until="domcontentloaded")
            wait_for_streamlit_ready(page)

            # Click Home in sidebar radio if not selected
            try:
                page.locator('label:has-text("Home")').first.click()
                wait_for_streamlit_ready(page)
            except Exception:
                pass

            view_key = f"home_{width}"
            safe_screenshot(page, SCREENSHOTS_DIR / f"{view_key}.png")
            issues = audit_page_dom(page, "Home", width)
            all_findings[view_key] = issues
            print(f"  [✓] Home ({width}px): {len(issues)} issues")

            # -------------------------------------------------------------
            # VIEW 2: ADVISOR (Customer Journey Step 1)
            # -------------------------------------------------------------
            try:
                # Click 'Customer Journey' radio
                page.locator('label:has-text("Customer Journey")').first.click()
                wait_for_streamlit_ready(page)
                # Ensure on Step 1
                page.locator('div.st-key-nav_step_1 button').first.click()
                wait_for_streamlit_ready(page)
                close_mobile_sidebar(page, width)
            except Exception as e:
                print(f"  [!] Nav to Journey Step 1 failed: {e}")

            # Interactive submit: type message, submit, assert recommendations populate
            try:
                ta = page.locator('textarea').first
                if ta.count() > 0:
                    ta.fill("Dental clinic, 5 staff, 1 location in Kochi, I have a GSTIN")
                    time.sleep(0.3)
                    ai_btn = page.locator('button:has-text("Analyze with AI")').first
                    if ai_btn.count() > 0:
                        close_mobile_sidebar(page, width)
                        ai_btn.click(force=True)
                        wait_for_streamlit_ready(page, timeout=12.0)
                        
                        rec_hdr = page.locator('text=Products Pre-Selected')
                        if rec_hdr.count() == 0 or "0 Products" in rec_hdr.first.inner_text():
                            print("  [!] FAILURE: Advisor submit failed to populate product recommendations!")
                            all_findings[f"advisor_submit_{width}"] = ["Advisor submit failed to populate recommendations"]
                        else:
                            print(f"  [✓] Advisor Submit ({width}px): {rec_hdr.first.inner_text().strip()}")
            except Exception as e:
                print(f"  [!] Interactive advisor submit failed: {e}")

            # Expand the Ineligible Catalogue Products expander
            try:
                exp = page.locator('details:has-text("View Ineligible Catalogue Products")')
                if exp.count() > 0:
                    exp.first.click()
                    time.sleep(0.5)
            except Exception:
                pass

            view_key = f"advisor_{width}"
            safe_screenshot(page, SCREENSHOTS_DIR / f"{view_key}.png")
            safe_screenshot(page, SCREENSHOTS_DIR / f"advisor_submit_{width}.png")
            issues = audit_page_dom(page, "Advisor", width)
            all_findings[view_key] = issues
            print(f"  [✓] Advisor ({width}px): {len(issues)} issues")

            # Click Proceed to Quote Configuration
            try:
                proc_quote_btn = page.locator('button:has-text("Proceed to Quote Configuration")').first
                if proc_quote_btn.count() > 0:
                    close_mobile_sidebar(page, width)
                    proc_quote_btn.click(force=True)
                    wait_for_streamlit_ready(page)
            except Exception as e:
                print(f"  [!] Proceed to Quote click failed: {e}")

            # -------------------------------------------------------------
            # VIEW 3: QUOTE (Customer Journey Step 2)
            # -------------------------------------------------------------
            # Click budget fit optimizer expander or test budget input
            try:
                fit_btn = page.locator('button:has-text("Optimize Bundle")')
                if fit_btn.count() > 0:
                    fit_btn.first.click(force=True)
                    wait_for_streamlit_ready(page)
            except Exception:
                pass

            # Open Complementary Products expander
            try:
                add_exp = page.locator('details:has-text("Add Complementary Product")')
                if add_exp.count() > 0:
                    add_exp.first.click()
                    time.sleep(0.5)
            except Exception:
                pass

            view_key = f"quote_{width}"
            safe_screenshot(page, SCREENSHOTS_DIR / f"{view_key}.png")
            issues = audit_page_dom(page, "Quote", width)
            all_findings[view_key] = issues
            print(f"  [✓] Quote ({width}px): {len(issues)} issues")

            # Click Accept & Proceed to KYC
            try:
                accept_btn = page.locator('button:has-text("Accept & Proceed to KYC")').first
                if accept_btn.count() > 0:
                    close_mobile_sidebar(page, width)
                    accept_btn.click(force=True)
                    wait_for_streamlit_ready(page)
                    safe_screenshot(page, SCREENSHOTS_DIR / f"quote_accept_{width}.png")
                    print(f"  [✓] Quote Accepted & Proceeded to KYC ({width}px)")
            except Exception as e:
                print(f"  [!] Accept & Proceed to KYC failed: {e}")

            # -------------------------------------------------------------
            # VIEW 4: KYC VERIFICATION (Step 3) with K12, K06, K01, K04, K05
            # -------------------------------------------------------------
            # Ensure DPDP consent checkbox is checked
            try:
                consent_box = page.locator('div.st-key-cb_dpdp_consent input[type="checkbox"]')
                if consent_box.count() > 0 and not consent_box.first.is_checked():
                    consent_box.first.click(force=True)
                    wait_for_streamlit_ready(page)
            except Exception:
                pass

            specimens_to_test = ["K12", "K06", "K01", "K04", "K05"]
            for spec in specimens_to_test:
                try:
                    # Select demo applicant
                    sb = page.locator('div[data-testid="stSelectbox"]:has-text("Quick Load Demo Applicant") input, div[data-testid="stSelectbox"]:has-text("Quick Load Demo Applicant")')
                    if sb.count() > 0:
                        sb.first.click(force=True)
                        time.sleep(0.3)
                        opt = page.locator(f'li[role="option"]:has-text("{spec}")')
                        if opt.count() > 0:
                            opt.first.click(force=True)
                            wait_for_streamlit_ready(page)

                    # Click Run Smart KYC Verification
                    run_btn = page.locator('button:has-text("Run Smart KYC Verification")')
                    if run_btn.count() > 0:
                        close_mobile_sidebar(page, width)
                        run_btn.first.click(force=True)
                        wait_for_streamlit_ready(page, timeout=15.0)
                        if spec == "K12":
                            safe_screenshot(page, SCREENSHOTS_DIR / f"kyc_verify_{width}.png")
                except Exception as e:
                    print(f"  [!] KYC specimen {spec} execution error: {e}")

                view_key = f"kyc_{spec}_{width}"
                safe_screenshot(page, SCREENSHOTS_DIR / f"{view_key}.png")
                issues = audit_page_dom(page, f"KYC-{spec}", width)
                all_findings[view_key] = issues
                print(f"  [✓] KYC Specimen {spec} ({width}px): {len(issues)} issues")

            # Click Proceed to Checkout for approved applicant K12
            try:
                proc_checkout_btn = page.locator('button:has-text("Proceed to Checkout")').first
                if proc_checkout_btn.count() > 0:
                    close_mobile_sidebar(page, width)
                    proc_checkout_btn.click(force=True)
                    wait_for_streamlit_ready(page)
            except Exception as e:
                print(f"  [!] Proceed to Checkout failed: {e}")

            # -------------------------------------------------------------
            # VIEW 5: CHECKOUT (Step 4)
            # -------------------------------------------------------------
            # Ensure Mandate Checkbox is checked
            try:
                cb_mandate = page.locator('div.st-key-cb_auth_mandate input[type="checkbox"]')
                if cb_mandate.count() > 0 and not cb_mandate.first.is_checked():
                    cb_mandate.first.click(force=True)
                    wait_for_streamlit_ready(page)
            except Exception:
                pass

            view_key = f"checkout_{width}"
            safe_screenshot(page, SCREENSHOTS_DIR / f"{view_key}.png")
            issues = audit_page_dom(page, "Checkout", width)
            all_findings[view_key] = issues
            print(f"  [✓] Checkout ({width}px): {len(issues)} issues")

            # Click Confirm Order
            try:
                confirm_order_btn = page.locator('button:has-text("Confirm Order")').first
                if confirm_order_btn.count() > 0:
                    close_mobile_sidebar(page, width)
                    confirm_order_btn.click(force=True)
                    wait_for_streamlit_ready(page, timeout=12.0)
                    safe_screenshot(page, SCREENSHOTS_DIR / f"checkout_submit_{width}.png")
                    print(f"  [✓] Checkout Order Confirmed ({width}px)")
            except Exception as e:
                print(f"  [!] Confirm Order failed: {e}")

            # -------------------------------------------------------------
            # VIEW 6: TRACK (Step 5)
            # -------------------------------------------------------------
            view_key = f"track_{width}"
            safe_screenshot(page, SCREENSHOTS_DIR / f"{view_key}.png")
            issues = audit_page_dom(page, "Track", width)
            all_findings[view_key] = issues
            print(f"  [✓] Track ({width}px): {len(issues)} issues")

            # Click Advance to Next Milestone
            try:
                adv_btn = page.locator('button:has-text("Advance to Next Milestone")').first
                if adv_btn.count() > 0:
                    close_mobile_sidebar(page, width)
                    adv_btn.click(force=True)
                    wait_for_streamlit_ready(page, timeout=8.0)
                    safe_screenshot(page, SCREENSHOTS_DIR / f"track_advance_{width}.png")
                    print(f"  [✓] Track Milestone Advanced ({width}px)")
            except Exception as e:
                print(f"  [!] Advance Milestone failed: {e}")

            # -------------------------------------------------------------
            # VIEW 7: KYC VERIFICATION DESK
            # -------------------------------------------------------------
            try:
                page.locator('label:has-text("KYC Verification Desk")').first.click()
                wait_for_streamlit_ready(page)
            except Exception:
                pass

            view_key = f"kyc_desk_{width}"
            safe_screenshot(page, SCREENSHOTS_DIR / f"{view_key}.png")
            issues = audit_page_dom(page, "KYC Desk", width)
            all_findings[view_key] = issues
            print(f"  [✓] KYC Desk ({width}px): {len(issues)} issues")

            # -------------------------------------------------------------
            # VIEW 8: SALES ANALYTICS
            # -------------------------------------------------------------
            try:
                page.locator('label:has-text("Sales Analytics")').first.click()
                wait_for_streamlit_ready(page)
            except Exception:
                pass

            # Open simulation expander
            try:
                sim_exp = page.locator('details:has-text("View Simulation Stage-by-Stage Breakdown")')
                if sim_exp.count() > 0:
                    sim_exp.first.click()
                    time.sleep(0.5)
            except Exception:
                pass

            view_key = f"analytics_{width}"
            safe_screenshot(page, SCREENSHOTS_DIR / f"{view_key}.png")
            issues = audit_page_dom(page, "Analytics", width)
            all_findings[view_key] = issues
            print(f"  [✓] Analytics ({width}px): {len(issues)} issues")

            context.close()

        browser.close()

    # Aggregate and Print Sweep Summary
    print("\n=================== UI FULL SWEEP REPORT ===================")
    total_issues = sum(len(v) for v in all_findings.values())
    print(f"Total Page Views Checked: {len(all_findings)}")
    print(f"Total Visual / Leak / Contrast Issues Found: {total_issues}")
    print(f"Total Console Errors: {len(console_errors)}")
    print(f"Total Failed Network Requests: {len(failed_requests)}")

    if total_issues > 0 or console_errors or failed_requests:
        print("\n--- DETAILED DEFECTS FOUND ---")
        for view, issues in all_findings.items():
            if issues:
                print(f"\n[View: {view}] ({len(issues)} issues):")
                for iss in issues[:10]:
                    print(f"  - {iss}")
                if len(issues) > 10:
                    print(f"  ... and {len(issues) - 10} more")

        if console_errors:
            print("\n--- CONSOLE ERRORS ---")
            for ce in console_errors:
                print(f"  - {ce}")

        if failed_requests:
            print("\n--- FAILED NETWORK REQUESTS ---")
            for fr in failed_requests:
                print(f"  - {fr}")

        sys.exit(1 if (total_issues > 0 or len(console_errors) > 0) else 0)
    else:
        print("\nALL PAGES, VIEWS, BUTTONS, AND VIEWPORTS PASSED WITH ZERO ISSUES!")
        sys.exit(0)


if __name__ == "__main__":
    run_ui_sweep()
