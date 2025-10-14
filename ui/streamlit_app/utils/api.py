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

def api_get(path: str, **params):
    url = f"{api_base()}{path if path.startswith('/') else '/'+path}"
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                continue  # Retry
            raise Exception(f"Request timed out after {max_retries + 1} attempts. The API might be slow.")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Could not connect to API at {url}")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"API error: {e}")

def api_post(path: str, json=None):
    url = f"{api_base()}{path if path.startswith('/') else '/'+path}"
    r = requests.post(url, json=json, timeout=15)
    r.raise_for_status()
    return r.json()
