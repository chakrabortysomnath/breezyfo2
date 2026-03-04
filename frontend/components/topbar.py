import streamlit as st

_TOPBAR_CSS = """
<style>
  /* Top bar container styling */
  .topbar-title {
    font-size: 20px;
    font-weight: 700;
    color: #1da1f2;
    margin: 0;
    line-height: 1.2;
  }
  .topbar-sub {
    font-size: 12px;
    color: #657786;
    margin: 0;
  }
  .topbar-user {
    font-size: 14px;
    color: #14171a;
    text-align: right;
  }
  /* Tab bar underline style (targets Streamlit's tab widget) */
  div[data-baseweb="tab-list"] {
    border-bottom: 1px solid #e1e8ed !important;
    gap: 0px !important;
  }
  div[data-baseweb="tab"] {
    font-size: 15px !important;
    font-weight: 600 !important;
    color: #657786 !important;
    padding: 12px 20px !important;
    border-bottom: 3px solid transparent !important;
  }
  div[data-baseweb="tab"][aria-selected="true"] {
    color: #1da1f2 !important;
    border-bottom: 3px solid #1da1f2 !important;
  }
  /* Hide sidebar completely */
  [data-testid="collapsedControl"] { display: none !important; }
  section[data-testid="stSidebar"] { display: none !important; }
</style>
"""


def render_topbar() -> None:
    """Renders the top navigation bar with logo, app name, and logout."""
    st.markdown(_TOPBAR_CSS, unsafe_allow_html=True)

    left, right = st.columns([5, 1])
    with left:
        st.markdown(
            '<p class="topbar-title">📈 F&O Trader</p>'
            '<p class="topbar-sub">Futures & Options Trading Platform</p>',
            unsafe_allow_html=True,
        )
    with right:
        username = st.session_state.get("username", "User")
        st.markdown(
            f'<p class="topbar-user">👤 {username}</p>',
            unsafe_allow_html=True,
        )
        if st.button("Sign out", key="topbar_logout"):
            for key in ["logged_in", "token", "username", "show_register"]:
                st.session_state.pop(key, None)
            st.rerun()

    st.markdown(
        '<hr style="margin:4px 0 0 0; border:none; border-top:1px solid #e1e8ed;">',
        unsafe_allow_html=True,
    )
