"""
NEXUS Logistic Mind - Gemini Backend Orchestrator
==================================================
The autonomous "second brain" that bridges chat and backend:
1. Watches chat logs for new messages
2. Extracts entities (social links, person names)
3. Triggers backend pipeline when needed
4. Computes CIT scores
5. Updates frontend state for dashboard rendering

Run standalone: python logistic_mind.py
"""

import os
import re
import json
import time
import glob
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from dotenv import load_dotenv

# For Gemini inference
import google.generativeai as genai

load_dotenv()


# --- Data Classes ---

@dataclass
class ExtractedEntity:
    """Represents an extracted entity from chat"""
    entity_type: str  # "github", "twitter", "linkedin", "email", "person_name"
    value: str
    confidence: float = 1.0
    source_message: str = ""


@dataclass
class CITScore:
    """Context, Intent, Timing scores"""
    context: int = 0      # 0-100: Semantic similarity
    intent: int = 0       # 0-100: User's networking intent match
    timing: int = 0       # 0-100: Target activity recency + optimal window
    total: int = 0        # Weighted sum
    execution_state: str = "UNKNOWN"  # STRONG_GO, PROCEED, CAUTION, ABORT
    
    def calculate_total(self, w_c: float = 0.4, w_i: float = 0.3, w_t: float = 0.3):
        """Calculate weighted total and execution state"""
        self.total = int(w_c * self.context + w_i * self.intent + w_t * self.timing)
        
        if self.total >= 85:
            self.execution_state = "STRONG_GO"
        elif self.total >= 70:
            self.execution_state = "PROCEED"
        elif self.total >= 50:
            self.execution_state = "CAUTION"
        else:
            self.execution_state = "ABORT"
        
        return self


@dataclass
class FrontendState:
    """Shared state for dashboard rendering"""
    active_person: Dict = field(default_factory=dict)
    cit_score: Dict = field(default_factory=dict)
    focus_keywords: List[str] = field(default_factory=list)
    intent_classification: str = "Unknown"
    activity_stream: List[Dict] = field(default_factory=list)
    tentative_strategy: List[Dict] = field(default_factory=list)
    conversations: List[Dict] = field(default_factory=list)
    last_updated: str = ""


# --- Entity Extraction Patterns ---

SOCIAL_PATTERNS = {
    "github": [
        r"github\.com/([a-zA-Z0-9_-]+)",
        r"@?([a-zA-Z0-9_-]+)\s+on\s+github",
        r"github\s*:\s*@?([a-zA-Z0-9_-]+)",
    ],
    "twitter": [
        r"(?:twitter|x)\.com/([a-zA-Z0-9_]+)",
        r"@([a-zA-Z0-9_]+)\s+on\s+(?:twitter|x)",
        r"(?:twitter|x)\s*:\s*@?([a-zA-Z0-9_]+)",
        r"(?:his|her|their)\s+(?:twitter|x)\s+(?:is\s+)?@([a-zA-Z0-9_]+)",
    ],
    "linkedin": [
        r"linkedin\.com/in/([a-zA-Z0-9_-]+)",
        r"linkedin\s*:\s*([a-zA-Z0-9_-]+)",
    ],
    "email": [
        r"([\w.-]+@[\w.-]+\.\w+)",
    ]
}


class LogisticMind:
    """
    The Gemini-powered backend orchestrator.
    Watches chat logs, extracts entities, and coordinates the entire pipeline.
    """
    
    def __init__(self, 
                 conversations_dir: Optional[str] = None,
                 state_file: Optional[str] = None,
                 poll_interval: float = 2.0):
        """
        Initialize the Logistic Mind.
        
        Args:
            conversations_dir: Path to chat log directory
            state_file: Path to frontend state JSON file
            poll_interval: Seconds between log checks
        """
        # Set up paths
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        self.conversations_dir = conversations_dir or os.path.join(
            backend_dir, "data", "conversations"
        )
        self.state_file = state_file or os.path.join(
            backend_dir, "data", "frontend_state.json"
        )
        self.poll_interval = poll_interval
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        # State tracking
        self.processed_messages: set = set()  # Track processed message timestamps
        self.current_state = FrontendState()
        self.detected_persons: Dict[str, Dict] = {}  # person_id -> data
        
        # Active target tracking for real-time updates
        self.active_target: Optional[Dict] = None  # {github_username, last_fetched, old_profile}
        self.REFRESH_INTERVAL_HOURS = 6  # Re-scrape if profile is older than this
        
        # Initialize Gemini for entity extraction and scoring
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your_gemini_api_key_here":
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("models/gemini-2.0-flash")
            self.gemini_enabled = True
            print("[OK] Logistic Mind: Gemini initialized")
        else:
            self.model = None
            self.gemini_enabled = False
            print("[WARNING] Logistic Mind: Running without Gemini (entity extraction limited)")
    
    
    def extract_entities_regex(self, text: str) -> List[ExtractedEntity]:
        """
        Extract social links and emails using regex patterns.
        
        Args:
            text: Message text to parse
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        for platform, patterns in SOCIAL_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    username = match.group(1)
                    entities.append(ExtractedEntity(
                        entity_type=platform,
                        value=username.lower().strip(),
                        confidence=1.0,
                        source_message=text[:100]
                    ))
        
        return entities
    
    
    def extract_entities_gemini(self, text: str, conversation_context: str = "") -> List[ExtractedEntity]:
        """
        Use Gemini to extract person names, discovery intents, and implicit references.
        
        Args:
            text: Current message
            conversation_context: Recent conversation history
            
        Returns:
            List of extracted entities including inferred person names and discovery intents
        """
        if not self.gemini_enabled:
            return []
        
        prompt = f"""Analyze this message and extract entities.

MESSAGE: {text}

RECENT CONTEXT: {conversation_context[:500]}

Extract:
1. Any explicitly mentioned person names
2. Any social platform usernames (GitHub, Twitter, LinkedIn)
3. Any implied person references ("that engineer", "my friend at Google")
4. DISCOVERY INTENT - Distinguish between SPECIFIC and VAGUE:

   SPECIFIC discovery_intent (ready to search):
   - "find me mentors in ML" -> discovery_intent: "ML mentors"
   - "suggest blockchain engineers" -> discovery_intent: "blockchain engineers"
   - "who works on AI at Google" -> discovery_intent: "AI engineers Google"
   
   VAGUE discovery_needs_context (needs more info):
   - "I don't know who to contact" -> discovery_needs_context: "general"
   - "who should I talk to?" -> discovery_needs_context: "unknown"
   - "help me find someone" -> discovery_needs_context: "unspecified"
   - "I need to network" -> discovery_needs_context: "networking"

5. USER CONTEXT SIGNALS from conversation (if any):
   - College/university mentions -> user_context: "college:BITS Pilani"
   - Skills mentioned -> user_context: "skills:Python,ML"
   - Goals -> user_context: "goal:mentorship"

Return JSON array only:
[{{"type": "person_name|github|twitter|linkedin|discovery_intent|discovery_needs_context|user_context", "value": "extracted_value", "confidence": 0.0-1.0}}]

If no entities found, return: []"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response (remove markdown code blocks if present)
            if response_text.startswith("```"):
                response_text = re.sub(r"```\w*\n?", "", response_text)
                response_text = response_text.strip()
            
            entities_data = json.loads(response_text)
            
            return [
                ExtractedEntity(
                    entity_type=e.get("type", "unknown"),
                    value=e.get("value", ""),
                    confidence=e.get("confidence", 0.5),
                    source_message=text[:100]
                )
                for e in entities_data
                if e.get("value")
            ]
        except Exception as e:
            print(f"[WARNING] Gemini entity extraction failed: {e}")
            return []
    
    
    def compute_cit_score(self, 
                          user_context: Dict, 
                          target_profile: Dict,
                          conversation_intent: str) -> CITScore:
        """
        Compute Context, Intent, Timing scores using Gemini.
        
        Args:
            user_context: User's mode, goals, skills
            target_profile: Consolidated target profile JSON
            conversation_intent: Inferred intent from chat
            
        Returns:
            CITScore with Gemini-generated values
        """
        score = CITScore()
        
        # If Gemini not available, fall back to basic defaults
        if not self.gemini_enabled:
            print("[WARNING] Gemini not available for CIT scoring, using defaults")
            score.context = 50
            score.intent = 50
            score.timing = 50
            score.calculate_total()
            return score
        
        # Build prompt for Gemini
        prompt = f"""Analyze this networking opportunity and generate CIT scores (0-100 each).

USER CONTEXT:
- Mode: {user_context.get('mode', 'Student')}
- Skills: {', '.join(user_context.get('skills', ['general'])[:10])}
- Goal: {conversation_intent}

TARGET PROFILE:
- Name: {target_profile.get('name', 'Unknown')}
- Role/Bio: {target_profile.get('role', target_profile.get('bio', 'Unknown'))[:200]}
- Skills/Topics: {', '.join((target_profile.get('skills', []) + target_profile.get('topics', []))[:10])}
- GitHub: {target_profile.get('github_username', 'N/A')}
- Last Activity: {target_profile.get('last_activity_hours', 'Unknown')} hours ago
- Recent Activity: {json.dumps(target_profile.get('recent_activity', [])[:3], default=str)[:300]}

SCORING CRITERIA:
- CONTEXT (0-100): How well do user's skills/goals align with target's expertise? Consider semantic similarity, shared interests, and professional relevance.
- INTENT (0-100): How likely is the target to respond to this type of outreach ({conversation_intent})? Consider their activity signals and openness.
- TIMING (0-100): Is this a good time to reach out? Consider their recent activity level (active = high score, dormant = low score).

Return ONLY a JSON object with this exact format:
{{"context": <number>, "intent": <number>, "timing": <number>, "reasoning": "<brief 1-sentence explanation>"}}
"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean markdown if present
            if response_text.startswith("```"):
                response_text = re.sub(r"```\w*\n?", "", response_text)
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            # Extract scores with validation
            score.context = max(0, min(100, int(result.get("context", 50))))
            score.intent = max(0, min(100, int(result.get("intent", 50))))
            score.timing = max(0, min(100, int(result.get("timing", 50))))
            
            # Log the reasoning
            reasoning = result.get("reasoning", "")
            if reasoning:
                print(f"[BRAIN] CIT Reasoning: {reasoning}")
            
            score.calculate_total()
            print(f"[OK] Gemini CIT Score: C={score.context}, I={score.intent}, T={score.timing} -> {score.total}/100 ({score.execution_state})")
            
            return score
            
        except Exception as e:
            print(f"[WARNING] Gemini CIT scoring failed: {e}")
            # Fallback to basic algorithm
            score.context = 50
            score.intent = 70 if conversation_intent in ["mentorship", "hiring", "collaboration"] else 50
            score.timing = 80 if target_profile.get("last_activity_hours", 999) < 24 else 40
            score.calculate_total()
            return score
    
    
    def infer_intent(self, conversation_history: List[Dict]) -> str:
        """
        Infer user's networking intent from conversation.
        
        Args:
            conversation_history: List of chat messages
            
        Returns:
            Intent classification: mentorship, hiring, collaboration, exploration, networking
        """
        if not conversation_history:
            return "exploration"
        
        # Combine recent messages
        recent_text = " ".join([
            msg.get("content", "") 
            for msg in conversation_history[-10:]
        ]).lower()
        
        # Keyword-based classification
        if any(w in recent_text for w in ["job", "hiring", "position", "apply", "interview", "recruit"]):
            return "hiring"
        if any(w in recent_text for w in ["mentor", "advice", "guidance", "learn from", "career"]):
            return "mentorship"
        if any(w in recent_text for w in ["collaborate", "work together", "project", "contribute", "open source"]):
            return "collaboration"
        if any(w in recent_text for w in ["know more", "curious", "explore", "discover"]):
            return "exploration"
        
        return "networking"
    
    
    def trigger_backend_pipeline(self, entity: ExtractedEntity) -> Optional[Dict]:
        """
        Trigger the backend pipeline for a detected entity.
        
        Args:
            entity: Extracted entity (github username, etc.)
            
        Returns:
            Consolidated profile dict, or None if failed
        """
        print(f"[REFRESH] Triggering pipeline for: {entity.entity_type}/{entity.value}")
        
        try:
            # Import pipeline orchestrator from new architecture
            from nexus_main import NexusOrchestrator
            
            orchestrator = NexusOrchestrator()
            
            # Build pipeline args based on entity type
            kwargs = {"auto_discover": True}
            
            if entity.entity_type == "github":
                kwargs["github_username"] = entity.value
                kwargs["name"] = entity.value  # Will be replaced by real name
            elif entity.entity_type == "twitter":
                kwargs["twitter_handle"] = entity.value
                kwargs["name"] = entity.value
            elif entity.entity_type == "linkedin":
                kwargs["linkedin_id"] = entity.value
                kwargs["name"] = entity.value
            else:
                print(f"[WARNING] Unsupported entity type: {entity.entity_type}")
                return None
            
            # Run pipeline
            result = orchestrator.process_person(**kwargs)
            
            # Pipeline returns: pipeline_status, unified_profile
            # Accept both "complete" and "partial_success" since GitHub data may be valid
            if result and result.get("pipeline_status") in ["complete", "partial_success"]:
                print(f"[OK] Pipeline {result.get('pipeline_status')} for {entity.value}")
                # Return the unified_profile with some key fields promoted
                unified = result.get("unified_profile", {})
                # Add convenience fields for CIT scoring
                unified["name"] = unified.get("name", entity.value)
                unified["github_username"] = entity.value if entity.entity_type == "github" else ""
                
                # Extract skills from GitHub repo languages (primary source)
                skills = []
                github_profile = unified.get("platforms", {}).get("github", {})
                if github_profile:
                    # Get languages from repositories
                    repos = github_profile.get("repositories", [])
                    for repo in repos:
                        lang = repo.get("language")
                        if lang and lang not in skills:
                            skills.append(lang)
                    
                    # Also get profile bio
                    profile_data = github_profile.get("profile", {})
                    unified["bio"] = profile_data.get("bio") or ""
                    unified["name"] = profile_data.get("name") or unified.get("name", entity.value)
                
                # Fallback to misc expertise if no GitHub skills found
                if not skills:
                    skills = list(unified.get("expertise", {}).get("top_technologies", []))
                
                unified["skills"] = skills[:10]
                unified["topics"] = list(unified.get("expertise", {}).get("topics", []))[:10]
                
                # Get recent activity from timeline
                recent_activity = []
                for activity in unified.get("activity_timeline", [])[:5]:
                    recent_activity.append({
                        "type": activity.get("type", "unknown"),
                        "content": activity.get("content", "")[:100],
                        "platform": activity.get("platform", "unknown")
                    })
                unified["recent_activity"] = recent_activity
                
                unified["last_activity_hours"] = self._calculate_hours_since_last_activity(unified)
                return unified
            else:
                print(f"[WARNING] Pipeline returned no data for {entity.value}")
                return None
                
        except ImportError as e:
            print(f"[WARNING] Could not import pipeline: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Pipeline error: {e}")
            return None
    
    
    def discover_profiles_from_name(self, name: str, context: str = "") -> List[ExtractedEntity]:
        """
        Use Google Search to discover social profiles from a person's name.
        
        Args:
            name: Person's name (e.g., "Aditya Melinkeri")
            context: Additional context (company, role)
            
        Returns:
            List of ExtractedEntity objects for discovered profiles
        """
        print(f"[SEARCH] Searching for profiles: {name}")
        
        try:
            from nexus_search import get_search_engine
            
            search_engine = get_search_engine()
            result = search_engine.discover_profiles(name, context)
            
            entities = []
            
            if result.get("search_status") in ["success", "mock"]:
                discovered = result.get("discovered_profiles", {})
                
                for platform, profile_data in discovered.items():
                    # Only use high-confidence matches
                    confidence = profile_data.get("confidence", 0.5)
                    if platform in ["github", "twitter", "linkedin"] and confidence >= 0.5:
                        identifier = profile_data.get("identifier", "")
                        if identifier:
                            entities.append(ExtractedEntity(
                                entity_type=platform,
                                value=identifier,
                                confidence=confidence,
                                source_message=f"Discovered via search for '{name}'"
                            ))
                            print(f"   [OK] Discovered {platform}: {identifier} (confidence: {confidence:.0%})")
                
                if not entities:
                    print(f"   [WARNING] No high-confidence profiles found for: {name}")
            else:
                print(f"   [ERROR] Search failed: {result.get('error', 'Unknown error')}")
            
            return entities
            
        except ImportError as e:
            print(f"[WARNING] Could not import search engine: {e}")
            return []
        except Exception as e:
            print(f"[ERROR] Profile discovery error: {e}")
            return []
    
    
    def discover_people(self, goal: str, user_context: Dict, max_results: int = 5) -> List[Dict]:
        """
        Discover people based on user's goal/keywords using GitHub Search.
        
        Args:
            goal: What user is looking for (e.g., "ML mentors", "blockchain experts")
            user_context: User's mode, skills, intent
            max_results: Maximum number of people to return
            
        Returns:
            List of discovered people with basic profiles
        """
        print(f"\n[ICON] Discovery Mode: Finding people for '{goal}'")
        
        try:
            from search_engine import GitHubSearchEngine
            
            github_search = GitHubSearchEngine()
            
            # Build search keywords from goal + user context
            keywords = goal
            user_mode = user_context.get('mode', 'Student')
            user_skills = user_context.get('skills', [])
            
            # Add relevant language filter based on user skills
            language = None
            for skill in user_skills:
                if skill.lower() in ['python', 'javascript', 'java', 'go', 'rust', 'c++']:
                    language = skill
                    break
            
            print(f"   Keywords: {keywords}")
            print(f"   User mode: {user_mode}")
            if language:
                print(f"   Language filter: {language}")
            
            # Search GitHub users
            results = github_search.search_users(
                query=keywords,
                language=language,
                min_followers=10,  # Lower threshold for better results
                min_repos=3,
                max_results=max_results * 2  # Get more to filter
            )
            
            if not results:
                print(f"   [WARNING] No GitHub users found for: {keywords}")
                return []
            
            print(f"   Found {len(results)} potential matches")
            
            # Convert to our format - search_users returns 'username' not 'login'
            people = []
            for user in results[:max_results]:
                username = user.get("username", "")  # GitHubSearchEngine returns 'username'
                people.append({
                    "name": username,  # Will be replaced by real name from profile
                    "github_username": username,
                    "bio": "",  # Not available from search API
                    "role": "",
                    "location": "",
                    "profile_url": user.get("profile_url", ""),
                    "avatar_url": user.get("avatar_url", ""),
                    "discovery_source": "github_search",
                    "discovery_goal": goal
                })
                print(f"   -> {username}")
            
            return people
            
        except ImportError as e:
            print(f"[WARNING] Could not import GitHub search: {e}")
            return []
        except Exception as e:
            print(f"[ERROR] Discovery error: {e}")
            return []
    
    
    def update_frontend_state(self, 
                               person: Dict,
                               cit_score: CITScore,
                               intent: str,
                               focus_keywords: List[str]):
        """
        Update the frontend state file for dashboard consumption.
        
        Args:
            person: Person profile data
            cit_score: Calculated CIT score
            intent: Inferred intent
            focus_keywords: Extracted focus areas
        """
        # Update activity stream
        now = datetime.now()
        new_activity = {
            "time": now.strftime("%H:%M"),
            "type": "signal",
            "content": f"Analyzed profile: {person.get('name', 'Unknown')}"
        }
        
        self.current_state.activity_stream.insert(0, new_activity)
        self.current_state.activity_stream = self.current_state.activity_stream[:10]  # Keep last 10
        
        # Update person context
        self.current_state.active_person = {
            "name": person.get("name", "Unknown"),
            "avatar": person.get("avatar", f"https://api.dicebear.com/7.x/avataaars/svg?seed={person.get('name', 'User')}"),
            "role": person.get("role", person.get("bio", "")[:50]),
            "github": person.get("github_username", ""),
            "twitter": person.get("twitter_handle", ""),
            "linkedin": person.get("linkedin_id", "")
        }
        
        # Update scores
        self.current_state.cit_score = asdict(cit_score)
        self.current_state.intent_classification = intent
        self.current_state.focus_keywords = focus_keywords[:5]
        
        # Generate tentative strategy based on CIT
        self.current_state.tentative_strategy = self._generate_strategy(cit_score)
        
        # Add to conversations sidebar
        person_id = person.get("github_username") or person.get("name", "unknown")
        if person_id not in [c.get("id") for c in self.current_state.conversations]:
            self.current_state.conversations.insert(0, {
                "id": person_id,
                "person": person.get("name", "Unknown"),
                "preview": f"CIT: {cit_score.total}/100 - {cit_score.execution_state}"
            })
        
        self.current_state.last_updated = now.isoformat()
        
        # Write to frontend state file
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.current_state), f, indent=2, ensure_ascii=False)
            print(f"[OK] Frontend state updated: {self.state_file}")
        except Exception as e:
            print(f"[ERROR] Failed to write state file: {e}")
        
        # --- WRITE ACTIVE CONTEXT FOR CHAT INJECTION ---
        # This file is read by the dashboard to inject into the chat engine
        active_context_file = os.path.join(
            os.path.dirname(self.state_file), 
            "active_context.json"
        )
        
        chat_context = {
            "target_profile": {
                "name": person.get("name", "Unknown"),
                "role": person.get("role", person.get("bio", "")[:100]),
                "github_username": person.get("github_username", ""),
                "twitter_handle": person.get("twitter_handle", ""),
                "linkedin_id": person.get("linkedin_id", ""),
                "skills": person.get("skills", [])[:10],
                "topics": person.get("topics", [])[:10],
                "last_activity_hours": person.get("last_activity_hours", 999),
                "recent_activity": person.get("recent_activity", [])[:5],
                "bio": person.get("bio", "")[:200]
            },
            "cit_score": asdict(cit_score),
            "intent": intent,
            "focus_keywords": focus_keywords[:5],
            "strategy": self.current_state.tentative_strategy,
            "timestamp": now.isoformat()
        }
        
        try:
            with open(active_context_file, "w", encoding="utf-8") as f:
                json.dump(chat_context, f, indent=2, ensure_ascii=False)
            print(f"[OK] Chat context written: {active_context_file}")
        except Exception as e:
            print(f"[ERROR] Failed to write chat context: {e}")
    
    
    def _calculate_hours_since_last_activity(self, profile: Dict) -> int:
        """Calculate hours since last activity from profile timeline."""
        timeline = profile.get("activity_timeline", [])
        if not timeline:
            return 999  # No activity
        
        # Get most recent activity timestamp
        for activity in timeline:
            ts = activity.get("timestamp")
            if ts:
                try:
                    # Parse timestamp
                    if isinstance(ts, str):
                        # Try common formats
                        for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"]:
                            try:
                                activity_time = datetime.strptime(ts[:26], fmt.replace("Z", ""))
                                break
                            except ValueError:
                                continue
                        else:
                            continue
                        
                        hours = (datetime.now() - activity_time).total_seconds() / 3600
                        return max(0, int(hours))
                except Exception:
                    continue
        
        return 168  # Default to 1 week if can't parse
    
    
    def _inject_discovery_guidance(self, intent_value: str, user_signals: Dict):
        """
        Write discovery clarification guidance to active_context.json.
        NEXUS chat will read this and ask clarifying questions.
        
        Args:
            intent_value: What user wants (e.g., "general", "unknown")
            user_signals: Extracted context like {college: "BITS Pilani", skills: "Python"}
        """
        active_context_file = os.path.join(
            os.path.dirname(self.state_file), 
            "active_context.json"
        )
        
        # Build suggested questions based on available signals
        questions = []
        if not user_signals.get("goal"):
            questions.append("What's your goal? (mentorship, job opportunities, collaboration)")
        if not user_signals.get("industry"):
            questions.append("What field or industry are you interested in?")
        if not user_signals.get("skills"):
            questions.append("What are your main skills or areas of expertise?")
        
        # Build confirmation prompt for detected signals
        confirmations = []
        if user_signals.get("college"):
            confirmations.append(f"I noticed you mentioned {user_signals['college']} - should I prioritize alumni connections?")
        if user_signals.get("skills"):
            confirmations.append(f"Should I search for people with similar skills in {user_signals['skills']}?")
        
        discovery_context = {
            "discovery_mode": True,
            "needs_clarification": True,
            "user_intent": intent_value,
            "extracted_signals": user_signals,
            "suggested_questions": questions[:2],  # Limit to 2 questions
            "signal_confirmations": confirmations[:1],  # Limit to 1 confirmation
            "guidance": "User wants to discover people but needs more context. Ask clarifying questions naturally.",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(active_context_file, "w", encoding="utf-8") as f:
                json.dump(discovery_context, f, indent=2, ensure_ascii=False)
            print(f"[OK] Discovery guidance written: {active_context_file}")
        except Exception as e:
            print(f"[ERROR] Failed to write discovery guidance: {e}")
    
    
    def _check_profile_refresh(self):
        """
        Check if active target's profile needs refresh (>6 hours old).
        If changes detected, inject update into chat. Silent if no changes.
        """
        if not self.active_target:
            return
        
        now = datetime.now()
        last_fetched_str = self.active_target.get("last_fetched")
        
        if not last_fetched_str:
            return
        
        try:
            last_fetched = datetime.fromisoformat(last_fetched_str)
            hours_since = (now - last_fetched).total_seconds() / 3600
            
            if hours_since < self.REFRESH_INTERVAL_HOURS:
                return  # Not stale yet
            
            print(f"\n[REFRESH] Profile refresh check: {self.active_target.get('github_username')} ({hours_since:.1f}h old)")
            
            # Re-run pipeline
            github_username = self.active_target.get("github_username")
            if not github_username:
                return
            
            entity = ExtractedEntity(
                entity_type="github",
                value=github_username,
                confidence=1.0,
                source_message="Profile refresh"
            )
            
            new_profile = self.trigger_backend_pipeline(entity)
            
            if not new_profile:
                print(f"   [WARNING] Refresh failed for {github_username}")
                return
            
            # Compare with old profile
            old_profile = self.active_target.get("old_profile", {})
            has_changes, changes = self._has_profile_changed(old_profile, new_profile)
            
            if has_changes:
                print(f"   [OK] Changes detected: {changes}")
                self._inject_profile_update(changes, new_profile)
                
                # Update tracking
                self.active_target["old_profile"] = new_profile
                self.active_target["last_fetched"] = now.isoformat()
            else:
                print(f"   -> No changes (silent)")
                # Just update timestamp
                self.active_target["last_fetched"] = now.isoformat()
                
        except Exception as e:
            print(f"[WARNING] Profile refresh error: {e}")
    
    
    def _has_profile_changed(self, old: Dict, new: Dict) -> tuple:
        """
        Compare old and new profiles to detect meaningful changes.
        
        Returns:
            (has_changes: bool, changes: List[str])
        """
        changes = []
        
        # Check recent activity (most important)
        old_timeline = old.get("activity_timeline", [])
        new_timeline = new.get("activity_timeline", [])
        
        if new_timeline and len(new_timeline) > len(old_timeline):
            # New activity items
            new_activity = new_timeline[0] if new_timeline else {}
            activity_type = new_activity.get("type", "activity")
            activity_desc = new_activity.get("description", "new activity")[:50]
            changes.append(f"new_{activity_type}: {activity_desc}")
        
        # Check repo count
        old_repos = old.get("public_repos", 0) or old.get("github_stats", {}).get("total_repos", 0)
        new_repos = new.get("public_repos", 0) or new.get("github_stats", {}).get("total_repos", 0)
        if new_repos > old_repos:
            changes.append(f"new_repos: +{new_repos - old_repos}")
        
        # Check followers
        old_followers = old.get("followers", 0) or old.get("github_stats", {}).get("followers", 0)
        new_followers = new.get("followers", 0) or new.get("github_stats", {}).get("followers", 0)
        if new_followers > old_followers + 5:  # Threshold to avoid noise
            changes.append(f"followers: +{new_followers - old_followers}")
        
        return (len(changes) > 0, changes)
    
    
    def _inject_profile_update(self, changes: List[str], new_profile: Dict):
        """
        Inject profile update notification into chat context.
        Only called when changes are detected.
        """
        active_context_file = os.path.join(
            os.path.dirname(self.state_file), 
            "active_context.json"
        )
        
        # Build human-readable summary
        change_summary = ", ".join(changes[:3])  # Limit to 3 changes
        person_name = new_profile.get("name", "Target")
        
        update_context = {
            "profile_update": True,
            "target_name": person_name,
            "changes": changes,
            "summary": f"New activity from {person_name}: {change_summary}",
            "guidance": f"Mention this update naturally in conversation. The user might want to reference this recent activity in their outreach.",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            with open(active_context_file, "w", encoding="utf-8") as f:
                json.dump(update_context, f, indent=2, ensure_ascii=False)
            print(f"[OK] Profile update injected: {change_summary}")
        except Exception as e:
            print(f"[ERROR] Failed to write profile update: {e}")
    
    
    def _generate_strategy(self, cit_score: CITScore) -> List[Dict]:
        """Generate tentative strategy based on CIT score"""
        from datetime import timedelta
        now = datetime.now()
        
        if cit_score.execution_state == "STRONG_GO":
            follow_up_date = (now + timedelta(days=2)).strftime("%b %d").upper()
            return [
                {"date": "NOW", "action": "Send personalized outreach"},
                {"date": follow_up_date, "action": "Follow up if no response"}
            ]
        elif cit_score.execution_state == "PROCEED":
            return [
                {"date": "TODAY", "action": "Draft and review message"},
                {"date": "TOMORROW", "action": "Send during optimal window (2-4pm)"}
            ]
        elif cit_score.execution_state == "CAUTION":
            return [
                {"date": "THIS WEEK", "action": "Engage with their content first"},
                {"date": "NEXT WEEK", "action": "Soft outreach after warming up"}
            ]
        else:
            return [
                {"date": "WATCHLIST", "action": "Monitor for activity signals"},
                {"date": "TBD", "action": "Revisit when timing improves"}
            ]
    
    
    def process_new_messages(self, chat_log: Dict) -> List[ExtractedEntity]:
        """
        Process new messages from a chat log file.
        
        Args:
            chat_log: Parsed chat log JSON
            
        Returns:
            List of newly extracted entities
        """
        messages = chat_log.get("messages", [])
        new_entities = []
        
        for msg in messages:
            # Skip if already processed
            msg_id = f"{msg.get('timestamp', '')}_{msg.get('content', '')[:50]}"
            if msg_id in self.processed_messages:
                continue
            
            self.processed_messages.add(msg_id)
            
            # Only process user messages for entity extraction
            if msg.get("role") != "user":
                continue
            
            content = msg.get("content", "")
            
            # Extract entities using regex
            entities = self.extract_entities_regex(content)
            
            # If no regex matches, try Gemini for person names
            if not entities and self.gemini_enabled:
                # Get conversation context
                context = " ".join([m.get("content", "") for m in messages[-5:]])
                entities = self.extract_entities_gemini(content, context)
            
            new_entities.extend(entities)
        
        return new_entities
    
    
    def get_latest_chat_log(self) -> Optional[Tuple[str, Dict]]:
        """
        Get the most recently modified chat log file.
        
        Returns:
            Tuple of (filepath, parsed_json) or None
        """
        pattern = os.path.join(self.conversations_dir, "chat_*.json")
        files = glob.glob(pattern)
        
        if not files:
            return None
        
        # Get most recent by modification time
        latest_file = max(files, key=os.path.getmtime)
        
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return (latest_file, data)
        except Exception as e:
            print(f"[WARNING] Failed to read chat log: {e}")
            return None
    
    
    def run_once(self) -> bool:
        """
        Run one iteration of the log processing loop.
        
        Returns:
            True if new entities were processed
        """
        # Check if active target needs refresh (>6 hours old)
        self._check_profile_refresh()
        
        result = self.get_latest_chat_log()
        if not result:
            return False
        
        filepath, chat_log = result
        entities = self.process_new_messages(chat_log)
        
        if not entities:
            return False
        
        print(f"[ICON] Found {len(entities)} new entities in {os.path.basename(filepath)}")
        
        # Process each entity
        for entity in entities:
            print(f"  -> {entity.entity_type}: {entity.value} (confidence: {entity.confidence})")
            
            # Handle person_name entities - discover their profiles via Google Search
            if entity.entity_type == "person_name":
                print(f"  [SEARCH] Person name detected, searching for profiles...")
                discovered_entities = self.discover_profiles_from_name(entity.value)
                
                if discovered_entities:
                    # Use the discovered entities instead
                    for discovered in discovered_entities:
                        print(f"     -> Discovered {discovered.entity_type}: {discovered.value}")
                        
                        # Trigger pipeline for discovered profile
                        profile = self.trigger_backend_pipeline(discovered)
                        if profile:
                            intent = self.infer_intent(chat_log.get("messages", []))
                            user_context = {
                                "skills": profile.get("user_skills", []),
                                "mode": profile.get("user_mode", "Student")
                            }
                            cit_score = self.compute_cit_score(user_context, profile, intent)
                            focus = profile.get("topics", []) or profile.get("skills", [])[:3]
                            self.update_frontend_state(profile, cit_score, intent, focus)
                            break  # Use first successful discovery
                else:
                    print(f"  [WARNING] Could not discover profiles for: {entity.value}")
            
            # Only trigger pipeline for high-confidence social links
            elif entity.entity_type in ["github", "twitter", "linkedin"] and entity.confidence >= 0.8:
                profile = self.trigger_backend_pipeline(entity)
                
                if profile:
                    # Infer intent from conversation
                    intent = self.infer_intent(chat_log.get("messages", []))
                    
                    # Compute CIT score
                    user_context = {
                        "skills": profile.get("user_skills", []),
                        "mode": profile.get("user_mode", "Student")
                    }
                    cit_score = self.compute_cit_score(user_context, profile, intent)
                    
                    # Extract focus keywords
                    focus = profile.get("topics", []) or profile.get("skills", [])[:3]
                    
                    # Update frontend state
                    self.update_frontend_state(profile, cit_score, intent, focus)
                    
                    # Track as active target for real-time updates
                    if entity.entity_type == "github":
                        self.active_target = {
                            "github_username": entity.value,
                            "last_fetched": datetime.now().isoformat(),
                            "old_profile": profile
                        }
                        print(f"  [ICON] Tracking active target: {entity.value}")
            
            # Handle discovery_intent - find people based on goals
            elif entity.entity_type == "discovery_intent":
                print(f"  [ICON] Discovery intent detected: {entity.value}")
                
                # Build user context from conversation
                user_context = {
                    "skills": [],  # Could extract from user profile
                    "mode": "Student"  # Default, ideally from session
                }
                
                # Discover people matching the goal
                discovered_people = self.discover_people(entity.value, user_context, max_results=5)
                
                if discovered_people:
                    print(f"  [OK] Found {len(discovered_people)} people matching '{entity.value}'")
                    
                    # Process first discovered person through full pipeline
                    for person in discovered_people[:1]:  # Start with top match
                        github_entity = ExtractedEntity(
                            entity_type="github",
                            value=person.get("github_username", ""),
                            confidence=0.9,
                            source_message=f"Discovered for: {entity.value}"
                        )
                        
                        profile = self.trigger_backend_pipeline(github_entity)
                        if profile:
                            # Add discovery metadata
                            profile["discovery_goal"] = entity.value
                            profile["discovery_results"] = discovered_people
                            
                            intent = self.infer_intent(chat_log.get("messages", []))
                            cit_score = self.compute_cit_score(user_context, profile, intent)
                            focus = [entity.value] + profile.get("skills", [])[:2]
                            self.update_frontend_state(profile, cit_score, intent, focus)
                else:
                    print(f"  [WARNING] No people found for: {entity.value}")
            
            # Handle vague discovery - needs clarification, don't search yet
            elif entity.entity_type == "discovery_needs_context":
                print(f"  [ICON] Vague discovery intent: {entity.value}")
                print(f"     -> Injecting clarification guidance into chat context")
                
                # Collect any user context signals from this extraction
                user_signals = {}
                for e in entities:
                    if e.entity_type == "user_context":
                        # Parse "college:BITS Pilani" format
                        if ":" in e.value:
                            key, val = e.value.split(":", 1)
                            user_signals[key.strip()] = val.strip()
                
                # Write discovery guidance to active_context.json
                self._inject_discovery_guidance(entity.value, user_signals)
            
            # Handle user_context signals - store for future use
            elif entity.entity_type == "user_context":
                print(f"  [ICON] User context signal: {entity.value}")
                # These are already processed above in discovery_needs_context handler
        
        return True
    
    
    def run(self):
        """
        Run the log watcher loop indefinitely.
        """
        print("=" * 60)
        print("NEXUS Logistic Mind - Starting")
        print("=" * 60)
        print(f"[DIR] Watching: {self.conversations_dir}")
        print(f"[FILE] State file: {self.state_file}")
        print(f"[TIMER] Poll interval: {self.poll_interval}s")
        print("-" * 60)
        
        try:
            while True:
                self.run_once()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            print("\n[STOP] Logistic Mind stopped")


def generate_search_keywords(name: str, hints: Dict[str, str]) -> str:
    """
    Convert person details to search keywords (placeholder for Google Search).
    
    Args:
        name: Person's name
        hints: Additional info like company, role
        
    Returns:
        CSV-formatted keywords string
    """
    keywords = [name]
    
    if hints.get("company"):
        keywords.append(hints["company"])
    if hints.get("role"):
        keywords.append(hints["role"])
    if hints.get("location"):
        keywords.append(hints["location"])
    
    # Always add platform keywords for social discovery
    keywords.extend(["GitHub", "Twitter", "LinkedIn"])
    
    return ", ".join(keywords)


# --- Main Entry Point ---

if __name__ == "__main__":
    # Run the Logistic Mind
    mind = LogisticMind()
    mind.run()
