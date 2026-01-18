import streamlit as st
import landing_page  # Assuming your landing page file is landing_page.py
import dashboard     # Assuming your dashboard file is dashboard.py

# --- PAGE CONFIGURATION ---
st.set_page_config(layout="wide", page_title="NEXUS", initial_sidebar_state="collapsed")

# --- ROUTER LOGIC ---
def main():
    # 1. Get current parameters
    # st.query_params returns a dictionary-like object
    query_params = st.query_params
    
    # 2. Check for Logout
    if query_params.get("logout", [""])[0] == "true":
        # Clear session and params
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

    # 3. Determine current page
    # Default to 'landing' if no page is set
    current_page = query_params.get("page", "landing")

    # 4. Render the appropriate view
    if current_page == "dashboard":
        # Capture the 'mode' if selected from landing page
        if "mode" in query_params:
            st.session_state.selected_mode = query_params["mode"]
        
        dashboard.render()
        
    else:
        # Default: Render Landing Page
        landing_page.render()

if __name__ == "__main__":
    main()