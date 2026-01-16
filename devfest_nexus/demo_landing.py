"""
NEXUS - Landing Page Demo
==========================
This script demonstrates how to integrate the custom landing page
into the main Streamlit application.

Usage:
    streamlit run demo_landing.py
"""

import streamlit as st
from logic.landing_page import render_landing_page

# Configure page
st.set_page_config(
    page_title="Nexus - Intelligent Networking",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="collapsed"  # Hide sidebar for landing page
)

# Remove default Streamlit padding and styling
st.markdown("""
<style>
    /* Remove default Streamlit padding */
    .main {
        padding: 0 !important;
    }
    
    /* Hide Streamlit header and footer */
    header {
        visibility: hidden;
    }
    
    footer {
        visibility: hidden;
    }
    
    /* Remove top padding */
    .block-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Hide the hamburger menu */
    #MainMenu {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Render the landing page
render_landing_page()
