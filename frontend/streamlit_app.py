"""
ATS Resume Scorer — Streamlit entry point.

Run from the frontend folder so Streamlit picks up .streamlit/config.toml
(theme + self-hosted fonts) and the static/ folder:

    cd frontend
    streamlit run streamlit_app.py

This file is the app shell. It runs on every page view and:
  1. handles Supabase auth callbacks (email confirmation, Google OAuth,
     password-reset links) that arrive as query parameters,
  2. loads the stylesheet,
  3. draws the top bar and hands off to the current page.
"""

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="ATS Resume Scorer",
    page_icon="🖍️",
    layout="wide",
    initial_sidebar_state="auto",
)

from frontend import navigation  # noqa: E402
from frontend.components.ui import esc, html  # noqa: E402
from frontend.services import store, supabase_client, theme  # noqa: E402
from frontend.services.session import (  # noqa: E402
    clear_auth_session,
    init_state,
    is_signed_in,
    store_auth_session,
)

init_state()
theme.init_theme()


# --------------------------------------------------------------------------
# Auth callbacks (query parameters set by Supabase redirects)
# --------------------------------------------------------------------------

query_params = st.query_params

# 1. Supabase reported an error.
if "error_description" in query_params:
    st.session_state.auth_error = f"Sign-in failed: {query_params.get('error_description')}"
    st.query_params.clear()
    st.rerun()

# 2. Email confirmation link (token hash).
if "token_hash" in query_params:
    token_hash = query_params.get("token_hash")
    token_type = query_params.get("type", "signup")

    if not token_hash:
        st.session_state.auth_error = "Email verification failed: the link has no verification token."
    elif token_type != "signup":
        st.session_state.auth_error = f"Email verification failed: unexpected link type “{token_type}”."
    else:
        result = supabase_client.verify_signup_token_hash(token_hash)
        if "error" in result:
            st.session_state.auth_error = f"Email verification failed: {result['error']}"
        elif result.get("access_token") and result.get("refresh_token"):
            store_auth_session(result)
            st.session_state.password_recovery_mode = False
            st.session_state.auth_info = "Email verified. Your account is ready."
        else:
            st.session_state.auth_error = "Email verification didn't return a session. Try signing in."

    st.query_params.clear()
    st.rerun()

# 3. Google OAuth or password-recovery callback (PKCE code).
if "code" in query_params:
    auth_code = query_params.get("code")
    recovery_mode = query_params.get("mode") == "recovery"

    if auth_code:
        result = supabase_client.exchange_code_for_session(auth_code)
        if "error" in result:
            st.session_state.auth_error = f"Sign-in failed: {result['error']}"
        else:
            store_auth_session(result)
            if recovery_mode:
                st.session_state.password_recovery_mode = True
                st.session_state.auth_info = "Reset link verified. Choose a new password."
            else:
                st.session_state.password_recovery_mode = False
                st.session_state.auth_info = "Signed in."
    else:
        st.session_state.auth_error = "Sign-in failed: the link has no authorization code."

    st.query_params.clear()
    st.rerun()


# --------------------------------------------------------------------------
# Shell
# --------------------------------------------------------------------------

theme.load_css()

pages = navigation.build_pages()
current = st.navigation(list(pages.values()), position="hidden")
current_slug = navigation.slug_of(current)

# A password-reset link must land on the Account page, wherever it pointed.
if st.session_state.password_recovery_mode and current_slug != "account":
    navigation.go("account")


def _render_topbar(active: str) -> None:
    # Highlight the active link with the same marker stroke as the wordmark.
    st.html(
        "<style>"
        f".st-key-nav_{active} a[data-testid='stPageLink-NavLink'] p {{"
        "color: var(--nav-active-fg, var(--ink)) !important; font-weight: 700 !important;"
        "background-image: var(--nav-active-bg, linear-gradient(var(--marker), var(--marker)));"
        "background-repeat: no-repeat; background-size: 100% 40%; background-position: 0 92%;"
        "}"
        "</style>"
    )

    with st.container(horizontal=True, vertical_alignment="center", key="topbar", gap="small"):
        html(
            '<a class="rs-wordmark" href="/" target="_self" aria-label="ATS Resume Scorer, home">'
            "<b>ATS</b> Resume Scorer</a>"
        )
        st.space("stretch")

        for slug in navigation.NAV_ORDER:
            with st.container(key=f"nav_{slug}", width="content"):
                st.page_link(navigation.page(slug))

        st.space("small")
        with st.container(key="theme_slot", width="content"):
            theme.picker()

        if is_signed_in():
            with st.container(key="nav_account", width="content"):
                st.page_link(navigation.page("account"), label="Account")
            if st.button("Sign out", type="tertiary", key="topbar_signout"):
                supabase_client.sign_out()
                clear_auth_session()
                navigation.go("home")
        elif store.accounts_enabled():
            if st.button("Sign in", type="primary", key="topbar_signin"):
                navigation.go("account")


def _user_name() -> str:
    email = st.session_state.user_email or ""
    local = email.split("@")[0]
    first = local.replace(".", " ").replace("_", " ").split()[0] if local else ""
    return first.capitalize()


def _render_sidebar(active: str) -> None:
    st.html(
        "<style>"
        f".st-key-side_nav_{active} a[data-testid='stPageLink-NavLink'] {{"
        "background: linear-gradient(180deg, #3B82F6, #2563EB) !important;"
        "box-shadow: 0 8px 18px -10px rgba(37, 99, 235, .8); }"
        f".st-key-side_nav_{active} a[data-testid='stPageLink-NavLink'] p,"
        f".st-key-side_nav_{active} a[data-testid='stPageLink-NavLink'] [data-testid='stIconMaterial'] {{"
        "color: #fff !important; }"
        "</style>"
    )
    with st.sidebar:
        html(
            '<a class="rs-brand" href="/" target="_self">'
            '<img src="app/static/art/logo-robot.svg" alt="">'
            "<span>AI Resume<br>ATS Scorer</span></a>"
        )
        for slug, (label, icon) in navigation.SIDE_NAV.items():
            with st.container(key=f"side_nav_{slug}"):
                st.page_link(navigation.page(slug), label=label, icon=icon)

        with st.container(key="side_user"):
            with st.container(key="side_theme"):
                theme.picker()
            if is_signed_in():
                email = st.session_state.user_email or ""
                name = _user_name() or "You"
                html(
                    f'<div class="rs-user"><span class="rs-avatar">{esc(name[:1].upper())}</span>'
                    f"<div><b>{esc(name)}</b><small>{esc(email)}</small></div></div>"
                )
                with st.container(key="side_signout"):
                    if st.button("Sign Out", type="tertiary", icon=":material/logout:", key="side_signout_btn"):
                        supabase_client.sign_out()
                        clear_auth_session()
                        navigation.go("home")
            else:
                html(
                    '<div class="rs-user"><span class="rs-avatar">G</span>'
                    "<div><b>Guest</b><small>Checks stay in this tab</small></div></div>"
                )
                if store.accounts_enabled():
                    if st.button("Sign in", type="primary", icon=":material/login:", key="side_signin",
                                 use_container_width=True):
                        navigation.go("account")


if theme.uses_sidebar():
    _render_sidebar(current_slug)
else:
    _render_topbar(current_slug)
current.run()
