import requests
import streamlit as st
from requests.exceptions import ConnectionError, ReadTimeout

API_BASE = st.secrets.get("API_BASE_URL", "http://localhost:8000")


@st.cache_data(ttl=300, show_spinner=False)
def _wake_backend() -> str:
    """Ping the backend health endpoint so Render wakes up before login is attempted."""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=30)
        if resp.ok:
            return "ok"
        return f"degraded ({resp.status_code})"
    except (ConnectionError, ReadTimeout):
        return "unreachable"

# ── Shared card CSS injected once ─────────────────────────────────────────────
_CARD_CSS = """
<style>
  /* Hide Streamlit branding */
  #MainMenu, footer, header { visibility: hidden; }

  .auth-card {
    background: #ffffff;
    border: 1px solid #e1e8ed;
    border-radius: 12px;
    padding: 36px 40px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  }
  .auth-title {
    font-size: 24px;
    font-weight: 700;
    color: #14171a;
    margin-bottom: 4px;
  }
  .auth-sub {
    color: #657786;
    font-size: 14px;
    margin-bottom: 24px;
  }
  .brand-bar {
    text-align: center;
    font-size: 32px;
    margin-bottom: 8px;
  }
</style>
"""


def render_login() -> None:
    """Centered login card. Sets session_state on successful login."""
    st.markdown(_CARD_CSS, unsafe_allow_html=True)

    # Wake the backend in the background (cached for 5 min)
    with st.spinner("Connecting to server…"):
        status = _wake_backend()
    if status == "unreachable":
        st.warning("Backend is unavailable. Please try again in a moment.")

    # Page layout: blank gutters on each side
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown('<div class="brand-bar">📈</div>', unsafe_allow_html=True)
        st.markdown(
            '<p class="auth-title">Sign in to F&O Trader</p>'
            '<p class="auth-sub">Your F&O trading platform</p>',
            unsafe_allow_html=True,
        )

        username = st.text_input("Username", key="login_username", placeholder="Enter username")
        password = st.text_input(
            "Password", type="password", key="login_password", placeholder="Enter password"
        )

        if st.button("Sign In", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("Please fill in both fields.")
                return
            try:
                resp = requests.post(
                    f"{API_BASE}/auth/login",
                    json={"username": username, "password": password},
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.logged_in = True
                    st.session_state.token = data["access_token"]
                    st.session_state.username = username
                    st.rerun()
                elif resp.status_code == 403:
                    detail = resp.json().get("detail", "")
                    if "pending" in detail.lower():
                        st.warning("Your account is pending admin approval. Check back soon.")
                    else:
                        st.error(detail)
                else:
                    st.error(resp.json().get("detail", "Invalid username or password."))
            except (ConnectionError, ReadTimeout):
                st.error("Server is waking up — please wait a moment and try again.")

        st.markdown("---")
        st.markdown(
            '<p style="text-align:center;color:#657786;font-size:13px;">New to F&O Trader?</p>',
            unsafe_allow_html=True,
        )
        if st.button("Create an account", use_container_width=True):
            st.session_state.show_register = True
            st.rerun()


def render_register() -> None:
    """Centered registration card. Shows pending message on success."""
    st.markdown(_CARD_CSS, unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown('<div class="brand-bar">📈</div>', unsafe_allow_html=True)
        st.markdown(
            '<p class="auth-title">Create your account</p>'
            '<p class="auth-sub">Request access to F&O Trader</p>',
            unsafe_allow_html=True,
        )

        username = st.text_input("Username", key="reg_username", placeholder="Choose a username")
        email = st.text_input("Email address", key="reg_email", placeholder="you@example.com")
        password = st.text_input(
            "Password", type="password", key="reg_password", placeholder="Create a password"
        )
        confirm = st.text_input(
            "Confirm password",
            type="password",
            key="reg_confirm",
            placeholder="Repeat password",
        )

        if st.button("Register", use_container_width=True, type="primary"):
            if not all([username, email, password, confirm]):
                st.error("All fields are required.")
                return
            if password != confirm:
                st.error("Passwords do not match.")
                return
            try:
                resp = requests.post(
                    f"{API_BASE}/auth/register",
                    json={
                        "username": username,
                        "email": email,
                        "password": password,
                    },
                    timeout=60,
                )
                if resp.status_code == 201:
                    st.success(
                        "Account request submitted! You will be notified once an admin approves your access."
                    )
                    st.info("Return to login once you receive approval.")
                else:
                    st.error(resp.json().get("detail", "Registration failed. Please try again."))
            except (ConnectionError, ReadTimeout):
                st.error("Server is waking up — please wait a moment and try again.")

        st.markdown("---")
        if st.button("Back to Sign In", use_container_width=True):
            st.session_state.show_register = False
            st.rerun()
