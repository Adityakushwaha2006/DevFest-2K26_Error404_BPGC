"""
NEXUS - AI-Powered Networking Intelligence System
==================================================
Main Application - Routes to Landing Page or Dashboard
"""

import streamlit as st
import subprocess
import os
import sys
from logic.landing_page import render_landing_page
from logic.dashboard import render_dashboard

# Page config
st.set_page_config(page_title="NEXUS", layout="wide", initial_sidebar_state="collapsed")


def start_logistic_mind():
    """
    Start Logistic Mind backend as a subprocess (once per session).
    Runs in background and watches chat logs for entity extraction.
    """
    if 'logistic_mind_started' not in st.session_state:
        try:
            # Get path to logistic_mind.py
            backend_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "backend"
            )
            logistic_mind_path = os.path.join(backend_dir, "logistic_mind.py")
            
            if os.path.exists(logistic_mind_path):
                # Start as background subprocess
                subprocess.Popen(
                    [sys.executable, logistic_mind_path],
                    cwd=backend_dir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )
                st.session_state.logistic_mind_started = True
                print("[OK] Logistic Mind auto-started in background")
            else:
                print(f"[WARNING] Logistic Mind not found at: {logistic_mind_path}")
        except Exception as e:
            print(f"[WARNING] Failed to start Logistic Mind: {e}")
            st.session_state.logistic_mind_started = False


# Auto-start Logistic Mind backend
start_logistic_mind()

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
