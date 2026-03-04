import streamlit as st
import requests
from frontend.components.charts import render_pnl_chart

st.title("Portfolio Dashboard")

API_BASE = st.secrets.get("API_BASE_URL", "http://localhost:8000")


def fetch_positions():
    try:
        resp = requests.get(f"{API_BASE}/api/positions/")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        st.error(f"Failed to fetch positions: {e}")
        return {}


positions = fetch_positions()
st.subheader("Open Positions")
st.json(positions)
