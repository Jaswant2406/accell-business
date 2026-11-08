"""
Render ACCEL_BUSINESS_COMPLETE_QA_REPORT.md to executive PDF using Playwright and marked.js.
"""

from pathlib import Path
from playwright.sync_api import sync_playwright

DOCS_DIR = Path("docs")
MD_PATH = DOCS_DIR / "ACCEL_BUSINESS_COMPLETE_QA_REPORT.md"
OUTPUT_PDF = DOCS_DIR / "ACCEL_BUSINESS_COMPLETE_QA_REPORT.pdf"
HTML_TEMP = DOCS_DIR / "_temp_qa_pdf.html"

def generate_qa_pdf():
    print(f"Reading {MD_PATH} ...")
    md_text = MD_PATH.read_text(encoding="utf-8")
    # Escape backticks and backslashes for js string template
    escaped_md = md_text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Accel Business — Complete QA Report</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Manrope:wght@600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    @page {{
      size: A4 portrait;
      margin: 18mm 16mm 18mm 16mm;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #111827;
      background: #FFFFFF;
      font-size: 10pt;
      line-height: 1.55;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    h1, h2, h3, h4 {{
      font-family: 'Manrope', sans-serif;
      color: #111827;
      letter-spacing: -0.02em;
    }}
    h1 {{
      font-size: 20pt;
      font-weight: 800;
      color: #1E3A8A;
      margin-bottom: 12px;
      border-bottom: 2px solid #1E3A8A;
      padding-bottom: 8px;
    }}
    h2 {{
      font-size: 13pt;
      font-weight: 800;
      margin-top: 20px;
      margin-bottom: 8px;
      border-left: 4px solid #1E3A8A;
      padding-left: 8px;
      color: #111827;
    }}
    h3 {{
      font-size: 11pt;
      font-weight: 700;
      margin-top: 14px;
      margin-bottom: 6px;
      color: #1E3A8A;
    }}
    p {{
      margin-bottom: 8px;
      font-size: 9pt;
      color: #374151;
    }}
    ul, ol {{
      margin-left: 20px;
      margin-bottom: 10px;
      font-size: 9pt;
      color: #374151;
    }}
    li {{
      margin-bottom: 3px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0;
      font-size: 8pt;
      page-break-inside: avoid;
    }}
    th, td {{
      padding: 5px 8px;
      border: 1px solid #CBD5E1;
      text-align: left;
    }}
    th {{
      background: #F1F5F9;
      color: #0F172A;
      font-weight: 700;
      font-family: 'Manrope', sans-serif;
    }}
    tr:nth-child(even) td {{
      background: #F8FAFC;
    }}
    code {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 8pt;
      background: #F1F5F9;
      padding: 1px 3px;
      border-radius: 3px;
      color: #1E3A8A;
    }}
    pre code {{
      display: block;
      padding: 8px;
      background: #F8FAFC;
      border: 1px solid #E2E8F0;
      border-radius: 4px;
      white-space: pre-wrap;
    }}
    blockquote {{
      border-left: 3px solid #3B82F6;
      background: #EFF6FF;
      padding: 6px 12px;
      margin: 8px 0;
      font-size: 8.5pt;
    }}
  </style>
</head>
<body>
  <div id="content"></div>
  <script>
    const md = `{escaped_md}`;
    document.getElementById('content').innerHTML = marked.parse(md);
  </script>
</body>
</html>
"""
    HTML_TEMP.write_text(html_content, encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file:///{HTML_TEMP.resolve().as_posix()}", wait_until="networkidle")
        page.wait_for_timeout(1000)

        print(f"Generating QA PDF: {OUTPUT_PDF} ...")
        page.pdf(
            path=str(OUTPUT_PDF),
            format="A4",
            print_background=True,
            margin={"top": "16mm", "bottom": "16mm", "left": "16mm", "right": "16mm"},
            display_header_footer=True,
            header_template='<div style="font-family: \'Inter\', sans-serif; font-size: 7.5pt; color: #64748B; width: 100%; display: flex; justify-content: space-between; padding: 0 16mm;"><span>ACCEL BUSINESS • QA VALIDATION REPORT</span><span>PROGRAMMATIC AUDIT</span></div>',
            footer_template='<div style="font-family: \'Inter\', sans-serif; font-size: 7.5pt; color: #64748B; width: 100%; display: flex; justify-content: space-between; padding: 0 16mm;"><span>CONFIDENTIAL • TRACK A</span><span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>'
        )
        print(f"Successfully generated {OUTPUT_PDF}")
        browser.close()

    if HTML_TEMP.exists():
        HTML_TEMP.unlink()

if __name__ == "__main__":
    generate_qa_pdf()
