"""
Page registry for the multi-page app.

Each page gets its own URL (/analyze, /report, /history, /guide, /account),
so the browser back button, bookmarks and shared links work. Views are
imported lazily so a page only loads its own code.
"""

from typing import Dict

import streamlit as st


def _home():
    from frontend.views import landing
    landing.render()


def _analyze():
    from frontend.views import scorer
    scorer.render()


def _report():
    from frontend.views import report
    report.render()


def _history():
    from frontend.views import history
    history.render()


def _bullets():
    from frontend.views import bullets
    bullets.render()


def _guide():
    from frontend.views import resources
    resources.render()


def _account():
    from frontend.views import account
    account.render()


# slug → (title, callable). Order is the order shown in the top bar.
_REGISTRY = {
    "home": ("Home", _home),
    "analyze": ("Analyze", _analyze),
    "report": ("Report", _report),
    "history": ("History", _history),
    "bullets": ("Bullet Lab", _bullets),
    "guide": ("Resources", _guide),
    "account": ("Account", _account),
}

NAV_ORDER = ["home", "analyze", "report", "history", "bullets", "guide"]

# Sidebar (Clarity theme) labels and icons.
SIDE_NAV = {
    "home": ("Home", ":material/home:"),
    "analyze": ("ATS Scorer", ":material/track_changes:"),
    "report": ("Report", ":material/insights:"),
    "history": ("History", ":material/history:"),
    "bullets": ("Bullet Lab", ":material/edit_note:"),
    "guide": ("Resources", ":material/menu_book:"),
}

_PAGES: Dict[str, "st.Page"] = {}


def build_pages() -> Dict[str, "st.Page"]:
    _PAGES.clear()
    for slug, (title, fn) in _REGISTRY.items():
        _PAGES[slug] = st.Page(
            fn,
            title=title,
            url_path="resources" if slug == "guide" else slug,
            default=(slug == "home"),
        )
    return _PAGES


def page(slug: str) -> "st.Page":
    return _PAGES[slug]


def go(slug: str) -> None:
    st.switch_page(_PAGES[slug])


def slug_of(current_page) -> str:
    for slug, candidate in _PAGES.items():
        if candidate.url_path == current_page.url_path:
            return slug
    return "home"
