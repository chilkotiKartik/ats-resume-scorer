"""
Small rendering helpers shared by every page.

All dynamic text that ends up inside raw HTML goes through `esc()` — resume
content, file names and LLM output can contain `<`, `&` or quotes.
"""

from html import escape
from pathlib import Path
from typing import Iterable, Optional, Tuple

import streamlit as st


def esc(value) -> str:
    return escape(str(value if value is not None else ""), quote=True)


def html(markup: str) -> None:
    """Render a block of trusted markup (built with esc() for any user data)."""
    st.html(markup)


def load_global_css() -> None:
    css_path = Path(__file__).resolve().parent.parent / "assets" / "styles.css"
    try:
        st.html(f"<style>{css_path.read_text(encoding='utf-8')}</style>")
    except FileNotFoundError:
        pass


# --------------------------------------------------------------------------
# Score bands — thresholds mirror backend/services/ats_scorer.py
# _generate_score_interpretation(), so the label always agrees with the text.
# --------------------------------------------------------------------------

def score_band(score: float) -> Tuple[str, str]:
    """Return (label, tone) where tone is one of green / ochre / red."""
    if score >= 90:
        return "Excellent", "green"
    if score >= 80:
        return "Great", "green"
    if score >= 70:
        return "Good", "green"
    if score >= 60:
        return "Fair", "ochre"
    if score >= 50:
        return "Below average", "red"
    return "Poor", "red"


def normalize_severity(level: Optional[str]) -> str:
    """Backend emits High / Moderate / Low; older code used critical/medium."""
    value = (level or "low").strip().lower()
    if value in ("critical", "high", "severe"):
        return "high"
    if value in ("moderate", "medium"):
        return "medium"
    return "low"


SEVERITY_LABEL = {"high": "High priority", "medium": "Medium priority", "low": "Low priority"}
SEVERITY_BADGE = {"high": ":red-badge[High]", "medium": ":orange-badge[Medium]", "low": ":green-badge[Low]"}


def page_head(title: str, lede: str = "") -> None:
    lede_html = f'<p class="rs-lede">{esc(lede)}</p>' if lede else ""
    html(f'<div class="rs-pagehead"><h1 class="rs-h1">{esc(title)}</h1>{lede_html}</div>')


def section_head(title: str, body: str = "", tight: bool = False) -> None:
    cls = "rs-section rs-section--tight" if tight else "rs-section"
    body_html = f'<p class="rs-body">{esc(body)}</p>' if body else ""
    html(f'<div class="{cls}"><h2 class="rs-h2">{esc(title)}</h2>{body_html}</div>')


def chips(items: Iterable[str], kind: str = "") -> str:
    cls = f"rs-chip rs-chip--{kind}" if kind else "rs-chip"
    return '<div class="rs-chips">' + "".join(
        f'<span class="{cls}">{esc(item)}</span>' for item in items
    ) + "</div>"


def bullet_list(items: Iterable[str], kind: str = "plain") -> str:
    return f'<ul class="rs-list rs-list--{kind}">' + "".join(
        f"<li>{esc(item)}</li>" for item in items
    ) + "</ul>"


def notice(text_html: str, tone: str = "") -> None:
    cls = f"rs-notice rs-notice--{tone}" if tone else "rs-notice"
    html(f'<div class="{cls}"><p>{text_html}</p></div>')


def footer() -> None:
    html(
        '<div class="rs-footer">'
        "<span>ATS Resume Scorer</span>"
        "<span>Scores are guidance from automated checks, not a hiring decision.</span>"
        "</div>"
    )
