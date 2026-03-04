import streamlit as st
import requests

st.title("Place Order")

API_BASE = st.secrets.get("API_BASE_URL", "http://localhost:8000")

with st.form("order_form"):
    stock_code = st.text_input("Stock / Index Code", placeholder="NIFTY")
    quantity = st.number_input("Quantity (lots)", min_value=1, step=1)
    action = st.selectbox("Action", ["buy", "sell"])
    order_type = st.selectbox("Order Type", ["market", "limit", "stop_loss"])
    price = st.number_input("Price (0 for market)", min_value=0.0, step=0.05)
    submitted = st.form_submit_button("Place Order")

if submitted:
    payload = {
        "stock_code": stock_code,
        "quantity": quantity,
        "action": action,
        "order_type": order_type,
        "price": price,
    }
    try:
        resp = requests.post(f"{API_BASE}/api/orders/", json=payload)
        resp.raise_for_status()
        st.success(f"Order placed: {resp.json()}")
    except Exception as e:
        st.error(f"Order failed: {e}")
