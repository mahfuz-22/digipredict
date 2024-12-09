# admin_auth.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
from functools import wraps

def check_admin_auth():
    """Check if admin is authenticated in the current session"""
    return 'admin_authenticated' in st.session_state and st.session_state.admin_authenticated

def admin_login_required(func):
    """Decorator to require admin authentication for pages"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not check_admin_auth():
            st.warning("Please login as admin first")
            show_admin_login()
            return
        return func(*args, **kwargs)
    return wrapper

def show_admin_login():
    """Display admin login form"""
    st.subheader("Admin Login")
    
    # Create login form
    with st.form("admin_login"):
        email = st.text_input("Admin Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            try:
                # Verify admin credentials using Firebase Auth
                user = auth.get_user_by_email(email)
                
                # Check if user has admin custom claim
                if user.custom_claims and user.custom_claims.get('admin'):
                    st.session_state.admin_authenticated = True
                    st.session_state.admin_email = email
                    st.success("Successfully logged in as admin!")
                    st.rerun()
                else:
                    st.error("User is not authorized as admin")
            except auth.UserNotFoundError:
                st.error("Invalid credentials")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

def init_admin():
    """Initialize admin authentication"""
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False