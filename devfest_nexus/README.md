# Nexus - Intelligent Networking Engine

## Overview
NEXUS is an AI-powered networking intelligence system built for DevFest 2026. It analyzes real-time developer activity, calculates connection readiness scores, and generates personalized outreach strategies.

## Project Structure
```
devfest_nexus/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .gitignore             # Git ignore rules
├── .streamlit/
│   └── config.toml        # Streamlit theme configuration
├── assets/                # Images and media files
├── components/            # Reusable UI components
└── logic/                 # Backend integration stubs
    ├── data_loader.py     # Data fetching and graph generation
    ├── ai_engine.py       # LLM integration for strategy & messaging
    └── scoring.py         # Momentum, relevance, readiness calculations
```

## Setup Instructions

### 1. Create Virtual Environment
```bash
cd devfest_nexus
python -m venv venv
```

### 2. Activate Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Features
- 🌐 **Network Exploration**: Force-directed graph visualization of connections
- 🎯 **Target Analysis**: Deep dive into specific prospects with momentum tracking
- ⚡ **Strategy Execution**: AI-powered message drafting and timing recommendations

## Backend Integration Points
All backend functions are stubbed in the `logic/` directory with comprehensive docstrings. Frontend can be developed independently while backend team implements:

- `logic/data_loader.py` - ChromaDB/vector store integration
- `logic/ai_engine.py` - Gemini/OpenAI LLM calls
- `logic/scoring.py` - Time series analysis and scoring algorithms

## Development Notes
- The UI is fully functional with placeholder data
- All backend calls are marked with TODO comments
- Session state management is configured for multi-step workflow
- Custom CSS styling applied for premium aesthetics

## Team
- **Frontend**: Streamlit + streamlit-agraph
- **Backend**: Python + LLM + Vector DB (to be integrated)
- **Visualization**: Plotly + NetworkX
