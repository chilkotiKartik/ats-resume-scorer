import requests
import streamlit as st

from frontend import navigation
from frontend.components.dashboard import display_results_dashboard
from frontend.components.report_sections import summary_text
from frontend.components.ui import esc, footer, html, notice
from frontend.services import store, theme
from frontend.services.errors import describe_backend_error
from frontend.services.sample_report import SAMPLE_ANALYSIS, SAMPLE_FILENAME
from frontend.services.session import format_when, open_report


def _empty_state() -> None:
    mascot = (f'<img src="{theme.art("scout-search")}" alt="" style="width:120px;float:right;margin:-.5rem 0 0 1rem">'
              if theme.show_mascot() else "")
    html(
        '<div class="rs-pagehead"><h1 class="rs-h1">Report</h1></div>'
        f'<div class="rs-empty">{mascot}<h2 class="rs-h2">No report open</h2>'
        '<p class="rs-body">Score a resume to see its report here, open a past one from History, '
        'or look through the sample first.</p><div style="clear:both"></div></div>'
    )
    with st.container(horizontal=True, gap="small"):
        if st.button("Score a resume", type="primary", key="empty_score"):
            navigation.go("analyze")
        if st.button("Open the sample report", key="empty_sample"):
            open_report(SAMPLE_ANALYSIS, SAMPLE_FILENAME, source="sample", with_jd=True)
            st.rerun()
        if st.button("Go to History", type="tertiary", key="empty_history"):
            navigation.go("history")


def _export_bar(analysis, meta) -> None:
    html('<div class="rs-exportbar"><div><div class="rs-h3">Take it with you</div>'
         '<p class="rs-small" style="margin:0">The PDF has the score, every issue and the action plan.</p></div></div>')

    with st.container(horizontal=True, gap="small"):
        can_pdf = store.can_pdf() and meta.get("source") != "sample"
        if "scorer_pdf_bytes" in st.session_state:
            st.download_button(
                "Download PDF report",
                data=st.session_state["scorer_pdf_bytes"],
                file_name="ats_resume_report.pdf",
                mime="application/pdf",
                type="primary",
                key="download_pdf_report",
            )
        elif st.button("Prepare PDF report", type="primary", disabled=not can_pdf, key="make_pdf"):
            try:
                with st.spinner("Building the PDF…"):
                    pdf = store.pdf(analysis, meta.get("history_id"))
                st.session_state["scorer_pdf_bytes"] = pdf
                st.rerun()
            except requests.RequestException as exc:
                notice(esc(describe_backend_error(exc)), "red")
            except Exception as exc:
                notice(f"The PDF couldn't be built. {esc(exc)}", "red")

        st.download_button(
            "Download summary (.txt)",
            data=summary_text(analysis, meta.get("filename", "")),
            file_name="ats_summary.txt",
            mime="text/plain",
            key="download_summary",
        )
        if st.button("Score another resume", type="tertiary", key="again"):
            navigation.go("analyze")

    if meta.get("source") == "sample":
        html('<p class="rs-small" style="margin-top:.5rem">PDF export is available for your own reports.</p>')
    elif not store.can_pdf():
        html('<p class="rs-small" style="margin-top:.5rem">Sign in to export the PDF report.</p>')


def render() -> None:
    analysis = st.session_state.get("scorer_analysis")
    meta = st.session_state.get("report_meta") or {}
    if not analysis:
        _empty_state()
        footer()
        return

    filename = meta.get("filename") or "Resume"
    mode = "Compared with a job post" if meta.get("with_jd") else "General check, no job post"
    when = format_when(meta.get("created_at"))
    origin = {"history": "From your history", "sample": "Sample report"}.get(meta.get("source"), "")

    meta_bits = [f"<span><b>{esc(mode)}</b></span>"]
    if when and meta.get("source") != "sample":
        meta_bits.append(f"<span>Scored {esc(when)}</span>")
    if origin:
        meta_bits.append(f"<span>{esc(origin)}</span>")

    html(
        '<div class="rs-reporthead"><div>'
        f'<h1 class="rs-h1">{esc(filename)}</h1>'
        f'<div class="rs-meta">{"".join(meta_bits)}</div>'
        "</div></div>"
    )

    if meta.get("source") == "sample":
        notice(
            "<strong>This is a sample.</strong> It shows a data-analyst resume compared with a job post, "
            "so every section has something in it. Your own report has the same layout."
        )

    def _add_jd():
        st.session_state["analyze_mode"] = "Resume + job post"
        navigation.go("analyze")

    display_results_dashboard(analysis, meta.get("report_id", filename), on_add_jd=_add_jd)
    _export_bar(analysis, meta)
    footer()
