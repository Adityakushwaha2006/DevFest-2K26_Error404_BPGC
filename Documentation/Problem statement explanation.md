# DevFest 5.0: Project Requirement Analysis
## Problem Statement: AI-Powered Networking System

### 1. The Core Philosophy (The "Why")
**The Shift:** The problem statement explicitly asks to move away from *Static Profiles* (who someone is generally) to *Dynamic Context* (what someone is doing right now).

* **Old Way (LinkedIn):** "This person is a Software Engineer at Google." (Static)
* **Your Way (DevFest):** "This person just pushed a commit to a React repo at 2 AM and tweeted about coffee. They are in a 'Build Phase'." (Dynamic)

**The Demand:** Your system must answer three questions that LinkedIn cannot:
1.  **Why** should I connect? (Shared Context)
2.  **When** should I connect? (Timing/Readiness)
3.  **How** should I start? (Interaction Insight)

---

### 2. The Technical Pillars (The "What")

#### Pillar A: The Data Layer (Ingestion)
* **Requirement:** "Analyze publicly available information... GitHub, Twitter (X)."
* **The Demand:** You need a pipeline that ingests *unstructured* and *time-stamped* data.
* **Constraint:** Do not waste time trying to hack LinkedIn's firewall.
* **Strategy:**
    * **Primary Source:** GitHub API (Public events, commits, starred repos). It is clean, rich, and developer-focused.
    * **Secondary Source:** Twitter/X (Recent tweets/replies). Use a mock dataset if API access is restricted.
    * **Tertiary Source:** RSS Feeds or Blog headers (if available).

#### Pillar B: The Context Engine (Semantic Analysis)
* **Requirement:** "Understand professional context... shared events, overlapping interests."
* **The Demand:** You must go deeper than keyword matching.
    * *Bad:* "You both like AI."
    * *Good:* "You are researching 'Face ID', and he just starred a repo about 'Facial Landmark Detection'. This is a **Contextual Trigger**."
* **Tech Stack:** LLM (Gemini/OpenAI) to extract "Current Focus" from bio/tweets/readmes.

#### Pillar C: The Temporal Engine (Timing & Patterns)
* **Requirement:** "Identify... based on timing" and "Readiness Score."
* **The Demand:** This is your **Winning Differentiator**. You must quantify "Timing."
* **The Logic (Leveraging your `aeon` background):**
    * **Activity Bursts:** Is the user active *right now*?
    * **Gap Analysis:** Have they been silent for 2 weeks? (Maybe on vacation—Low Readiness).
    * **Consistency:** Do they post every Friday? (Predictable interaction window).

#### Pillar D: The Action Layer (Generative Output)
* **Requirement:** "Suggested conversation angles... interaction-ready insights."
* **The Demand:** Don't just give a link to the profile. Write the cold DM for the user.
* **Output:** A drafted message based on the *specific* overlapping trigger found in Pillar B.

---

### 3. The "Readiness Score" Algorithm
The problem explicitly asks for a **score**. This needs to be a concrete mathematical logic, not a random number.

**Formula Concept:**
$$S_{total} = (W_1 \times C) + (W_2 \times T) + (W_3 \times I)$$

1.  **Context (C):** Semantic similarity (Vector Cosine Similarity between your profile and theirs).
2.  **Timing (T):** Recency of activity (Time Decay function). $1 / (DaysSinceLastActivity + 1)$.
3.  **Intent (I):** Explicit signals (e.g., phrases like "hiring", "looking for contributors", "stuck on").

---

### 4. User Experience Flow (The "How")

1.  **Input:** User pastes a GitHub/Twitter handle of a person they *want* to reach (or the system suggests one).
2.  **Processing (The "Black Box"):**
    * Fetch last 50 events.
    * Analyze text for "Intent".
    * Analyze timestamps for "Momentum".
3.  **Output Card:**
    * **Name & Role**
    * **Readiness Score:** "92/100 (High Momentum)"
    * **Why Now?** "User just finished a major sprint (High Activity Drop-off)."
    * **Icebreaker:** "Hey [Name], I noticed you switched from PyTorch to JAX in your latest repo. How are you finding the transition?"

---

### 5. Execution Roadmap (For Your Team)

| Component | Responsibility | Technical Task |
| :--- | :--- | :--- |
| **Data Ingestion** | **Aksh / Bhuvanesh** | Build a script to fetch JSON from GitHub API (`/users/{username}/events`). Create a dummy JSON for Twitter data. |
| **Logic & Scoring** | **Aditya Kushwaha** | Design the Python function that takes the JSON and calculates the "Readiness Score" based on timestamps. |
| **Context & NLP** | **Aditya Melinkeri** | Write the LLM Prompt that reads the text data and outputs the "Icebreaker" and "Intent Category". |
| **Frontend** | **Bhuvanesh / Aksh** | Set up a Streamlit or React dashboard. Needs a search bar and a "Result Card" display. |

### 6. What will make you LOSE (Avoid these)
* **Trying to scrape LinkedIn:** You will get IP banned and waste 10 hours. Mock the data if you need LinkedIn-style profiles.
* **Generic Matches:** If your tool suggests connecting just because "You both go to BITS Goa", you fail. It must be *activity-based*.
* **ignoring "Timing":** If you recommend connecting with someone who hasn't been active in 3 years, the "AI" is broken.