"""
DEMO: Dashboard Integration
============================
Quick example showing how to use the dashboard component.
"""

import streamlit as st
from logic.dashboard import render_dashboard

# Configure page
st.set_page_config(page_title="Nexus Console", layout="wide")

# Render the dashboard
render_dashboard()
