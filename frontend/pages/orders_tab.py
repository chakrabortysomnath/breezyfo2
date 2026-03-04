import streamlit as st
from components.api_client import api_post


def render_orders_tab() -> None:
    st.subheader("Place Order")

    with st.form("order_form"):
        stock_code = st.text_input("Stock / Index Code", placeholder="NIFTY")
        quantity = st.number_input("Quantity (lots)", min_value=1, step=1)
        action = st.selectbox("Action", ["buy", "sell"])
        order_type = st.selectbox("Order Type", ["market", "limit", "stop_loss"])
        price = st.number_input("Price (0 for market)", min_value=0.0, step=0.05)
        submitted = st.form_submit_button("Place Order", use_container_width=True)

    if submitted:
        payload = {
            "stock_code": stock_code,
            "quantity": int(quantity),
            "action": action,
            "order_type": order_type,
            "price": price,
        }
        try:
            resp = api_post("/api/orders/", json=payload)
            if resp.status_code == 401:
                st.error("Session expired. Please sign out and sign back in.")
                return
            resp.raise_for_status()
            st.success(f"Order placed successfully: {resp.json()}")
        except Exception as e:
            st.error(f"Order failed: {e}")
