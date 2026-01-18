# NEXUS: Project Context & Architecture Documentation

## 1. Project Overview
**NEXUS** is an AI-powered professional networking intelligence system. It shifts from static profile matching to dynamic **Intent & Momentum Analysis**, identifying the "Path of Least Resistance" for connections.

**Core Value Prop**:
1.  **Context**: Semantic relevance (shared tech stack, interests).
2.  **Momentum**: Current activity levels (is the user active *now*?).
3.  **Intent**: Explicit signals (e.g., "hiring", "learning Rust").

---

## 2. Technical Architecture

### 2.1 High-Level Pipeline
The system uses a "Second Brain" architecture where an autonomous agent (`logistic_mind.py`) watches user interactions and orchestrates the backend pipeline:

```
User Chat (Frontend) -> [log file] -> Logistic Mind (Watcher)
                                          (Analyses Chat for Entities)
                                          ↓
                                    [Entity Extraction] (Gemini/Regex)
                                          ↓
                                    [Backend Pipeline] (NexusOrchestrator)
                                      (Fetches & Consolidates Data)
                                          ↓
                                    [Scoring] (Gemini CIT Model)
                                      (Computes Context-Intent-Timing)
                                          ↓
                                    [State Update] (frontend_state.json)
                                          ↓
User Dashboard (Frontend) <- [State Read]
```

### 2.2 Tech Stack
-   **Backend Logic**: Python 3.10+, `google-generativeai`.
-   **Autonomous Agent**: `logistic_mind.py` (Background process).
-   **Frontend**: Streamlit (Chat + Dashboard).
-   **Communication**: File-based IPC (JSON logs and state files).
-   **Database**: ChromaDB (Vector Search), JSON files (Storage).
-   **APIs**:
    -   GitHub API (Real-time data).
    -   Dev.to API (Content).
    -   Google Custom Search (Discovery).
    -   Gemini API (Analysis & Scoring).

---

## 3. Directory Structure & Key Files

### Root
-   `README.md`: Setup and quickstart.
-   `.env.example`: Config template.

### `backend/` (Core Logic)
-   `logistic_mind.py`: **Autonomous Orchestrator**. The "Brain" of the system.
    -   Watches `data/conversations/`.
    -   Extracts entities (GitHub, Twitter, Names).
    -   Triggers `nexus_main` pipeline.
    -   Computes CIT (Context, Intent, Timing) scores using Gemini.
    -   Updates `frontend_state.json` and `active_context.json` for the UI.
-   `nexus_main.py`: **Pipeline Orchestrator**. Coordinates data fetching and consolidation.
-   `nexus_logic.py`: **Data Controller**. Handles profile consolidation logic.
-   `nexus_fetch.py`: **Data Fetching**. Consolidated fetcher classes.
-   `nexus_search.py`: **Discovery**. Google/GitHub search integration.
-   `search_engine.py`: **GitHub Search**. Specific logic for finding users on GitHub.

### `devfest_nexus/` (Frontend)
-   `app.py`: **UI Entry Point**.
-   `logic/`:
    -   `chat_engine.py`: **Chat Interface**. Wraps Gemini API and logs chat to `backend/data/conversations/`.
    -   `dashboard.py`: Renders the main UI (Graph + Dossier) based on `frontend_state.json`.
    -   `landing_page.py`: Search/Start screen.

---

## 4. Key Data Flow & Logic

### 4.1 The "Logistic Mind" Loop
1.  **Watch**: Polls `backend/data/conversations/` for new user messages.
2.  **Extract**: Uses Regex + Gemini to find entities (e.g., "Check out torvalds").
3.  **Trigger**: If a valid entity (GitHub/Twitter) is found, calls `nexus_main.py`.
4.  **Score**: Uses Gemini to calculate CIT Score (Context-Intent-Timing).
5.  **Update**: Writes result to `frontend_state.json`.
6.  **Feedback**: Injects "context" back into the chat (via `active_context.json`) so the Chatbot knows about the profile.

### 4.2 Scoring Engine (CIT)
Managed by `logistic_mind.py` (via Gemini Prompt):
$$ \text{Readiness} = (0.4 \times \text{Context}) + (0.3 \times \text{Timing}) + (0.3 \times \text{Intent}) $$
-   Calculated via LLM prompt with access to user goal and target profile.
-   Classifies execution state: `STRONG_GO`, `PROCEED`, `CAUTION`, `ABORT`.

### 4.3 Chat Integration
The frontend `chat_engine.py` reads `active_context.json` to be "aware" of the backend's findings. This creates a loop:
User speaks -> Backend analyzes -> Backend updates Context -> Chatbot speaks with Context.

---

## 5. Current Implementation Status

| Component | Status | Notes |
| :--- | :--- | :--- |
| **Autonomous Agent** | ✅ **Active** | `logistic_mind.py` is fully implemented. |
| **GitHub Integration** | ✅ **Live** | Full API fetch via `nexus_fetch.py`. |
| **Dev.to Integration** | ✅ **Live** | Full API fetch via `nexus_fetch.py`. |
| **Scoring Engine** | ✅ **AI-Driven** | CIT Scoring implemented via Gemini Prompts. |
| **Frontend** | ✅ **Live** | Streamlit dashboard + Chat integrated. |
| **Simulated Data** | ⚠️ **Partial** | LinkedIn/Twitter still simulated due to API blocks. |

---

## 6. How to Run

1.  **Setup**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
2.  **Start Backend (Autonomous Agent)**:
    ```bash
    cd backend
    python logistic_mind.py
    ```
3.  **Start Frontend (In separate terminal)**:
    ```bash
    streamlit run devfest_nexus/app.py
    ```
