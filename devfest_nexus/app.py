"""
NEXUS - AI-Powered Networking Intelligence System
==================================================
Main Application - Routes to Landing Page or Dashboard
"""

import streamlit as st
from logic.landing_page import render_landing_page
from logic.dashboard import render_dashboard

# Page config
st.set_page_config(page_title="NEXUS", layout="wide", initial_sidebar_state="collapsed")

# Check query parameters for navigation and mode
query_params = st.query_params

# Capture selected mode from landing page
if 'mode' in query_params:
    st.session_state.selected_mode = query_params['mode']

# Handle page navigation
if 'page' in query_params and query_params['page'] == 'dashboard':
    if 'page' not in st.session_state or st.session_state.page != 'dashboard':
        st.session_state.page = 'dashboard'
        st.rerun()

# Session state for page routing
if 'page' not in st.session_state:
    st.session_state.page = 'landing'  # 'landing' or 'dashboard'

# Initialize selected_mode if not set
if 'selected_mode' not in st.session_state:
    st.session_state.selected_mode = 'Student / Intern'  # Default

# Simple routing - show landing page or dashboard
if st.session_state.page == 'landing':
    render_landing_page()
else:
    render_dashboard()
