# NEXUS Data Pipeline - Technical Documentation

## Executive Summary

NEXUS implements a **node-based identity resolution system** that aggregates professional profiles across multiple platforms to provide timing-aware networking intelligence. This document outlines the two core search features, the underlying architecture, and the phased implementation approach.

---

## 1. Core Features

### 1.1 Feature A: Person Search (Targeted Lookup)

**Use Case:** User knows a specific person they want to connect with.

**Input Example:**
```
"John Smith, Senior Engineer at IBM, based in Austin, TX"
```

**Pipeline:**
```
User Input (Name + Context)
        ↓
Search Engine (Google/LinkedIn)
        ↓
Extract Social Handles (GitHub, Twitter, LinkedIn URL)
        ↓
Node-Based Identity Resolution
        ↓
Social Profile Building Algorithm
        ↓
Scoring (Context + Intent + Timing)
        ↓
Connection Strategy + Optimal Timing
```

### 1.2 Feature B: Professional Search (Discovery)

**Use Case:** User wants to find professionals in a specific domain.

**Input Example:**
```
"Blockchain engineers working on Ethereum Layer 2 scaling"
```

**Pipeline:**
```
User Query (Domain + Criteria)
        ↓
Batch Search (GitHub API / LinkedIn / Google)
        ↓
Fetch N candidates
        ↓
For each candidate:
  └→ Run Social Profile Building Algorithm
  └→ Calculate Score (Context × Intent × Timing)
        ↓
Filter: Score > Threshold?
  ├→ YES: Add to results
  └→ NO: Fetch next batch, repeat
        ↓
Return top X highest-scoring candidates
```

**Iterative Scoring Algorithm:**
```python
def find_top_professionals(query, target_count=10, threshold=60):
    results = []
    batch_size = 20
    offset = 0
    
    while len(results) < target_count:
        # Fetch next batch
        candidates = search_engine.search(query, limit=batch_size, offset=offset)
        
        if not candidates:
            break  # No more results
        
        for candidate in candidates:
            # Build social profile
            profile = build_social_profile(candidate)
            
            # Calculate composite score
            score = calculate_score(profile)
            
            if score >= threshold:
                results.append((candidate, score))
        
        offset += batch_size
    
    # Return top X by score
    return sorted(results, key=lambda x: x[1], reverse=True)[:target_count]
```

---

## 2. Node-Based Identity Resolution Architecture

### 2.1 Core Concept

Each platform (GitHub, LinkedIn, Twitter, Dev.to) is treated as a **node** containing partial identity information. Nodes are linked through **cross-references** (e.g., GitHub bio contains Twitter handle).

```
                    ┌─────────────────┐
                    │   SEED INPUT    │
                    │ (Name/Username) │
                    └────────┬────────┘
                             ↓
            ┌────────────────┼────────────────┐
            ↓                ↓                ↓
    ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
    │  GitHub Node  │ │ LinkedIn Node │ │  Twitter Node │
    │  (Primary)    │ │ (Validation)  │ │ (Validation)  │
    └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              ↓
                    ┌─────────────────┐
                    │  Cross-Validate │
                    │  (Name, Bio,    │
                    │   Location)     │
                    └────────┬────────┘
                             ↓
                    ┌─────────────────┐
                    │ Unified Profile │
                    │ + Confidence %  │
                    └─────────────────┘
```

### 2.2 Cross-Validation Scoring

**Confidence Formula:**
```
Confidence = Σ(validation_weights)

Where:
- Name match across platforms:     +30%
- Bidirectional cross-references:  +40%
- Location/Company match:          +20%
- Bio keyword overlap:             +10%
```

### 2.3 IdentityNode Class Structure

```python
class IdentityNode:
    platform: Platform          # github, linkedin, twitter, devto
    identifier: str             # username/handle
    data: Dict                  # raw profile data
    cross_references: List      # links to other platforms
    activities: List            # timestamped events
    confidence_score: float     # 0.0 - 1.0
    last_updated: datetime
```

---

## 3. Scoring Engine: Context × Intent × Timing

### 3.1 The Three Pillars

| Component | Weight | Description |
|-----------|--------|-------------|
| **Context** | 30% | Profile similarity to user's goal |
| **Timing** | 50% | Current activity level (momentum) |
| **Intent** | 20% | Explicit signals of receptivity |

### 3.2 Readiness Score Formula

```
Readiness = (0.30 × Context) + (0.50 × Timing) + (0.20 × Intent)
```

### 3.3 Momentum Calculation

```python
def calculate_momentum(activities, decay_factor=0.8):
    """
    Recent activity weighted by time decay.
    Activity from 7 days ago = 80%^7 = 21% weight
    """
    score = 0
    for activity in activities:
        days_ago = (now - activity.timestamp).days
        weight = decay_factor ** days_ago
        score += weight
    
    return normalize_to_100(score)
```

### 3.4 Intent Detection

Keywords scanned in bio/recent posts:
- Hiring signals: "hiring", "looking for", "recruiting"
- Openness: "open to", "available for", "DM me"
- Collaboration: "seeking", "collaboration", "contributors wanted"

---

## 4. Implementation Phases

### Phase 1: Currently Feasible (Hackathon Demo)

| Component | Status | Implementation |
|-----------|--------|----------------|
| **GitHub API** | ✅ Live | User search, profile fetch, activity events |
| **Dev.to API** | ✅ Live | Profile + articles, no auth required |
| **Gemini API** | ✅ Live | LLM for context analysis, message drafting |
| **Scoring Engine** | ✅ Live | Momentum, readiness, win probability |
| **Identity Resolution** | ✅ Live | Cross-platform validation |

### Phase 2: Simulated (Proof of Concept)

| Component | Status | Simulation Approach |
|-----------|--------|---------------------|
| **Google Search API** | 🔶 Simulated | Mock search results based on query |
| **LinkedIn Data** | 🔶 Simulated | Structured mock profiles |
| **Twitter/X Data** | 🔶 Simulated | Generated from GitHub activity |

### Phase 3: Deployment Feasible (With Funding)

| Component | Access Method | Cost Estimate |
|-----------|---------------|---------------|
| **Google Custom Search** | API Key | $5/1000 queries |
| **LinkedIn** | Official API (Partner) | Enterprise pricing |
| **Twitter/X** | Official API v2 | $100/month (Basic) |
| **People Data Labs** | Bulk profile data | $0.02/profile |
| **Apollo.io** | B2B data platform | $49/month starter |

---

## 5. Justification for Simulated Data

### 5.1 Why Simulation is Valid for Demo

1. **Architecture Proof:** Simulated data flows through the exact same pipeline as live data. The scoring algorithms, cross-validation logic, and UI all function identically.

2. **API Compatibility:** Mock fetchers implement the same interface as live fetchers. Swapping simulated → live requires only API key configuration.

3. **Realistic Patterns:** Simulated data includes:
   - Realistic timestamps and activity patterns
   - Cross-platform consistency (same name/bio across nodes)
   - Believable engagement metrics

### 5.2 Evidence of Deployment Feasibility

| Platform | Proof of Accessibility |
|----------|------------------------|
| **Google Search** | [Programmable Search Engine](https://developers.google.com/custom-search) - 100 free queries/day, $5/1000 after |
| **LinkedIn** | [Marketing API](https://docs.microsoft.com/linkedin/) - Available to approved partners; [RapidAPI scrapers](https://rapidapi.com/search/linkedin) available |
| **Twitter/X** | [X API v2](https://developer.twitter.com/en/docs/twitter-api) - Free tier exists, paid tiers for higher volume |
| **Bulk People Data** | [People Data Labs](https://www.peopledatalabs.com/) - 1.5B profiles accessible via API |

### 5.3 Simulation → Production Migration Path

```
Demo (Simulated)              Production (Live)
─────────────────────────────────────────────────
MockLinkedInFetcher    →    LinkedInAPIFetcher
MockTwitterFetcher     →    TwitterAPIFetcher  
MockGoogleSearch       →    GoogleSearchEngine

# Code change required: Update .env with API keys
# No architectural changes needed
```

---

## 6. Data Flow Diagrams

### 6.1 Person Search Flow

```
┌──────────────────────────────────────────────────────────────┐
│                      PERSON SEARCH                           │
└──────────────────────────────────────────────────────────────┘

Input: "John Smith, IBM Engineer, Austin TX"
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  SEARCH LAYER (Google API / Simulated)                       │
│  Query: "John Smith IBM Austin site:linkedin.com OR          │
│          site:github.com"                                    │
│  Output: Candidate URLs                                      │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  IDENTITY RESOLUTION                                         │
│  • Create nodes for each discovered platform                 │
│  • Extract cross-references (GitHub → Twitter, etc.)         │
│  • Fetch additional nodes from cross-refs                    │
│  • Calculate identity confidence                             │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  SCORING ENGINE                                              │
│  • Momentum: Activity recency/frequency                      │
│  • Context: Match to user's goal                             │
│  • Intent: Receptivity signals                               │
│  Output: Readiness Score (0-100)                             │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  OUTPUT                                                      │
│  • Unified profile with confidence %                         │
│  • Win probability                                           │
│  • Recommendation: "Act Now" / "Wait X days"                 │
│  • Suggested connection approach                             │
└──────────────────────────────────────────────────────────────┘
```

### 6.2 Professional Search Flow

```
┌──────────────────────────────────────────────────────────────┐
│                   PROFESSIONAL SEARCH                        │
└──────────────────────────────────────────────────────────────┘

Input: "Ethereum L2 engineers with 3+ years experience"
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  DISCOVERY LAYER                                             │
│  GitHub Search: "ethereum layer2" + followers:>50            │
│  LinkedIn Search: "Ethereum" + "Layer 2" (simulated)         │
│  Output: Batch of N candidates                               │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼ (for each candidate)
┌──────────────────────────────────────────────────────────────┐
│  SOCIAL PROFILE BUILDING                                     │
│  1. Fetch primary platform (GitHub)                          │
│  2. Discover cross-references                                │
│  3. Fetch secondary platforms (Dev.to, simulated LinkedIn)   │
│  4. Cross-validate identity                                  │
│  5. Aggregate activities                                     │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  BATCH SCORING                                               │
│  For each candidate:                                         │
│    Score = (0.3 × Context) + (0.5 × Timing) + (0.2 × Intent) │
│                                                              │
│  Filter: Score >= Threshold (default: 60)                    │
│  If results < target: Fetch next batch                       │
└──────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────┐
│  RANKED OUTPUT                                               │
│  Top X candidates sorted by:                                 │
│    1. Readiness score                                        │
│    2. Identity confidence                                    │
│    3. Momentum (tiebreaker)                                  │
│                                                              │
│  Each result includes:                                       │
│    • Profile summary                                         │
│    • Score breakdown                                         │
│    • "Contact Now" / "Wait" recommendation                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. API Reference (Current Implementation)

### 7.1 Platform Fetchers

| Class | Platform | Status | Method |
|-------|----------|--------|--------|
| `GitHubFetcher` | GitHub | ✅ Live | REST API |
| `DevToFetcher` | Dev.to | ✅ Live | REST API (no auth) |
| `MockLinkedInFetcher` | LinkedIn | 🔶 Mock | Simulated data |

### 7.2 Search Engine

| Method | Description |
|--------|-------------|
| `search_users(query, location, language, min_followers)` | Search GitHub users |
| `search_repositories(query, language, min_stars)` | Search repos |
| `get_repo_contributors(repo_name)` | Get contributor usernames |

### 7.3 Scoring Engine

| Class | Method | Returns |
|-------|--------|---------|
| `MomentumScorer` | `calculate_momentum(activities)` | 0-100 score |
| `ReadinessScorer` | `calculate_readiness(context, timing, intent)` | 0-100 score |
| `WinProbabilityCalculator` | `calculate_win_probability(node)` | Dict with recommendation |

---

## 8. File Structure

```
backend/
├── identity_node.py        # IdentityNode, IdentityGraph classes
├── platform_fetchers.py    # GitHub, Dev.to, Mock LinkedIn fetchers
├── search_engine.py        # GitHub search, discovery engine
├── scoring_engine.py       # Momentum, readiness, win probability
├── demo_identity_resolution.py
├── demo_search.py
└── demo_scoring.py
```

---

## 9. Success Metrics

### 9.1 Demo Success Criteria

| Metric | Target |
|--------|--------|
| Identity resolution accuracy | >80% cross-platform match |
| Momentum score reliability | Correlates with actual activity |
| Search relevance | Top 5 candidates match query intent |
| Response time | <3 seconds per profile |

### 9.2 Deployment Success Criteria

| Metric | Target |
|--------|--------|
| Platform coverage | 4+ platforms (GitHub, LinkedIn, Twitter, Dev.to) |
| Profile database | 10,000+ indexed profiles |
| Win probability accuracy | >60% of "Act Now" recommendations result in response |

---

## 10. Conclusion

NEXUS differentiates itself through **timing intelligence** - not just finding connections, but determining the optimal moment to reach out. The node-based architecture ensures identity accuracy, while the three-pillar scoring system (Context × Intent × Timing) provides actionable recommendations.

The phased implementation approach allows demonstration of the complete concept using simulated data where live APIs are inaccessible, with a clear migration path to full production deployment.
