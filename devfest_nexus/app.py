import streamlit as st
import sys
import os

# Path setup to ensure imports work relative to the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from devfest_nexus.auth import check_login, logout
from devfest_nexus.logic import dashboard, landing_page


# Import code modules
from devfest_nexus.auth import check_login, logout
from devfest_nexus.logic import dashboard, chat_engine, landing_page

# Page Config
st.set_page_config(page_title="NEXUS | AI Networking", layout="wide")

def main():
    # Capture 'landing' request from query params
    query_page = st.query_params.get("page", "landing")
    
    # If explicitly requesting landing page, show it and return
    # This preserves the public landing page functionality
    if query_page == "landing":
        landing_page.render()
        return

    # --- AUTHENTICATION GATE ---
    # For all other pages (dashboard), enforce login
    if not check_login():
        st.stop()  # Stop execution if not logged in

    # --- MAIN APP LOGIC (Only runs if logged in) ---
    
    # Initialize session state for mode if present in URL
    if "mode" in st.query_params:
        st.session_state["selected_mode"] = st.query_params["mode"]

    # Sidebar for User Profile & Navigation
    with st.sidebar:
        # Use a default user name if missing
        user_name = st.session_state.get("user_name", "User")
        # Use ui-avatars for profile picture
        st.image(f"https://ui-avatars.com/api/?name={user_name}&background=random", width=50)
        st.write(f"**{user_name}**")
        st.caption(st.session_state.get("user_email"))
        
        if st.button("Logout"):
            logout()
            
        st.markdown("---")
        app_mode = st.radio("Navigate", ["Dashboard", "Search & Discovery"])

    # Load respective modules based on selection
    if app_mode == "Dashboard":
        dashboard.render() 
        # chat_engine.render_chat() # Commented out until verified if it should be here or inside dashboard
        
    elif app_mode == "Search & Discovery":
        # If user wants to go back to landing page from sidebar
        landing_page.render()

if __name__ == "__main__":
    main()