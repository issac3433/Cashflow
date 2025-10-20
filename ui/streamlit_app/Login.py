import streamlit as st
from utils.api import api_get, api_post
from utils.supabase_auth import SupabaseAuth, check_supabase_auth, logout, get_user_email, is_supabase_configured
import os

st.set_page_config(page_title="Cashflow Login", page_icon="🔐", layout="centered")

# Check if user is already authenticated
if check_supabase_auth():
    st.switch_page("pages/00_Home.py")

st.title("🔐 Cashflow — Login")

# Check if Supabase is configured
supabase_configured = is_supabase_configured()

if supabase_configured:
    st.success("🔥 Supabase Authentication Enabled")
    
    # Initialize Supabase auth
    auth = SupabaseAuth()
    
    # Create tabs for sign in and sign up
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    with tab1:
        st.subheader("🔑 Sign In")
        st.write("Enter your email and password to access your portfolios.")
        
        with st.form("sign_in_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign In", type="primary")
            
            if submit:
                if email and password:
                    with st.spinner("Signing in..."):
                        result = auth.sign_in(email, password)
                    
                    # Debug output
                    st.write("**Debug Info:**")
                    st.write(f"- Success: {result.get('success', False)}")
                    st.write(f"- Message: {result.get('message', 'No message')}")
                    st.write(f"- Error: {result.get('error', 'No error')}")
                    
                    if result["success"]:
                        st.success("✅ Signed in successfully!")
                        
                        # Store user info in session
                        st.session_state.supabase_user = result["user"]
                        st.session_state.supabase_token = result["access_token"]
                        st.session_state.is_authed = True
                        st.session_state.jwt_token = result["access_token"]  # For API calls
                        
                        st.write("**Session State After Sign In:**")
                        st.write(f"- is_authed: {st.session_state.get('is_authed', False)}")
                        st.write(f"- jwt_token: {'Present' if st.session_state.get('jwt_token') else 'Missing'}")
                        st.write(f"- supabase_user: {'Present' if st.session_state.get('supabase_user') else 'Missing'}")
                        
                        st.info("🔄 Redirecting to home page...")
                        
                        # Force redirect to home page
                        st.switch_page("pages/00_Home.py")
                    else:
                        error_msg = result.get('error', '')
                        if 'email not confirmed' in error_msg.lower():
                            st.error("❌ Email not verified!")
                            st.info("📧 Please check your email and click the verification link, then try signing in again.")
                        else:
                            st.error(f"❌ {result['message']}: {error_msg}")
                else:
                    st.warning("Please enter both email and password.")
    
    with tab2:
        st.subheader("📝 Sign Up")
        st.write("Create a new account to start managing your portfolios.")
        
        with st.form("sign_up_form"):
            email = st.text_input("Email", placeholder="your@email.com", key="signup_email")
            password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Sign Up", type="primary")
            
            if submit:
                if email and password and confirm_password:
                    if password != confirm_password:
                        st.error("❌ Passwords don't match!")
                    elif len(password) < 6:
                        st.error("❌ Password must be at least 6 characters!")
                    else:
                        result = auth.sign_up(email, password)
                        if result["success"]:
                            st.success("✅ Account created! " + result["message"])
                        else:
                            st.error(f"❌ {result['message']}: {result.get('error', '')}")
                else:
                    st.warning("Please fill in all fields.")
    
    # Connection test
    st.divider()
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🧪 Test Backend Connection"):
            try:
                res = api_get("/debug")
                st.success(f"✅ Backend connected: {res.get('ok')}")
            except Exception as e:
                st.error(f"❌ Backend connection failed: {e}")
    
    with col2:
        if st.button("🔥 Test Supabase Connection"):
            try:
                user = auth.get_current_user()
                if user:
                    # Supabase User object has attributes, not dictionary keys
                    email = getattr(user, 'email', 'Unknown')
                    st.success(f"✅ Supabase connected! User: {email}")
                else:
                    st.info("ℹ️ Supabase connected (no user signed in)")
            except Exception as e:
                st.error(f"❌ Supabase connection failed: {e}")

else:
    st.warning("⚠️ Supabase not configured. Using development mode.")
    
    tab1, tab2 = st.tabs(["Quick Dev Login", "Manual JWT"])
    
    with tab1:
        st.write("Use this for local development (no real auth).")
        if st.button("Initialize Dev User"):
            try:
                res = api_post("/me/init")
                st.success(f"Initialized user: {res.get('id')}")
                st.session_state["is_authed"] = True
                st.switch_page("pages/00_Home.py")
            except Exception as e:
                st.error(f"Failed: {e}")
    
    with tab2:
        st.write("Paste a **JWT** token for testing.")
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
                    res = api_get("/debug")
                    st.success(f"Valid ✅ — user_id: {res.get('user_id')}")
                    st.switch_page("pages/00_Home.py")
                except Exception as e:
                    st.error(f"Invalid ❌ — {e}")
