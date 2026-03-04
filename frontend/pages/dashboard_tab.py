import streamlit as st
from components.api_client import api_get
from components.charts import render_pnl_chart


def render_dashboard_tab() -> None:
    st.subheader("Portfolio Dashboard")

    try:
        resp = api_get("/api/positions/")
        if resp.status_code == 401:
            st.error("Session expired. Please sign out and sign back in.")
            return
        resp.raise_for_status()
        positions = resp.json()
        st.subheader("Open Positions")
        st.json(positions)
    except Exception as e:
        st.error(f"Failed to fetch positions: {e}")
