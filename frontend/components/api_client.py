import requests
import streamlit as st

API_BASE = st.secrets.get("API_BASE_URL", "http://localhost:8000")


def _auth_headers() -> dict:
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"}


def api_get(path: str, **kwargs) -> requests.Response:
    return requests.get(f"{API_BASE}{path}", headers=_auth_headers(), timeout=15, **kwargs)


def api_post(path: str, json: dict = None, **kwargs) -> requests.Response:
    return requests.post(
        f"{API_BASE}{path}", json=json, headers=_auth_headers(), timeout=15, **kwargs
    )
