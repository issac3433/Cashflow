import streamlit as st
from utils.api import api_get

st.set_page_config(page_title="Cashflow", page_icon="💸", layout="wide")

if not st.session_state.get("is_authed"):
    st.switch_page("Login.py")

left, right = st.columns([4,1])
with left:
    st.title("💸 Cashflow — Home")
    try:
        who = api_get("/auth/debug")
        st.caption(f"Signed in as: `{who.get('user_id')}`")
    except Exception:
        st.caption("Signed in")

with right:
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("Login.py")

st.markdown("### Quick Links")
c1, c2 = st.columns(2)
with c1:
    if st.button("📁 Go to Portfolio"):
        st.switch_page("pages/01_Portfolio.py")
with c2:
    if st.button("📈 Go to Forecast"):
        st.switch_page("pages/02_Forecast.py")

st.info("Use the buttons above to manage holdings and run a 12-month forecast.")
