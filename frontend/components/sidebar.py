import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.header("Settings")
        st.text_input("API Base URL", key="api_base_url")
        st.divider()
        st.caption("F&O Trading App v1.0")
