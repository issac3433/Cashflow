import requests
import streamlit as st

def _headers():
    h = {"Content-Type": "application/json"}
    token = st.session_state.get("jwt_token")
    if token:
        h["Authorization"] = f"Bearer {token}"
    else:
        h["Authorization"] = "Bearer dev"  # dev mode
    return h

def api_get(path: str):
    base = st.secrets["API_BASE"]
    r = requests.get(f"{base}{path}", headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()

def api_post(path: str, json=None):
    base = st.secrets["API_BASE"]
    r = requests.post(f"{base}{path}", headers=_headers(), json=json, timeout=30)
    r.raise_for_status()
    return r.json()
