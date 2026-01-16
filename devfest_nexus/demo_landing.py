"""
DEMO: Landing Page Integration
================================
Quick example showing how to use the landing page in your Streamlit app.
"""

import streamlit as st
from logic.landing_page import render_landing_page

# DEMO: Simple integration
st.set_page_config(page_title="Nexus Demo", layout="wide")

# Render the custom landing page
render_landing_page()

# Note: The landing page is rendered in an iframe at 1080px height.
# It includes:
# - 5-second SVG animation intro (NEXUS letters drawing)
# - Particle physics background that responds to mouse movement
# - Three context cards: Student/Intern, Founder, Researcher
# - Matte charcoal aesthetic with glassmorphism effects
