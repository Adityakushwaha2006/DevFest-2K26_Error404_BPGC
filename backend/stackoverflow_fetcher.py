"""
Stack Overflow / Stack Exchange Fetcher
Extracts developer profile data from Stack Exchange API.

Data available:
- User profile (reputation, badges, about_me)
- Top answers and questions
- Top tags (areas of expertise)
- Activity timeline
"""

import requests
from datetime import datetime
from typing import Optional, List, Dict, Any


class StackOverflowFetcher:
    """
    Fetches developer data from Stack Exchange API.
    Free to use with rate limits (300 requests/day without key, 10k/day with key).
    """
    
    BASE_URL = "https://api.stackexchange.com/2.3"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize fetcher.
        
        Args:
            api_key: Optional Stack Exchange API key for higher rate limits
        """
        self.api_key = api_key
        self.default_params = {
            "site": "stackoverflow",
            "filter": "default"
        }
        if api_key:
            self.default_params["key"] = api_key
    
    def search_user_by_name(self, name: str, limit: int = 5) -> List[Dict]:
        """
        Search for users by display name.
        
        Args:
            name: Display name to search for
            limit: Max results
            
        Returns:
            List of matching users with basic info
        """
        url = f"{self.BASE_URL}/users"
        params = {
            **self.default_params,
            "inname": name,
            "pagesize": min(limit, 100),
            "order": "desc",
            "sort": "reputation"
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "user_id": user.get("user_id"),
                        "display_name": user.get("display_name"),
                        "reputation": user.get("reputation"),
                        "profile_url": user.get("link"),
                        "profile_image": user.get("profile_image")
                    }
                    for user in data.get("items", [])
                ]
        except Exception as e:
            print(f"Error searching SO users: {e}")
        
        return []
    
    def fetch_user_profile(self, user_id: int) -> Optional[Dict]:
        """
        Fetch complete user profile by ID.
        
        Args:
            user_id: Stack Overflow user ID
            
        Returns:
            User profile dict or None
        """
        url = f"{self.BASE_URL}/users/{user_id}"
        params = {
            **self.default_params,
            "filter": "!BTeL*Mb3d_MI8Y_Gj2yBJq7y0qAP.J"  # Include more fields
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                if items:
                    user = items[0]
                    return {
                        "user_id": user.get("user_id"),
                        "display_name": user.get("display_name"),
                        "reputation": user.get("reputation", 0),
                        "badge_counts": user.get("badge_counts", {}),
                        "profile_url": user.get("link"),
                        "website_url": user.get("website_url"),
                        "location": user.get("location"),
                        "about_me": user.get("about_me", ""),
                        "creation_date": datetime.fromtimestamp(
                            user.get("creation_date", 0)
                        ).isoformat() if user.get("creation_date") else None,
                        "last_access_date": datetime.fromtimestamp(
                            user.get("last_access_date", 0)
                        ).isoformat() if user.get("last_access_date") else None,
                        "answer_count": user.get("answer_count", 0),
                        "question_count": user.get("question_count", 0),
                        "up_vote_count": user.get("up_vote_count", 0),
                        "down_vote_count": user.get("down_vote_count", 0)
                    }
        except Exception as e:
            print(f"Error fetching SO profile: {e}")
        
        return None
    
    def fetch_top_tags(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Fetch user's top tags (areas of expertise).
        
        Args:
            user_id: Stack Overflow user ID
            limit: Max tags to return
            
        Returns:
            List of tags with answer counts
        """
        url = f"{self.BASE_URL}/users/{user_id}/top-tags"
        params = {
            **self.default_params,
            "pagesize": min(limit, 30)
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "tag_name": tag.get("tag_name"),
                        "answer_count": tag.get("answer_count", 0),
                        "answer_score": tag.get("answer_score", 0),
                        "question_count": tag.get("question_count", 0),
                        "question_score": tag.get("question_score", 0)
                    }
                    for tag in data.get("items", [])
                ]
        except Exception as e:
            print(f"Error fetching SO tags: {e}")
        
        return []
    
    def fetch_recent_answers(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Fetch user's recent answers.
        
        Args:
            user_id: Stack Overflow user ID
            limit: Max answers to return
            
        Returns:
            List of recent answers
        """
        url = f"{self.BASE_URL}/users/{user_id}/answers"
        params = {
            **self.default_params,
            "pagesize": min(limit, 30),
            "order": "desc",
            "sort": "activity",
            "filter": "withbody"
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "answer_id": ans.get("answer_id"),
                        "question_id": ans.get("question_id"),
                        "score": ans.get("score", 0),
                        "is_accepted": ans.get("is_accepted", False),
                        "creation_date": datetime.fromtimestamp(
                            ans.get("creation_date", 0)
                        ).isoformat() if ans.get("creation_date") else None,
                        "body_preview": (ans.get("body", "")[:300] + "...") if ans.get("body") else None,
                        "link": ans.get("link")
                    }
                    for ans in data.get("items", [])
                ]
        except Exception as e:
            print(f"Error fetching SO answers: {e}")
        
        return []
    
    def fetch_full_profile(self, user_id: int) -> Dict[str, Any]:
        """
        Fetch complete Stack Overflow profile with all data.
        
        Args:
            user_id: Stack Overflow user ID
            
        Returns:
            Complete profile dict
        """
        print(f"  → Fetching Stack Overflow data for user ID: {user_id}")
        
        result = {
            "platform": "stackoverflow",
            "user_id": user_id,
            "fetched_at": datetime.now().isoformat(),
            "profile": None,
            "top_tags": [],
            "recent_answers": [],
            "fetch_status": "pending"
        }
        
        # Fetch profile
        profile = self.fetch_user_profile(user_id)
        if profile:
            result["profile"] = profile
            
            # Fetch top tags
            result["top_tags"] = self.fetch_top_tags(user_id)
            
            # Fetch recent answers
            result["recent_answers"] = self.fetch_recent_answers(user_id)
            
            result["fetch_status"] = "success"
            print(f"    ✓ Reputation: {profile.get('reputation', 0):,}")
            print(f"    ✓ Top tags: {[t['tag_name'] for t in result['top_tags'][:5]]}")
        else:
            result["fetch_status"] = "failed"
            print(f"    ✗ Failed to fetch profile")
        
        return result
    
    def search_and_fetch(self, name: str) -> Optional[Dict]:
        """
        Convenience method: search by name and fetch best match.
        
        Args:
            name: Display name to search for
            
        Returns:
            Profile for best matching user or None
        """
        users = self.search_user_by_name(name, limit=3)
        
        if not users:
            print(f"  ⚠️ No Stack Overflow users found for: {name}")
            return None
        
        # Return first (highest rep) match
        best_match = users[0]
        print(f"  → Found SO user: {best_match['display_name']} (rep: {best_match['reputation']:,})")
        
        return self.fetch_full_profile(best_match["user_id"])


# Test
if __name__ == "__main__":
    fetcher = StackOverflowFetcher()
    
    print("=" * 60)
    print("Stack Overflow Fetcher Test")
    print("=" * 60)
    
    # Search and fetch by name
    result = fetcher.search_and_fetch("Kent C. Dodds")
    
    if result and result["fetch_status"] == "success":
        print(f"\n📊 Profile Summary:")
        print(f"  Name: {result['profile']['display_name']}")
        print(f"  Reputation: {result['profile']['reputation']:,}")
        print(f"  Badges: {result['profile']['badge_counts']}")
        print(f"  Top Tags: {[t['tag_name'] for t in result['top_tags'][:5]]}")
