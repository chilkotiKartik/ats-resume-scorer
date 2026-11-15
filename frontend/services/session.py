"""Session-state helpers shared by the app shell and the pages."""

from datetime import datetime
from typing import Any, Dict, Optional

import streamlit as st


DEFAULT_STATE = {
    "access_token": None,
    "refresh_token": None,
    "user_id": None,
    "user_email": None,
    "auth_error": None,
    "auth_info": None,
    "password_recovery_mode": False,
    # The report currently open on the Report page.
    "scorer_analysis": None,
    "report_meta": None,
    # Ticked items on the Report → Action plan tab, keyed by report id.
    "done_actions": {},
}


def init_state() -> None:
    for key, default in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = default.copy() if isinstance(default, dict) else default


def is_signed_in() -> bool:
    return bool(st.session_state.get("access_token"))


def store_auth_session(result: Dict[str, Any]) -> None:
    st.session_state.access_token = result["access_token"]
    st.session_state.refresh_token = result["refresh_token"]
    st.session_state.user_id = result["user_id"]
    st.session_state.user_email = result["email"]


def clear_auth_session() -> None:
    for key in ("access_token", "refresh_token", "user_id", "user_email"):
        st.session_state[key] = None
    st.session_state.password_recovery_mode = False
    st.session_state.auth_info = None
    st.session_state.auth_error = None
    st.session_state.scorer_analysis = None
    st.session_state.report_meta = None
    st.session_state.pop("scorer_pdf_bytes", None)


def open_report(
    analysis: Dict[str, Any],
    filename: str,
    *,
    source: str = "new",
    created_at: Optional[str] = None,
    history_id: Optional[str] = None,
    with_jd: Optional[bool] = None,
) -> None:
    """Put an analysis on the Report page. `source` is new / history / sample."""
    if with_jd is None:
        with_jd = bool(analysis.get("jd_comparison") or analysis.get("jd_match_analysis"))
    st.session_state.scorer_analysis = analysis
    st.session_state.report_meta = {
        "filename": filename,
        "source": source,
        "created_at": created_at or datetime.now().isoformat(timespec="minutes"),
        "history_id": history_id,
        "with_jd": with_jd,
        "report_id": history_id or f"{source}:{filename}:{created_at or datetime.now().isoformat()}",
    }
    st.session_state.pop("scorer_pdf_bytes", None)


def format_when(value: Optional[str]) -> str:
    """'2026-11-15T09:12:44.123+00:00' → '15 Nov 2026, 09:12'."""
    if not value:
        return ""
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed.strftime("%d %b %Y, %H:%M").lstrip("0")
    except ValueError:
        return str(value)
