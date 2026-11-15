"""Account page: sign in, create an account, reset a password, sign out."""

import streamlit as st

from frontend import navigation
from frontend.components.ui import esc, footer, html, notice, page_head
from frontend.services import store, supabase_client, theme
from frontend.services.session import clear_auth_session, is_signed_in, store_auth_session


def _messages() -> None:
    if st.session_state.auth_error:
        notice(esc(st.session_state.auth_error), "red")
        st.session_state.auth_error = None
    if st.session_state.auth_info:
        notice(esc(st.session_state.auth_info))
        st.session_state.auth_info = None


def _recovery_form() -> None:
    page_head("Choose a new password", "Use at least 6 characters.")
    _messages()
    left, _ = st.columns([1, 1])
    with left:
        with st.form("new_password_form"):
            new_password = st.text_input("New password", type="password")
            confirm = st.text_input("Type it again", type="password")
            submitted = st.form_submit_button("Update password", type="primary", use_container_width=True)
        if submitted:
            if len(new_password) < 6:
                notice("Passwords need at least 6 characters.", "red")
            elif new_password != confirm:
                notice("The two passwords don't match.", "red")
            else:
                result = supabase_client.update_user_password(new_password)
                if "error" in result:
                    notice(esc(result["error"]), "red")
                else:
                    st.session_state.password_recovery_mode = False
                    st.session_state.auth_info = "Password updated."
                    st.rerun()


def _signed_in() -> None:
    page_head("Account")
    _messages()
    email = st.session_state.user_email or "your account"
    html(
        '<div class="rs-empty">'
        f'<h2 class="rs-h2">Signed in as {esc(email)}</h2>'
        '<p class="rs-body">Every check you run is saved to History with its full report.</p></div>'
    )
    with st.container(horizontal=True, gap="small"):
        if st.button("Score a resume", type="primary", key="acc_score"):
            navigation.go("analyze")
        if st.button("Open History", key="acc_history"):
            navigation.go("history")
        if st.button("Sign out", type="tertiary", key="acc_signout"):
            supabase_client.sign_out()
            clear_auth_session()
            navigation.go("home")


def _sign_in_tab() -> None:
    with st.form("signin_form", clear_on_submit=False, border=False):
        email = st.text_input("Email", key="signin_email", autocomplete="email")
        password = st.text_input("Password", type="password", key="signin_pw", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
    if submitted:
        if not email.strip() or not password:
            notice("Enter your email and password.", "red")
        else:
            result = supabase_client.sign_in_with_password(email.strip(), password)
            if "error" in result:
                st.session_state.auth_error = result["error"]
                st.rerun()
            store_auth_session(result)
            st.session_state.auth_info = "Signed in."
            navigation.go("analyze")

    with st.expander("Forgot your password?"):
        html('<p class="rs-body" style="margin-bottom:.5rem">We\u2019ll email you a link to choose a new one.</p>')
        reset_email = st.text_input("Email for the reset link", key="reset_email")
        if st.button("Email me a reset link", key="send_reset"):
            if not reset_email.strip():
                notice("Enter the email you signed up with.", "red")
            else:
                result = supabase_client.send_password_reset_email(reset_email.strip())
                if "error" in result:
                    notice(esc(result["error"]), "red")
                else:
                    notice(f"If <strong>{esc(reset_email.strip())}</strong> has an account, the link is on its way.")


def _sign_up_tab() -> None:
    with st.form("signup_form", clear_on_submit=False, border=False):
        email = st.text_input("Email", key="signup_email", autocomplete="email")
        password = st.text_input("Password", type="password", key="signup_pw",
                                 help="At least 6 characters.", autocomplete="new-password")
        submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
    if submitted:
        if not email.strip() or not password:
            notice("Enter an email and choose a password.", "red")
        elif len(password) < 6:
            notice("Passwords need at least 6 characters.", "red")
        else:
            result = supabase_client.sign_up_with_password(email.strip(), password)
            if "error" in result:
                st.session_state.auth_error = result["error"]
            elif result.get("pending_confirmation"):
                st.session_state.auth_info = (
                    f"Check {result['email']} for a confirmation link, then come back and sign in."
                )
            elif result.get("access_token"):
                store_auth_session(result)
                st.session_state.auth_info = "Account created."
                navigation.go("analyze")
            else:
                st.session_state.auth_error = "Sign-up didn't complete. Try again."
            st.rerun()


def _accounts_off() -> None:
    page_head("Account")
    mascot = (f'<img src="{theme.art("scout-wave")}" alt="" style="width:120px;float:right;margin:-.5rem 0 0 1rem">'
              if theme.show_mascot() else "")
    html(
        f'<div class="rs-empty">{mascot}<h2 class="rs-h2">You don’t need an account here</h2>'
        '<p class="rs-body">Sign-in isn’t switched on for this copy of the app, so every check runs as a guest. '
        "Your reports stay in History until you close the tab, and you can download any of them as a PDF.</p>"
        '<div style="clear:both"></div></div>'
    )
    if st.button("Score a resume", type="primary", key="acc_off_score"):
        navigation.go("analyze")


def render() -> None:
    if not store.accounts_enabled() and not is_signed_in():
        _accounts_off()
        footer()
        return
    if st.session_state.password_recovery_mode and is_signed_in():
        _recovery_form()
        footer()
        return
    if is_signed_in():
        _signed_in()
        footer()
        return

    left, right = st.columns([1, 1], gap="large")
    with left:
        html(
            '<div class="rs-why">'
            + (f'<img src="{theme.art("scout-wave")}" alt="" style="width:110px;margin-bottom:.5rem">'
               if theme.show_mascot() else "")
            + '<h1 class="rs-h1">Sign in to keep your checks</h1>'
            '<p class="rs-lede">An account keeps every check you run, so you can see '
            "whether each edit moved the score.</p>"
            "<ul>"
            "<li><b>Your history in one place</b>Scores, issues and the full report for every version.</li>"
            "<li><b>A trend line</b>See the score climb as you fix things.</li>"
            "<li><b>PDF reports</b>Download any report to share with a mentor or placement cell.</li>"
            "</ul></div>"
        )
    with right:
        _messages()
        with st.container(border=True, key="auth_card"):
            tab_in, tab_up = st.tabs(["Sign in", "Create account"])
            with tab_in:
                _sign_in_tab()
            with tab_up:
                _sign_up_tab()

            html('<div class="rs-or">or</div>')
            oauth = supabase_client.google_oauth_url()
            if "error" in oauth:
                st.button("Continue with Google", disabled=True, use_container_width=True, key="google_off")
                html('<p class="rs-small" style="margin:.4rem 0 0">Google sign-in isn\'t configured on this server.</p>')
            else:
                st.link_button("Continue with Google", url=oauth["url"], use_container_width=True)
    footer()
