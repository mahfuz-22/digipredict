import streamlit as st
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials
import json

# Security configurations
SESSION_DURATION = timedelta(hours=12)

def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'login_time' not in st.session_state:
        st.session_state.login_time = None
    if 'current_app' not in st.session_state:
        st.session_state.current_app = None

def check_session_expired():
    """Check if the current session has expired"""
    if st.session_state.login_time:
        return datetime.now() - st.session_state.login_time > SESSION_DURATION
    return True

def authenticate():
    """Handle user authentication using secrets"""
    # Get credentials from secrets
    ADMIN_USERNAME = st.secrets["admin_credentials"]["username"]
    ADMIN_PASSWORD = st.secrets["admin_credentials"]["password"]

    if st.session_state.authenticated:
        if check_session_expired():
            st.session_state.authenticated = False
            st.session_state.login_time = None
            st.rerun()
        return True

    st.title("DigiPredict Admin Portal")
    st.markdown("Please login to continue")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.login_time = datetime.now()
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    return False
'''
@st.cache_resource
def init_firebase():
    """Initialize Firebase with credentials from secrets"""
    if not firebase_admin._apps:
        # Get Firebase credentials from secrets
        cred = credentials.Certificate(st.secrets["firebase"])
        firebase_admin.initialize_app(cred)
'''

@st.cache_resource
def init_firebase():
    """Initialize Firebase with credentials from secrets"""
    try:
        if not firebase_admin._apps:
            # Get Firebase credentials and print structure (without sensitive data)
            firebase_creds = dict(st.secrets["firebase"])
            st.write("Firebase credentials keys:", list(firebase_creds.keys()))
            
            # Verify required fields
            required_fields = [
                "type", "project_id", "private_key_id", "private_key",
                "client_email", "client_id", "auth_uri", "token_uri",
                "auth_provider_x509_cert_url", "client_x509_cert_url"
            ]
            missing_fields = [field for field in required_fields if field not in firebase_creds]
            
            if missing_fields:
                st.error(f"Missing required fields: {missing_fields}")
                return
            
            cred = credentials.Certificate(firebase_creds)
            firebase_admin.initialize_app(cred)
            st.success("Firebase initialized successfully!")
    except Exception as e:
        st.error(f"Firebase initialization error: {str(e)}")
        st.error(f"Error type: {type(e)}")
        raise


def show_navigation():
    """Display navigation after successful login"""
    st.title("DigiPredict Admin Portal")
    st.markdown("### Select an Operation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👥 Onboard New Participant", use_container_width=True):
            st.session_state.current_app = 'server'
            st.rerun()
    
    with col2:
        if st.button("📝 Modify Participant Data", use_container_width=True):
            st.session_state.current_app = 'modify'
            st.rerun()

def main():
    try:
        init_session_state()
        init_firebase()
        
        # Show logout in sidebar if authenticated
        if st.session_state.authenticated:
            with st.sidebar:
                if st.button("🔙 Back to Main Menu"):
                    st.session_state.current_app = None
                    st.rerun()
                if st.button("🚪 Logout"):
                    st.session_state.clear()
                    st.rerun()

        # Check authentication
        if not authenticate():
            return

        # Show navigation or selected app
        if st.session_state.current_app is None:
            show_navigation()
        elif st.session_state.current_app == 'server':
            import server
            server.main()
        elif st.session_state.current_app == 'modify':
            import modify
            modify.main()

    except Exception as e:
            st.error(f"Application error: {str(e)}")
            st.error(f"Error type: {type(e)}")
            
            # Print the secrets structure (without actual values)
            if 'firebase' in st.secrets:
                st.write("Firebase config keys:", list(st.secrets["firebase"].keys()))
            else:
                st.error("Firebase configuration not found in secrets!")            

if __name__ == "__main__":
    main()