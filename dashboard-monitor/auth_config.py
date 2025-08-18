"""
Simple authentication for Streamlit dashboard
"""
import streamlit as st
import hashlib
import os
from datetime import datetime, timedelta

# Authorized users - in production, store these securely
AUTHORIZED_USERS = {
    "admin": os.getenv("ADMIN_PASSWORD_HASH", "5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5"),  # default: 12345
    "viewer": os.getenv("VIEWER_PASSWORD_HASH", "5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5")
}

def hash_password(password):
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth():
    """Check if user is authenticated"""
    # Initialize session state
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'auth_time' not in st.session_state:
        st.session_state.auth_time = None
    
    # Check if already authenticated and not expired (24 hour session)
    if st.session_state.authenticated and st.session_state.auth_time:
        if datetime.now() - st.session_state.auth_time < timedelta(hours=24):
            return True
        else:
            st.session_state.authenticated = False
            st.session_state.auth_time = None
    
    # Show login form
    with st.container():
        st.markdown("## 🔐 Meta Ads Budget Monitor - Login Required")
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter username")
                password = st.text_input("Password", type="password", placeholder="Enter password")
                submit = st.form_submit_button("Login", type="primary", use_container_width=True)
                
                if submit:
                    if username in AUTHORIZED_USERS:
                        if hash_password(password) == AUTHORIZED_USERS[username]:
                            st.session_state.authenticated = True
                            st.session_state.auth_time = datetime.now()
                            st.session_state.username = username
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid password")
                    else:
                        st.error("❌ Invalid username")
        
        st.markdown("---")
        st.caption("Contact your administrator for access credentials")
    
    # Stop execution if not authenticated
    st.stop()

def logout_button():
    """Add a logout button to the sidebar"""
    if st.sidebar.button("🚪 Logout", key="logout_btn"):
        st.session_state.authenticated = False
        st.session_state.auth_time = None
        st.session_state.username = None
        st.rerun()
    
    if 'username' in st.session_state:
        st.sidebar.caption(f"Logged in as: {st.session_state.username}")