"""
Central HTML rendering helper for Accel Business Udyam Digital.
Ensures zero raw HTML leak into Markdown code blocks:
- Strips leading and trailing whitespace per line (no line starts with 4+ spaces).
- Discards all blank lines inside HTML blocks.
- Renders via st.html() so Streamlit renders pure DOM elements without Markdown parsing.
- Tracks all rendered HTML strings for automated compliance testing.
"""

from typing import List
import streamlit as st

# Test inspection registry
RENDERED_HTML_REGISTRY: List[str] = []


def clean_html(html_str: str) -> str:
    """
    Format HTML string so no line starts with 4+ spaces and no blank lines exist.
    Strips leading and trailing whitespace from every line, filters out empty lines,
    and returns a clean, continuous HTML string.
    """
    if not html_str:
        return ""
    lines = [line.strip() for line in html_str.splitlines()]
    non_empty = [line for line in lines if line]
    # Join with newline so lines are distinct without any leading indentation
    return "\n".join(non_empty)


def render_html(html_str: str) -> None:
    """
    Safely render HTML without markdown code block interpretation.
    Uses st.html where available to prevent markdown parser interference.
    """
    if not html_str:
        return
    cleaned = clean_html(html_str)
    if not cleaned:
        return
    RENDERED_HTML_REGISTRY.append(cleaned)

    if hasattr(st, "html"):
        st.html(cleaned)
    else:
        st.markdown(cleaned, unsafe_allow_html=True)
