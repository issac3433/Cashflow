import streamlit as st
from utils.api import api_get
from utils.supabase_auth import get_user_email, logout
from utils.mobile_css import inject_mobile_css
import os

st.set_page_config(page_title="Cashflow", page_icon="💸", layout="wide")
inject_mobile_css()

if not st.session_state.get("is_authed"):
    st.switch_page("Login.py")

left, right = st.columns([4,1])
with left:
    st.title("💸 Cashflow — Home")
    try:
        who = api_get("/debug")
        user_id = who.get('user_id')
        
        # Try to get email from Supabase if available
        email = get_user_email()
        if email:
            st.caption(f"Signed in as: `{email}`")
        else:
            st.caption(f"Signed in as: `{user_id}`")
            
    except Exception:
        st.caption("Signed in")

with right:
    if st.button("🚪 Logout"):
        logout()

st.markdown("### Quick Links")
c1, c2 = st.columns(2)
with c1:
    if st.button("📁 Go to Portfolio"):
        st.switch_page("pages/01_Portfolio.py")
with c2:
    if st.button("📈 Go to Forecast"):
        st.switch_page("pages/02_Forecast.py")

st.info("Use the buttons above to manage holdings and run a 12-month forecast.")
