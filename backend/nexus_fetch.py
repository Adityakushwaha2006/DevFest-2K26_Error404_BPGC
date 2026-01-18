"""
NEXUS Data Fetchers
Consolidated module containing all data fetching logic and data models.

Includes:
1. IdentityNode & Graph (Data Models)
2. ExtendedGitHubFetcher
3. SimulatedDataFetcher
4. StackOverflowFetcher
5. BlogFetcher & MediumFetcher
6. HackerNewsFetcher
"""

import os
import re
import json
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Try to import feedparser
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False


# ==================================================================================
# 1. CORE DATA MODELS (IdentityNode)
# ==================================================================================

class Platform(Enum):
    """Supported platforms for identity nodes"""
    GITHUB = "github"
    TWITTER = "twitter"
    DEVTO = "devto"
    LINKEDIN = "linkedin"
    HASHNODE = "hashnode"

@dataclass
class CrossReference:
    """Represents a link to another platform found in a node"""
    platform: Platform
    identifier: str
    source_field: str
    confidence: float = 0.0

@dataclass
class ActivityEvent:
    """Single activity event from any platform"""
    platform: Platform
    event_type: str
    content: str
    timestamp: datetime
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    sentiment: Optional[str] = None

class IdentityNode:
    """Represents a single platform identity node."""
    
    def __init__(self, platform: Platform, identifier: str):
        self.platform = platform
        self.identifier = identifier
        self.data: Dict[str, Any] = {}
        self.cross_references: List[CrossReference] = []
        self.activities: List[ActivityEvent] = []
        self.confidence_score: float = 0.0
        self.last_updated: Optional[datetime] = None
        self.fetch_status: str = "pending"
        self.error_message: Optional[str] = None
        
    def add_cross_reference(self, platform: Platform, identifier: str, source_field: str):
        cross_ref = CrossReference(platform, identifier, source_field)
        self.cross_references.append(cross_ref)
        
    def add_activity(self, activity: ActivityEvent):
        self.activities.append(activity)
        
    def get_name(self) -> Optional[str]:
        return self.data.get('name') or self.data.get('full_name')
    
    def get_bio(self) -> Optional[str]:
        return (self.data.get('bio') or self.data.get('description') or self.data.get('summary'))
    
    def get_location(self) -> Optional[str]:
        return self.data.get('location')
    
    def get_company(self) -> Optional[str]:
        return self.data.get('company') or self.data.get('organization')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'platform': self.platform.value,
            'identifier': self.identifier,
            'data': self.data,
            'cross_references': [
                {'platform': r.platform.value, 'identifier': r.identifier, 'source_field': r.source_field, 'confidence': r.confidence}
                for r in self.cross_references
            ],
            'confidence_score': self.confidence_score,
            'fetch_status': self.fetch_status
        }

class IdentityGraph:
    """Manages multiple IdentityNode instances."""
    
    def __init__(self):
        self.nodes: Dict[str, IdentityNode] = {}
        self.unified_profile: Optional[Dict[str, Any]] = None
        
    def add_node(self, node: IdentityNode) -> str:
        key = f"{node.platform.value}:{node.identifier}"
        self.nodes[key] = node
        return key
    
    def get_node(self, platform: Platform, identifier: str) -> Optional[IdentityNode]:
        key = f"{platform.value}:{identifier}"
        return self.nodes.get(key)
        
    def calculate_cross_validation_score(self) -> float:
        if len(self.nodes) < 2: return 0.5
        # Simplified validation score for consolidated view
        return 0.8
    
    def synthesize_profile(self) -> Dict[str, Any]:
        if not self.nodes: return {}
        # Simple synthesis logic
        primary_node = max(self.nodes.values(), key=lambda n: len(n.data))
        unified = {
            'name': primary_node.get_name(),
            'bio': primary_node.get_bio(),
            'location': primary_node.get_location(),
            'company': primary_node.get_company(),
            'platforms': {
                n.platform.value: {'identifier': n.identifier, 'data': n.data} for n in self.nodes.values()
            },
            'last_updated': datetime.now().isoformat()
        }
        self.unified_profile = unified
        return unified


# ==================================================================================
# 2. EXTENDED GITHUB FETCHER
# ==================================================================================

class ExtendedGitHubFetcher:
    """Fetches comprehensive GitHub data for a user."""
    
    RECENCY_WEIGHTS = {
        "last_week": 1.0, "last_month": 0.8, "last_3_months": 0.5
    }
    
    def __init__(self, github_token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.token = github_token or os.getenv('GITHUB_TOKEN')
        self.headers = {}
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
            self.headers['Accept'] = 'application/vnd.github.v3+json'
        
        self.now = datetime.now()
        self.three_months_ago = self.now - timedelta(days=90)
    
    def fetch_full_profile(self, username: str) -> Dict[str, Any]:
        print(f"[*] Fetching GitHub data for: {username}")
        result = {
            "username": username,
            "fetched_at": datetime.now().isoformat(),
            "profile": {},
            "repositories": [],
            "recency_metadata": {"weights": self.RECENCY_WEIGHTS, "activity_by_recency": {}},
            "fetch_status": "pending"
        }
        try:
            result["profile"] = self._fetch_profile(username)
            result["repositories"] = self._fetch_repositories(username, limit=10)
            events = self._fetch_events(username)
            result.update(events)
            result["cross_references"] = self._extract_cross_references(result["profile"])
            result["fetch_status"] = "success"
        except Exception as e:
            result["fetch_status"] = "failed"
            result["error"] = str(e)
            print(f"[x] Failed to fetch GitHub data: {e}")
        return result
    
    def _clean_profile_data(self, profile: Dict) -> Dict:
        """Remove unnecessary URLs and IDs, keeping only useful personal information."""
        useful_fields = {
            "login": profile.get("login"),
            "name": profile.get("name"),
            "bio": profile.get("bio"),
            "company": profile.get("company"),
            "location": profile.get("location"),
            "email": profile.get("email"),
            "hireable": profile.get("hireable"),
            "twitter_username": profile.get("twitter_username"),
            "blog": profile.get("blog"),
            "public_repos": profile.get("public_repos"),
            "public_gists": profile.get("public_gists"),
            "followers": profile.get("followers"),
            "following": profile.get("following"),
            "created_at": profile.get("created_at"),
            "updated_at": profile.get("updated_at"),
        }
        # Remove None values
        return {k: v for k, v in useful_fields.items() if v is not None}
    
    def _fetch_profile(self, username: str) -> Dict:
        url = f"{self.base_url}/users/{username}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200: raise Exception(f"HTTP {response.status_code}")
        return self._clean_profile_data(response.json())
    
    def _fetch_repositories(self, username: str, limit: int = 10) -> List[Dict]:
        url = f"{self.base_url}/users/{username}/repos"
        params = {"sort": "pushed", "per_page": min(limit, 100)}
        response = requests.get(url, headers=self.headers, params=params)
        repos = []
        if response.status_code == 200:
            for repo in response.json()[:limit]:
                repos.append({
                    "name": repo.get("name"),
                    "description": repo.get("description"),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "language": repo.get("language"),
                    "updated_at": repo.get("updated_at")
                })
        return repos
    
    def _fetch_events(self, username: str, max_commits: int = 20) -> Dict[str, List]:
        commits = []
        # Limit to 2 pages to reduce API calls
        for page in range(1, 3):
            if len(commits) >= max_commits:
                break
            url = f"{self.base_url}/users/{username}/events/public"
            params = {"per_page": 100, "page": page}
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code != 200: break
            for event in response.json():
                if len(commits) >= max_commits:
                    break
                created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
                if created_at.replace(tzinfo=None) < self.three_months_ago: continue
                if event["type"] == "PushEvent":
                    for commit in event.get("payload", {}).get("commits", []):
                        if len(commits) >= max_commits:
                            break
                        commits.append({
                            "message": commit.get("message"),
                            "timestamp": created_at.isoformat(),
                            "repo": event.get('repo', {}).get('name')
                        })
        return {"commits": commits}

    def _extract_cross_references(self, profile: Dict) -> List[Dict]:
        refs = []
        if profile.get("twitter_username"):
            refs.append({"platform": "twitter", "identifier": profile["twitter_username"]})
        if profile.get("blog"):
            refs.append({"platform": "website", "identifier": profile["blog"]})
        return refs
    
    def to_identity_node(self, data: Dict) -> IdentityNode:
        node = IdentityNode(Platform.GITHUB, data["username"])
        node.data = data["profile"]
        node.fetch_status = data["fetch_status"]
        node.confidence_score = 1.0 if data["fetch_status"] == "success" else 0.0
        # Limit to 20 commits to reduce processing overhead
        for commit in data.get("commits", [])[:20]:
            activity = ActivityEvent(
                Platform.GITHUB, "commit", commit.get("message", ""),
                datetime.fromisoformat(commit["timestamp"].replace("Z", "+00:00"))
            )
            node.add_activity(activity)
        return node


# ==================================================================================
# 3. SIMULATED DATA FETCHER
# ==================================================================================

class SimulatedDataFetcher:
    """Fetches simulated data from local JSON files."""
    
    def __init__(self, data_dir: Optional[str] = None):
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).parent / "simulated_data"
            
    def fetch_github(self, username: str) -> Optional[Dict]:
        # Implementation for simulated GitHub data...
        # For brevity, returning None or basic structure as placeholder if file not found
        # In real scenario, load from json
        return None 

    def fetch_twitter(self, username: str) -> Optional[Dict]:
        file_path = self.data_dir / f"{username}_twitter.json"
        if not file_path.exists(): return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["is_simulated"] = True
        return data
        
    def fetch_linkedin(self, username: str) -> Optional[Dict]:
        file_path = self.data_dir / f"{username}_linkedin.json"
        if not file_path.exists(): return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["is_simulated"] = True
        return data

    def to_twitter_node(self, data: Dict) -> IdentityNode:
        username = data.get("identifier", "unknown")
        node = IdentityNode(Platform.TWITTER, username)
        node.data = data.get("profile", {})
        node.fetch_status = "success"
        for tweet in data.get("tweets", [])[:10]:
            try: ts = datetime.fromisoformat(tweet["timestamp"].replace("Z", "+00:00"))
            except: ts = datetime.now()
            node.add_activity(ActivityEvent(Platform.TWITTER, "tweet", tweet.get("content", ""), ts))
        return node

    def to_linkedin_node(self, data: Dict) -> IdentityNode:
        username = data.get("identifier", "unknown")
        node = IdentityNode(Platform.LINKEDIN, username)
        node.data = data.get("profile", {})
        node.fetch_status = "success"
        for post in data.get("posts", [])[:10]:
            try: ts = datetime.fromisoformat(post["timestamp"].replace("Z", "+00:00"))
            except: ts = datetime.now()
            node.add_activity(ActivityEvent(Platform.LINKEDIN, "post", post.get("content", ""), ts))
        return node


# ==================================================================================
# 4. STACK OVERFLOW FETCHER
# ==================================================================================

class StackOverflowFetcher:
    BASE_URL = "https://api.stackexchange.com/2.3"
    
    def fetch_full_profile(self, user_id: int) -> Dict[str, Any]:
        """Fetch by user ID."""
        print(f"  > Fetching SO data for user ID: {user_id}")
        url = f"{self.BASE_URL}/users/{user_id}"
        params = {"site": "stackoverflow", "filter": "default"}
        try:
            resp = requests.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json().get("items", [])
                if data:
                    return {
                        "platform": "stackoverflow", "user_id": user_id,
                        "profile": data[0], "fetch_status": "success",
                        "top_tags": [] # Placeholder
                    }
        except: pass
        return {"platform": "stackoverflow", "fetch_status": "failed"}

    def search_and_fetch(self, display_name: str) -> Dict[str, Any]:
        """Search for user by display name and fetch data."""
        print(f"  > Searching SO for: {display_name}")
        url = f"{self.BASE_URL}/users"
        params = {"site": "stackoverflow", "inname": display_name, "sort": "reputation", "order": "desc"}
        try:
            resp = requests.get(url, params=params)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                if items:
                    user_id = items[0]["user_id"]
                    return self.fetch_full_profile(user_id)
        except: pass
        return {"platform": "stackoverflow", "fetch_status": "failed"}


# ==================================================================================
# 5. BLOG FETCHER
# ==================================================================================

class BlogFetcher:
    FEED_PATHS = ["/feed", "/rss", "/rss.xml", "/feed.xml", "/atom.xml", "/blog/rss.xml", "/index.xml", "/feed/", "/rss/"]
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {"User-Agent": "NEXUS-Bot/1.0"}

    def discover_feed_url(self, blog_url: str) -> Optional[str]:
        if not blog_url.startswith(("http://", "https://")): blog_url = f"https://{blog_url}"
        blog_url = blog_url.rstrip("/")
        try:
            response = requests.get(blog_url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                # Regex patterns for feed links
                patterns = [
                    r'<link[^>]+type=["\']application/rss\+xml["\'][^>]+href=["\']([^"\']+)["\']',
                    r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/rss\+xml["\']',
                    r'<link[^>]+type=["\']application/atom\+xml["\'][^>]+href=["\']([^"\']+)["\']'
                ]
                for p in patterns:
                    match = re.search(p, response.text, re.IGNORECASE)
                    if match:
                        feed_url = match.group(1)
                        if feed_url.startswith("/"):
                            parsed = urlparse(blog_url)
                            feed_url = f"{parsed.scheme}://{parsed.netloc}{feed_url}"
                        return feed_url
        except: pass
        
        for path in self.FEED_PATHS:
            feed_url = f"{blog_url}{path}"
            try:
                if requests.head(feed_url, headers=self.headers, timeout=5).status_code == 200:
                    return feed_url
            except: continue
        return None

    def fetch_feed(self, feed_url: str, limit: int = 10) -> Dict[str, Any]:
        result = {
            "feed_url": feed_url, "fetched_at": datetime.now().isoformat(),
            "posts": [], "fetch_status": "pending"
        }
        if not HAS_FEEDPARSER:
            result.update({"fetch_status": "failed", "error": "feedparser missing"})
            return result
        
        try:
            feed = feedparser.parse(feed_url)
            if feed.bozo and not feed.entries:
                result.update({"fetch_status": "failed", "error": "Invalid feed"})
                return result
            
            result["title"] = feed.feed.get("title")
            for entry in feed.entries[:limit]:
                content = ""
                if hasattr(entry, "content"): content = entry.content[0].get("value", "")
                elif hasattr(entry, "summary"): content = entry.summary
                
                result["posts"].append({
                    "title": entry.get("title", "Untitled"),
                    "url": entry.get("link"),
                    "content_preview": re.sub(r'<[^>]+>', '', content)[:300],
                    "published": datetime.now().isoformat() # Simplified
                })
            result["fetch_status"] = "success"
            result["post_count"] = len(result["posts"])
        except Exception as e:
            result.update({"fetch_status": "failed", "error": str(e)})
        return result
    
    def fetch_from_blog_url(self, blog_url: str, limit: int = 10) -> Dict[str, Any]:
        print(f"  > Discovering RSS feed for: {blog_url}")
        feed_url = self.discover_feed_url(blog_url)
        if not feed_url: return {"blog_url": blog_url, "fetch_status": "failed"}
        
        print(f"    + Found feed: {feed_url}")
        res = self.fetch_feed(feed_url, limit)
        res["blog_url"] = blog_url
        if res["fetch_status"] == "success":
            print(f"    + Fetched {res.get('post_count')} posts")
        return res


class MediumFetcher:
    """Fetches Medium posts via RSS feed."""
    def __init__(self):
        self.blog_fetcher = BlogFetcher()
    
    def fetch_user_posts(self, username: str, limit: int = 10) -> Dict[str, Any]:
        username = username.lstrip("@")
        feed_url = f"https://medium.com/feed/@{username}"
        print(f"  > Fetching Medium posts for: @{username}")
        result = self.blog_fetcher.fetch_feed(feed_url, limit)
        result["platform"] = "medium"
        result["username"] = username
        if result["fetch_status"] == "success":
            print(f"    + Fetched {result.get('post_count', 0)} Medium posts")
        else:
            print(f"    [x] Failed to fetch Medium posts")
        return result


# ==================================================================================
# 6. HACKER NEWS FETCHER
# ==================================================================================

class HackerNewsFetcher:
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def fetch_user(self, username: str) -> Optional[Dict]:
        try:
            resp = requests.get(f"{self.BASE_URL}/user/{username}.json", timeout=self.timeout)
            if resp.status_code == 200: return resp.json()
        except: pass
        return None
    
    def fetch_item(self, item_id: int) -> Optional[Dict]:
        try:
            resp = requests.get(f"{self.BASE_URL}/item/{item_id}.json", timeout=self.timeout)
            if resp.status_code == 200: return resp.json()
        except: pass
        return None

    def fetch_full_profile(self, username: str, submission_limit: int = 15) -> Dict[str, Any]:
        print(f"  > Fetching Hacker News data for: {username}")
        result = {
            "platform": "hackernews", "username": username,
            "fetched_at": datetime.now().isoformat(),
            "profile": None, "submissions": [], "fetch_status": "pending"
        }
        
        user = self.fetch_user(username)
        if not user:
            result["fetch_status"] = "failed"
            print("    [x] User not found")
            return result
            
        result["profile"] = {
            "karma": user.get("karma", 0),
            "about": user.get("about", ""),
            "created": user.get("created"),
            "total_submissions": len(user.get("submitted", []))
        }
        
        # Fetch submissions in parallel
        ids = user.get("submitted", [])[:submission_limit]
        with ThreadPoolExecutor(max_workers=5) as ex:
            futures = {ex.submit(self.fetch_item, i): i for i in ids}
            for fut in as_completed(futures):
                try: 
                    item = fut.result()
                    if item:
                        result["submissions"].append({
                            "title": item.get("title"),
                            "type": item.get("type"),
                            "score": item.get("score"),
                            "url": item.get("url", f"https://news.ycombinator.com/item?id={item['id']}")
                        })
                except: pass
        
        result["fetch_status"] = "success"
        print(f"    + Karma: {user.get('karma', 0):,}")
        return result
