# ui/streamlit_app/utils/supabase_auth.py
import streamlit as st
import os
from typing import Optional, Dict, Any
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseAuth:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            self.client = None
        else:
            self.client: Client = create_client(self.url, self.key)
    
    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Sign up a new user."""
        if not self.client:
            raise Exception("Supabase not configured")
        
        try:
            response = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            
            # Note: For new signups, user might need email verification first
            # So we don't initialize in backend until they sign in
            return {
                "success": True,
                "user": response.user,
                "session": response.session,
                "message": "Check your email for verification link!"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Sign up failed"
            }
    
    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in an existing user."""
        if not self.client:
            raise Exception("Supabase not configured")
        
        try:
            print(f"🔍 Attempting sign in for: {email}")
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            print(f"🔍 Sign in response: user={response.user is not None}, session={response.session is not None}")
            
            if response.user and response.session:
                print(f"🔍 User ID: {response.user.id}")
                print(f"🔍 Access token: {response.session.access_token[:50]}...")
                
                # Initialize user in our backend database
                self._initialize_user_in_backend(response.session.access_token)
            
            return {
                "success": True,
                "user": response.user,
                "session": response.session,
                "access_token": response.session.access_token if response.session else None
            }
        except Exception as e:
            error_msg = str(e)
            print(f"🔍 Sign in error: {error_msg}")
            
            # Handle email not confirmed error
            if "email not confirmed" in error_msg.lower():
                return {
                    "success": False,
                    "error": error_msg,
                    "message": "Please check your email and click the verification link before signing in."
                }
            return {
                "success": False,
                "error": error_msg,
                "message": "Sign in failed"
            }
    
    def _initialize_user_in_backend(self, access_token: str):
        """Initialize user in our backend database."""
        try:
            import requests
            headers = {"Authorization": f"Bearer {access_token}"}
            print(f"🔍 Initializing user in backend with token: {access_token[:50]}...")
            
            response = requests.post(
                "http://localhost:8000/me/init-supabase",
                headers=headers,
                timeout=10
            )
            
            print(f"🔍 Backend init response: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ User initialized in backend database")
            else:
                print(f"⚠️ Failed to initialize user in backend: {response.status_code}")
                print(f"Response: {response.text}")
        except Exception as e:
            print(f"⚠️ Error initializing user in backend: {e}")
    
    def sign_out(self) -> bool:
        """Sign out the current user."""
        if not self.client:
            return False
        
        try:
            self.client.auth.sign_out()
            return True
        except Exception as e:
            print(f"Sign out error: {e}")
            return False
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Get the current authenticated user."""
        if not self.client:
            return None
        
        try:
            user = self.client.auth.get_user()
            return user.user if user else None
        except Exception as e:
            print(f"Get user error: {e}")
            return None
    
    def get_access_token(self) -> Optional[str]:
        """Get the current access token."""
        if not self.client:
            return None
        
        try:
            session = self.client.auth.get_session()
            if session and hasattr(session, 'access_token'):
                # Return the access token directly from session
                return session.access_token
            return None
        except Exception as e:
            print(f"Get token error: {e}")
            return None

def init_supabase_session():
    """Initialize Supabase session state."""
    if "supabase_user" not in st.session_state:
        st.session_state.supabase_user = None
    if "supabase_token" not in st.session_state:
        st.session_state.supabase_token = None
    if "is_authed" not in st.session_state:
        st.session_state.is_authed = False

def check_supabase_auth() -> bool:
    """Check if user is authenticated with Supabase."""
    init_supabase_session()
    
    # Try to get current user from Supabase
    auth = SupabaseAuth()
    if auth.client:
        user = auth.get_current_user()
        if user:
            # Get fresh access token
            access_token = auth.get_access_token()
            if access_token:
                st.session_state.supabase_user = user
                st.session_state.supabase_token = access_token
                st.session_state.jwt_token = access_token  # This is the key fix!
                st.session_state.is_authed = True
                return True
    
    # Clear session if not authenticated
    st.session_state.supabase_user = None
    st.session_state.supabase_token = None
    st.session_state.jwt_token = None
    st.session_state.is_authed = False
    return False

def logout():
    """Logout user and clear session."""
    auth = SupabaseAuth()
    auth.sign_out()
    
    st.session_state.supabase_user = None
    st.session_state.supabase_token = None
    st.session_state.jwt_token = None  # Clear JWT token too
    st.session_state.is_authed = False
    st.rerun()

def get_user_id() -> Optional[str]:
    """Get current user ID."""
    if st.session_state.is_authed and st.session_state.supabase_user:
        # Supabase User object has attributes, not dictionary keys
        return getattr(st.session_state.supabase_user, 'id', None)
    return None

def get_user_email() -> Optional[str]:
    """Get current user email."""
    if st.session_state.is_authed and st.session_state.supabase_user:
        # Supabase User object has attributes, not dictionary keys
        return getattr(st.session_state.supabase_user, 'email', None)
    return None

def is_supabase_configured() -> bool:
    """Check if Supabase is properly configured."""
    return bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"))
