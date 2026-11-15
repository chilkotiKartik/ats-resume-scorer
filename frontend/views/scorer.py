"""Analyze page: choose a mode, add the resume (and job post), run the check."""

import requests
import streamlit as st

from frontend import navigation
from frontend.components.ui import esc, footer, html, notice, page_head
from frontend.services import store, theme
from frontend.services.errors import describe_backend_error
from frontend.services.sample_report import SAMPLE_ANALYSIS, SAMPLE_FILENAME
from frontend.services.session import is_signed_in, open_report

MODES = ["Resume only", "Resume + job post"]
MAX_RESUME_MB = 5  # backend/core/config.py MAX_FILE_SIZE_MB


def _step(n: int, title: str, hint: str, off: bool = False) -> None:
    html(
        f'<div class="rs-stephead{" rs-stephead--off" if off else ""}">'
        f'<span class="rs-stephead__n">{n}</span><span class="rs-stephead__t">{esc(title)}</span></div>'
        f'<p class="rs-stephead__hint">{esc(hint)}</p>'
    )


def _read_jd(jd_file, jd_text: str) -> str:
    """JD as plain text. .txt files are decoded here; other formats should be pasted."""
    if jd_text and jd_text.strip():
        return jd_text.strip()
    if jd_file is None:
        return ""
    return jd_file.getvalue().decode("utf-8", errors="ignore").strip()


def _access_notice() -> bool:
    """Explain who can run a check here. Returns False when the user must sign in first."""
    if store.engine_mode() == "remote" and not is_signed_in():
        notice(
            "<strong>Sign in to run a check.</strong> Results are saved to your account so you can "
            "compare versions of your resume later."
        )
        with st.container(horizontal=True, gap="small"):
            if st.button("Sign in or create an account", type="primary", key="an_signin"):
                navigation.go("account")
            if st.button("See a sample report first", key="an_sample"):
                open_report(SAMPLE_ANALYSIS, SAMPLE_FILENAME, source="sample", with_jd=True)
                navigation.go("report")
        st.space("medium")
        return False

    if not is_signed_in():
        mascot = f'<img src="{theme.art("scout-wave")}" alt="">' if theme.show_mascot() else ""
        account_line = (" Sign in to keep them for good." if store.accounts_enabled() else "")
        html(
            f'<div class="rs-notice"><div class="rs-guest">{mascot}<p><strong>No account needed.</strong> '
            "Checks you run now are kept in History until you close this tab."
            f"{esc(account_line)}</p></div></div>"
        )
    return True


def render() -> None:
    page_head(
        "Score a resume",
        "Takes 10 to 30 seconds. You'll get the score, the issues ranked by impact, and a checklist of fixes.",
    )

    allowed = _access_notice()

    # ---- 1. Mode ----------------------------------------------------------
    _step(1, "Choose what to compare",
          "A job post makes the check specific: you'll see which of its keywords you cover.")
    if st.session_state.get("analyze_mode") not in MODES:
        st.session_state["analyze_mode"] = MODES[1]
    mode = st.segmented_control(
        "Check type", MODES, key="analyze_mode", required=True, label_visibility="collapsed",
    )
    with_jd = mode == MODES[1]
    st.space("small")

    left, right = st.columns(2, gap="large")

    # ---- 2. Resume ----------------------------------------------------------
    with left:
        _step(2, "Add your resume", f"PDF, DOC or DOCX, up to {MAX_RESUME_MB} MB. Text must be selectable, not a scan.")
        resume_file = st.file_uploader(
            "Resume file", type=["pdf", "doc", "docx"], key="resume_upload", label_visibility="collapsed",
        )
        too_big = False
        if resume_file and resume_file.size > MAX_RESUME_MB * 1024 * 1024:
            too_big = True
            notice(f"<strong>{esc(resume_file.name)} is {resume_file.size / 1048576:.1f} MB.</strong> "
                   f"The limit is {MAX_RESUME_MB} MB. Export it again without images.", "red")

    # ---- 3. Job post ----------------------------------------------------------
    jd_file, jd_text = None, ""
    with right:
        if with_jd:
            _step(3, "Add the job post", "Paste the full description, including requirements and responsibilities.")
            method = st.segmented_control(
                "Job post input", ["Paste text", "Upload .txt"], default="Paste text",
                key="jd_input_method", label_visibility="collapsed",
            )
            if method == "Upload .txt":
                jd_file = st.file_uploader("Job post file", type=["txt"], key="jd_upload",
                                           label_visibility="collapsed")
            else:
                jd_text = st.text_area(
                    "Job post text", height=228, key="jd_text", label_visibility="collapsed",
                    placeholder="We're hiring a Data Analyst to join our growth team…",
                )
                words = len(jd_text.split())
                if words:
                    html(f'<p class="rs-small" style="margin-top:-.4rem">{words} words</p>')
        else:
            _step(3, "Add the job post", "Skipped. Switch to “Resume + job post” above to include one.", off=True)

    # ---- Run --------------------------------------------------------------------
    job_description = _read_jd(jd_file, jd_text) if with_jd else ""
    missing = []
    if not allowed:
        missing.append("sign in")
    if not resume_file or too_big:
        missing.append("add a resume")
    if with_jd and not job_description:
        missing.append("add the job post")

    html('<div class="rs-runbar"></div>')
    with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
        run = st.button("Score my resume", type="primary", disabled=bool(missing), key="run")
        if missing:
            html(f'<p class="rs-small" style="margin:0">To start, {esc(" and ".join(missing))}.</p>')

    if not run:
        footer()
        return

    run_analysis(resume_file, job_description, with_jd)
    footer()


def run_analysis(resume_file, job_description: str, with_jd: bool) -> None:
    """Score the file, then open the Report page. Shows progress and errors in place."""
    waiting = st.empty()
    mascot = (f'<img src="{theme.art("scout-think")}" alt="" style="width:84px">'
              if theme.show_mascot() else "")
    first_run = store.engine_mode() == "local" and not st.session_state.get("_engine_warm")
    extra = " The first check after the app wakes up also loads the language models, so it can take a minute." \
        if first_run else ""
    waiting.html(
        f'<div class="rs-wait" role="status">{mascot}<div class="rs-wait__bar"></div>'
        "<span>Reading your resume and checking it against "
        f"{'the job post' if with_jd else 'common ATS rules'}…{esc(extra)}</span></div>"
    )
    try:
        result = store.analyze(resume_file, job_description)
    except requests.RequestException as exc:
        waiting.empty()
        notice(esc(describe_backend_error(exc)), "red")
        return
    except Exception as exc:  # EngineError and anything unexpected from the pipeline
        waiting.empty()
        notice(f"<strong>That didn't work.</strong> {esc(exc)}", "red")
        return

    st.session_state["_engine_warm"] = True
    waiting.empty()
    open_report(result["analysis"], resume_file.name, source="new", with_jd=with_jd,
                history_id=result.get("history_id"))
    navigation.go("report")
