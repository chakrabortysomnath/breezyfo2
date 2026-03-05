import streamlit as st
from components.api_client import api_get


@st.cache_data(ttl=30, show_spinner=False)
def _fetch_positions(token: str):
    """Cache positions for 30 s to avoid a blocking API call on every rerun."""
    resp = api_get("/api/positions/")
    return resp.status_code, resp.json()


def render_dashboard_tab() -> None:
    st.subheader("Portfolio Dashboard")

    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("↺ Refresh", key="refresh_positions"):
            st.cache_data.clear()

    try:
        token = st.session_state.get("token", "")
        status, data = _fetch_positions(token)
        if status == 401:
            st.error("Session expired. Please sign out and sign back in.")
            return
        st.subheader("Open Positions")
        st.json(data)
    except Exception as e:
        st.error(f"Failed to fetch positions: {e}")
