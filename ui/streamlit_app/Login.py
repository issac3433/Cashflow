import streamlit as st
from utils.api import api_get, api_post

st.set_page_config(page_title="Cashflow Login", page_icon="🔐", layout="centered")
st.title("🔐 Cashflow — Login")

tab1, tab2 = st.tabs(["Quick Dev Login", "Paste Clerk JWT"])

with tab1:
    st.write("Use this for local demos (no real auth).")
    if st.button("Initialize Dev User"):
        try:
            res = api_post("/me/init")
            st.success(f"Initialized user: {res.get('id')}")
            st.session_state["is_authed"] = True
            st.switch_page("pages/00_Home.py")
        except Exception as e:
            st.error(f"Failed: {e}")

with tab2:
    st.write("Paste a **Clerk** JWT (RS256, audience `api`).")
    token = st.text_area("JWT", height=140, placeholder="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...")
    colA, colB = st.columns([1,1])
    with colA:
        if st.button("Use This Token"):
            if token.strip():
                st.session_state["jwt_token"] = token.strip()
                st.session_state["is_authed"] = True
                st.success("Token saved to session.")
            else:
                st.warning("Please paste a token first.")
    with colB:
        if st.button("Test Token"):
            try:
                if token.strip():
                    st.session_state["jwt_token"] = token.strip()
                res = api_get("/auth/debug")
                st.success(f"Valid ✅ — user_id: {res.get('user_id')}")
                st.switch_page("pages/00_Home.py")
            except Exception as e:
                st.error(f"Invalid ❌ — {e}")
