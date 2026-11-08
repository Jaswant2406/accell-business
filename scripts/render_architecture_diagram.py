"""
Render solution_architecture.mmd to high-resolution PNG using Playwright and Mermaid.js.
"""

from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

MMD_PATH = Path("docs/solution_architecture.mmd")
PNG_PATH = Path("docs/solution_architecture.png")
HTML_TEMP_PATH = Path("docs/_temp_diagram.html")

def render_diagram():
    if not MMD_PATH.exists():
        print(f"Error: {MMD_PATH} not found.")
        sys.exit(1)

    mmd_content = MMD_PATH.read_text(encoding="utf-8")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Accel Business - Solution Architecture</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      background-color: #FFFFFF;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      padding: 32px;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-width: 1600px;
    }}
    .header {{
      text-align: center;
      margin-bottom: 24px;
      max-width: 1400px;
      width: 100%;
    }}
    .eyebrow {{
      font-family: 'Inter', sans-serif;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #1E3A8A;
      margin-bottom: 6px;
    }}
    h1 {{
      font-family: 'Manrope', sans-serif;
      font-size: 28px;
      font-weight: 800;
      color: #111827;
      letter-spacing: -0.03em;
      margin-bottom: 8px;
    }}
    p.subtitle {{
      font-size: 14px;
      color: #4B5563;
      line-height: 1.5;
    }}
    #diagram {{
      width: 100%;
      display: flex;
      justify-content: center;
      background: #FFFFFF;
      padding: 16px;
      border-radius: 12px;
      border: 1px solid #E5E7EB;
    }}
    svg {{
      max-width: 100% !important;
      height: auto !important;
    }}
  </style>
</head>
<body>
  <div class="header">
    <div class="eyebrow">Enterprise Track A • Autonomous SMB Onboarding</div>
    <h1>Accel Business — Solution Architecture Diagram</h1>
    <p class="subtitle">Complete 6-Layer Architecture: Presentation, Processing, Intelligence, Financial Costing, Data & External Integrations</p>
  </div>
  <div id="diagram" class="mermaid">
{mmd_content}
  </div>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'base',
      themeVariables: {{
        fontFamily: 'Inter, system-ui, sans-serif',
        fontSize: '13px',
        primaryColor: '#FFFFFF',
        primaryBorderColor: '#1E3A8A',
        primaryTextColor: '#111827',
        lineColor: '#1E3A8A',
        secondaryColor: '#EFF6FF',
        tertiaryColor: '#F8FAFC',
        edgeLabelBackground: '#FFFFFF'
      }},
      flowchart: {{
        curve: 'basis',
        nodeSpacing: 35,
        rankSpacing: 45,
        useMaxWidth: false
      }}
    }});
  </script>
</body>
</html>
"""

    HTML_TEMP_PATH.write_text(html_content, encoding="utf-8")
    print(f"Generated HTML template at {HTML_TEMP_PATH}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2
        )
        page = context.new_page()
        page.on("console", lambda msg: print(f"[Browser console]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"[Browser error]: {err}"))

        file_url = f"file:///{HTML_TEMP_PATH.resolve().as_posix()}"
        print(f"Loading {file_url} ...")
        page.goto(file_url, wait_until="networkidle")

        # Wait for mermaid SVG to be rendered
        page.wait_for_selector("#diagram svg", timeout=20000)

        # Allow font rendering to settle
        page.wait_for_timeout(1500)

        # Screenshot the entire document
        page.screenshot(path=str(PNG_PATH), full_page=True)
        print(f"Successfully rendered diagram to {PNG_PATH}")

        browser.close()

    # Clean up temp html
    if HTML_TEMP_PATH.exists():
        HTML_TEMP_PATH.unlink()

if __name__ == "__main__":
    render_diagram()
