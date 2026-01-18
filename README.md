<a id="the-pitch"></a>
<p align="center">
  <a href="https://nexus-devfest-2k26.streamlit.app"><img src="https://img.shields.io/badge/🚀_Live_Demo-NEXUS-FF6F00?style=for-the-badge" /></a>
  <br/>
  <img src="https://img.shields.io/badge/DevFest-5.0-FF6F00?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Team-Error404-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/BITS-Pilani_Goa-green?style=for-the-badge" />

 
  <img src=".\additional_assets\logo_banner.png" alt="NEXUS" style="border-radius: 40px 40px 40px 40px;"  />
  <img src=".\additional_assets\image.png" alt="NEXUS" style="border-radius: 40px 40px 0 0;" />
  <img src=".\additional_assets\image copy.png" alt="NEXUS" />
  <img src=".\additional_assets\image copy 2.png" alt="NEXUS" />
  <img src=".\additional_assets\image copy 3.png" alt="NEXUS" />
  <img src=".\additional_assets\image copy 5.png" alt="NEXUS" />
  <img src=".\additional_assets\image copy 6.png" alt="NEXUS" />
  <img src=".\additional_assets\image copy 7.png" alt="NEXUS" />
  <img src=".\additional_assets\image copy 4.png" alt="NEXUS" style="border-radius: 0 0 40px 40px;" />



<p align="center">
  <strong><a href="#the-pitch">THE PITCH</a></strong>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <strong><a href="#the-technical-depth--architecture-and-functioning">TECHNICAL DEPTH</a></strong>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <strong><a href="#demo-operations--see-nexus-in-operation">DEMO OPERATIONS</a></strong>
</p>

</p>

---
# THE TECHNICAL DEPTH : ARCHITECTURE AND FUNCTIONING

NEXUS operates as a dual-process system: a **Streamlit UI** for the strategy console and a **Background Agent (Logistic Mind)** for autonomous intelligence.

```mermaid
graph TD
    %% SUBGRAPH: USER INTERFACE (Top Level)
    subgraph UI_Layer [User Interface]
        direction TB
        User([User]) <-->|Interacts| UI["Streamlit Dashboard<br/>(devfest_nexus/app.py)"]
    end

    %% SUBGRAPH: DATA STORES (Middle Layer - Left)
    subgraph Data_Stores [State & Context]
        direction TB
        ChatLogs[("Chat Logs JSON")]
        State[("Frontend State JSON")]
        Context[("Active Context JSON")]
    end

    %% SUBGRAPH: INTELLIGENCE (Middle Layer - Center)
    subgraph Brain_Core [Logistic Mind Agent]
        direction TB
        LM["Logistic Mind<br/>(Background Process)"]
        Gemini["Google Gemini 2.0 Flash<br/>(Reasoning Engine)"]
        
        LM <-->|Reasoning| Gemini
    end

    %% SUBGRAPH: ORCHESTRATION (Middle Layer - Right)
    subgraph Execution [Pipeline Execution]
        direction TB
        Orchestrator["Nexus Orchestrator"]
        Discovery["Search Engine"]
        SocialFetch["Social Fetchers"]
    end

    %% SUBGRAPH: EXTERNAL DATA (Bottom Layer)
    subgraph External [External Platforms]
        direction LR
        GitHub[("GitHub")] ~~~ LinkedIn[("LinkedIn")] ~~~ Twitter[("Twitter/X")]
    end

    %% CONNECTIONS ==========================================
    
    %% User Flow
    UI -->|Writes| ChatLogs
    ChatLogs -->|Watches| LM
    
    %% Feedback Loop
    LM -->|Updates| State
    LM -->|Updates| Context
    State -->|Reads| UI
    Context -->|Reads| UI

    %% Pipeline Logic
    LM -->|Triggers| Orchestrator
    Orchestrator -->|1. Find| Discovery
    Orchestrator -->|2. Fetch| SocialFetch
    
    %% External Calls
    Discovery -.->|Search| GitHub & LinkedIn & Twitter
    SocialFetch <-->|API| GitHub & LinkedIn & Twitter
    
    %% Unification
    SocialFetch -->|3. Merge| Unified["Unified Profile Builder"]
    Unified -->|Save| ProfileJSON[("Unified_Profile.json")]
    ProfileJSON -->|Hydrate| LM

    %% STYLING ==============================================
    classDef user fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef brain fill:#4c1d95,stroke:#8b5cf6,stroke-width:2px,color:#fff;
    classDef data fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#fff;
    classDef external fill:#000,stroke:#666,stroke-width:1px,color:#fff,stroke-dasharray: 5 5;

    class UI,User user;
    class LM,Gemini,Orchestrator,Discovery,SocialFetch,Unified brain;
    class ChatLogs,State,Context,ProfileJSON data;
    class GitHub,LinkedIn,Twitter external;
```

---

### 3. Identity Confidence Scoring — Verified Profiles

How does one confirm "John Smith on GitHub" is the same "John Smith on LinkedIn"?

**NEXUS verifies it.**

```mermaid
flowchart LR
    A["Input: A Name"] --> B["Search Across Platforms"]
    B --> C["GitHub"]
    B --> D["Dev.to"]
    B --> E["StackOverflow"]
    B --> F["LinkedIn"]
    
    C --> G["Cross-Reference Check"]
    D --> G
    E --> G
    F --> G
    
    G --> H["Same Name? +30%"]
    G --> I["Mutual Links? +40%"]
    G --> J["Same Location? +20%"]
    G --> K["Bio Overlap? +10%"]
    
    H --> L["Confidence: 85%<br/><em>Identity Verified</em>"]
    I --> L
    J --> L
    K --> L
```

<br/>

> The system does not just scrape. It **validates**. If data does not align across platforms, a lower confidence score appears — indicating how much to trust the profile.

<br/>

---

### 4. Psychological Timing — Reading Digital Body Language

<br/>

|   Activity Observed   |           Psychological State           |  System Response  |
| :-------------------: | :-------------------------------------: | :---------------: |
|    Coding at 2 AM     | Flow State — focused, open to tech talk | **+15 to score**  |
| Just shipped a launch |        Ego High — inbox flooded         | **Wait 72 hours** |
|      Friday 6 PM      |   Dead Zone — checked out for weekend   | **-40 to score**  |
|     Tuesday 3 PM      |  Dopamine Window — open to serendipity  | **+10 to score**  |
|  Ranting on Twitter   |        High Cortisol — defensive        |     **ABORT**     |

<br/>

> The engine does not just check "last active 2 hours ago." It interprets **what that activity means psychologically**.

<br/>

---

### 5. Proactive AI — Action Before Request

Most AI tools wait for explicit requests.

**NEXUS anticipates.**

<br/>

```mermaid
sequenceDiagram
    participant User
    participant NEXUS
    
    User->>NEXUS: "I want to connect with Aditya from BITS"
    
    Note over NEXUS: Automatically extracts "Aditya" + "BITS"
    Note over NEXUS: Searches across GitHub, LinkedIn, Dev.to
    Note over NEXUS: Builds unified profile
    Note over NEXUS: Calculates timing score
    
    NEXUS->>User: Here's Aditya's profile. Score: 78. PROCEED.
    
    Note over User: The user never asked for the profile.<br/>The user never asked for the score.<br/>NEXUS anticipated the need.
```

<br/>

> A name mentioned in conversation triggers a full dossier. No buttons. No manual lookup. **True agent behavior.**

<br/>

---

# DEMO OPERATIONS : SEE NEXUS IN OPERATION 

> **📌 Note on Data Sources:**
> 
> Some platform data is **simulated** in this demo due to API restrictions:
> - **LinkedIn**: Scraping violates Terms of Service
> - **Twitter/X**: API access requires paid enterprise subscription
> - **GitHub**: Fully functional with live API
>
> For platforms where live data isn't accessible, we use GitHub profile data to simulate corresponding LinkedIn/Twitter information. This demonstrates that **multi-source data compilation and identity verification works as designed**.
>
> In a production deployment with funding, paid API access would enable full real-time data retrieval across all platforms. 

  <img src=".\additional_assets\demo\image copy 8.png" alt="NEXUS" style="border-radius: 40px" />
  <br/>
  <img src=".\additional_assets\demo\image copy 9.png" alt="NEXUS" style="border-radius: 40px" />
  <br/>
  <img src=".\additional_assets\demo\image.png" alt="NEXUS" style="border-radius: 40px 40px 0 0;" />
  <img src=".\additional_assets\demo\image copy.png" alt="NEXUS" />
  <img src=".\additional_assets\demo\image copy 2.png" alt="NEXUS" />
  <img src=".\additional_assets\demo\image copy 3.png" alt="NEXUS" />
  <img src=".\additional_assets\demo\image copy 4.png" alt="NEXUS" />
  <img src=".\additional_assets\demo\image copy 5.png" alt="NEXUS" />
  <img src=".\additional_assets\demo\image copy 6.png" alt="NEXUS" />
  <img src=".\additional_assets\demo\image copy 7.png" alt="NEXUS"" style="border-radius: 0 0 40px 40px ; />
<br/>

---

<p align="center">
  <img src="https://img.shields.io/badge/Gemini_2.0-AI_Engine-4285F4?style=for-the-badge&logo=google" />
  <img src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit" />
  <img src="https://img.shields.io/badge/GitHub_API-Data-181717?style=for-the-badge&logo=github" />
  <img src="https://img.shields.io/badge/Python-Backend-3776AB?style=for-the-badge&logo=python" />
  <img src="./additional_assets/image copy 8.png" style="border-radius: 40px;" />
</p>

