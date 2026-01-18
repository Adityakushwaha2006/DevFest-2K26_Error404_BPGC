# NEXUS Codebase Context Document
## Complete Reference for External AI Systems

**Project:** NEXUS - AI-Powered Networking Intelligence Engine  
**Hackathon:** DevFest 5.0  
**Team:** Error404 (BITS Pilani Goa)

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Summary](#architecture-summary)
3. [Backend Modules](#backend-modules)
4. [Frontend Modules](#frontend-modules)
5. [Data Models](#data-models)
6. [Environment Variables](#environment-variables)
7. [Suggested USPs](#suggested-usps)

---

## Project Overview

NEXUS is a professional networking intelligence platform that answers three questions static profile tools cannot:
- **WHEN** is the optimal moment to reach out?
- **WHY** would they respond to me specifically?
- **HOW** should I approach based on their current psychological state?

The system aggregates data from multiple platforms (GitHub, Dev.to, StackOverflow, LinkedIn, Medium, HackerNews), validates identity through cross-referencing, calculates a Context-Intent-Timing (CIT) score, and provides strategic advice through a Gemini-powered chatbot.

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Streamlit)                      │
├─────────────────────────────────────────────────────────────────┤
│  Landing Page → Mode Selection → Dashboard → Chat Interface      │
│  devfest_nexus/                                                   │
│    ├── app.py (entry point)                                       │
│    └── logic/                                                     │
│         ├── landing_page.py                                       │
│         ├── dashboard.py                                          │
│         ├── chat_engine.py (Gemini wrapper)                       │
│         ├── context_loader.py (600-line prompt system)            │
│         └── scoring.py                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        BACKEND (Python)                          │
├─────────────────────────────────────────────────────────────────┤
│  backend/                                                         │
│    ├── nexus_main.py (NexusOrchestrator - master controller)     │
│    ├── nexus_logic.py (ProfileConsolidator, MiscConsolidator)    │
│    ├── nexus_fetch.py (All platform fetchers + data models)      │
│    ├── nexus_search.py (GoogleSearchEngine, MockProfileDiscovery)│
│    ├── logistic_mind.py (Autonomous agent orchestrator)          │
│    └── devto_fetcher.py (Dev.to API integration)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Backend Modules

### 1. nexus_main.py (332 lines)
**Purpose:** Master pipeline orchestrator. Coordinates all data fetching.

**Class: `NexusOrchestrator`**
```python
class NexusOrchestrator:
    def __init__(self, output_dir, google_api_key, google_cse_id, github_token, enable_fallback)
    def process_person(self, name, github_username, twitter_handle, linkedin_id, 
                       stackoverflow_name, blog_url, hackernews_username, 
                       company, role, auto_discover) -> Dict
    def _merge_profiles(self, name, social, misc, discovery) -> Dict
```

**Pipeline Steps:**
1. STEP 1: Search to Sites (discovery via Google CSE or mock)
2. STEP 2: Social to JSON (GitHub, Twitter, LinkedIn)
3. STEP 3: Misc to JSON (StackOverflow, blogs, HackerNews)
4. STEP 4: Unified Profile (merge all sources)

**Output Structure:**
```python
{
    "meta": {"pipeline_version": "2.1", "processed_at": str, "errors": []},
    "discovery": {...},
    "social_profile": {...},
    "misc_profile": {...},
    "unified_profile": {...},
    "pipeline_status": "complete" | "partial_success"
}
```

---

### 2. nexus_logic.py (428 lines)
**Purpose:** Data processing, orchestration, and aggregation logic.

**Class: `ProfileConsolidator`**
```python
class ProfileConsolidator:
    def __init__(self, output_dir, github_token)
    def consolidate(self, github_username, twitter_handle, linkedin_id, output_file, use_simulated_github) -> Dict
    def _fetch_github(self, username, use_simulated) -> Dict
    def _fetch_twitter(self, handle) -> Dict
    def _fetch_linkedin(self, identifier) -> Dict
    def _detect_handles(self, github_data) -> Tuple[str, str]
    def _build_identity_graph(self, github_data, twitter_data, linkedin_data) -> IdentityGraph
    def _aggregate_activities(self, github, twitter, linkedin, limit=100) -> List[Dict]
```

**Consolidation Steps:**
1. Fetch GitHub data (live API)
2. Auto-detect social handles from GitHub bio/links
3. Fetch Twitter data (simulated)
4. Fetch LinkedIn data (simulated)
5. Build identity graph and calculate confidence score
6. Aggregate activity timeline (chronological)
7. Calculate engagement metrics
8. Generate summary

**Class: `MiscConsolidator`**
```python
class MiscConsolidator:
    def __init__(self, output_dir)
    def consolidate(self, name, stackoverflow_name, blog_url, medium_username, hackernews_username, output_file) -> Dict
```

---

### 3. nexus_fetch.py (565 lines)
**Purpose:** All platform fetchers and core data models.

**Data Models:**

```python
class Platform(Enum):
    GITHUB = "github"
    TWITTER = "twitter"
    DEVTO = "devto"
    LINKEDIN = "linkedin"
    HASHNODE = "hashnode"

@dataclass
class CrossReference:
    platform: Platform
    identifier: str
    source_field: str
    confidence: float = 0.0

@dataclass
class ActivityEvent:
    platform: Platform
    event_type: str
    content: str
    timestamp: datetime
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    sentiment: Optional[str] = None

class IdentityNode:
    def __init__(self, platform: Platform, identifier: str)
    # Properties: data, cross_references, activities, confidence_score
    def add_cross_reference(self, platform, identifier, source_field)
    def add_activity(self, activity: ActivityEvent)
    def get_name(self) -> Optional[str]
    def get_bio(self) -> Optional[str]
    def get_location(self) -> Optional[str]
    def get_company(self) -> Optional[str]
    def to_dict(self) -> Dict

class IdentityGraph:
    def __init__(self)
    # Properties: nodes (Dict[str, IdentityNode]), unified_profile
    def add_node(self, node: IdentityNode) -> str
    def get_node(self, platform: Platform, identifier: str) -> Optional[IdentityNode]
    def calculate_cross_validation_score(self) -> float
    def synthesize_profile(self) -> Dict
```

**Fetcher Classes:**

```python
class ExtendedGitHubFetcher:
    RECENCY_WEIGHTS = {"last_week": 1.0, "last_month": 0.8, "last_3_months": 0.5}
    def __init__(self, github_token)
    def fetch_full_profile(self, username) -> Dict  # Returns profile, repos, commits, cross_references
    def to_identity_node(self, data) -> IdentityNode

class SimulatedDataFetcher:
    def __init__(self, data_dir)
    def fetch_github(self, username) -> Optional[Dict]
    def fetch_twitter(self, username) -> Optional[Dict]
    def fetch_linkedin(self, username) -> Optional[Dict]
    def to_twitter_node(self, data) -> IdentityNode
    def to_linkedin_node(self, data) -> IdentityNode

class StackOverflowFetcher:
    BASE_URL = "https://api.stackexchange.com/2.3"
    def fetch_full_profile(self, user_id) -> Dict
    def search_and_fetch(self, display_name) -> Dict

class BlogFetcher:
    FEED_PATHS = ["/feed", "/rss", "/rss.xml", "/feed.xml", "/atom.xml", ...]
    def discover_feed_url(self, blog_url) -> Optional[str]
    def fetch_feed(self, feed_url, limit=10) -> Dict
    def fetch_from_blog_url(self, blog_url, limit=10) -> Dict

class MediumFetcher:
    def fetch_user_posts(self, username, limit=10) -> Dict

class HackerNewsFetcher:
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    def fetch_user(self, username) -> Optional[Dict]
    def fetch_item(self, item_id) -> Optional[Dict]
    def fetch_full_profile(self, username, submission_limit=15) -> Dict
```

---

### 4. nexus_search.py (405 lines)
**Purpose:** Profile discovery via Google Custom Search API.

```python
class GoogleSearchEngine:
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    PLATFORM_PATTERNS = {
        "github": r"github\.com/([A-Za-z0-9_-]+)",
        "twitter": r"(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)",
        "linkedin": r"linkedin\.com/in/([A-Za-z0-9_-]+)",
        "devto": r"dev\.to/([A-Za-z0-9_]+)",
        "medium": r"medium\.com/@([A-Za-z0-9_.-]+)",
        "stackoverflow": r"stackoverflow\.com/users/(\d+)",
        "hackernews": r"news\.ycombinator\.com/user\?id=([A-Za-z0-9_]+)"
    }
    
    def __init__(self, api_key, search_engine_id, enable_fallback=True)
    def is_configured(self) -> bool
    def search(self, query, num_results=10, site_restrict=None) -> List[Dict]
    def discover_profiles(self, name, context=None) -> Dict
    def search_person_comprehensive(self, name, company, role, location) -> Dict
    def _calculate_confidence(self, name, result, platform) -> float

class MockProfileDiscovery:
    # Fallback when Google CSE not configured
    def __init__(self)
    def discover_profiles(self, name) -> Dict
    def search_person_comprehensive(self, name, **kwargs) -> Dict

def get_search_engine(api_key, search_engine_id, enable_fallback=True) -> GoogleSearchEngine | MockProfileDiscovery
```

---

### 5. logistic_mind.py (~800 lines, partially documented)
**Purpose:** Autonomous Gemini-powered backend orchestrator.

```python
@dataclass
class ExtractedEntity:
    entity_type: str  # "person_name", "github_handle", "twitter_handle", etc.
    value: str
    confidence: float
    source_message: str

@dataclass
class CITScore:
    context: int = 50  # 0-100
    intent: int = 50
    timing: int = 50
    total: int = 50
    execution_state: str = "UNKNOWN"  # STRONG_GO, PROCEED, CAUTION, ABORT
    
    def calculate_total(self, weights=(0.30, 0.50, 0.20)) -> int:
        # S_total = (W1 × Context) + (W2 × Timing) + (W3 × Intent)
        return int(weights[0]*self.context + weights[1]*self.timing + weights[2]*self.intent)

class LogisticMind:
    def __init__(self, gemini_api_key, github_token)
    def extract_entities_regex(self, text) -> List[ExtractedEntity]
    def extract_entities_gemini(self, text, conversation_context) -> List[ExtractedEntity]
    def compute_cit_score(self, user_context, target_profile, conversation_intent) -> CITScore
    def infer_intent(self, conversation_history) -> str
    def trigger_pipeline(self, entities)  # Calls NexusOrchestrator
    def update_frontend_state(self, profile, cit_score)
    def check_profile_refresh(self, profile_path, max_age_hours=6) -> bool
```

**Key Behaviors:**
- Watches chat logs for entity mentions
- Automatically extracts person names, handles via regex + Gemini
- Triggers backend pipeline when entities detected
- Computes CIT scores using Gemini
- Updates frontend state JSON files for dashboard refresh

---

## Frontend Modules

### 1. chat_engine.py (558 lines)
**Purpose:** Gemini API wrapper with session management.

```python
class GeminiChatEngine:
    DEFAULT_SYSTEM_PROMPT = "..."  # ~190 lines of NEXUS identity prompt
    
    def __init__(self, system_prompt, model_name="gemini-3-flash-preview", session_id)
    def send_message(self, user_message) -> str
    def get_history(self) -> List[Dict]
    def clear_history(self)
    def reset(self)
    def load_history(self, messages: list)
    def set_context(self, context_data: Dict)
    def get_context(self) -> Dict
    def inject_context(self, cit_score: Dict, target_profile: Dict, intent: str)
    
def create_chat_engine(system_prompt, session_id) -> Optional[GeminiChatEngine]
```

**Features:**
- Session persistence to JSON files
- Conversation history management
- Context injection for CIT scores and target profiles
- Handles incomplete data gracefully (warns against hallucination)

---

### 2. context_loader.py (591 lines)
**Purpose:** Advanced prompt engineering system for mode-specific AI behavior.

```python
class NEXUSContextLoader:
    BASE_SYSTEM_PROMPT = "..."  # Identity, communication style, conversation flow
    STRATEGY_MATRIX = "..."     # Mode-specific scoring algorithms
    RESPONSE_STRUCTURE = "..."  # Response formatting rules
    CONTEXT_TEMPLATE = "..."    # Dynamic variable injection
    
    @staticmethod
    def build_complete_prompt(user_context, target_context, current_time) -> str
    
    @staticmethod
    def _prepare_context_variables(user_context, target_context, current_time) -> Dict

def get_nexus_system_prompt(user_context, target_context) -> str
```

**Mode-Specific Scoring Algorithms (from STRATEGY_MATRIX):**

**STUDENT + HIRING Intent:**
```
Weights: W_A=0.4, W_B=0.3, W_C=0.3
Variables:
- Recency: Activity < 1h = 100; < 24h = 80; < 3d = 50; > 7d = 10
- Alumni: Same University = 100; Same Degree/Major = 80; None = 0
- SkillMatch: High Overlap = 100; Partial = 50; None = 0

Overrides:
- IF Target Role == "Recruiter" AND Post contains "Hiring": SCORE = 98
- IF Target Role == "Engineer" AND User GitHub commits == 0 (Last 30d): FORCE SCORE = 5
```

**FOUNDER + FUNDING Intent:**
```
Weights: W_A=0.5, W_B=0.2, W_C=0.3
Variables:
- SignalHeat: Announced New Fund = 100; "Active Investing" in bio = 80
- IntroPath: 1st Degree (Direct) = 100; 2nd Degree = 80; Cold = 10
- SectorFit: Exact Match = 100; Adjacent = 50; Mismatch = 0

Overrides:
- IF Target Tweets "Request for Startups (RFS)" in User's domain: FORCE SCORE = 99
- IF User Stage < Target Min Ticket: FORCE SCORE = 0
```

**RESEARCHER + COLLABORATION Intent:**
```
Weights: W_A=0.6, W_B=0.2, W_C=0.2
Variables:
- Citation: User cited Target = 100; Target cited User = 100
- TopicVelocity: Target publishing frequently = 100
- EventOverlap: Both at same upcoming conf = 100

Overrides:
- IF Target Status == "Sabbatical": FORCE SCORE = 0
- IF Target recently became "Lab Head" / "PI": Boost +10
```

**Temporal Psychology Rules:**
- Friday 5PM - Sunday 2PM: "Dead Zone" → Penalty -40
- Monday 8AM - 11:30AM: "Monday Blues" → Penalty -20
- Tuesday-Thursday 2PM - 4:30PM: "Dopamine Window" → Boost +10
- Target coding at 2AM: "Flow State" → Boost +15

---

### 3. landing_page.py (507 lines)
**Purpose:** Fullscreen animated landing page with mode selection.

**Modes Available:**
1. **Student / Intern** → Alumni Networks, Campus Recruiters, Mentorship Paths
2. **Founder** → Venture Capital, Co-founder Matching, Talent Acquisition
3. **Researcher** → Lab Opportunities, Citation Networks, Conference Circles

**Technical Notes:**
- Uses Streamlit `components.html()` with height=0 trick
- Injects CSS to force iframe fullscreen
- Animated SVG intro sequence (draws NEXUS letter by letter)
- Particle background canvas

---

## Data Models

### Unified Profile Structure
```json
{
    "name": "string",
    "generated_at": "ISO datetime",
    "identity": {
        "primary_name": "string",
        "confidence_score": 0.0-1.0,
        "verified_platforms": ["github", "linkedin", ...],
        "cross_references": [...]
    },
    "platforms": {
        "github": {...},
        "twitter": {...},
        "linkedin": {...},
        "stackoverflow": {...},
        "blog": {...},
        "hackernews": {...}
    },
    "activity_timeline": [
        {"platform": "github", "type": "commit", "content": "...", "timestamp": "..."},
        ...
    ],
    "expertise": {...},
    "content": {...},
    "recency_weighting": {...}
}
```

### CIT Score Structure
```json
{
    "context": 0-100,
    "intent": 0-100,
    "timing": 0-100,
    "total": 0-100,
    "execution_state": "STRONG_GO | PROCEED | CAUTION | ABORT",
    "reasoning": "string"
}
```

### Execution States
| Score Range | State | Meaning |
|-------------|-------|---------|
| 90-100 | STRONG_GO | Perfect timing. Act immediately. |
| 75-89 | PROCEED | Good conditions. Draft carefully. |
| 55-74 | CAUTION | Friction detected. Nurture first. |
| 0-54 | ABORT | Door is shut. Wait for signal change. |

---

## Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (for live GitHub data)
GITHUB_TOKEN=your_github_personal_access_token

# Optional (for Google Custom Search profile discovery)
GOOGLE_CSE_API_KEY=your_google_cse_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id
```

---

## **SUGGESTIONS AND INSIGHTS (Take as Recommendations)**

**The following section contains suggested USPs and strategic insights. These are recommendations based on codebase analysis and should be considered as suggestions, not definitive facts.**

### Suggested USPs

1. **Three Mode-Specific AI Strategists**
   - Not one generic chatbot — each mode (Student/Founder/Researcher) runs different scoring algorithms with different weights
   - The AI understands the user's specific context by default

2. **"Don't Reach Out Yet" Intelligence**
   - Unique feature: the system tells users when NOT to act
   - Execution states (CAUTION/ABORT) prevent wasted outreach
   - Temporal psychology engine interprets what activity means, not just when it happened

3. **Identity Confidence Scoring**
   - Cross-platform validation with quantified confidence (0-100%)
   - Checks: name match (+30%), bidirectional links (+40%), location (+20%), bio overlap (+10%)
   - Users know how much to trust synthesized profiles

4. **Proactive Agent Behavior (LogisticMind)**
   - True autonomous agent: watches chat, extracts entities, triggers pipelines automatically
   - Profile appears without user explicitly requesting it
   - Refreshes stale data after 6 hours

5. **Temporal Psychology Engine**
   - Maps activity signals to psychological states
   - "Flow State" (coding 2AM) → receptive to tech talk (+15)
   - "Dead Zone" (Friday evening) → personal mode (-40)
   - "Dopamine Window" (Tue-Thu 2-4PM) → open to serendipity (+10)

### Suggested Differentiation Points

| Typical Hackathon Submission | NEXUS Approach |
|------------------------------|----------------|
| Single API wrapper | 6-platform aggregation |
| Generic LLM chatbot | Mode-specific scoring algorithms |
| Static recommendations | Real-time temporal psychology |
| Manual workflow | Autonomous agent behavior |
| "Here's a profile" | "Wait 72 hours, then approach" |

### Suggested Demo Flow

1. User selects mode (Student/Founder/Researcher)
2. User mentions a name in chat: "Help me connect with Aditya from BITS"
3. LogisticMind auto-extracts entity, triggers pipeline
4. Profile appears with CIT score and execution state
5. AI provides timing-aware strategy: "Score 78, PROCEED. She just posted about mentoring."

---

*Document generated for external AI context. Codebase total: ~5000+ lines across 15 modules.*
