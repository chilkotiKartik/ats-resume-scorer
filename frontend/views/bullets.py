"""Bullet Lab: paste bullets, get an instant score and a fix for each one."""

import streamlit as st

from frontend import navigation
from frontend.components.ui import esc, footer, html, score_band
from frontend.services import theme
from frontend.services.bullet_checker import check, split_bullets

EXAMPLES = """Responsible for building the backend of the campus events app
Built a FastAPI backend serving 5,000 requests a day, cutting page load time from 3.1 s to 0.8 s
Worked on various dashboards for the sales team
Led a team of 4 to launch a recommendation feature that raised repeat orders by 12%
I helped with data cleaning and other tasks"""


def _fill_examples() -> None:
    st.session_state["bullet_text"] = EXAMPLES


def render() -> None:
    mascot = (f'<img src="{theme.art("scout-highlight")}" alt="" '
              'style="width:118px;float:right;margin:-1rem 0 0 1rem">' if theme.show_mascot() else "")
    html(
        f'<div class="rs-pagehead">{mascot}<h1 class="rs-h1">Bullet Lab</h1>'
        '<p class="rs-lede">Paste your experience or project bullets, one per line. Each gets an instant '
        "score out of 100 and the single change that would improve it most. Nothing is uploaded or saved.</p>"
        '<div style="clear:both"></div></div>'
    )

    st.text_area(
        "Your bullets", key="bullet_text", height=190,
        placeholder="Built a churn model in Python that flagged 1,200 at-risk customers a month…",
    )
    with st.container(horizontal=True, gap="small"):
        st.button("Try with examples", on_click=_fill_examples, key="bl_examples")
        if st.button("Score a full resume", type="tertiary", key="bl_full"):
            navigation.go("analyze")

    bullets = split_bullets(st.session_state.get("bullet_text", ""))
    if not bullets:
        html('<p class="rs-empty-line">Results appear here once you click outside the box or press Ctrl+Enter.</p>')
        footer()
        return

    reports = [check(b) for b in bullets]
    avg = sum(r.score for r in reports) / len(reports)
    strong = sum(1 for r in reports if r.score >= 80)
    html(
        '<div class="rs-trend" style="margin-top:1.5rem"><div class="rs-trend__head" style="margin:0">'
        f'<div><div class="rs-stat__v">{avg:.0f}</div><div class="rs-stat__l">Average bullet score</div></div>'
        f'<div><div class="rs-stat__v">{strong} of {len(reports)}</div><div class="rs-stat__l">Bullets scoring 80+</div></div>'
        "</div></div>"
    )

    cards = []
    for r in sorted(reports, key=lambda r: r.score):
        _, tone = score_band(r.score)
        pills = "".join(
            f'<span class="rs-check {"ok" if ok else "no"}">{"✓" if ok else "✗"} {esc(label)}</span>'
            for label, ok in r.checks
        )
        cards.append(
            '<div class="rs-bullet">'
            f'<div class="rs-bullet__score {tone}" aria-label="Score {r.score}">{r.score}</div>'
            f'<div><p class="rs-bullet__text">{esc(r.text)}</p><div class="rs-checks">{pills}</div>'
            f'<p class="rs-tip"><b>Next fix:</b> {esc(r.tip)}</p></div></div>'
        )
    html('<div class="rs-h3" style="margin:1rem 0 .75rem">Weakest first</div>' + "".join(cards))
    footer()
