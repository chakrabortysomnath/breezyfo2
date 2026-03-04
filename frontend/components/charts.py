import streamlit as st
import pandas as pd
import plotly.express as px


def render_pnl_chart(data: list[dict]):
    if not data:
        st.warning("No P&L data available.")
        return
    df = pd.DataFrame(data)
    fig = px.line(df, x="date", y="pnl", title="Daily P&L")
    st.plotly_chart(fig, use_container_width=True)
