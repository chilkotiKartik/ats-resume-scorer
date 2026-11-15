"""
Sections of the Report page. Each function reads the fields it needs straight
from the backend AnalysisResponse dict (or a saved history `analysis_result`).
"""

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from frontend.services import theme
from frontend.components.ui import (
    SEVERITY_BADGE,
    SEVERITY_LABEL,
    bullet_list,
    chips,
    esc,
    html,
    normalize_severity,
    score_band,
)

# Max points per component — matches backend/core/config.py SCORE_WEIGHTS.
COMPONENTS: List[Tuple[str, str, int]] = [
    ("Formatting", "formatting", 20),
    ("Keywords & skills", "keywords", 25),
    ("Content quality", "content", 25),
    ("Skill evidence", "skill_validation", 15),
    ("ATS safety", "ats_compatibility", 15),
]

SEVERITY_ORDER = ["high", "medium", "low"]


def overall_score(analysis: Dict[str, Any]) -> float:
    return float(analysis.get("ATS_score", analysis.get("ats_score", 0)) or 0)


def jd_of(analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return analysis.get("jd_comparison") or analysis.get("jd_match_analysis")


def _clean(text: str) -> str:
    return str(text or "").strip()


# --------------------------------------------------------------------------
# Score card
# --------------------------------------------------------------------------

def display_scorecard(analysis: Dict[str, Any]) -> None:
    if theme.current() == "clarity":
        _scorecard_clarity(analysis)
        return
    score = overall_score(analysis)
    band, tone = score_band(score)
    reading = _clean(analysis.get("interpretation"))
    # The backend opens with the band word ("Good! …"); the badge already says it.
    reading = re.sub(r"^(excellent|great|good|fair|below average|poor)[!.]\s*", "", reading, flags=re.IGNORECASE)
    components = analysis.get("component_scores") or {}

    pcts = []
    for label, key, max_pts in COMPONENTS:
        value = float(components.get(key, 0) or 0)
        pcts.append((value / max_pts if max_pts else 0, label, key, max_pts, value))
    weakest = min(pcts, key=lambda row: row[0]) if pcts else None

    rulers = []
    for pct, label, key, max_pts, value in pcts:
        is_weak = weakest is not None and key == weakest[2] and pct < 0.75
        note = (
            '<div class="rs-ruler__note">Lowest share of points. Start here.</div>' if is_weak else ""
        )
        rulers.append(
            f'<div class="rs-ruler{" rs-ruler--weak" if is_weak else ""}">'
            f'<div class="rs-ruler__row"><span class="rs-ruler__name">{esc(label)}</span>'
            f'<span class="rs-ruler__val"><b>{value:.0f}</b> of {max_pts}</span></div>'
            f'<div class="rs-ruler__track" style="--max:{max_pts}" role="img" '
            f'aria-label="{esc(label)}: {value:.0f} of {max_pts} points">'
            f'<div class="rs-ruler__fill" style="width:{min(max(pct, 0), 1) * 100:.1f}%"></div></div>'
            f"{note}</div>"
        )

    marker = min(max(score, 0), 100)
    extras = ""
    burst = f'<img class="rs-burst" src="{theme.art("burst")}" alt="">' if theme.current() == "toon" else ""
    if score >= 80:
        extras += _confetti()
    if theme.show_mascot():
        extras += (f'<img class="rs-mascot-react rs-pop" src="{theme.art(theme.mascot_for_score(score))}" '
                   f'alt="Scout reacting to your score">')
    html(
        '<div class="rs-scorecard">'
        '<div class="rs-score">'
        f"{extras}"
        f'<div class="rs-score__num" aria-label="Overall score {score:.0f} out of 100">{burst}'
        f'<span class="rs-count" style="--to:{round(score)}" aria-hidden="true"></span><small>/ 100</small></div>'
        f'<span class="rs-band rs-band--{tone}">{esc(band)}</span>'
        f'<p class="rs-score__read">{esc(reading)}</p>'
        f'<div class="rs-score__scale" aria-hidden="true"><i style="left:{marker:.1f}%"></i></div>'
        '<div class="rs-score__ticks" aria-hidden="true"><span style="left:0">0</span><span style="left:50%">50</span>'
        '<span style="left:70%">70</span><span style="left:100%">100</span></div>'
        "</div>"
        '<div class="rs-rulers">'
        '<div class="rs-rulers__head"><span class="rs-h3">Points by check</span>'
        '<span class="rs-small">Each tick is one point</span></div>'
        + "".join(rulers)
        + "</div></div>"
    )


_RING = {"green": "#22C55E", "ochre": "#F59E0B", "red": "#E5484D"}
_CHECK_TEXT = {
    "formatting": ("Clean, parser-friendly structure", "Structure needs work"),
    "keywords": ("Strong keyword match", "Keywords are thin"),
    "content": ("Bullets show real impact", "Bullets need numbers and action verbs"),
    "skill_validation": ("Skills are backed by your work", "Many skills lack evidence"),
    "ats_compatibility": ("Safe for ATS parsing", "Some ATS-unsafe formatting"),
}


def _scorecard_clarity(analysis: Dict[str, Any]) -> None:
    """Clarity layout: ring gauge, summary checks, skills match and insights."""
    from frontend.services import store

    score = overall_score(analysis)
    band, tone = score_band(score)
    jd = jd_of(analysis)
    components = analysis.get("component_scores") or {}
    reading = re.sub(r"^(excellent|great|good|fair|below average|poor)[!.]\s*", "",
                     _clean(analysis.get("interpretation")), flags=re.IGNORECASE)
    pill = f"{band} Match!" if jd and score >= 70 else (f"{band} match" if jd else band)
    icon = "✓" if tone == "green" else "!"

    top_l, top_r = st.columns([1.15, 1], gap="medium")
    with top_l:
        with st.container(key="card_ring"):
            html(
                '<div class="rs-ringcard">'
                + (_confetti() if score >= 80 else "")
                + '<h3>🏆 Your ATS Score is</h3>'
                f'<div class="rs-ringwrap"><div class="rs-ring" style="--pct:{min(max(score, 0), 100):.0f};--ring:{_RING[tone]}"></div>'
                f'<div class="num" aria-label="Score {score:.0f} percent"><span><span class="rs-count" style="--to:{round(score)}"></span><small>%</small></span></div></div>'
                f'<div class="rs-matchpill {tone}"><span>{icon}</span>{esc(pill)}</div>'
                "</div>"
            )
    with top_r:
        with st.container(key="card_summary"):
            items = ""
            for label, key, max_pts in COMPONENTS:
                pct = float(components.get(key, 0) or 0) / max_pts if max_pts else 0
                good, weak = _CHECK_TEXT[key]
                cls, mark, text = ("ok", "✓", good) if pct >= .7 else (("warn", "!", weak) if pct >= .5 else ("bad", "✕", weak))
                items += f'<li><i class="{cls}">{mark}</i><span>{esc(text)} <span class="rs-small">({pct * 100:.0f}%)</span></span></li>'
            html(f'<p class="rs-summaryline">{esc(reading or band)}</p><ul class="rs-checks2">{items}</ul>')

    bot_l, bot_r = st.columns([1.15, 1], gap="medium")
    with bot_l:
        with st.container(key="card_skills"):
            details = analysis.get("skill_validation_details") or {}
            validated = [v for v in details.get("validated") or [] if isinstance(v.get("similarity"), (int, float))]
            rows = ""
            if validated:
                title = "Skills Match"
                pill_val = details.get("validation_pct") or 0
                for v in sorted(validated, key=lambda v: v["similarity"], reverse=True)[:6]:
                    p = max(0, min(1, float(v["similarity"]))) * 100
                    rows += (f'<div class="rs-barrow"><span>{esc(v.get("skill"))}</span>'
                             f'<div class="t"><i style="width:{p:.0f}%"></i></div><em>{p:.0f}%</em></div>')
                note = '<p class="rs-small" style="margin:.6rem 0 0">How strongly each skill is backed by a project or role.</p>'
            else:
                title = "Score breakdown"
                pill_val = score
                weakest = min(COMPONENTS, key=lambda c: float(components.get(c[1], 0) or 0) / c[2])[1]
                for label, key, max_pts in COMPONENTS:
                    p = float(components.get(key, 0) or 0) / max_pts * 100
                    rows += (f'<div class="rs-barrow{" weak" if key == weakest else ""}"><span>{esc(label)}</span>'
                             f'<div class="t"><i style="width:{p:.0f}%"></i></div><em>{p:.0f}%</em></div>')
                note = ""
            if jd:
                pill_val = float(jd.get("match_percentage", 0) or 0)
            html(f'<div class="rs-cardtitle"><b>📊 {title}</b><span class="rs-pill">{float(pill_val):.0f}%</span></div>'
                 f'<div class="rs-bars">{rows}</div>{note}')
    with bot_r:
        with st.container(key="card_insights"):
            insights = []
            for s_ in (analysis.get("suggestions") or [])[:2]:
                insights.append(("ok", "💡", _clean(s_)))
            for s_ in (analysis.get("strengths") or [])[:2]:
                insights.append(("ok", "✓", _clean(s_)))
            missing = (jd or {}).get("missing_keywords") or []
            if missing:
                quoted = ", ".join(f"“{m}”" for m in missing[:2])
                insights.insert(0, ("warn", "!", f"Consider adding keywords like {quoted} if you have that experience."))
            items = "".join(
                f'<li><i class="{cls}">{"✓" if cls == "ok" else "!"}</i><span>{esc(text)}</span></li>'
                for cls, _, text in insights[:4] if text
            ) or '<li><i class="ok">✓</i><span>No extra insights for this resume.</span></li>'
            html(f'<div class="rs-cardtitle"><b>💡 Resume Insights</b></div><ul class="rs-checks2">{items}</ul>')
            meta = st.session_state.get("report_meta") or {}
            if store.can_pdf():
                st.download_button(
                    "Download Detailed Report",
                    data=lambda: store.pdf(analysis, meta.get("history_id")),
                    file_name="ats_resume_report.pdf",
                    mime="application/pdf",
                    type="primary",
                    icon=":material/download:",
                    use_container_width=True,
                    key="dl_detailed",
                    on_click="ignore",
                )
    st.space("medium")


_CONFETTI_COLORS = ["#FFD23F", "#FF5A4E", "#4DA3FF", "#3DDC97", "#7B5CFF", "#FF9DB0"]


def _confetti() -> str:
    """A one-time burst of paper confetti for scores of 80 and up (CSS only)."""
    pieces = []
    for i in range(28):
        left = (i * 37) % 100
        delay = (i % 7) * 0.12
        dx = ((i * 53) % 120) - 60
        rot = 360 + (i * 47) % 360
        color = _CONFETTI_COLORS[i % len(_CONFETTI_COLORS)]
        shape = "border-radius:50%;width:10px;height:10px;" if i % 3 == 0 else ""
        pieces.append(
            f'<i style="left:{left}%;background:{color};animation-delay:{delay:.2f}s;'
            f'--dx:{dx}px;--rot:{rot}deg;{shape}"></i>'
        )
    return f'<div class="rs-confetti" aria-hidden="true">{"".join(pieces)}</div>'


# Where the remaining points are, and what usually earns them.
_WIN_HOW = {
    "formatting": "Use the standard headings, put every role and project in bullet points, fill each section.",
    "keywords": "Add the job post’s exact terms for skills you really have, in Skills and in your bullets.",
    "content": "Open bullets with action verbs and put a number in at least half of them.",
    "skill_validation": "Mention each listed skill in the project or role where you used it.",
    "ats_compatibility": "Drop table layouts and special characters; keep only city and country.",
}


def display_quick_wins(analysis: Dict[str, Any]) -> None:
    components = analysis.get("component_scores") or {}
    gaps = []
    for label, key, max_pts in COMPONENTS:
        missing = max_pts - float(components.get(key, 0) or 0)
        if missing >= 1:
            gaps.append((missing, label, key))
    gaps.sort(reverse=True)
    if not gaps:
        return
    cards = "".join(
        f'<div class="rs-win"><div class="rs-win__pts">+{missing:.0f}</div>'
        f'<div class="rs-win__name">{esc(label)}</div><p class="rs-win__how">{esc(_WIN_HOW[key])}</p></div>'
        for missing, label, key in gaps[:3]
    )
    html(
        '<div class="rs-h3" style="margin-bottom:.75rem">Where your next points are</div>'
        f'<div class="rs-wins">{cards}</div>'
    )


# --------------------------------------------------------------------------
# Summary tab
# --------------------------------------------------------------------------

def display_summary(analysis: Dict[str, Any]) -> None:
    strengths = [_clean(s) for s in (analysis.get("strengths") or []) if _clean(s)]
    flagged: List[str] = []
    for item in (analysis.get("critical_issues") or []) + (analysis.get("issues_summary") or []):
        item = _clean(item)
        if item and item not in flagged:
            flagged.append(item)

    left = '<div><div class="rs-h3">What’s working</div>'
    left += bullet_list(strengths, "good") if strengths else (
        '<p class="rs-empty-line">Nothing stands out yet. The fixes tab shows where to start.</p>'
    )
    left += "</div>"

    right = '<div><div class="rs-h3">What’s holding it back</div>'
    right += bullet_list(flagged, "bad") if flagged else (
        '<p class="rs-empty-line">No issues were flagged on this resume.</p>'
    )
    right += "</div>"

    html(f'<div class="rs-cols">{left}{right}</div>')

    suggestions = [_clean(s) for s in (analysis.get("suggestions") or []) if _clean(s)]
    if suggestions:
        html(
            '<div style="margin-top:2.5rem"><div class="rs-h3">Suggestions for this role</div>'
            + bullet_list(suggestions, "plain")
            + "</div>"
        )

    warnings = [_clean(w) for w in (analysis.get("warnings") or []) if _clean(w)]
    if warnings:
        html(
            '<div style="margin-top:2rem"><div class="rs-h3">Notes from the parser</div>'
            + bullet_list(warnings, "plain")
            + "</div>"
        )


# --------------------------------------------------------------------------
# Fixes tab
# --------------------------------------------------------------------------

def _before_after(example: str) -> str:
    """Show 'Before: … After: …' examples side by side; anything else as one block."""
    match = re.search(r"before:\s*(.*?)\s*after:\s*(.*)", example, flags=re.IGNORECASE | re.DOTALL)
    if match:
        before, after = match.group(1).strip(), match.group(2).strip()
        return (
            '<div class="rs-ba">'
            f'<div class="rs-ba__col rs-ba__col--before"><div class="rs-ba__label">Before</div>'
            f'<p class="rs-ba__text">{esc(before)}</p></div>'
            f'<div class="rs-ba__col rs-ba__col--after"><div class="rs-ba__label">After</div>'
            f'<p class="rs-ba__text">{esc(after)}</p></div></div>'
        )
    return (
        '<div class="rs-ba" style="grid-template-columns:1fr">'
        '<div class="rs-ba__col rs-ba__col--after"><div class="rs-ba__label">Example</div>'
        f'<p class="rs-ba__text">{esc(example)}</p></div></div>'
    )


def _md_safe(text: str) -> str:
    return re.sub(r"([\[\]*_`#|])", r"\\\1", text)


def display_fixes(analysis: Dict[str, Any]) -> None:
    issues = analysis.get("detailed_feedback") or []
    if not issues:
        html('<p class="rs-empty-line">No detailed issues were found for this resume.</p>')
        return

    grouped: Dict[str, List[Dict[str, Any]]] = {level: [] for level in SEVERITY_ORDER}
    for issue in issues:
        grouped[normalize_severity(issue.get("severity_level"))].append(issue)

    for level in SEVERITY_ORDER:
        items = grouped[level]
        if not items:
            continue
        html(
            f'<div class="rs-sevhead"><i class="rs-sevdot rs-sevdot--{level}"></i>'
            f"<span>{SEVERITY_LABEL[level]}</span><em>{len(items)} issue{'s' if len(items) != 1 else ''}</em></div>"
        )
        for issue in items:
            title = _clean(issue.get("issue_title")) or "Untitled issue"
            with st.expander(f"{SEVERITY_BADGE[level]} {_md_safe(title)}", expanded=False):
                rows = []
                for label, key in (
                    ("What’s happening", "explanation"),
                    ("Where", "where_it_appears"),
                    ("How to fix", "how_to_fix"),
                    ("Effect on screening", "ats_impact"),
                ):
                    value = _clean(issue.get(key))
                    if value:
                        rows.append(f"<dt>{label}</dt><dd>{esc(value)}</dd>")
                body = f'<dl class="rs-kv">{"".join(rows)}</dl>' if rows else ""
                actions = [_clean(a) for a in (issue.get("action_items") or []) if _clean(a)]
                if actions:
                    body += '<div class="rs-h3" style="margin-top:1rem">Steps</div>' + bullet_list(actions, "plain")
                example = _clean(issue.get("example_improvement"))
                if example:
                    body += '<div class="rs-h3" style="margin-top:1.25rem">Rewrite example</div>' + _before_after(example)
                html(body)


# --------------------------------------------------------------------------
# Skills tab
# --------------------------------------------------------------------------

def display_skills(analysis: Dict[str, Any]) -> None:
    details = analysis.get("skill_validation_details") or {}
    validated = details.get("validated") or []
    unvalidated = details.get("unvalidated") or []
    total = int(details.get("total") or (len(validated) + len(unvalidated)))
    pct = float(details.get("validation_pct") or (len(validated) / total * 100 if total else 0))

    if total == 0:
        html('<p class="rs-empty-line">No skills were detected on this resume. '
             "Add a Skills section with the tools you use.</p>")
        return

    html(
        '<div class="rs-progress">'
        f'<div class="rs-progress__bar" role="img" aria-label="{pct:.0f}% of skills have evidence">'
        f'<i style="width:{min(pct, 100):.0f}%"></i></div>'
        f"<span><b>{len(validated)} of {total}</b> listed skills show up in your projects or experience ({pct:.0f}%)</span>"
        "</div>"
    )

    rows = []
    for entry in validated:
        skill = entry.get("skill", "?")
        projects = entry.get("projects") or []
        where = ", ".join(str(p) for p in projects[:3]) if projects else "Experience section"
        similarity = entry.get("similarity")
        if isinstance(similarity, (int, float)):
            where += f" ({similarity * 100:.0f}% match)"
        rows.append(
            f'<div class="rs-evidence__row"><span class="rs-evidence__skill">{esc(skill)}</span>'
            f'<span class="rs-evidence__where">{esc(where)}</span></div>'
        )

    left = '<div><div class="rs-h3">Backed by your work</div>'
    left += f'<div class="rs-evidence">{"".join(rows)}</div>' if rows else (
        '<p class="rs-empty-line">None of the listed skills appear in a project or role yet.</p>'
    )
    left += "</div>"

    right = '<div><div class="rs-h3">Listed, but never shown</div>'
    if unvalidated:
        right += (
            '<p class="rs-body" style="margin-top:.35rem">Recruiters cross-check skills against your work. '
            "Mention each of these in a bullet, or drop it.</p>" + chips(unvalidated, "gap")
        )
    else:
        right += '<p class="rs-empty-line">Every listed skill has evidence. Nice.</p>'
    right += "</div>"

    html(f'<div class="rs-cols">{left}{right}</div>')


# --------------------------------------------------------------------------
# Job match tab
# --------------------------------------------------------------------------

def display_jd_match(jd: Dict[str, Any]) -> None:
    match_pct = float(jd.get("match_percentage", 0) or 0)
    semantic = float(jd.get("semantic_similarity", 0) or 0) * 100
    matched = jd.get("matched_keywords") or []
    missing = jd.get("missing_keywords") or []
    missing_lower = {str(m).lower() for m in missing}
    gap = [g for g in (jd.get("skills_gap") or []) if str(g).lower() in missing_lower]

    html(
        '<div class="rs-match">'
        f'<div><div class="rs-match__num">{match_pct:.0f}<small>%</small></div>'
        f'<div class="rs-match__bar"><i style="width:{min(match_pct, 100):.0f}%"></i></div>'
        '<div class="rs-h3">Keyword match</div><p class="rs-body">Share of the job post’s key terms '
        "that appear on your resume, allowing for close spellings.</p></div>"
        f'<div><div class="rs-match__num">{semantic:.0f}<small>%</small></div>'
        f'<div class="rs-match__bar"><i style="width:{min(semantic, 100):.0f}%"></i></div>'
        '<div class="rs-h3">Meaning match</div><p class="rs-body">How close the resume is to the job post '
        "in meaning, even where the wording differs.</p></div>"
        "</div>"
    )

    left = '<div><div class="rs-h3">Already on your resume</div>'
    left += chips(matched, "hit") if matched else '<p class="rs-empty-line">No shared keywords yet.</p>'
    left += "</div>"

    right = '<div><div class="rs-h3">In the job post, missing from your resume</div>'
    right += chips(missing, "gap") if missing else '<p class="rs-empty-line">You cover every key term.</p>'
    if gap:
        right += (
            '<p class="rs-body" style="margin-top:1.25rem">Of these, the skills to address first:</p>'
            + chips(gap, "")
        )
    right += "</div>"

    html(f'<div class="rs-cols">{left}{right}</div>')


# --------------------------------------------------------------------------
# Action plan tab
# --------------------------------------------------------------------------

def collect_actions(analysis: Dict[str, Any]) -> List[Tuple[str, str, List[str]]]:
    """[(severity, issue title, [actions])] ordered by severity."""
    groups = []
    for issue in analysis.get("detailed_feedback") or []:
        actions = [_clean(a) for a in (issue.get("action_items") or []) if _clean(a)]
        if actions:
            groups.append((normalize_severity(issue.get("severity_level")), _clean(issue.get("issue_title")), actions))
    if not groups:
        suggestions = [_clean(s) for s in (analysis.get("suggestions") or []) if _clean(s)]
        if suggestions:
            groups.append(("medium", "Suggestions", suggestions))
    groups.sort(key=lambda g: SEVERITY_ORDER.index(g[0]))
    return groups


def display_action_plan(analysis: Dict[str, Any], report_id: str) -> None:
    groups = collect_actions(analysis)
    if not groups:
        html('<p class="rs-empty-line">There’s nothing to act on for this resume.</p>')
        return

    prefix = "act_" + hashlib.sha1(report_id.encode("utf-8")).hexdigest()[:10]
    keys = [f"{prefix}_{gi}_{ai}" for gi, (_, _, acts) in enumerate(groups) for ai in range(len(acts))]
    done = sum(1 for k in keys if st.session_state.get(k))
    total = len(keys)
    pct = done / total * 100 if total else 0

    html(
        '<div class="rs-progress">'
        f'<div class="rs-progress__bar" role="img" aria-label="{done} of {total} steps done">'
        f'<i style="width:{pct:.0f}%"></i></div>'
        f"<span><b>{done} of {total}</b> steps done. Tick them off as you edit; they stay ticked while this tab is open.</span>"
        "</div>"
    )

    for gi, (level, title, actions) in enumerate(groups):
        html(
            f'<div class="rs-sevhead"><i class="rs-sevdot rs-sevdot--{level}"></i>'
            f"<span>{esc(title)}</span><em>{SEVERITY_LABEL[level]}</em></div>"
        )
        for ai, action in enumerate(actions):
            st.checkbox(action, key=f"{prefix}_{gi}_{ai}")


def summary_text(analysis: Dict[str, Any], filename: str = "") -> str:
    """Plain-text summary for the .txt download."""
    score = overall_score(analysis)
    band, _ = score_band(score)
    lines = [f"ATS Resume Scorer report{f' for {filename}' if filename else ''}", "",
             f"Overall score: {score:.0f}/100 ({band})"]
    if analysis.get("interpretation"):
        lines.append(_clean(analysis["interpretation"]))
    lines.append("")
    components = analysis.get("component_scores") or {}
    lines.append("Points by check:")
    for label, key, max_pts in COMPONENTS:
        lines.append(f"  {label}: {float(components.get(key, 0) or 0):.0f}/{max_pts}")
    lines.append("")
    jd = jd_of(analysis)
    if jd:
        lines.append(f"Keyword match with job post: {float(jd.get('match_percentage', 0)):.0f}%")
        if jd.get("missing_keywords"):
            lines.append("Missing keywords: " + ", ".join(jd["missing_keywords"]))
        lines.append("")
    if analysis.get("strengths"):
        lines.append("What's working:")
        lines.extend(f"  - {_clean(s)}" for s in analysis["strengths"])
        lines.append("")
    groups = collect_actions(analysis)
    if groups:
        lines.append("Action plan:")
        for level, title, actions in groups:
            lines.append(f"  {title} [{level}]")
            lines.extend(f"    [ ] {a}" for a in actions)
    return "\n".join(lines)
