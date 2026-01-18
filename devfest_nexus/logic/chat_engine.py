"""
Gemini Chat Engine - AI Chatbot Integration for NEXUS
=====================================================
Provides a reusable wrapper around Google's Gemini API for conversational AI.

Features:
- Session-based chat with conversation history
- System prompt for NEXUS personality
- Error handling for API failures
- Context management for target profiles
"""

import os
import json
import uuid
from typing import List, Dict, Optional
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

# Import advanced context loader
from logic.context_loader import get_nexus_system_prompt

# Load environment variables
load_dotenv()



class GeminiChatEngine:
    """
    Wrapper for Gemini API with conversation history management.
    Maintains chat context and provides a clean interface for dashboard integration.
    """
    
    
    # NEXUS Master System Prompt - Professional Networking Strategist
    DEFAULT_SYSTEM_PROMPT = """SYSTEM IDENTITY: NEXUS

You are NEXUS, a professional networking strategist and career consultant. Your role is to provide strategic guidance for professional relationship building, with the analytical rigor of a management consultant and the tactical precision of a career advisor.

COMMUNICATION STYLE:
- Professional and consultative tone at all times
- Structured, well-spaced responses with clear hierarchy
- No emojis, exclamation marks, or informal language
- Polite, respectful, and measured communication
- Present insights as a trusted advisor, not an enthusiastic assistant

CORE PURPOSE:
To bridge the gap between professional intent and actionable opportunity. You provide data-driven strategy backed by practical execution frameworks. Your recommendations balance optimism about goals with honesty about challenges.

CRITICAL DATA INTEGRITY RULE:
You have access to a backend that fetches real profile data from GitHub and other sources. When you receive a "CONTEXT INJECTION" system message:
- If it says "DATA FETCH INCOMPLETE" or "has_real_data: false" - you MUST NOT make up any details
- NEVER invent technologies, commit counts, project names, institutions, or any other specific facts
- If you do not have verified data, say clearly: "I was unable to retrieve complete profile data for this person"
- Offer to guide the user to check the profile directly or ask them to provide context
- DO NOT GUESS based on usernames or make assumptions about a person's background
- This is non-negotiable. Hallucinated information destroys user trust.

---

PART 1: USER CONTEXT PROTOCOL

Before generating any strategy, you must verify you have sufficient context about the user.

Cold Start Protocol:

If user context is missing or incomplete (role, goal, or key constraints unknown):
- Pause strategy generation
- Politely request the specific information needed
- Explain why this context is essential for accurate guidance

Example response:
"To provide strategic recommendations tailored to your situation, I need to understand your current context. Could you please share:

1. Your current professional role or status
2. Your primary networking objective
3. Any relevant constraints or preferences

This information will allow me to calibrate my recommendations appropriately."

Dynamic Context Updates:

When users provide new information during conversation:
- Acknowledge the update professionally
- Note how it affects your recommendations
- Adjust strategy accordingly

Example: "Thank you for clarifying. Given your preference for asynchronous communication, I'll adjust the outreach strategy to favor email over calls."

---

PART 2: READINESS ASSESSMENT FRAMEWORK

For each networking target, calculate a Readiness Score (0-100) based on available data.

Student/Intern Context - Hiring Intent:
Base calculation: (Activity Recency × 0.4) + (Skill Alignment × 0.4) + (Connection Strength × 0.2)

Adjustments:
- Alumni connection: +20 points
- Exam period (May/December): -15 points
- Recent hiring announcement: +25 points

Founder Context - Funding Intent:
Base calculation: (Signal Strength × 0.5) + (Introduction Path Quality × 0.5)

Adjustments:
- Recent fund announcement: +40 points
- Hiring freeze signals: -50 points (consider abort)
- Warm introduction available: +30 points

Researcher Context - Collaboration Intent:
Base calculation: (Research Alignment × 0.6) + (Publication Recency × 0.4)

Adjustments:
- Recent conference activity: +30 points
- Citation overlap: +20 points
- No recent publications (>2 years): -25 points

---

PART 3: TEMPORAL STRATEGY

Consider timing in all recommendations based on current date and time.

Professional Availability Patterns:

Low-Activity Periods (Friday evening through Sunday):
- Recommendation: "Given the weekend timing, I recommend scheduling this outreach for Monday morning between 10:00-11:00 AM, when inbox attention is typically highest."

Optimal Windows (Tuesday-Thursday, 10:00 AM - 2:00 PM):
- Readiness scores receive +10 modifier
- Recommendation: "Current timing falls within optimal outreach windows. Immediate action is strategically sound."

Holiday Considerations:
- Major holidays: Readiness score drops to 0
- Recommendation: "Given the holiday period, I advise waiting 2-3 business days to ensure proper attention to your outreach."

---

PART 4: RESPONSE STRUCTURE

All strategic recommendations should follow this format:

TARGET PROFILE:
[Name and relevant context]

READINESS ASSESSMENT:
Score: [X]/100
Rationale: [Brief explanation of score components]

STRATEGIC ANALYSIS:
Context: [Current situation and constraints]
Opportunity: [Specific angle or leverage point]
Challenge: [Honest assessment of difficulty]

RECOMMENDED APPROACH:
Timing: [When to act]
Channel: [Best communication method]
Message Framework: [Key points to include]

DRAFT COMMUNICATION:
[If requested, provide a specific draft]

---

METHODOLOGY:

Analysis-First Approach:
- Gather all available information before recommending action
- Identify gaps in data and request clarification
- Explain reasoning behind each recommendation
- Present options when multiple approaches are viable

Consultant Mindset:
- Ask clarifying questions to understand context fully
- Break complex objectives into staged approaches
- Validate assumptions before proceeding
- Provide reasoning for all recommendations

Progressive Strategy:
- One clear action per recommendation
- Build on previous context in ongoing conversations
- Adapt based on feedback and new information
- Focus on informed decisions over quick fixes

---

CONTEXT VARIABLES:

The following variables may be available for analysis:
- user_context: Role, goals, skills, constraints, preferences
- target_context: Profile data, activity patterns, connection strength
- current_time: Date and time for temporal strategy

When these are not available, request them before strategizing."""

    def __init__(self, system_prompt: Optional[str] = None, model_name: str = "models/gemini-2.0-flash", session_id: Optional[str] = None):
        """
        Initialize the Gemini chat engine.
        
        Args:
            system_prompt: Custom system prompt (uses default if None)
            model_name: Gemini model to use (default: gemini-1.0-pro)
            session_id: ID of an existing session to resume
        
        Raises:
            ValueError: If GEMINI_API_KEY is not set in environment
        """
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key or api_key == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please create a .env file with your API key. "
                "Get one from: https://makersuite.google.com/app/apikey"
            )
        
        # Configure Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
        # Build complete system prompt
        if system_prompt:
            self.system_prompt = system_prompt
        else:
            self.system_prompt = get_nexus_system_prompt(
                user_context=None,
                target_context=None
            )
            
        # Context data for real-time injection
        self.context_data: Dict = {}
        self.user_context: Dict = {}
        self.target_context: Dict = {}
        
        # --- LOGGING & SESSION SETUP ---
        import glob
        
        self.history: List[Dict[str, str]] = []
        gemini_history = []
        
        # Directory for logs
        self.conversations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "backend", "data", "conversations"
        )
        os.makedirs(self.conversations_dir, exist_ok=True)
        
        if session_id:
            # Try to find existing file
            pattern = os.path.join(self.conversations_dir, f"chat_*_{session_id}.json")
            matching_files = glob.glob(pattern)
            
            if matching_files:
                # Load the most recent one (though ID should be unique)
                self.log_file_path = matching_files[0]
                try:
                    with open(self.log_file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.session_id = data.get("session_id", session_id)
                        self.history = data.get("messages", [])
                        
                        # Reconstruct compatible history for Gemini
                        for msg in self.history:
                            role = "user" if msg["role"] == "user" else "model"
                            gemini_history.append({
                                "role": role,
                                "parts": [msg["content"]]
                            })
                except Exception as e:
                    print(f"⚠️ Failed to restore session {session_id}: {e}")
                    self.session_id = session_id
            else:
                self.session_id = session_id
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.log_file_path = os.path.join(self.conversations_dir, f"chat_{timestamp}_{self.session_id}.json")
        else:
            self.session_id = str(uuid.uuid4())[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_file_path = os.path.join(self.conversations_dir, f"chat_{timestamp}_{self.session_id}.json")
            self._log_to_file()
        
        # Initialize chat session with restored history if any
        self.chat = self.model.start_chat(history=gemini_history)
        
    def _log_to_file(self):
        """Writes the current conversation state to the JSON log file."""
        try:
            log_data = {
                "session_id": self.session_id,
                "last_updated": datetime.now().isoformat(),
                "messages": self.history
            }
            with open(self.log_file_path, "w", encoding="utf-8") as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Failed to log conversation: {e}")
    
    def send_message(self, user_message: str) -> str:
        """
        Send a message to the AI and get a response.
        
        Args:
            user_message: The user's message
            
        Returns:
            AI's response text
            
        Raises:
            Exception: If API call fails
        """
        try:
            # Add user message to history
            self.history.append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat()
            })
            self._log_to_file()  # Log immediately so LogisticMind can see it
            
            # --- FLAG-BASED ACTION DISPATCH ---
            # Use LLM to analyze full chat context and determine actions
            import re
            import time
            import sys
            
            # Add backend to path for imports
            backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "backend")
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            print(f"\n{'='*50}")
            print(f"[CHAT] Processing message: {user_message[:80]}...")
            
            # Import flag-related modules
            from logistic_mind import ActionFlag, analyze_chat_for_actions
            
            # Use LLM to analyze full conversation context and determine actions
            print("[LLM] Analyzing chat context for actions...")
            analysis = analyze_chat_for_actions(self.history, user_message)
            
            # Parse LLM analysis results
            llm_flags = analysis.get("flags", [])
            entities = analysis.get("entities", {})
            needs_clarification = analysis.get("needs_clarification", False)
            clarification_prompt = analysis.get("clarification_prompt", "")
            
            print(f"[LLM] Result: flags={llm_flags} entities={entities} needs_clarification={needs_clarification}")
            
            # Build action context from LLM-extracted entities
            action_context = {
                "github_username": entities.get("github_username"),
                "person_name": entities.get("person_name"),
                "search_goal": entities.get("search_goal"),
                "intent": "networking"
            }
            
            # Also check for GitHub URLs as fallback (very reliable detection)
            github_match = re.search(r'github\.com/([a-zA-Z0-9_-]+)', user_message, re.IGNORECASE)
            if github_match and not action_context.get("github_username"):
                action_context["github_username"] = github_match.group(1)
                if "FETCH_GITHUB" not in llm_flags:
                    llm_flags.append("FETCH_GITHUB")
            
            # Convert string flags to ActionFlag enums
            detected_flags = []
            for flag_name in llm_flags:
                try:
                    detected_flags.append(ActionFlag[flag_name])
                except KeyError:
                    print(f"[WARNING] Unknown flag from LLM: {flag_name}")
            
            # If FETCH_GITHUB is set, also add COMPUTE_CIT and UPDATE_DASHBOARD
            if ActionFlag.FETCH_GITHUB in detected_flags:
                if ActionFlag.COMPUTE_CIT not in detected_flags:
                    detected_flags.append(ActionFlag.COMPUTE_CIT)
                if ActionFlag.UPDATE_DASHBOARD not in detected_flags:
                    detected_flags.append(ActionFlag.UPDATE_DASHBOARD)
            
            print(f"[FLAGS] Final: {[f.value for f in detected_flags] if detected_flags else 'None'}")
            
            # Execute flags through LogisticMind dispatcher if we have actions
            dispatch_results = None
            if detected_flags:
                try:
                    from logistic_mind import LogisticMind
                    print("[DISPATCH] Initializing LogisticMind...")
                    mind = LogisticMind()
                    dispatch_results = mind.dispatch_actions(detected_flags, action_context)
                    
                    print(f"[DISPATCH] Results: executed={dispatch_results.get('flags_executed')}, errors={dispatch_results.get('errors')}")
                    
                    # Inject results into context for the chat response
                    if dispatch_results.get("profile"):
                        profile = dispatch_results["profile"]
                        cit = dispatch_results.get("cit_score", {})
                        print(f"[INJECT] Profile: {profile.get('name', 'Unknown')}, CIT: {cit.get('total', 0)}/100")
                        self.inject_context(cit, profile, action_context.get("intent", "networking"))
                        print(f"✅ Flag dispatch complete: {dispatch_results['flags_executed']}")
                    elif dispatch_results.get("discovered_users"):
                        # User discovery completed
                        users = dispatch_results["discovered_users"]
                        print(f"✅ Discovered {len(users)} users: {[u.get('name', u.get('github_username')) for u in users[:3]]}")
                        
                except Exception as e:
                    print(f"⚠️ Flag dispatch error: {e}")
                    import traceback
                    traceback.print_exc()
                    # Continue without dispatch results
            
            # Also check for existing context from LogisticMind (INCREASED wait time to 30s)
            active_context_path = os.path.join(
                os.path.dirname(self.log_file_path),
                "active_context.json"
            )
            
            # If no context was injected yet, wait for LogisticMind
            if not any(msg.get("type") == "context_injection" and msg.get("has_real_data") for msg in self.history[-5:]):
                print("[WAIT] Waiting for additional context from LogisticMind (30s max)...")
                max_wait = 30  # INCREASED from 15 to 30 seconds
                start_time = time.time()
                initial_mtime = os.path.getmtime(active_context_path) if os.path.exists(active_context_path) else 0
                
                while time.time() - start_time < max_wait:
                    if os.path.exists(active_context_path):
                        current_mtime = os.path.getmtime(active_context_path)
                        if current_mtime > initial_mtime:
                            try:
                                with open(active_context_path, 'r', encoding='utf-8') as f:
                                    context = json.load(f)
                                    target = context.get('target_profile', {})
                                    cit = context.get('cit_score', {})
                                    intent = context.get('intent', '')
                                    
                                    print(f"[CONTEXT] Loaded: target={target.get('name')}, CIT={cit.get('total', 0)}")
                                    
                                    if target.get('skills') or target.get('bio'):
                                        self.inject_context(cit, target, intent)
                                        print(f"✅ Context from LogisticMind: {target.get('name')} (CIT: {cit.get('total', 0)}/100)")
                                        break
                            except Exception as e:
                                print(f"⚠️ Failed to load context: {e}")
                    time.sleep(0.5)
                else:
                    print("⏱️ No additional context received within 30s")
            
            print(f"{'='*50}\n")
            
            # Construct prompt with system context and any injected profile data
            # Check for recent context injection in history
            context_injection = ""
            for msg in reversed(self.history[-5:]):  # Check last 5 messages
                if msg.get("type") == "context_injection":
                    context_injection = msg.get("content", "")
                    break
            
            if context_injection:
                full_prompt = f"{self.system_prompt}\n\n{context_injection}\n\nUser: {user_message}"
            else:
                full_prompt = f"{self.system_prompt}\n\nUser: {user_message}"
            
            # Send to Gemini
            response = self.chat.send_message(full_prompt)
            
            # Extract response text with proper error handling for empty responses
            response_text = None
            try:
                # Try to get text from response
                if hasattr(response, 'text') and response.text:
                    response_text = response.text
                elif hasattr(response, 'parts') and response.parts:
                    # Try to extract from parts
                    response_text = ''.join(part.text for part in response.parts if hasattr(part, 'text'))
                elif hasattr(response, 'candidates') and response.candidates:
                    # Try candidates
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and candidate.content.parts:
                            response_text = ''.join(p.text for p in candidate.content.parts if hasattr(p, 'text'))
                            break
            except Exception as text_error:
                print(f"[WARN] Could not extract response text: {text_error}")
            
            # Fallback if no text could be extracted
            if not response_text:
                response_text = "I apologize, but I couldn't generate a response at the moment. Please try rephrasing your question or try again shortly."
            
            # Add assistant response to history
            self.history.append({
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.now().isoformat()
            })
            self._log_to_file()  # Log response
            
            return response_text
            
        except Exception as e:
            # Log error and return user-friendly message
            error_msg = f"I'm having trouble connecting to my AI brain. Error: {str(e)}"
            
            self.history.append({
                "role": "assistant",
                "content": error_msg,
                "timestamp": datetime.now().isoformat()
            })
            self._log_to_file()
            
            return error_msg
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Get conversation history.
        
        Returns:
            List of messages with 'role' and 'content' keys
        """
        return self.history.copy()
    
    def clear_history(self):
        """
        Clear conversation history and reset chat session.
        """
        self.chat = self.model.start_chat(history=[])
        self.history = [
            {
                "role": "assistant",
                "content": "Chat history cleared. How can I help you?"
            }
        ]
    
    def reset(self):
        """
        Reset the chat engine for a new session.
        Creates a new session ID and clears history.
        """
        import uuid
        # Generate new session ID
        self.session_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = os.path.join(self.conversations_dir, f"chat_{timestamp}_{self.session_id}.json")
        
        # Reset chat with fresh history
        self.chat = self.model.start_chat(history=[])
        self.history = []
        self.context_data = {}
        self.target_context = {}
        
        # Log the new session
        self._log_to_file()
    
    def load_history(self, messages: list):
        """
        Load a conversation history into the engine.
        Used when switching between sessions.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
        """
        self.history = messages.copy() if messages else []
        
        # Reconstruct Gemini-compatible history
        gemini_history = []
        for msg in self.history:
            if msg.get("role") in ["user", "assistant"]:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({
                    "role": role,
                    "parts": [msg.get("content", "")]
                })
        
        # Restart chat with loaded history
        self.chat = self.model.start_chat(history=gemini_history)
    
    def set_context(self, context_data: Dict):
        """
        Set context data for more informed responses.
        
        Args:
            context_data: Dictionary containing target profile, scores, etc.
            
        Example:
            engine.set_context({
                "target_name": "John Doe",
                "momentum_score": 85,
                "readiness_score": 92,
                "last_activity": "Pushed code 2h ago"
            })
        """
        self.context_data = context_data
    
    def get_context(self) -> Dict:
        """Get current context data."""
        return self.context_data.copy()
    
    def inject_context(self, cit_score: Dict, target_profile: Dict, intent: str = ""):
        """
        Inject CIT score and target profile into the chat context.
        Called by Logistic Mind when new profile data is available.
        
        Args:
            cit_score: Dict with context, intent, timing, total scores
            target_profile: Consolidated profile data
            intent: Inferred user intent
        """
        # Store for reference
        self.target_context = target_profile
        self.user_context["intent"] = intent
        
        # Check if we have REAL data or just empty/failed fetch
        has_real_data = bool(
            target_profile.get('skills') or 
            target_profile.get('topics') or 
            target_profile.get('bio') or
            target_profile.get('recent_activity') or
            (target_profile.get('last_activity_hours', 999) < 999)
        )
        
        if has_real_data:
            # Format recent activity for display
            recent_activities_str = ""
            for act in target_profile.get('recent_activity', [])[:3]:
                recent_activities_str += f"\n  - [{act.get('platform', 'unknown')}] {act.get('content', '')[:60]}..."
            
            # Format repositories for display
            repos_str = ""
            repos = target_profile.get('repositories', [])
            if repos:
                repos_str = "\n\nREPOSITORIES (Open Source Contributions):"
                for repo in repos[:10]:
                    name = repo.get('name', 'Unknown')
                    desc = repo.get('description', 'No description')[:80]
                    lang = repo.get('language', 'Unknown')
                    stars = repo.get('stars', 0)
                    repos_str += f"\n  - {name} ({lang}) ★{stars}: {desc}"
            
            # Build context injection message with REAL data
            context_injection = f"""
--- REAL-TIME CONTEXT INJECTION (VERIFIED DATA) ---
Target: {target_profile.get('name', 'Unknown')}
GitHub Username: {target_profile.get('github_username', 'N/A')}
Bio: {target_profile.get('bio', 'Not available')[:300]}

CIT SCORE BREAKDOWN:
- Context: {cit_score.get('context', 0)}/100 (Skill/interest overlap)
- Intent: {cit_score.get('intent', 0)}/100 (Goal alignment)
- Timing: {cit_score.get('timing', 0)}/100 (Activity recency)
- TOTAL: {cit_score.get('total', 0)}/100
- Execution State: {cit_score.get('execution_state', 'UNKNOWN')}

User's Inferred Intent: {intent}

VERIFIED TECHNOLOGIES/SKILLS: {', '.join(target_profile.get('skills', [])) or 'None detected'}
Total Public Repos: {target_profile.get('total_public_repos', 'Unknown')}
Followers: {target_profile.get('followers', 'Unknown')}
Last Active: {target_profile.get('last_activity_hours', 'Unknown')} hours ago
Recent Activity:{recent_activities_str or ' None recorded'}
{repos_str}

IMPORTANT: Use ONLY this verified data when discussing this person. Reference specific repositories when asked about their contributions.
--- END CONTEXT ---
"""
        else:
            # CRITICAL: Warn about missing data to prevent hallucination
            context_injection = f"""
--- CONTEXT INJECTION (DATA FETCH INCOMPLETE) ---
Target Username: {target_profile.get('github_username', target_profile.get('name', 'Unknown'))}

⚠️ CRITICAL: Profile data fetch was incomplete or failed.
DO NOT make up or hallucinate any details about this person's:
- Repositories or projects
- Technologies or skills  
- Employment history
- Activity patterns

Instead, you MUST:
1. Tell the user that you could not retrieve complete profile data
2. Suggest they check the profile directly: https://github.com/{target_profile.get('github_username', '')}
3. Ask if they want to provide any context about this person manually

CIT Score: {cit_score.get('total', 0)}/100 (Low confidence due to missing data)
--- END CONTEXT ---
"""
        
        # Add as system message to history for context
        self.history.append({
            "role": "system",
            "content": context_injection,
            "timestamp": datetime.now().isoformat(),
            "type": "context_injection",
            "has_real_data": has_real_data
        })
        
        # Log the injection
        self._log_to_file()
        data_status = "VERIFIED" if has_real_data else "INCOMPLETE"
        print(f"✅ Context injected for: {target_profile.get('name', 'Unknown')} (CIT: {cit_score.get('total', 0)}, Data: {data_status})")



def create_chat_engine(system_prompt: Optional[str] = None, session_id: Optional[str] = None) -> Optional[GeminiChatEngine]:
    """
    Factory function to create a chat engine with error handling.
    
    Args:
        system_prompt: Custom system prompt (optional)
        session_id: Existing session ID to resume (optional)
        
    Returns:
        GeminiChatEngine instance or None if API key is missing
    """
    try:
        return GeminiChatEngine(system_prompt=system_prompt, session_id=session_id)
    except ValueError as e:
        print(f"❌ Chat engine initialization failed: {e}")
        return None


# Example usage for testing
if __name__ == "__main__":
    # Test the chat engine
    engine = create_chat_engine()
    
    if engine:
        print("✅ Chat engine initialized successfully!")
        print(f"Model: {engine.model_name}\n")
        
        # Test conversation
        test_messages = [
            "What can you help me with?",
            "How do I know when to reach out to someone?"
        ]
        
        for msg in test_messages:
            print(f"User: {msg}")
            response = engine.send_message(msg)
            print(f"NEXUS: {response}\n")
    else:
        print("❌ Failed to initialize. Check your .env file.")
