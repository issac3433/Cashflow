# ui/streamlit_app/utils/clerk_auth.py
import streamlit as st
import os
from typing import Optional, Dict, Any
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ClerkAuth:
    def __init__(self):
        self.publishable_key = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
        self.secret_key = os.getenv("CLERK_SECRET_KEY")
        self.api_url = "https://api.clerk.com/v1"
        
    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token with Clerk and return user info."""
        if not self.secret_key:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            # Verify the token
            response = requests.get(
                f"{self.api_url}/sessions/{token}/verify",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Clerk verification failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error verifying token: {e}")
            return None
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from Clerk."""
        if not self.secret_key:
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{self.api_url}/users/{user_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get user info: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None

def init_clerk_session():
    """Initialize Clerk session state."""
    if "clerk_user" not in st.session_state:
        st.session_state.clerk_user = None
    if "clerk_token" not in st.session_state:
        st.session_state.clerk_token = None
    if "is_authed" not in st.session_state:
        st.session_state.is_authed = False

def check_clerk_auth() -> bool:
    """Check if user is authenticated with Clerk."""
    init_clerk_session()
    
    # Check if we have a token in URL params (from Clerk redirect)
    query_params = st.query_params
    if "token" in query_params:
        token = query_params["token"]
        st.session_state.clerk_token = token
        
        # Verify token with Clerk
        clerk_auth = ClerkAuth()
        user_data = clerk_auth.get_user_from_token(token)
        
        if user_data:
            st.session_state.clerk_user = user_data
            st.session_state.is_authed = True
            # Clear the token from URL
            st.query_params.clear()
            return True
    
    # Check if we already have a valid session
    if st.session_state.is_authed and st.session_state.clerk_user:
        return True
    
    return False

def get_clerk_login_url() -> str:
    """Get Clerk login URL."""
    publishable_key = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY")
    if not publishable_key:
        return "#"
    
    # This would typically redirect to your Clerk-hosted login page
    # For now, we'll use a simple approach
    return f"https://accounts.clerk.dev/sign-in?redirect_url={st.get_option('server.baseUrlPath') or 'http://localhost:8501'}"

def logout():
    """Logout user and clear session."""
    st.session_state.clerk_user = None
    st.session_state.clerk_token = None
    st.session_state.is_authed = False
    st.rerun()

def get_user_id() -> Optional[str]:
    """Get current user ID."""
    if st.session_state.is_authed and st.session_state.clerk_user:
        return st.session_state.clerk_user.get("user_id")
    return None

def get_user_email() -> Optional[str]:
    """Get current user email."""
    if st.session_state.is_authed and st.session_state.clerk_user:
        return st.session_state.clerk_user.get("email_addresses", [{}])[0].get("email_address")
    return None
