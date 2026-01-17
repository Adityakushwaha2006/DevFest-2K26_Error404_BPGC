"""
Gemini-Powered Mock Data Generators
Generate realistic LinkedIn and Twitter profiles based on GitHub data.

Features:
- Gemini API for text content (bios, tweets, posts)
- Algorithmic cross-references (must match exactly)
- Checkpoint system for pause/resume on rate limits
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Import our identity classes
from identity_node import IdentityNode, Platform, ActivityEvent, CrossReference

# Initialize Gemini
import google.generativeai as genai



class CheckpointManager:
    """
    Manages saving and loading of generation checkpoints.
    Allows pause/resume functionality when switching API keys.
    """
    
    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.current_session: Dict[str, Any] = {}
        self.session_file = self.checkpoint_dir / "current_session.json"
    
    def save_checkpoint(self, username: str, platform: str, data: Dict):
        """Save generated data for a user/platform combination"""
        checkpoint_file = self.checkpoint_dir / f"{username}_{platform}.json"
        
        checkpoint_data = {
            "username": username,
            "platform": platform,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
        
        print(f"💾 Checkpoint saved: {checkpoint_file.name}")
        
        # Update session tracking
        self._update_session(username, platform)
    
    def load_checkpoint(self, username: str, platform: str) -> Optional[Dict]:
        """Load existing checkpoint if available"""
        checkpoint_file = self.checkpoint_dir / f"{username}_{platform}.json"
        
        if checkpoint_file.exists():
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
            print(f"📂 Loaded checkpoint: {checkpoint_file.name}")
            return checkpoint.get("data")
        
        return None
    
    def has_checkpoint(self, username: str, platform: str) -> bool:
        """Check if a checkpoint exists"""
        checkpoint_file = self.checkpoint_dir / f"{username}_{platform}.json"
        return checkpoint_file.exists()
    
    def _update_session(self, username: str, platform: str):
        """Track completed generations in current session"""
        if username not in self.current_session:
            self.current_session[username] = {}
        
        self.current_session[username][platform] = {
            "completed": True,
            "timestamp": datetime.now().isoformat()
        }
        
        # Save session state
        with open(self.session_file, 'w', encoding='utf-8') as f:
            json.dump(self.current_session, f, indent=2)
    
    def get_pending_platforms(self, username: str, platforms: List[str]) -> List[str]:
        """Get list of platforms not yet generated for a user"""
        pending = []
        for platform in platforms:
            if not self.has_checkpoint(username, platform):
                pending.append(platform)
        return pending
    
    def clear_checkpoints(self, username: str = None):
        """Clear checkpoints for a user or all checkpoints"""
        if username:
            for f in self.checkpoint_dir.glob(f"{username}_*.json"):
                f.unlink()
            print(f"🗑️ Cleared checkpoints for: {username}")
        else:
            for f in self.checkpoint_dir.glob("*.json"):
                f.unlink()
            print("🗑️ Cleared all checkpoints")


class GeminiMockGenerator:
    """
    Base class for Gemini-powered mock data generation.
    Handles API configuration, checkpointing, and error handling.
    """
    
    # Delay between API calls in seconds (to avoid rate limits)
    API_CALL_DELAY = 4
    
    def __init__(self, api_key: Optional[str] = None, checkpoint_manager: Optional[CheckpointManager] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Set it in .env or pass directly.")
        
        genai.configure(api_key=self.api_key)
        # Using 2.5-flash as requested
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()
    
    def _generate_content(self, prompt: str) -> str:
        """
        Call Gemini API with retry logic and rate limit handling.
        """
        import time
        
        max_retries = 3
        base_delay = 5  # Start with 5s delay
        
        for attempt in range(max_retries + 1):
            try:
                # Add small delay before every call to spread them out
                time.sleep(2)
                
                response = self.model.generate_content(prompt)
                result = response.text
                
                # Success!
                return result
                
            except Exception as e:
                error_msg = str(e)
                error_lower = error_msg.lower()
                
                is_rate_limit = (
                    "429" in error_msg or
                    "resource_exhausted" in error_lower or
                    "quota" in error_lower or
                    "rate limit" in error_lower
                )
                
                if is_rate_limit:
                    if attempt < max_retries:
                        wait_time = base_delay * (2 ** attempt)  # 5s, 10s, 20s
                        print(f"\n⚠️ Rate limit hit. Retrying in {wait_time}s (Attempt {attempt+1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"\n❌ FAILED after {max_retries} retries due to Rate Limit.")
                        print("💡 Check your API quota. You might be hitting the daily limit.")
                        raise RateLimitError(error_msg)
                else:
                    # Non-rate-limit error, raise immediately
                    print(f"\n❌ Gemini API Error: {error_msg}")
                    raise


    
    def _parse_json_response(self, text: str) -> Dict:
        """Parse JSON from Gemini response (handles markdown wrapping)"""
        text = text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith('```'):
            lines = text.split('\n')
            # Find end of code block
            end_idx = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '```':
                    end_idx = i
                    break
            if end_idx > 0:
                text = '\n'.join(lines[1:end_idx])
            else:
                text = '\n'.join(lines[1:-1])
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse JSON: {text[:100]}...")
            raise ValueError(f"Invalid JSON response from Gemini: {e}")
    
    def _random_date_recent(self, days_back: int = 30) -> datetime:
        """Generate a random recent datetime"""
        days_ago = random.randint(0, days_back)
        hours_ago = random.randint(0, 23)
        return datetime.now() - timedelta(days=days_ago, hours=hours_ago)


class RateLimitError(Exception):
    """Raised when API rate limit is hit"""
    pass


class MockTwitterGenerator(GeminiMockGenerator):
    """
    Generate realistic Twitter/X profiles and tweets based on GitHub data.
    """
    
    def generate_from_github(self, github_node: IdentityNode, skip_if_checkpointed: bool = True) -> IdentityNode:
        """
        Generate a mock Twitter profile based on real GitHub data.
        
        Args:
            github_node: Real GitHub IdentityNode with profile and activity data
            skip_if_checkpointed: If True, skip generation if checkpoint exists
        
        Returns:
            Mock Twitter IdentityNode with realistic content
        """
        username = github_node.identifier
        
        # Check for existing checkpoint
        if skip_if_checkpointed and self.checkpoint_manager.has_checkpoint(username, "twitter"):
            print(f"⏭️ Skipping Twitter for {username} (checkpoint exists)")
            cached_data = self.checkpoint_manager.load_checkpoint(username, "twitter")
            return self._build_node_from_data(username, cached_data)
        
        print(f"🐦 Generating Twitter profile for: {username}")
        
        name = github_node.get_name() or username
        bio = github_node.get_bio() or ""
        location = github_node.get_location() or "Unknown"
        company = github_node.get_company() or ""
        
        # Extract tech interests from GitHub
        tech_interests = self._extract_tech_interests(github_node)
        
        # Generate profile via Gemini
        profile_data = self._generate_twitter_profile(name, bio, location, company, tech_interests)
        
        # CHECKPOINT: Save profile before generating tweets
        partial_data = {"profile": profile_data, "tweets": []}
        self.checkpoint_manager.save_checkpoint(username, "twitter_partial", partial_data)
        
        # Generate tweets via Gemini
        tweets = self._generate_tweets(github_node, profile_data)
        
        # Build full data
        full_data = {
            "profile": profile_data,
            "tweets": tweets
        }
        
        # CHECKPOINT: Save complete data
        self.checkpoint_manager.save_checkpoint(username, "twitter", full_data)
        
        return self._build_node_from_data(username, full_data)
    
    def _build_node_from_data(self, username: str, data: Dict) -> IdentityNode:
        """Build IdentityNode from saved/generated data"""
        node = IdentityNode(Platform.TWITTER, username)
        node.data = data.get("profile", {})
        
        for tweet in data.get("tweets", []):
            # Handle timestamp - could be string from JSON
            timestamp = tweet.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            elif timestamp is None:
                timestamp = self._random_date_recent()
            
            activity = ActivityEvent(
                platform=Platform.TWITTER,
                event_type='tweet',
                content=tweet['content'],
                timestamp=timestamp,
                url=f"https://twitter.com/{username}/status/{random.randint(1000000000, 9999999999)}",
                metadata={
                    'likes': tweet.get('likes', 0),
                    'retweets': tweet.get('retweets', 0),
                    'replies': tweet.get('replies', 0)
                }
            )
            node.add_activity(activity)
        
        # ALGORITHMIC: Cross-references (must match exactly)
        node.add_cross_reference(Platform.GITHUB, username, 'bio')
        
        node.fetch_status = "success"
        node.last_updated = datetime.now()
        node.confidence_score = 0.85
        
        return node
    
    def _extract_tech_interests(self, github_node: IdentityNode) -> List[str]:
        """Extract technology interests from GitHub profile"""
        interests = []
        
        bio = github_node.get_bio() or ""
        tech_keywords = ['python', 'javascript', 'rust', 'go', 'typescript', 'react', 
                         'node', 'blockchain', 'ai', 'ml', 'web3', 'devops', 'cloud',
                         'kubernetes', 'docker', 'aws', 'deep learning', 'nlp']
        
        for keyword in tech_keywords:
            if keyword.lower() in bio.lower():
                interests.append(keyword)
        
        for activity in github_node.activities[:10]:
            for keyword in tech_keywords:
                if keyword.lower() in activity.content.lower():
                    if keyword not in interests:
                        interests.append(keyword)
        
        return interests[:5]
    
    def _generate_twitter_profile(
        self, 
        name: str, 
        github_bio: str, 
        location: str, 
        company: str,
        tech_interests: List[str]
    ) -> Dict[str, Any]:
        """Generate Twitter profile data using Gemini"""
        
        prompt = f"""
        Generate a realistic Twitter profile for a software developer with these details:
        - Name: {name}
        - Current bio on GitHub: {github_bio}
        - Location: {location}
        - Company: {company}
        - Technical interests: {', '.join(tech_interests) if tech_interests else 'software development'}
        
        Return ONLY a valid JSON object (no markdown, no explanation) with these exact fields:
        {{
            "name": "{name}",
            "username": "twitter_handle_here",
            "bio": "Twitter bio (160 chars max, can include emojis, mentions of tech interests)",
            "location": "{location}",
            "website": "personal site or GitHub URL",
            "followers": realistic_number_for_developer,
            "following": realistic_number,
            "tweets_count": realistic_total_tweets,
            "joined_date": "Month Year format",
            "is_verified": false
        }}
        
        Make it feel authentic - use tech Twitter culture (hot takes, learning in public, etc).
        Follower count should be realistic (100-50000 range for most developers).
        """
        
        response = self._generate_content(prompt)
        profile = self._parse_json_response(response)
        
        # Always use the actual GitHub username for cross-validation
        profile['github_username'] = name
        
        return profile
    
    def _generate_tweets(self, github_node: IdentityNode, profile: Dict) -> List[Dict]:
        """Generate realistic tweets based on GitHub activity"""
        
        recent_commits = [
            act.content for act in github_node.activities[:5] 
            if act.event_type == 'commit'
        ]
        
        name = github_node.get_name() or github_node.identifier
        bio = github_node.get_bio() or "Software developer"
        
        prompt = f"""
        Generate 15-20 realistic tweets for a developer with this profile:
        - Name: {name}
        - Bio: {bio}
        - Recent GitHub commits: {json.dumps(recent_commits[:3])}
        
        Include a variety of tweet types:
        - Tech opinions/hot takes
        - Learning in public (sharing what they're building)
        - Retweet-style comments on tech news
        - Developer humor
        - Career/work updates
        - Open source contributions
        
        Return ONLY a valid JSON array (no markdown) with this structure:
        [
            {{
                "content": "Tweet text (280 chars max)",
                "likes": number,
                "retweets": number,
                "replies": number,
                "type": "original|reply|thread"
            }}
        ]
        
        Make them feel authentic to tech Twitter culture.
        Vary the engagement numbers realistically (most tweets get 0-10 likes).
        """
        
        response = self._generate_content(prompt)
        tweets_data = self._parse_json_response(response)
        
        if not isinstance(tweets_data, list):
            raise ValueError("Expected JSON array of tweets")
        
        # Add timestamps
        tweets = []
        for tweet in tweets_data:
            tweet['timestamp'] = self._random_date_recent(days_back=30).isoformat()
            tweets.append(tweet)
        
        # Sort by timestamp (most recent first)
        tweets.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return tweets


class MockLinkedInGenerator(GeminiMockGenerator):
    """
    Generate realistic LinkedIn profiles based on GitHub data.
    """
    
    def generate_from_github(self, github_node: IdentityNode, skip_if_checkpointed: bool = True) -> IdentityNode:
        """
        Generate a mock LinkedIn profile based on real GitHub data.
        """
        username = github_node.identifier
        
        # Check for existing checkpoint
        if skip_if_checkpointed and self.checkpoint_manager.has_checkpoint(username, "linkedin"):
            print(f"⏭️ Skipping LinkedIn for {username} (checkpoint exists)")
            cached_data = self.checkpoint_manager.load_checkpoint(username, "linkedin")
            return self._build_node_from_data(username, cached_data)
        
        print(f"💼 Generating LinkedIn profile for: {username}")
        
        name = github_node.get_name() or username
        bio = github_node.get_bio() or ""
        location = github_node.get_location() or "Unknown"
        company = github_node.get_company() or "Freelance"
        
        tech_interests = self._extract_tech_interests(github_node)
        
        # Generate profile
        profile_data = self._generate_linkedin_profile(name, bio, location, company, tech_interests)
        
        # CHECKPOINT: Save after profile
        partial = {"profile": profile_data}
        self.checkpoint_manager.save_checkpoint(username, "linkedin_partial", partial)
        
        # Generate experience
        experience = self._generate_experience(name, company, tech_interests)
        profile_data['experience'] = experience
        
        # Generate education
        education = self._generate_education()
        profile_data['education'] = education
        
        # Generate skills
        skills = self._generate_skills(tech_interests)
        profile_data['skills'] = skills
        
        # Generate posts
        posts = self._generate_linkedin_posts(github_node, profile_data)
        
        full_data = {
            "profile": profile_data,
            "posts": posts
        }
        
        # CHECKPOINT: Save complete data
        self.checkpoint_manager.save_checkpoint(username, "linkedin", full_data)
        
        return self._build_node_from_data(username, full_data)
    
    def _build_node_from_data(self, username: str, data: Dict) -> IdentityNode:
        """Build IdentityNode from saved/generated data"""
        node = IdentityNode(Platform.LINKEDIN, username)
        node.data = data.get("profile", {})
        
        for post in data.get("posts", []):
            timestamp = post.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            elif timestamp is None:
                timestamp = self._random_date_recent(days_back=60)
            
            activity = ActivityEvent(
                platform=Platform.LINKEDIN,
                event_type='post',
                content=post['content'],
                timestamp=timestamp,
                url=f"https://linkedin.com/posts/{username}-{random.randint(1000, 9999)}",
                metadata={
                    'likes': post.get('likes', 0),
                    'comments': post.get('comments', 0)
                }
            )
            node.add_activity(activity)
        
        node.add_cross_reference(Platform.GITHUB, username, 'contact_info')
        
        node.fetch_status = "success"
        node.last_updated = datetime.now()
        node.confidence_score = 0.75
        
        return node
    
    def _extract_tech_interests(self, github_node: IdentityNode) -> List[str]:
        """Extract tech interests from GitHub"""
        interests = []
        bio = github_node.get_bio() or ""
        tech_keywords = ['python', 'javascript', 'rust', 'go', 'typescript', 'react', 
                         'node', 'blockchain', 'ai', 'ml', 'web3', 'devops', 'cloud',
                         'kubernetes', 'docker', 'aws', 'deep learning', 'nlp']
        
        for keyword in tech_keywords:
            if keyword.lower() in bio.lower():
                interests.append(keyword)
        
        return interests[:5]
    
    def _generate_linkedin_profile(
        self, 
        name: str, 
        github_bio: str, 
        location: str, 
        company: str,
        tech_interests: List[str]
    ) -> Dict[str, Any]:
        """Generate LinkedIn profile data using Gemini"""
        
        prompt = f"""
        Generate a realistic LinkedIn profile for a software professional:
        - Name: {name}
        - Current GitHub bio: {github_bio}
        - Location: {location}
        - Current company: {company}
        - Technical skills: {', '.join(tech_interests) if tech_interests else 'software development'}
        
        Return ONLY a valid JSON object (no markdown) with these fields:
        {{
            "name": "{name}",
            "headline": "Professional headline (e.g., 'Senior Software Engineer at Company | Tech Stack')",
            "location": "{location}",
            "about": "Professional summary paragraph (2-3 sentences, first person)",
            "current_company": "{company or 'Self-Employed'}",
            "current_position": "Job title",
            "connections": realistic_number_100_500_range,
            "followers": realistic_number,
            "profile_views_last_90_days": number,
            "open_to_work": boolean,
            "open_to_hiring": boolean,
            "creator_mode": boolean
        }}
        
        Make it professional but authentic to tech LinkedIn.
        """
        
        response = self._generate_content(prompt)
        return self._parse_json_response(response)
    
    def _generate_experience(self, name: str, current_company: str, tech: List[str]) -> List[Dict]:
        """Generate work experience history"""
        
        prompt = f"""
        Generate a realistic work experience history for a software developer:
        - Current company: {current_company}
        - Tech stack: {', '.join(tech) if tech else 'various technologies'}
        
        Return ONLY a valid JSON array of 2-4 positions (no markdown):
        [
            {{
                "title": "Job Title",
                "company": "Company Name",
                "location": "City, Country",
                "start_date": "Month Year",
                "end_date": "Month Year or Present",
                "description": "2-3 bullet points describing responsibilities and achievements",
                "is_current": boolean
            }}
        ]
        
        Make it realistic for a mid-to-senior developer career progression.
        """
        
        response = self._generate_content(prompt)
        experience = self._parse_json_response(response)
        
        if not isinstance(experience, list):
            raise ValueError("Expected JSON array of experience")
        
        return experience
    
    def _generate_education(self) -> List[Dict]:
        """Generate education history"""
        
        prompt = """
        Generate a realistic education background for a software developer.
        
        Return ONLY a valid JSON array of 1-2 entries (no markdown):
        [
            {
                "institution": "University Name",
                "degree": "Degree Type",
                "field_of_study": "Computer Science, Engineering, etc.",
                "start_year": number,
                "end_year": number,
                "activities": "Optional clubs, honors"
            }
        ]
        """
        
        response = self._generate_content(prompt)
        education = self._parse_json_response(response)
        
        if not isinstance(education, list):
            raise ValueError("Expected JSON array of education")
        
        return education
    
    def _generate_skills(self, tech_interests: List[str]) -> List[Dict]:
        """Generate skills with endorsement counts"""
        skills = []
        
        for tech in tech_interests:
            skills.append({
                "name": tech.title(),
                "endorsements": random.randint(10, 99)
            })
        
        generic_skills = ["Problem Solving", "Team Leadership", "Agile", "Git", "API Design"]
        for skill in generic_skills[:3]:
            skills.append({
                "name": skill,
                "endorsements": random.randint(5, 50)
            })
        
        return skills
    
    def _generate_linkedin_posts(self, github_node: IdentityNode, profile: Dict) -> List[Dict]:
        """Generate LinkedIn posts based on activity"""
        
        headline = profile.get('headline', 'Software Developer')
        
        prompt = f"""
        Generate 10-15 realistic LinkedIn posts for a {headline}.
        
        Include a variety of post types:
        - Professional achievements/updates
        - Industry insights/opinions
        - Sharing articles with commentary
        - Career advice
        - Company announcements
        - Celebrating team wins
        
        Return ONLY a valid JSON array (no markdown):
        [
            {{
                "content": "Post text (can be 1-3 paragraphs)",
                "likes": number,
                "comments": number,
                "type": "text|article_share|achievement"
            }}
        ]
        
        Make them authentic to LinkedIn culture (professional but not too corporate).
        Most posts get 10-100 likes, occasional viral posts get more.
        """
        
        response = self._generate_content(prompt)
        posts_data = self._parse_json_response(response)
        
        if not isinstance(posts_data, list):
            raise ValueError("Expected JSON array of posts")
        
        # Add timestamps
        posts = []
        for post in posts_data:
            post['timestamp'] = self._random_date_recent(days_back=60).isoformat()
            posts.append(post)
        
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return posts


def generate_mock_profiles_batch(
    github_usernames: List[str],
    platforms: List[str] = ["twitter", "linkedin"],
    api_key: Optional[str] = None
) -> Dict[str, Dict]:
    """
    Generate mock profiles for multiple users with checkpoint support.
    
    Args:
        github_usernames: List of GitHub usernames to process
        platforms: Platforms to generate mocks for
        api_key: Optional API key override
    
    Returns:
        Dict mapping username -> platform -> generated data
    """
    from platform_fetchers import get_fetcher
    
    checkpoint_mgr = CheckpointManager()
    results = {}
    
    twitter_gen = MockTwitterGenerator(api_key=api_key, checkpoint_manager=checkpoint_mgr)
    linkedin_gen = MockLinkedInGenerator(api_key=api_key, checkpoint_manager=checkpoint_mgr)
    
    github_fetcher = get_fetcher(Platform.GITHUB, github_token=os.getenv('GITHUB_TOKEN'))
    
    for username in github_usernames:
        print(f"\n{'='*60}")
        print(f"Processing: {username}")
        print('='*60)
        
        results[username] = {}
        
        try:
            # Fetch GitHub data
            github_node = github_fetcher.fetch(username)
            
            if github_node.fetch_status != "success":
                print(f"❌ Failed to fetch GitHub: {github_node.error_message}")
                continue
            
            results[username]["github"] = github_node
            
            # Generate mocks for each platform
            if "twitter" in platforms:
                try:
                    twitter_node = twitter_gen.generate_from_github(github_node)
                    results[username]["twitter"] = twitter_node
                except RateLimitError:
                    print(f"⏸️ Paused at Twitter for {username}. Resume with new key.")
                    raise
            
            if "linkedin" in platforms:
                try:
                    linkedin_node = linkedin_gen.generate_from_github(github_node)
                    results[username]["linkedin"] = linkedin_node
                except RateLimitError:
                    print(f"⏸️ Paused at LinkedIn for {username}. Resume with new key.")
                    raise
            
            print(f"✅ Completed: {username}")
            
        except RateLimitError:
            print("\n" + "="*60)
            print("⚠️ RATE LIMIT - Generation paused")
            print("="*60)
            print("To resume:")
            print("1. Get a new API key from https://aistudio.google.com/apikey")
            print("2. Update GEMINI_API_KEY in .env")
            print("3. Re-run this script - it will resume from checkpoint")
            break
        except Exception as e:
            print(f"❌ Error processing {username}: {e}")
            continue
    
    return results
