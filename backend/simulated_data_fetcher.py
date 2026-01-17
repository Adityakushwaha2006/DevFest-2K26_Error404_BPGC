"""
Simulated Data Fetcher
Loads pre-generated mock Twitter and LinkedIn data from simulated_data folder.

This fetcher:
- Loads JSON files from backend/simulated_data/
- Converts them to IdentityNode format
- Provides recency weighting for activities
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import identity classes
from identity_node import IdentityNode, Platform, ActivityEvent


class SimulatedDataFetcher:
    """
    Fetches simulated Twitter and LinkedIn data from JSON files.
    Used for demo purposes when live APIs are unavailable.
    """
    
    RECENCY_WEIGHTS = {
        "last_week": 1.0,
        "last_month": 0.8,
        "last_3_months": 0.5
    }
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize with path to simulated_data folder.
        
        Args:
            data_dir: Path to simulated_data folder. Defaults to backend/simulated_data/
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            # Default to simulated_data folder relative to this file
            self.data_dir = Path(__file__).parent / "simulated_data"
        
        # Cache of available profiles
        self._manifest = None
        self._load_manifest()
        
        # Date boundaries for recency
        self.now = datetime.now()
        self.one_week_ago = self.now - timedelta(days=7)
        self.one_month_ago = self.now - timedelta(days=30)
    
    def _load_manifest(self):
        """Load manifest.json if available"""
        manifest_path = self.data_dir / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, "r", encoding="utf-8") as f:
                self._manifest = json.load(f)
    
    def list_available_profiles(self) -> List[str]:
        """List all usernames that have simulated data"""
        if self._manifest:
            return list(self._manifest.get("profiles", {}).keys())
        
        # Fallback: scan directory for *_github.json files
        usernames = set()
        for file in self.data_dir.glob("*_github.json"):
            username = file.stem.replace("_github", "")
            usernames.add(username)
        
        return sorted(usernames)
    
    def has_profile(self, username: str) -> bool:
        """Check if simulated data exists for a username"""
        return username in self.list_available_profiles()
    
    def fetch_twitter(self, username: str) -> Optional[Dict]:
        """
        Fetch simulated Twitter data for a username.
        
        Returns dict with profile, tweets, and recency metadata.
        Returns None if no data exists.
        """
        file_path = self.data_dir / f"{username}_twitter.json"
        
        if not file_path.exists():
            print(f"  ⚠️ No simulated Twitter data for: {username}")
            return None
        
        print(f"  → Loading simulated Twitter data for: {username}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Add recency weighting to tweets
        tweets_with_recency = []
        for tweet in data.get("tweets", []):
            timestamp = tweet.get("timestamp")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    recency = self._get_recency_bucket(dt)
                    tweet["recency_bucket"] = recency
                    tweet["recency_weight"] = self.RECENCY_WEIGHTS[recency]
                except:
                    tweet["recency_bucket"] = "last_3_months"
                    tweet["recency_weight"] = 0.5
            tweets_with_recency.append(tweet)
        
        data["tweets"] = tweets_with_recency
        data["recency_metadata"] = {
            "weights": self.RECENCY_WEIGHTS,
            "activity_by_recency": self._count_by_recency(tweets_with_recency)
        }
        data["is_simulated"] = True
        
        return data
    
    def fetch_linkedin(self, username: str) -> Optional[Dict]:
        """
        Fetch simulated LinkedIn data for a username.
        
        Returns dict with profile, posts, and experience.
        Returns None if no data exists.
        """
        file_path = self.data_dir / f"{username}_linkedin.json"
        
        if not file_path.exists():
            print(f"  ⚠️ No simulated LinkedIn data for: {username}")
            return None
        
        print(f"  → Loading simulated LinkedIn data for: {username}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Add recency weighting to posts if present
        posts = data.get("posts", [])
        posts_with_recency = []
        for post in posts:
            timestamp = post.get("timestamp")
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    recency = self._get_recency_bucket(dt)
                    post["recency_bucket"] = recency
                    post["recency_weight"] = self.RECENCY_WEIGHTS[recency]
                except:
                    post["recency_bucket"] = "last_3_months"
                    post["recency_weight"] = 0.5
            posts_with_recency.append(post)
        
        data["posts"] = posts_with_recency
        data["recency_metadata"] = {
            "weights": self.RECENCY_WEIGHTS,
            "activity_by_recency": self._count_by_recency(posts_with_recency)
        }
        data["is_simulated"] = True
        
        return data
    
    def fetch_github(self, username: str) -> Optional[Dict]:
        """
        Fetch simulated GitHub data (if available).
        Generally prefer live GitHub data, but useful for offline testing.
        """
        file_path = self.data_dir / f"{username}_github.json"
        
        if not file_path.exists():
            return None
        
        print(f"  → Loading simulated GitHub data for: {username}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        data["is_simulated"] = True
        return data
    
    def to_twitter_node(self, data: Dict) -> IdentityNode:
        """Convert Twitter data to IdentityNode format"""
        username = data.get("identifier", data.get("profile", {}).get("username", "unknown"))
        
        node = IdentityNode(Platform.TWITTER, username)
        node.data = data.get("profile", {})
        node.fetch_status = "success"
        node.last_updated = datetime.now()
        node.confidence_score = data.get("confidence_score", 0.85)
        
        # Add cross-references
        cross_refs = data.get("cross_references", {})
        if isinstance(cross_refs, dict):
            if "github" in cross_refs:
                node.add_cross_reference(Platform.GITHUB, username, "cross_reference")
            if "linkedin" in cross_refs:
                node.add_cross_reference(Platform.LINKEDIN, username, "cross_reference")
        
        # Add tweet activities
        for tweet in data.get("tweets", [])[:30]:
            try:
                timestamp = datetime.fromisoformat(tweet["timestamp"].replace("Z", "+00:00"))
            except:
                timestamp = datetime.now()
            
            activity = ActivityEvent(
                platform=Platform.TWITTER,
                event_type="tweet",
                content=tweet.get("content", ""),
                timestamp=timestamp,
                url=tweet.get("url"),
                metadata={
                    "engagement": tweet.get("engagement", {}),
                    "recency_weight": tweet.get("recency_weight", 0.5)
                }
            )
            node.add_activity(activity)
        
        return node
    
    def to_linkedin_node(self, data: Dict) -> IdentityNode:
        """Convert LinkedIn data to IdentityNode format"""
        username = data.get("identifier", data.get("profile", {}).get("username", "unknown"))
        
        node = IdentityNode(Platform.LINKEDIN, username)
        node.data = data.get("profile", {})
        node.fetch_status = "success"
        node.last_updated = datetime.now()
        node.confidence_score = data.get("confidence_score", 0.8)
        
        # Add cross-references
        cross_refs = data.get("cross_references", {})
        if isinstance(cross_refs, dict):
            if "github" in cross_refs:
                node.add_cross_reference(Platform.GITHUB, username, "cross_reference")
            if "twitter" in cross_refs:
                node.add_cross_reference(Platform.TWITTER, username, "cross_reference")
        
        # Add post activities
        for post in data.get("posts", [])[:20]:
            try:
                timestamp = datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00"))
            except:
                timestamp = datetime.now()
            
            activity = ActivityEvent(
                platform=Platform.LINKEDIN,
                event_type="post",
                content=post.get("content", ""),
                timestamp=timestamp,
                url=post.get("url"),
                metadata={
                    "engagement": post.get("engagement", {}),
                    "recency_weight": post.get("recency_weight", 0.5)
                }
            )
            node.add_activity(activity)
        
        return node
    
    def _get_recency_bucket(self, dt: datetime) -> str:
        """Determine recency bucket for a timestamp"""
        dt_naive = dt.replace(tzinfo=None) if dt.tzinfo else dt
        
        if dt_naive >= self.one_week_ago:
            return "last_week"
        elif dt_naive >= self.one_month_ago:
            return "last_month"
        else:
            return "last_3_months"
    
    def _count_by_recency(self, activities: List[Dict]) -> Dict[str, int]:
        """Count activities by recency bucket"""
        counts = {"last_week": 0, "last_month": 0, "last_3_months": 0}
        
        for activity in activities:
            bucket = activity.get("recency_bucket", "last_3_months")
            if bucket in counts:
                counts[bucket] += 1
        
        return counts


# Quick test
if __name__ == "__main__":
    fetcher = SimulatedDataFetcher()
    
    print("=" * 60)
    print("Testing SimulatedDataFetcher")
    print("=" * 60)
    
    # List available profiles
    profiles = fetcher.list_available_profiles()
    print(f"\n📋 Available profiles: {len(profiles)}")
    for p in profiles[:10]:
        print(f"  • {p}")
    if len(profiles) > 10:
        print(f"  ... and {len(profiles) - 10} more")
    
    # Test fetching a profile
    test_user = "kentcdodds" if "kentcdodds" in profiles else (profiles[0] if profiles else None)
    
    if test_user:
        print(f"\n🔍 Testing with: {test_user}")
        
        twitter_data = fetcher.fetch_twitter(test_user)
        if twitter_data:
            print(f"\n  Twitter Data:")
            print(f"    • Name: {twitter_data.get('profile', {}).get('name')}")
            print(f"    • Tweets: {len(twitter_data.get('tweets', []))}")
            print(f"    • Recency: {twitter_data.get('recency_metadata', {}).get('activity_by_recency')}")
        
        linkedin_data = fetcher.fetch_linkedin(test_user)
        if linkedin_data:
            print(f"\n  LinkedIn Data:")
            print(f"    • Name: {linkedin_data.get('profile', {}).get('name')}")
            print(f"    • Posts: {len(linkedin_data.get('posts', []))}")
    else:
        print("\n⚠️ No profiles found in simulated_data folder")
