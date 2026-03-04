import streamlit as st

st.set_page_config(
    page_title="F&O Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("F&O Trading Dashboard")
st.caption("Powered by Breeze API")

st.info("Select a page from the sidebar to get started.")
