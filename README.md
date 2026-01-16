# NEXUS - Quick Start Guide

## 🚀 Getting Started (5 Minutes)

### Step 1: Environment Setup
```bash
# Navigate to project directory
cd "Devfest 25/DevFest-2K26_Error404_BPGC"

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Keys
```bash
# Copy environment template
copy .env.example .env

# Edit .env and add your keys:
# - GITHUB_TOKEN (get from https://github.com/settings/tokens)
# - GEMINI_API_KEY (get from https://makersuite.google.com/app/apikey)
```

### Step 3: Test the Identity Resolution
```bash
cd backend
python demo_identity_resolution.py <github_username>

# Example:
python demo_identity_resolution.py torvalds
```

## 📁 Project Structure

```
DevFest-2K26_Error404_BPGC/
├── backend/
│   ├── identity_node.py          # Core node classes
│   ├── platform_fetchers.py      # GitHub/Dev.to/LinkedIn fetchers
│   ├── demo_identity_resolution.py  # Demo script
│   ├── scoring_engine.py         # (TO BE CREATED)
│   └── llm_agent.py              # (TO BE CREATED)
├── frontend/
│   └── app.py                    # (TO BE CREATED)
├── data/
│   └── mock_profiles.json        # (TO BE CREATED)
├── requirements.txt
├── .env.example
└── README.md
```

## 🎯 What We've Built So Far

### ✅ Completed
1. **Core Identity System**
   - `IdentityNode` class for platform data
   - `IdentityGraph` for multi-platform validation
   - Cross-reference detection
   - Confidence scoring

2. **Platform Fetchers**
   - GitHub API integration (full featured)
   - Dev.to API integration (full featured)
   - Mock LinkedIn (for demo)

3. **Demo Flow**
   - Seed from GitHub username
   - Auto-discover Twitter/Dev.to handles
   - Cross-validate across platforms
   - Synthesize unified profile

### 🔨 Next Steps

1. **Scoring Engine** (Priority 1)
   - Momentum score calculation
   - Readiness score formula
   - Sentiment analysis integration

2. **LLM Integration** (Priority 2)
   - Message drafting
   - Context summarization
   - Style mirroring

3. **Frontend** (Priority 3)
   - Streamlit dashboard
   - Force-directed graph visualization
   - Dossier panel

## 🧪 Testing the Demo

### Test with Real GitHub Users
```bash
# Test with developers who have cross-platform presence
python demo_identity_resolution.py kentcdodds  # Has Twitter + Dev.to
python demo_identity_resolution.py sindresorhus
python demo_identity_resolution.py wesbos
```

### Expected Output
```
==============================================================
NEXUS - Node-Based Identity Resolution Demo
==============================================================

🌱 Seed: github/kentcdodds

📡 Step 1: Fetching github profile...
✅ Fetched: Kent C. Dodds
   Bio: Improving the world with quality software...
   Activities: 30 events

🔍 Step 2: Discovering cross-platform references...
   Found 2 cross-references:
      → twitter: kentcdodds (from twitter_username)
      → devto: kentcdodds (from blog)

📡 Step 3: Fetching cross-referenced profiles...
   Fetching twitter/kentcdodds...
   Fetching devto/kentcdodds...
   ✅ Success: Kent C. Dodds

🎯 Step 4: Cross-validation analysis...
   Overall Identity Confidence: 85.00%
   ✅ HIGH CONFIDENCE - Identity validated across platforms

...
```

## 🎨 Architecture Diagram

```
User Input (GitHub: "username")
        ↓
┌──────────────────────────────────┐
│   GitHubFetcher                  │
│   - Fetch profile                │
│   - Extract cross-refs           │
│   - Parse activity               │
└──────────────────────────────────┘
        ↓
┌──────────────────────────────────┐
│   IdentityGraph                  │
│   - Add GitHub node              │
│   - Discover Twitter/Dev.to      │
│   - Fetch additional nodes       │
│   - Calculate confidence         │
└──────────────────────────────────┘
        ↓
┌──────────────────────────────────┐
│   Unified Profile                │
│   - Name (validated)             │
│   - All activities (sorted)      │
│   - Confidence score             │
│   - Platform connections         │
└──────────────────────────────────┘
        ↓
    (Next: Scoring Engine + LLM + UI)
```

## 🔑 Key Features Implemented

- ✅ **Multi-platform data aggregation** (GitHub + Dev.to working)
- ✅ **Cross-reference validation** (bidirectional link checking)
- ✅ **Confidence scoring** (name/bio/location matching)
- ✅ **Activity timeline** (aggregated from all platforms)
- ✅ **Fuzzy matching** (handles name variations)
- ✅ **Error handling** (graceful failures)

## 💡 Pro Tips

1. **GitHub Token**: Without a token, you're limited to 60 requests/hour. With token: 5000/hour
2. **Dev.to**: No auth needed, completely free
3. **Twitter**: For hackathon, use mock data or Nitter scraping
4. **LinkedIn**: Use mock data only (real scraping violates ToS)

## 🚨 Troubleshooting

### "Module not found" error
```bash
# Make sure you're in the right directory and venv is activated
pip install -r requirements.txt
```

### GitHub API rate limit
```bash
# Add GITHUB_TOKEN to .env file
# Check rate limit: curl https://api.github.com/rate_limit
```

### Cross-references not found
```
# Normal! Not all GitHub users have Twitter/Dev.to listed
# Try users like: kentcdodds, wesbos, sindresorhus
```

## 📊 Validation Metrics

The system calculates confidence based on:
- **30%**: Name matching across platforms
- **40%**: Bidirectional cross-references (GitHub links to Twitter AND Twitter links to GitHub)
- **20%**: Metadata matching (location, company)
- **10%**: Bio keyword overlap

## Next: Building the Scoring Engine
Run the next demo to see momentum scoring in action!
