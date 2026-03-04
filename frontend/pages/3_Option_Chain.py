import streamlit as st
import requests
import pandas as pd

st.title("Option Chain")

API_BASE = st.secrets.get("API_BASE_URL", "http://localhost:8000")

col1, col2, col3 = st.columns(3)
with col1:
    stock_code = st.text_input("Stock / Index", value="NIFTY")
with col2:
    expiry_date = st.text_input("Expiry Date (YYYY-MM-DD)", placeholder="2026-03-27")
with col3:
    option_type = st.selectbox("Option Type", ["call", "put"])

if st.button("Fetch Option Chain"):
    payload = {"stock_code": stock_code, "expiry_date": expiry_date, "option_type": option_type}
    try:
        resp = requests.post(f"{API_BASE}/api/market/option-chain", json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data:
            st.dataframe(pd.DataFrame(data))
        else:
            st.warning("No data returned.")
    except Exception as e:
        st.error(f"Error: {e}")
