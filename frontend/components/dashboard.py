from typing import Any, Dict

import streamlit as st

from frontend.components.report_sections import (
    collect_actions,
    display_action_plan,
    display_fixes,
    display_jd_match,
    display_scorecard,
    display_skills,
    display_quick_wins,
    display_summary,
    jd_of,
)
from frontend.components.ui import html


def display_results_dashboard(analysis: Dict[str, Any], report_id: str, on_add_jd=None) -> None:
    """Score card followed by the report tabs."""
    display_scorecard(analysis)

    issues = analysis.get("detailed_feedback") or []
    steps = sum(len(actions) for _, _, actions in collect_actions(analysis))
    details = analysis.get("skill_validation_details") or {}
    unvalidated = len(details.get("unvalidated") or [])
    jd = jd_of(analysis)

    labels = [
        "Summary",
        f"Fixes ({len(issues)})" if issues else "Fixes",
        f"Skills ({unvalidated} unproven)" if unvalidated else "Skills",
        "Job match",
        f"Action plan ({steps})" if steps else "Action plan",
    ]
    t_summary, t_fixes, t_skills, t_jd, t_plan = st.tabs(labels)

    with t_summary:
        display_quick_wins(analysis)
        display_summary(analysis)
    with t_fixes:
        display_fixes(analysis)
    with t_skills:
        display_skills(analysis)
    with t_jd:
        if jd:
            display_jd_match(jd)
        else:
            html(
                '<div class="rs-empty"><h2 class="rs-h2">This check didn’t include a job post</h2>'
                '<p class="rs-body">Score the resume again with the job description pasted in to see '
                "which of its keywords you cover and which are missing.</p></div>"
            )
            if on_add_jd and st.button("Score again with a job post", key="jd_again"):
                on_add_jd()
    with t_plan:
        display_action_plan(analysis, report_id)
