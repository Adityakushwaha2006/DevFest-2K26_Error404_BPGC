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

    def __init__(self, system_prompt: Optional[str] = None, model_name: str = "models/gemini-3-flash-preview"):
        """
        Initialize the Gemini chat engine.
        
        Args:
            system_prompt: Custom system prompt (uses default if None)
            model_name: Gemini model to use (default: gemini-1.0-pro)
        
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
        
        # Build complete system prompt with Strategy Matrix
        # If custom prompt provided, use it. Otherwise, build the God Prompt
        if system_prompt:
            self.system_prompt = system_prompt
        else:
            # Generate complete NEXUS prompt with Strategy Matrix
            # Initial context is empty - will be injected via set_context()
            self.system_prompt = get_nexus_system_prompt(
                user_context=None,
                target_context=None
            )
        
        # Initialize chat session
        self.chat = self.model.start_chat(history=[])
        
        # Store conversation history (starts empty - no greeting)
        # First message will appear only after user sends input
        self.history: List[Dict[str, str]] = []
        
        # Context data for real-time injection
        self.context_data: Dict = {}
        self.user_context: Dict = {}
        self.target_context: Dict = {}
    
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
                "content": user_message
            })
            
            # Construct prompt with system context
            full_prompt = f"{self.system_prompt}\n\nUser: {user_message}"
            
            # Send to Gemini
            response = self.chat.send_message(full_prompt)
            
            # Extract response text
            response_text = response.text
            
            # Add assistant response to history
            self.history.append({
                "role": "assistant",
                "content": response_text
            })
            
            return response_text
            
        except Exception as e:
            # Log error and return user-friendly message
            error_msg = f"I'm having trouble connecting to my AI brain. Error: {str(e)}"
            
            self.history.append({
                "role": "assistant",
                "content": error_msg
            })
            
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


def create_chat_engine(system_prompt: Optional[str] = None) -> Optional[GeminiChatEngine]:
    """
    Factory function to create a chat engine with error handling.
    
    Args:
        system_prompt: Custom system prompt (optional)
        
    Returns:
        GeminiChatEngine instance or None if API key is missing
    """
    try:
        return GeminiChatEngine(system_prompt=system_prompt)
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
