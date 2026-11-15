"""Home page for the Clarity theme: greeting, quick analyze, progress and shortcuts."""

from datetime import datetime

import streamlit as st

from frontend import navigation
from frontend.components.ui import esc, footer, html, score_band
from frontend.services import store
from frontend.services.sample_report import SAMPLE_ANALYSIS, SAMPLE_FILENAME
from frontend.services.session import format_when, is_signed_in, open_report
from frontend.views.scorer import MAX_RESUME_MB, run_analysis


def _first_name() -> str:
    email = st.session_state.get("user_email") or ""
    local = email.split("@")[0].replace(".", " ").replace("_", " ").split()
    return local[0].capitalize() if local else ""


def _safe_history():
    try:
        return store.history()
    except Exception:
        return []


def _notifications(history) -> None:
    with st.popover("", icon=":material/notifications:", key="bell"):
        html('<div class="rs-h3" style="margin-bottom:.5rem">What’s new</div>')
        items = [
            ("🧪", "Bullet Lab scores single bullets instantly. Try it before editing the whole resume."),
            ("🎨", "Four themes now: Clarity, Toon, Paper and Midnight. Switch from the sidebar."),
            ("📄", "Resources has ATS-friendly resume templates you can download as Word files."),
        ]
        if history:
            best = max(float(e.get("ats_score", 0) or 0) for e in history)
            items.insert(0, ("🏆", f"Your best score so far is {best:.0f}. Compare versions in History."))
        html("".join(
            f'<div style="display:flex;gap:.6rem;padding:.55rem 0;border-top:1px solid var(--rule)">'
            f'<span style="font-size:1.1rem">{icon}</span><span style="font-size:.9rem;color:var(--graphite)">{esc(text)}</span></div>'
            for icon, text in items
        ))


def render() -> None:
    history = _safe_history()

    with st.container(horizontal=True, vertical_alignment="center"):
        html(f'<span class="rs-small">{datetime.now().strftime("%A, %d %B %Y")}</span>')
        st.space("stretch")
        _notifications(history)

    name = _first_name()
    greeting = f"Hello, {esc(name)}!" if name and is_signed_in() else "Hello there!"
    html(
        '<div class="rs-banner">'
        f'<div><h1>{greeting} <span class="rs-wave">👋</span></h1>'
        "<p>Your AI-powered resume analyzer for a better career. Upload a resume, add the job post, "
        "and see exactly what to fix.</p></div>"
        '<img src="app/static/art/banner.svg" alt="">'
        "</div>"
    )
    st.space("small")

    left, right = st.columns(2, gap="medium")
    with left:
        with st.container(key="card_upload"):
            html('<div class="rs-cardhead"><span class="ic">📄</span><b>Upload Resume</b></div>'
                 f'<p class="rs-cardsub">Upload your resume (PDF, DOC or DOCX, up to {MAX_RESUME_MB} MB)</p>')
            resume_file = st.file_uploader("Resume", type=["pdf", "doc", "docx"], key="home_resume",
                                           label_visibility="collapsed")
    with right:
        with st.container(key="card_jd"):
            html('<div class="rs-cardhead"><span class="ic">💼</span><b>Job Description</b></div>'
                 '<p class="rs-cardsub">Paste the job description here (optional, enables keyword match)</p>')
            jd = st.text_area("Job description", key="home_jd", height=150, max_chars=5000,
                              placeholder="Enter job description…", label_visibility="collapsed")

    too_big = bool(resume_file and resume_file.size > MAX_RESUME_MB * 1024 * 1024)
    blocked = not store.can_analyze()
    disabled = not resume_file or too_big or blocked
    with st.container(key="hero_run"):
        clicked = st.button("Analyze Resume ✨", type="primary", disabled=disabled, key="home_run")
    if blocked:
        html('<p class="rs-small" style="text-align:center">Sign in to run a check.</p>')
    elif too_big:
        html(f'<p class="rs-small" style="text-align:center;color:var(--redpen)">That file is over {MAX_RESUME_MB} MB.</p>')
    elif not resume_file:
        html('<p class="rs-small" style="text-align:center">Add a resume to start. The job post is optional.</p>')
    if clicked and resume_file:
        run_analysis(resume_file, (jd or "").strip(), with_jd=bool((jd or "").strip()))

    # ---- Progress -------------------------------------------------------------
    if history:
        scores = [float(e.get("ats_score", 0) or 0) for e in history]
        latest, best = scores[0], max(scores)
        delta = latest - scores[1] if len(scores) > 1 else 0
        cls = "up" if delta > 0 else "down" if delta < 0 else ""
        html(
            '<div class="rs-section rs-section--tight"><h2 class="rs-h2">Your progress</h2></div>'
            '<div class="rs-tiles">'
            f'<div class="rs-tile"><div class="v">{latest:.0f}</div><div class="l">Latest score</div>'
            f'<div class="bar"><i style="width:{latest:.0f}%"></i></div></div>'
            f'<div class="rs-tile"><div class="v">{best:.0f}</div><div class="l">Best score</div>'
            f'<div class="bar"><i style="width:{best:.0f}%"></i></div></div>'
            f'<div class="rs-tile"><div class="v {cls}">{"+" if delta > 0 else ""}{delta:.0f}</div>'
            '<div class="l">Change since last check</div></div>'
            f'<div class="rs-tile"><div class="v">{len(history)}</div><div class="l">Checks saved</div></div>'
            "</div>"
        )
        rows = ""
        for e in history[:3]:
            score = float(e.get("ats_score", 0) or 0)
            band, tone = score_band(score)
            rows += (
                '<div class="rs-barrow" style="grid-template-columns:minmax(0,2fr) 1.2fr 4rem">'
                f'<span><b>{esc(e.get("filename") or "resume")}</b><br><small class="rs-small">{esc(format_when(e.get("created_at")))}</small></span>'
                f'<span class="rs-status"><i class="{tone}"></i>{esc(band)}</span>'
                f'<em><span class="rs-scorepill {tone}">{score:.0f}%</span></em></div>'
            )
        with st.container(key="card_recent"):
            html(f'<div class="rs-cardtitle"><b>🕒 Recent analyses</b></div><div class="rs-bars">{rows}</div>')
            if st.button("View all history", type="tertiary", icon=":material/arrow_forward:",
                         icon_position="right", key="home_hist"):
                navigation.go("history")

    # ---- Explore ----------------------------------------------------------------
    html('<div class="rs-section rs-section--tight"><h2 class="rs-h2">Explore</h2></div>')
    c1, c2, c3 = st.columns(3, gap="medium")
    cards = [
        (c1, "res_tips", "icon-tips", "Bullet Lab", "Score single bullets and get the one fix that helps most.", "bullets"),
        (c2, "res_guide", "icon-guide", "Resources", "ATS guide, interview prep and downloadable resume templates.", "guide"),
        (c3, "res_templates", "icon-templates", "Sample report", "See a finished report before you upload anything.", "sample"),
    ]
    for col, key, icon, title, text, target in cards:
        with col:
            with st.container(key=f"{key}_home"):
                html(f'<div class="rs-rescard"><img src="app/static/art/{icon}.svg" alt=""><b>{title}</b><p>{esc(text)}</p></div>')
                if st.button("Open", type="tertiary", icon=":material/arrow_forward:", icon_position="right",
                             key=f"open_{target}"):
                    if target == "sample":
                        open_report(SAMPLE_ANALYSIS, SAMPLE_FILENAME, source="sample", with_jd=True)
                        navigation.go("report")
                    navigation.go(target)
    footer()
