"""History page: every saved analysis, the score trend, and per-entry actions."""

import base64
from typing import Any, Dict, List

import requests
import streamlit as st

from frontend import navigation
from frontend.components.report_sections import COMPONENTS
from frontend.components.ui import bullet_list, esc, footer, html, notice, page_head, score_band
from frontend.services import store, theme
from frontend.services.errors import describe_backend_error
from frontend.services.session import format_when, is_signed_in, open_report


SHORT_LABELS = ["Format", "Keywords", "Content", "Evidence", "Safety"]


def _trend_svg(scores: List[float], labels: List[str]) -> str:
    """Score over time, oldest on the left. Bands at 50 and 70 match the score labels."""
    w, h, pad_l, pad_r, pad_t, pad_b = 1000, 170, 34, 16, 12, 26
    inner_w, inner_h = w - pad_l - pad_r, h - pad_t - pad_b

    def x(i):
        return pad_l + (inner_w * i / (len(scores) - 1) if len(scores) > 1 else inner_w / 2)

    def y(v):
        return pad_t + inner_h * (1 - max(0, min(100, v)) / 100)

    grid = ""
    for v in (0, 50, 70, 100):
        dash = "" if v in (0, 100) else 'stroke-dasharray="4 5"'
        grid += (
            f'<line x1="{pad_l}" x2="{w - pad_r}" y1="{y(v):.1f}" y2="{y(v):.1f}" '
            f'stroke="#D3D8E0" stroke-width="1" {dash}/>'
            f'<text x="{pad_l - 8}" y="{y(v) + 4:.1f}" text-anchor="end" font-size="12" fill="#7D8597">{v}</text>'
        )
    points = " ".join(f"{x(i):.1f},{y(s):.1f}" for i, s in enumerate(scores))
    dots = ""
    for i, s in enumerate(scores):
        last = i == len(scores) - 1
        dots += (
            f'<circle cx="{x(i):.1f}" cy="{y(s):.1f}" r="{7 if last else 4.5}" '
            f'fill="{"#FFE04A" if last else "#18213A"}" stroke="#18213A" stroke-width="{2.5 if last else 0}"'
            "/>"
        )
    ends = (
        f'<text x="{pad_l}" y="{h - 4}" font-size="12" fill="#7D8597">{esc(labels[0])}</text>'
        f'<text x="{w - pad_r}" y="{h - 4}" text-anchor="end" font-size="12" fill="#7D8597">{esc(labels[-1])}</text>'
        if len(labels) > 1 else ""
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        'font-family="Schibsted Grotesk, system-ui, sans-serif">'
        f"{grid}"
        f'<polyline points="{points}" fill="none" stroke="#18213A" stroke-width="2.25" stroke-linejoin="round"/>'
        f"{dots}{ends}</svg>"
    )
    # st.html sanitises inline <svg>, so the chart is embedded as an image.
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    summary = ", ".join(f"{lab} {sc:.0f}" for lab, sc in zip(labels, scores))
    return (f'<img class="rs-trend__chart" src="data:image/svg+xml;base64,{encoded}" '
            f'alt="ATS score over time: {esc(summary)}">')


def _trend(history: List[Dict[str, Any]]) -> None:
    ordered = list(reversed(history))  # API returns newest first
    scores = [float(e.get("ats_score", 0) or 0) for e in ordered]
    labels = [format_when(e.get("created_at")).split(",")[0] for e in ordered]

    best = max(scores)
    latest = scores[-1]
    change_html = ""
    if len(scores) > 1:
        delta = latest - scores[-2]
        cls = "up" if delta > 0 else "down" if delta < 0 else ""
        sign = "+" if delta > 0 else ""
        change_html = (
            f'<div><div class="rs-stat__v {cls}">{sign}{delta:.0f}</div>'
            '<div class="rs-stat__l">Change since the previous check</div></div>'
        )

    html(
        '<div class="rs-trend"><div class="rs-trend__head">'
        f'<div><div class="rs-stat__v">{latest:.0f}</div><div class="rs-stat__l">Latest score</div></div>'
        f"{change_html}"
        f'<div><div class="rs-stat__v">{best:.0f}</div><div class="rs-stat__l">Best so far</div></div>'
        f'<div><div class="rs-stat__v">{len(scores)}</div><div class="rs-stat__l">Checks saved</div></div>'
        "</div>"
        + (_trend_svg(scores, labels) if len(scores) > 1 else
           '<p class="rs-small" style="margin:0">Score another version to start a trend line.</p>')
        + "</div>"
    )


def _row(entry: Dict[str, Any], idx: int) -> None:
    filename = entry.get("filename") or "resume"
    score = float(entry.get("ats_score", 0) or 0)
    when = format_when(entry.get("created_at"))
    analysis = entry.get("analysis_result") or {}
    components = analysis.get("component_scores") or {}
    jd = analysis.get("jd_comparison") or analysis.get("jd_match_analysis")
    entry_id = str(entry.get("id") or "")
    _, tone = score_band(score)

    with st.container(border=True, key=f"hist_{idx}"):
        info, bars, actions = st.columns([3.1, 3.4, 2.3], gap="medium", vertical_alignment="center")
        with info:
            jd_line = (f'<div class="rs-hrow__when">Job post match {float(jd.get("match_percentage", 0)):.0f}%</div>'
                       if jd else '<div class="rs-hrow__when">General check</div>')
            html(
                '<div class="rs-hrow">'
                f'<div class="rs-hrow__score {tone}" aria-label="Score {score:.0f}">{score:.0f}</div>'
                f'<div><div class="rs-hrow__file">{esc(filename)}</div>'
                f'<div class="rs-hrow__when">{esc(when)}</div>{jd_line}</div></div>'
            )
        with bars:
            minis = ""
            for (label, key, max_pts), short in zip(COMPONENTS, SHORT_LABELS):
                v = float(components.get(key, 0) or 0)
                minis += (
                    f'<div><div class="rs-mini__l" title="{esc(label)}">{esc(short)}</div>'
                    f'<div class="rs-mini__t"><i style="width:{min(v / max_pts, 1) * 100:.0f}%"></i></div>'
                    f'<div class="rs-mini__v">{v:.0f}/{max_pts}</div></div>'
                )
            html(f'<div class="rs-minis">{minis}</div>')
        with actions:
            confirm_key = f"confirm_delete_{entry_id}"
            if st.session_state.get(confirm_key):
                html('<p class="rs-small" style="margin:0 0 .4rem;color:#C93A2E">Delete this check for good?</p>')
                with st.container(horizontal=True, gap="small"):
                    if st.button("Delete", type="primary", key=f"del_yes_{idx}"):
                        try:
                            store.delete(entry_id)
                            st.session_state.pop(confirm_key, None)
                            st.session_state.pop("history_cache", None)
                            st.toast(f"Deleted {filename}")
                            st.rerun()
                        except requests.RequestException as exc:
                            notice(esc(describe_backend_error(exc)), "red")
                        except Exception as exc:
                            notice(f"Couldn't delete it. {esc(exc)}", "red")
                    if st.button("Keep", key=f"del_no_{idx}"):
                        st.session_state.pop(confirm_key, None)
                        st.rerun()
            else:
                with st.container(horizontal=True, gap="small", horizontal_alignment="right"):
                    if st.button("Open report", key=f"open_{idx}", disabled=not analysis):
                        open_report(analysis, filename, source="history",
                                    created_at=entry.get("created_at"), history_id=entry_id or None)
                        navigation.go("report")
                    if entry_id and st.button("Delete", type="tertiary", key=f"del_{idx}"):
                        st.session_state[confirm_key] = True
                        st.rerun()


def _issue_titles(entry: Dict[str, Any]) -> List[str]:
    analysis = entry.get("analysis_result") or {}
    titles = [str(i.get("issue_title", "")).strip() for i in analysis.get("detailed_feedback") or []]
    return [t for t in titles if t]


def _compare(history: List[Dict[str, Any]]) -> None:
    """Pick two checks and see what changed between them."""
    labels = {
        str(e.get("id")): f"{e.get('filename') or 'resume'} ({format_when(e.get('created_at'))}, "
                          f"{float(e.get('ats_score', 0) or 0):.0f})"
        for e in history
    }
    ids = list(labels)
    with st.expander("Compare two versions", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            old_id = st.selectbox("Earlier version", ids, index=min(1, len(ids) - 1),
                                  format_func=labels.get, key="cmp_old")
        with c2:
            new_id = st.selectbox("Later version", ids, index=0, format_func=labels.get, key="cmp_new")
        if old_id == new_id:
            html('<p class="rs-small">Pick two different checks to compare.</p>')
            return
        old = next(e for e in history if str(e.get("id")) == old_id)
        new = next(e for e in history if str(e.get("id")) == new_id)
        oc = (old.get("analysis_result") or {}).get("component_scores") or {}
        nc = (new.get("analysis_result") or {}).get("component_scores") or {}

        def cls(d):
            return "up" if d > 0.4 else "down" if d < -0.4 else "same"

        def fmt(d):
            return f"+{d:.0f}" if d > 0.4 else (f"{d:.0f}" if d < -0.4 else "0")

        rows = ['<div class="rs-delta-row head"><span>Check</span><span>Before</span><span>After</span><span>Change</span></div>']
        o_total = float(old.get("ats_score", 0) or 0)
        n_total = float(new.get("ats_score", 0) or 0)
        rows.append(
            f'<div class="rs-delta-row"><b>Overall</b><span>{o_total:.0f}</span><span>{n_total:.0f}</span>'
            f'<span class="{cls(n_total - o_total)}">{fmt(n_total - o_total)}</span></div>'
        )
        for label, key, max_pts in COMPONENTS:
            o, n = float(oc.get(key, 0) or 0), float(nc.get(key, 0) or 0)
            rows.append(
                f'<div class="rs-delta-row"><span>{esc(label)}</span><span>{o:.0f}/{max_pts}</span>'
                f'<span>{n:.0f}/{max_pts}</span><span class="{cls(n - o)}">{fmt(n - o)}</span></div>'
            )
        fixed = [t for t in _issue_titles(old) if t not in _issue_titles(new)]
        added = [t for t in _issue_titles(new) if t not in _issue_titles(old)]
        lists = '<div class="rs-cols" style="margin-top:1.5rem">'
        lists += '<div><div class="rs-h3">Fixed since the earlier version</div>' + (
            bullet_list(fixed, "good") if fixed else '<p class="rs-empty-line">Nothing resolved yet.</p>') + "</div>"
        lists += '<div><div class="rs-h3">New in the later version</div>' + (
            bullet_list(added, "bad") if added else '<p class="rs-empty-line">No new issues.</p>') + "</div></div>"
        html(f'<div class="rs-compare">{"".join(rows)}{lists}</div>')


PAGE_SIZE = 5


def _status(score: float):
    if score >= 80:
        return "Excellent", "green"
    if score >= 70:
        return "Good", "blue"
    if score >= 60:
        return "Fair", "ochre"
    return "Needs Improvement", "red"


@st.dialog("Delete this analysis?")
def _confirm_delete(entry_id: str, filename: str) -> None:
    html(f'<p class="rs-body">{esc(filename)} and its report will be removed. This can’t be undone.</p>')
    with st.container(horizontal=True, gap="small"):
        if st.button("Delete", type="primary", key="dlg_del"):
            try:
                store.delete(entry_id)
                st.toast(f"Deleted {filename}")
            except Exception as exc:
                st.error(f"Couldn't delete it. {exc}")
                return
            st.rerun()
        if st.button("Cancel", key="dlg_cancel"):
            st.rerun()


@st.dialog("Clear all history?")
def _confirm_clear(history: List[Dict[str, Any]]) -> None:
    html(f'<p class="rs-body">All {len(history)} saved analyses will be removed. This can’t be undone.</p>')
    with st.container(horizontal=True, gap="small"):
        if st.button("Clear history", type="primary", key="dlg_clear"):
            failed = 0
            for e in history:
                try:
                    store.delete(str(e.get("id")))
                except Exception:
                    failed += 1
            st.session_state["hist_page"] = 1
            st.toast("History cleared" if not failed else f"{failed} couldn't be deleted")
            st.rerun()
        if st.button("Cancel", key="dlg_clear_cancel"):
            st.rerun()


def _table(history: List[Dict[str, Any]]) -> None:
    pages = max(1, (len(history) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(max(1, st.session_state.get("hist_page", 1)), pages)
    rows = history[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]

    html('<div class="rs-thead"><span>Date &amp; Time</span><span>Resume Name</span><span>ATS Score</span>'
         "<span>Status</span><span>Actions</span></div>")
    for idx, e in enumerate(rows):
        score = float(e.get("ats_score", 0) or 0)
        _, tone = score_band(score)
        status, dot = _status(score)
        entry_id = str(e.get("id") or "")
        filename = e.get("filename") or "resume"
        analysis = e.get("analysis_result") or {}
        when = format_when(e.get("created_at")).replace(",", " •")
        with st.container(key=f"hrow_{idx}"):
            c = st.columns([1.6, 2, .9, 1.3, 1.1], gap="medium", vertical_alignment="center")
            c[0].html(f'<span class="rs-when">📅 {esc(when)}</span>')
            c[1].html(f'<span class="rs-file">{esc(filename)}</span>')
            c[2].html(f'<span class="rs-scorepill {tone}">{score:.0f}%</span>')
            c[3].html(f'<span class="rs-status"><i class="{dot}"></i>{status}</span>')
            with c[4]:
                with st.container(horizontal=True, gap="small"):
                    if st.button("", icon=":material/visibility:", key=f"view_{idx}", help="Open report",
                                 disabled=not analysis):
                        open_report(analysis, filename, source="history",
                                    created_at=e.get("created_at"), history_id=entry_id or None)
                        navigation.go("report")
                    if analysis and store.can_pdf():
                        st.download_button(
                            "", data=lambda a=analysis, i=entry_id: store.pdf(a, i), icon=":material/download:",
                            file_name=f"ats_report_{filename.rsplit('.', 1)[0]}.pdf", mime="application/pdf",
                            key=f"dl_{idx}", help="Download PDF report", on_click="ignore",
                        )
                    if entry_id and st.button("", icon=":material/delete:", key=f"del_{idx}", help="Delete"):
                        _confirm_delete(entry_id, filename)

    if pages > 1:
        with st.container(horizontal=True, horizontal_alignment="center", gap="small", key="pager"):
            if st.button("Previous", icon=":material/arrow_back:", disabled=page == 1, key="pg_prev"):
                st.session_state["hist_page"] = page - 1
                st.rerun()
            for n in range(1, pages + 1):
                if st.button(str(n), type="primary" if n == page else "secondary", key=f"pg_{n}"):
                    st.session_state["hist_page"] = n
                    st.rerun()
            if st.button("Next", icon=":material/arrow_forward:", icon_position="right",
                         disabled=page == pages, key="pg_next"):
                st.session_state["hist_page"] = page + 1
                st.rerun()


def _render_clarity(history: List[Dict[str, Any]]) -> None:
    with st.container(horizontal=True, vertical_alignment="center"):
        html('<div class="rs-pagehead" style="margin:0"><h1 class="rs-h1">🕒 Your Analysis History</h1>'
             '<p class="rs-lede">Track your previous resume analyses</p></div>')
        st.space("stretch")
        if history and st.button("Clear History", icon=":material/delete_sweep:", key="clear_hist"):
            _confirm_clear(history)
    st.space("small")
    if store.history_kind() == "guest" and history:
        notice("<strong>These checks live in this tab only.</strong> Download the PDF of any report you want to keep.")
    if not history:
        html('<div class="rs-empty"><h2 class="rs-h2">No analyses yet</h2>'
             '<p class="rs-body">Score your resume once and it will appear here. Score it again after '
             "editing to see the change.</p></div>")
        if st.button("Analyze a resume", type="primary", key="hist_score_c"):
            navigation.go("home")
        footer()
        return
    _table(history)
    html('<div class="rs-section rs-section--tight"><h2 class="rs-h2">📈 Score trend</h2></div>')
    _trend(history)
    if len(history) > 1:
        _compare(history)
    footer()


def render() -> None:
    if not theme.uses_sidebar():
        page_head("History", "Every resume you've scored. Open one to see its full report, or compare two versions.")

    if store.engine_mode() == "remote" and not is_signed_in():
        html(
            '<div class="rs-empty"><h2 class="rs-h2">Sign in to see your history</h2>'
            '<p class="rs-body">Checks you run while signed in are saved here with their scores, '
            "so you can see whether each edit moved the number.</p></div>"
        )
        if st.button("Sign in", type="primary", key="hist_signin"):
            navigation.go("account")
        footer()
        return

    try:
        history = store.history()
    except requests.RequestException as exc:
        notice(esc(describe_backend_error(exc)), "red")
        footer()
        return
    except Exception as exc:
        notice(f"History couldn't be loaded. {esc(exc)}", "red")
        footer()
        return

    if theme.uses_sidebar():
        _render_clarity(history)
        return

    if store.history_kind() == "guest" and history:
        notice("<strong>These checks live in this tab only.</strong> Close it and they’re gone"
               + (", so sign in if you want to keep them." if store.accounts_enabled() else ". Download the PDF of any report you want to keep."))

    if not history:
        mascot = (f'<img src="{theme.art("scout-search")}" alt="" style="width:120px;float:right;margin:-.5rem 0 0 1rem">'
                  if theme.show_mascot() else "")
        html(
            f'<div class="rs-empty">{mascot}<h2 class="rs-h2">No checks saved yet</h2>'
            '<p class="rs-body">Score your resume once and it will appear here. Score it again after '
            'editing to see the change.</p><div style="clear:both"></div></div>'
        )
        if st.button("Score a resume", type="primary", key="hist_score"):
            navigation.go("analyze")
        footer()
        return

    _trend(history)
    if len(history) > 1:
        _compare(history)
    for idx, entry in enumerate(history):
        _row(entry, idx)
    footer()
