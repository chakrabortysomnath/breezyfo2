import streamlit as st

st.set_page_config(
    page_title="F&O Trader",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS — Twitter/Facebook-like UI ─────────────────────────────────────
st.markdown(
    """
    <style>
      /* Remove sidebar entirely */
      [data-testid="collapsedControl"] { display: none !important; }
      section[data-testid="stSidebar"]  { display: none !important; }

      /* Page background */
      .stApp { background-color: #f5f8fa; }

      /* Reduce default top padding */
      .block-container { padding-top: 16px !important; }

      /* Tab bar — Twitter-style underline indicator */
      div[data-baseweb="tab-list"] {
        border-bottom: 1px solid #e1e8ed !important;
        background: #ffffff;
        gap: 0 !important;
      }
      div[data-baseweb="tab"] {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #657786 !important;
        padding: 14px 22px !important;
        border-bottom: 3px solid transparent !important;
        background: transparent !important;
      }
      div[data-baseweb="tab"]:hover {
        color: #1da1f2 !important;
        background: #e8f5fe !important;
      }
      div[data-baseweb="tab"][aria-selected="true"] {
        color: #1da1f2 !important;
        border-bottom: 3px solid #1da1f2 !important;
      }

      /* Hide Streamlit footer */
      footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Session state initialisation ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "show_register" not in st.session_state:
    st.session_state.show_register = False

# ── Auth gate ─────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    from components.auth_ui import render_login, render_register

    if st.session_state.show_register:
        render_register()
    else:
        render_login()
    st.stop()  # Critical: prevents tab layout from rendering below the auth screen

# ── Authenticated layout ──────────────────────────────────────────────────────
from components.topbar import render_topbar
from pages.home_tab import render_home_tab
from pages.dashboard_tab import render_dashboard_tab
from pages.orders_tab import render_orders_tab

render_topbar()

tab_home, tab_dashboard, tab_orders = st.tabs(["🏠  Home", "📊  Dashboard", "📋  Orders"])

with tab_home:
    render_home_tab()

with tab_dashboard:
    render_dashboard_tab()

with tab_orders:
    render_orders_tab()
