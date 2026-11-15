"""
Visual themes. The base stylesheet (assets/styles.css) is the Paper theme;
the others layer an override file from assets/themes/ on top of it.

The choice lives in the session and can be preset with ?theme=toon|paper|midnight.
"""

from pathlib import Path
from typing import Dict

import streamlit as st

THEMES: Dict[str, Dict[str, str]] = {
    "clarity": {
        "label": "Clarity",
        "caption": "Clean workspace with a sidebar",
        "swatch": "#F3F6FC,#2563EB,#22C55E,#0F1B3D",
    },
    "toon": {
        "label": "Toon",
        "caption": "Bright and playful, with Scout the mascot",
        "swatch": "#FFD23F,#FF5A4E,#4DA3FF,#1E1B3A",
    },
    "paper": {
        "label": "Paper",
        "caption": "Calm and editorial, like a marked-up page",
        "swatch": "#EDEFF2,#FFE04A,#C93A2E,#18213A",
    },
    "midnight": {
        "label": "Midnight",
        "caption": "Dark, easy on the eyes at night",
        "swatch": "#0E1530,#172142,#FFE04A,#4FD1A1",
    },
}
DEFAULT_THEME = "clarity"
ASSETS = Path(__file__).resolve().parent.parent / "assets"


def init_theme() -> None:
    if "theme" not in st.session_state:
        requested = st.query_params.get("theme", "")
        st.session_state.theme = requested if requested in THEMES else DEFAULT_THEME


def current() -> str:
    return st.session_state.get("theme", DEFAULT_THEME)


def uses_sidebar() -> bool:
    return current() == "clarity"


def show_mascot() -> bool:
    return current() in ("toon", "midnight")


def load_css() -> None:
    css = (ASSETS / "styles.css").read_text(encoding="utf-8")
    override = ASSETS / "themes" / f"{current()}.css"
    if override.exists():
        css += "\n" + override.read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")


def art(name: str) -> str:
    """URL of an illustration in static/art/."""
    return f"/app/static/art/{name}.svg"


def mascot_for_score(score: float) -> str:
    if score >= 80:
        return "scout-cheer"
    if score >= 60:
        return "scout-okay"
    return "scout-worried"


def picker() -> None:
    """Theme chooser shown in the top bar."""
    options = list(THEMES)
    with st.popover(f"Theme: {THEMES[current()]['label']}", key="theme_popover", icon=":material/palette:",
                    use_container_width=uses_sidebar()):
        st.session_state["theme_radio"] = current()
        st.radio(
            "Choose a look",
            options,
            format_func=lambda k: THEMES[k]["label"],
            captions=[THEMES[k]["caption"] for k in options],
            key="theme_radio",
            on_change=_apply_choice,
        )


def _apply_choice() -> None:
    st.session_state.theme = st.session_state.get("theme_radio", DEFAULT_THEME)
