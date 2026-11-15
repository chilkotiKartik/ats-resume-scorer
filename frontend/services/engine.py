"""
Built-in scoring engine.

Runs the same pipeline as POST /api/v1/analyze-resume, but inside the Streamlit
process. Used when no `[backend] url` is configured in secrets — this is what
lets the app run as a single service on Streamlit Community Cloud.

Models are loaded once per server process and shared by every visitor.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

import streamlit as st

logger = logging.getLogger("ats_resume_scorer.engine")


class EngineError(Exception):
    """A failure the user can act on (unreadable file, model missing, …)."""


@st.cache_resource(show_spinner=False)
def _models():
    import spacy
    from sentence_transformers import SentenceTransformer

    from backend.core.config import (
        SENTENCE_TRANSFORMER_MODEL,
        SPACY_MODEL_PRIMARY,
        SPACY_MODEL_SECONDARY,
    )

    try:
        nlp = spacy.load(SPACY_MODEL_PRIMARY)
    except OSError:
        nlp = spacy.load(SPACY_MODEL_SECONDARY)
    embedder = SentenceTransformer(SENTENCE_TRANSFORMER_MODEL)
    return nlp, embedder


def warm_up() -> None:
    """Load the models ahead of the first analysis (safe to call repeatedly)."""
    _models()


def analyze(file_bytes: bytes, filename: str, job_description: str = "") -> Dict[str, Any]:
    from backend.models.schemas import (
        AnalysisResponse,
        ComponentScores,
        JDComparison,
        SkillValidationDetails,
    )
    from backend.services.resume_analyzer import analyze_full_resume
    from backend.services.resume_parser import parse_resume_file

    try:
        resume_text, _meta = parse_resume_file(file_bytes, filename)
    except Exception as exc:  # parser raises several custom types
        raise EngineError(f"The file couldn't be read: {exc}") from exc

    if not resume_text or len(resume_text.strip()) < 50:
        raise EngineError(
            "Almost no text came out of this file. If it's a scanned image, export it again "
            "from Word or Google Docs so the text is selectable."
        )

    nlp, embedder = _models()
    try:
        result = analyze_full_resume(
            resume_text=resume_text, nlp=nlp, embedder=embedder, job_description=job_description,
        )
    except Exception as exc:
        logger.exception("analysis failed")
        raise EngineError(f"The analysis failed: {exc}") from exc

    jd = None
    if result.get("jd_comparison"):
        raw = result["jd_comparison"]
        jd = JDComparison(
            match_percentage=round(float(raw.get("match_percentage", 0.0)), 1),
            semantic_similarity=round(float(raw.get("semantic_similarity", 0.0)), 3),
            matched_keywords=raw.get("matched_keywords", [])[:20],
            missing_keywords=raw.get("missing_keywords", [])[:15],
            skills_gap=raw.get("skills_gap", [])[:10],
        )

    svd = result.get("skill_validation_details") or {}
    response = AnalysisResponse(
        ATS_score=result["ats_score"],
        component_scores=ComponentScores(**result["component_scores"]),
        issues_summary=result["issues_summary"],
        detailed_feedback=result.get("detailed_feedback", []),
        jd_match_analysis=jd,
        skill_validation_details=SkillValidationDetails(
            validated=svd.get("validated", []),
            unvalidated=svd.get("unvalidated", []),
            total=svd.get("total", 0),
            validated_count=svd.get("validated_count", 0),
            validation_pct=svd.get("validation_pct", 0.0),
        ),
        ats_score=result["ats_score"],
        keyword_match=jd.match_percentage if jd else 0.0,
        missing_keywords=result.get("missing_keywords", []),
        matched_keywords=result.get("matched_keywords", []),
        skills=list(result.get("skills", [])[:20]),
        jd_comparison=jd,
        interpretation=result.get("interpretation", ""),
    )
    data = response.model_dump()
    # Keep extra fields the analyzer produces (strengths, suggestions, …) for the report.
    for key in ("strengths", "critical_issues", "suggestions", "warnings"):
        if key in result and not data.get(key):
            data[key] = result[key]
    return data


def pdf_bytes(analysis: Dict[str, Any]) -> bytes:
    from backend.services.pdf_export import generate_combined_pdf
    from backend.services.report_generator import generate_html_reports

    try:
        return generate_combined_pdf(generate_html_reports(analysis))
    except Exception as exc:
        raise EngineError(f"The PDF couldn't be built: {exc}") from exc


# --------------------------------------------------------------------------
# Account history through Supabase (only when the service key is configured)
# --------------------------------------------------------------------------

def db_available() -> bool:
    from backend.core.config import SUPABASE_KEY, SUPABASE_URL
    return bool(SUPABASE_URL and SUPABASE_KEY)


def db_save(user_id: str, filename: str, analysis: Dict[str, Any]) -> Optional[str]:
    from backend.database.supabase_db import save_analysis
    return asyncio.run(save_analysis(user_id, filename, analysis))


def db_history(user_id: str) -> List[Dict[str, Any]]:
    from backend.database.supabase_db import get_user_history
    return asyncio.run(get_user_history(user_id)) or []


def db_delete(analysis_id: str, user_id: str) -> bool:
    from backend.database.supabase_db import delete_analysis
    return asyncio.run(delete_analysis(analysis_id, user_id))
