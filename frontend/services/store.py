"""
One place that decides *where* analyses run and *where* history lives.

Engine
  remote  — a FastAPI backend is configured in secrets ([backend] url). Needs sign-in.
  local   — no backend configured: the scoring pipeline runs inside Streamlit.

History
  account — signed in, and either the backend or Supabase (service key) can store it.
  guest   — kept in this browser session only; gone when the tab closes.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st

from frontend.services import api_client
from frontend.services.session import is_signed_in


def engine_mode() -> str:
    try:
        url = st.secrets["backend"]["url"]
        if url:
            return "remote"
    except (KeyError, FileNotFoundError, AttributeError):
        pass
    return "local"


def accounts_enabled() -> bool:
    from frontend.services import supabase_client
    return not supabase_client._missing_config()


def can_analyze() -> bool:
    """Remote backends check tokens, so they need a signed-in user. Local runs don't."""
    return engine_mode() == "local" or is_signed_in()


def history_kind() -> str:
    if is_signed_in():
        if engine_mode() == "remote":
            return "account"
        from frontend.services import engine
        if engine.db_available():
            return "account"
    return "guest"


def _guest_history() -> List[Dict[str, Any]]:
    return st.session_state.setdefault("guest_history", [])


def analyze(resume_file, job_description: str) -> Dict[str, Any]:
    """Run an analysis and save it. Returns {'analysis': ..., 'history_id': ...}."""
    if engine_mode() == "remote":
        analysis = api_client.analyze_resume(
            resume_file=resume_file,
            access_token=st.session_state["access_token"],
            job_description=job_description,
        )
        return {"analysis": analysis, "history_id": None}

    from frontend.services import engine
    analysis = engine.analyze(resume_file.getvalue(), resume_file.name, job_description)

    history_id = None
    if history_kind() == "account":
        try:
            history_id = engine.db_save(st.session_state.user_id, resume_file.name, analysis)
        except Exception:  # saving must never lose the user's result
            history_id = None
    if history_id is None:
        history_id = f"guest-{uuid.uuid4().hex[:10]}"
        _guest_history().insert(0, {
            "id": history_id,
            "filename": resume_file.name,
            "ats_score": analysis.get("ATS_score", analysis.get("ats_score", 0)),
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "analysis_result": analysis,
        })
    return {"analysis": analysis, "history_id": history_id}


def history() -> List[Dict[str, Any]]:
    if history_kind() == "account":
        if engine_mode() == "remote":
            return api_client.get_history(st.session_state["access_token"])
        from frontend.services import engine
        return engine.db_history(st.session_state.user_id)
    return list(_guest_history())


def delete(entry_id: str) -> None:
    if entry_id.startswith("guest-"):
        st.session_state["guest_history"] = [e for e in _guest_history() if e.get("id") != entry_id]
        return
    if engine_mode() == "remote":
        api_client.delete_history_entry(entry_id, st.session_state["access_token"])
    else:
        from frontend.services import engine
        engine.db_delete(entry_id, st.session_state.user_id)


def pdf(analysis: Dict[str, Any], history_id: Optional[str]) -> bytes:
    if engine_mode() == "remote":
        token = st.session_state["access_token"]
        if history_id and not history_id.startswith("guest-"):
            return api_client.get_history_pdf(history_id, token)
        return api_client.generate_pdf(analysis, access_token=token)
    from frontend.services import engine
    return engine.pdf_bytes(analysis)


def can_pdf() -> bool:
    return engine_mode() == "local" or is_signed_in()
