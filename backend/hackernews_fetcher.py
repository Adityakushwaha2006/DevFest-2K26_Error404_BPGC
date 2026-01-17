"""
Hacker News Fetcher
Extracts user activity from Hacker News API.

Data available:
- User profile (karma, about, created)
- Submitted stories and comments
- Activity patterns
"""

import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed


class HackerNewsFetcher:
    """
    Fetches user data from the official Hacker News Firebase API.
    Completely free with no authentication required.
    """
    
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def fetch_user(self, username: str) -> Optional[Dict]:
        """
        Fetch user profile.
        
        Args:
            username: HN username (case-sensitive)
            
        Returns:
            User profile dict or None
        """
        url = f"{self.BASE_URL}/user/{username}.json"
        
        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return {
                        "username": data.get("id"),
                        "karma": data.get("karma", 0),
                        "about": data.get("about", ""),
                        "created": datetime.fromtimestamp(
                            data.get("created", 0)
                        ).isoformat() if data.get("created") else None,
                        "submitted_count": len(data.get("submitted", [])),
                        "submitted_ids": data.get("submitted", [])[:100]  # Limit for performance
                    }
        except Exception as e:
            print(f"Error fetching HN user: {e}")
        
        return None
    
    def fetch_item(self, item_id: int) -> Optional[Dict]:
        """
        Fetch a single item (story, comment, etc.)
        
        Args:
            item_id: HN item ID
            
        Returns:
            Item dict or None
        """
        url = f"{self.BASE_URL}/item/{item_id}.json"
        
        try:
            response = requests.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        
        return None
    
    def fetch_user_submissions(
        self, 
        username: str, 
        limit: int = 20,
        include_comments: bool = True
    ) -> List[Dict]:
        """
        Fetch user's recent submissions (stories and optionally comments).
        
        Args:
            username: HN username
            limit: Max items to fetch
            include_comments: Whether to include comments
            
        Returns:
            List of submission dicts
        """
        user = self.fetch_user(username)
        if not user:
            return []
        
        submissions = []
        item_ids = user.get("submitted_ids", [])[:limit * 2]  # Fetch extra in case we filter
        
        # Fetch items in parallel for speed
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.fetch_item, item_id): item_id 
                      for item_id in item_ids}
            
            for future in as_completed(futures):
                try:
                    item = future.result()
                    if item:
                        item_type = item.get("type")
                        
                        # Filter based on settings
                        if not include_comments and item_type == "comment":
                            continue
                        
                        submission = {
                            "id": item.get("id"),
                            "type": item_type,
                            "time": datetime.fromtimestamp(
                                item.get("time", 0)
                            ).isoformat() if item.get("time") else None,
                            "score": item.get("score", 0),
                            "url": item.get("url"),
                            "title": item.get("title"),
                            "text": (item.get("text", "")[:200] + "...") if item.get("text") else None,
                            "descendants": item.get("descendants", 0)  # Comment count for stories
                        }
                        submissions.append(submission)
                except:
                    continue
        
        # Sort by time (most recent first)
        submissions.sort(key=lambda x: x.get("time") or "", reverse=True)
        
        return submissions[:limit]
    
    def fetch_full_profile(self, username: str, submission_limit: int = 15) -> Dict[str, Any]:
        """
        Fetch complete HN profile with submissions.
        
        Args:
            username: HN username
            submission_limit: Max submissions to include
            
        Returns:
            Complete profile dict
        """
        print(f"  → Fetching Hacker News data for: {username}")
        
        result = {
            "platform": "hackernews",
            "username": username,
            "fetched_at": datetime.now().isoformat(),
            "profile": None,
            "submissions": [],
            "activity_summary": {},
            "fetch_status": "pending"
        }
        
        # Fetch user profile
        user = self.fetch_user(username)
        
        if not user:
            result["fetch_status"] = "failed"
            print(f"    ✗ User not found")
            return result
        
        result["profile"] = {
            "username": user["username"],
            "karma": user["karma"],
            "about": user["about"],
            "created": user["created"],
            "total_submissions": user["submitted_count"]
        }
        
        print(f"    ✓ Karma: {user['karma']:,}")
        
        # Fetch recent submissions
        result["submissions"] = self.fetch_user_submissions(
            username, 
            limit=submission_limit,
            include_comments=True
        )
        
        # Calculate activity summary
        stories = [s for s in result["submissions"] if s["type"] == "story"]
        comments = [s for s in result["submissions"] if s["type"] == "comment"]
        
        result["activity_summary"] = {
            "recent_stories": len(stories),
            "recent_comments": len(comments),
            "total_story_score": sum(s.get("score", 0) for s in stories),
            "avg_story_score": (
                sum(s.get("score", 0) for s in stories) / len(stories) 
                if stories else 0
            )
        }
        
        print(f"    ✓ Submissions: {len(stories)} stories, {len(comments)} comments")
        
        result["fetch_status"] = "success"
        return result


# Test
if __name__ == "__main__":
    print("=" * 60)
    print("Hacker News Fetcher Test")
    print("=" * 60)
    
    fetcher = HackerNewsFetcher()
    
    # Test with a known user
    test_users = ["pg", "dang"]  # Paul Graham, HN moderator
    
    for username in test_users:
        print(f"\nFetching: {username}")
        result = fetcher.fetch_full_profile(username, submission_limit=5)
        
        if result["fetch_status"] == "success":
            print(f"  Profile:")
            print(f"    Karma: {result['profile']['karma']:,}")
            print(f"    Member since: {result['profile']['created']}")
            print(f"    Total submissions: {result['profile']['total_submissions']}")
            print(f"  Recent Activity:")
            print(f"    Stories: {result['activity_summary']['recent_stories']}")
            print(f"    Comments: {result['activity_summary']['recent_comments']}")
