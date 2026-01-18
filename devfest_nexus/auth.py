import os
import streamlit as st
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests

# Configuration
# Ensure 'client_secret.json' is in the root directory
CLIENT_SECRETS_FILE = "client_secret.json" 
SCOPES = [
    'openid', 
    'https://www.googleapis.com/auth/userinfo.email', 
    'https://www.googleapis.com/auth/userinfo.profile'
]
# Ensure this matches your Google Cloud Console "Authorized redirect URIs"
REDIRECT_URI = "http://localhost:8501" 

def check_login():
    """
    Checks session state for login and handles the OAuth 2.0 flow.
    Returns:
        True if logged in, False otherwise.
    """
    
    # 1. Check if already authenticated in Session State
    if "google_auth_token" in st.session_state:
        return True

    # 2. Handle the OAuth Redirect (Code Exchange)
    # When Google redirects back, it adds '?code=...' to the URL
    if "code" in st.query_params:
        try:
            code = st.query_params["code"]
            
            # Create flow to fetch the token
            flow = Flow.from_client_secrets_file(
                CLIENT_SECRETS_FILE,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Verify token ID with 10 seconds of leeway for clock skew
            # This prevents "Token used too early" errors
            id_info = id_token.verify_oauth2_token(
                credentials.id_token,
                requests.Request(),
                audience=flow.client_config["client_id"],
                clock_skew_in_seconds=10 
            )

            # Store user info in session
            st.session_state["google_auth_token"] = credentials
            st.session_state["user_email"] = id_info.get("email")
            st.session_state["user_name"] = id_info.get("name")
            
            # Clear query params to clean URL
            st.query_params.clear()
            st.rerun()
            
        except Exception as e:
            st.error(f"Authentication failed: {e}")
            print(f"Auth Error: {e}")
            return False
            
    # 3. Show Login Button if not logged in
    else:
        show_login_button()
        return False

def show_login_button():
    """
    Generates the Google Login URL and displays a styled button.
    Uses target="_top" to ensure the login page breaks out of any iframes.
    """
    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        # HTML Button with target="_top"
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; margin-top: 50px;">
                <a href="{auth_url}" target="_top" style="
                    background-color: #4285F4;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    font-family: sans-serif;
                    border-radius: 5px;
                    font-weight: bold;
                    transition: background-color 0.3s;">
                    Sign in with Google
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.error("⚠️ client_secret.json not found! Please add it to the project root.")
    except Exception as e:
        st.error(f"⚠️ Error loading login configuration: {e}")

def logout():
    """Clears authentication keys from session state and reruns the app."""
    for key in ["google_auth_token", "user_email", "user_name"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()