import os
import sys
import time
from playwright.sync_api import sync_playwright

def test_reproduce(msg, lang, api_key_set=False, block_google=False, tag=""):
    print(f"\n=======================================================")
    print(f"TESTING: msg='{msg}' | lang='{lang}' | api_key={api_key_set} | block_google={block_google} | tag={tag}")
    print(f"=======================================================")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        
        if block_google:
            context.route("**/*googleapis.com/**", lambda route: route.abort())
            context.route("**/*google.com/**", lambda route: route.abort())
            
        page = context.new_page()
        console_logs = []
        page.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        
        page.goto("http://localhost:8501", wait_until="domcontentloaded")
        time.sleep(2)
        
        # Click Customer Journey
        page.locator('label:has-text("Customer Journey")').first.click()
        time.sleep(2)
        
        # Select Language if needed
        if lang != "English":
            sb = page.locator('div[data-testid="stSelectbox"]').filter(has_text="Language")
            if sb.count() > 0:
                # Click the combobox or baseweb container
                combobox = sb.locator('input[role="combobox"], div[data-baseweb="select"]').first
                combobox.click()
                time.sleep(0.5)
                opt = page.locator('li[role="option"]').filter(has_text=lang).first
                if opt.count() > 0:
                    opt.click()
                time.sleep(1)
        
        # Check initial text area content
        ta = page.locator('textarea').first
        print("Initial textarea value:", ta.input_value()[:60], "...")
        
        # Clear and fill new message
        ta.fill("")
        ta.fill(msg)
        time.sleep(0.5)
        print("Filled textarea with new text:", ta.input_value())
        
        # Click Submit button ("Analyze with AI")
        btn = page.locator('button:has-text("Analyze with AI")').first
        btn.click()
        print("Clicked Analyze with AI button...")
        
        # Wait up to 6s
        time.sleep(5)
        
        # Inspect alerts
        alerts = page.locator('[data-testid="stAlert"]')
        print(f"Alerts present ({alerts.count()}):")
        for i in range(alerts.count()):
            print("  Alert:", alerts.nth(i).inner_text().strip())
            
        # Check Strategic Rationale card
        rationale = page.locator('.bordered-card-subtle')
        if rationale.count() > 0:
            print("Strategic Rationale card text:", rationale.first.inner_text().strip().replace("\n", " "))
            
        # Check recommended products card
        rec = page.locator('text=Products Pre-Selected')
        if rec.count() > 0:
            print("Pre-selected count header:", rec.first.inner_text().strip())
        else:
            print("[!] 'Products Pre-Selected' header not found!")
            
        # Check mode badge ("Running in rules mode" or "AI Powered")
        badge = page.locator('span:has-text("Running in rules mode"), span:has-text("AI Powered")')
        if badge.count() > 0:
            print("Mode badge text:", badge.first.inner_text().strip())
            
        # Check Primary City inside structured expander
        city_input = page.get_by_label("Primary City:")
        if city_input.count() > 0:
            print("City input value in structured expander:", city_input.input_value())
            
        # Check screenshot via CDP (no font delay)
        import base64
        os.makedirs("docs/repro_screenshots", exist_ok=True)
        screenshot_path = f"docs/repro_screenshots/repro_{tag}.png"
        try:
            cdp = page.context.new_cdp_session(page)
            res = cdp.send("Page.captureScreenshot")
            with open(screenshot_path, "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"Saved screenshot to {screenshot_path}")
        except Exception as e:
            print(f"Screenshot warning: {e}")
        print("Console logs:", console_logs)
        browser.close()

if __name__ == "__main__":
    # Test 1: English, GEMINI_API_KEY unset
    test_reproduce(
        msg="Dental clinic, 5 staff, 1 location in Kochi, I have a GSTIN",
        lang="English",
        api_key_set=False,
        block_google=False,
        tag="en_nokey"
    )
    # Test 2: Hindi, GEMINI_API_KEY unset
    test_reproduce(
        msg="जयपुर में डेंटल क्लिनिक है, 5 कर्मचारी हैं और 1 स्थान है, हमारे पास जीएसटी है",
        lang="Hindi",
        api_key_set=False,
        block_google=False,
        tag="hi_nokey"
    )
    # Test 3: Tamil, GEMINI_API_KEY unset
    test_reproduce(
        msg="சென்னையில் மருத்துவமனை, 5 ஊழியர்கள், 1 இடம், எங்களிடம் ஜிஎஸ்டி உள்ளது",
        lang="Tamil",
        api_key_set=False,
        block_google=False,
        tag="ta_nokey"
    )
    # Test 4: English with Google network blocked
    test_reproduce(
        msg="Dental clinic, 5 staff, 1 location in Kochi, I have a GSTIN",
        lang="English",
        api_key_set=True,
        block_google=True,
        tag="en_blocked"
    )
