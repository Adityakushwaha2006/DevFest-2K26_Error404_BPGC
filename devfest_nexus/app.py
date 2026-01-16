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

# Session state for page routing
if 'page' not in st.session_state:
    st.session_state.page = 'landing'  # 'landing' or 'dashboard'

# Simple routing - show landing page or dashboard
if st.session_state.page == 'landing':
    render_landing_page()
else:
    render_dashboard()
