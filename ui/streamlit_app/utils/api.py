# ui/streamlit_app/lib/api.py
import os, requests, streamlit as st

def api_base() -> str:
    # 1) st.secrets["API_URL"] (set in .streamlit/secrets.toml), else
    # 2) ENV var API_URL, else default to local 8000
    return (
        st.secrets.get("API_URL")
        or os.getenv("API_URL")
        or "http://localhost:8000"
    ).rstrip("/")

def _get_headers():
    """Get headers with JWT token if available."""
    headers = {"Content-Type": "application/json"}
    
    # Check for JWT token in session state
    if "jwt_token" in st.session_state and st.session_state["jwt_token"]:
        headers["Authorization"] = f"Bearer {st.session_state['jwt_token']}"
    
    return headers

def api_get(path: str, **params):
    url = f"{api_base()}{path if path.startswith('/') else '/'+path}"
    headers = _get_headers()
    
    # Longer timeout for endpoints that fetch prices (can be slow)
    if "/portfolios/" in path and path.count("/") == 2:
        timeout = 30  # Portfolio details with price fetching
    elif path == "/profile":
        timeout = 30  # Profile endpoint also fetches prices for all portfolios
    else:
        timeout = 10
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.Timeout:
        raise Exception(f"Request timed out after {timeout} seconds. The API might be slow.")
    except requests.exceptions.ConnectionError:
        raise Exception(f"Could not connect to API at {url}")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"API error: {e}")

def api_post(path: str, json=None):
    url = f"{api_base()}{path if path.startswith('/') else '/'+path}"
    headers = _get_headers()
    r = requests.post(url, json=json, headers=headers, timeout=10)  # Reduced from 15s to 10s
    r.raise_for_status()
    return r.json()

def api_delete(path: str):
    url = f"{api_base()}{path if path.startswith('/') else '/'+path}"
    headers = _get_headers()
    r = requests.delete(url, headers=headers, timeout=10)
    r.raise_for_status()
    return r.json()
