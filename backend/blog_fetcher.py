"""
Blog / RSS Feed Fetcher
Extracts recent posts from personal blogs and RSS feeds.

Supports:
- Standard RSS 2.0
- Atom feeds
- Common blog platforms (WordPress, Ghost, Jekyll, Hugo)
"""

import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
import re

# Try to import feedparser, provide fallback
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    print("Warning: feedparser not installed. Install with: pip install feedparser")


class BlogFetcher:
    """
    Fetches recent blog posts from RSS/Atom feeds.
    """
    
    # Common RSS feed paths to try
    FEED_PATHS = [
        "/feed",
        "/rss",
        "/rss.xml",
        "/feed.xml",
        "/atom.xml",
        "/blog/rss.xml",
        "/blog/feed",
        "/index.xml",  # Hugo default
        "/feed/",
        "/rss/",
    ]
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "NEXUS-Bot/1.0 (Social Profile Aggregator)"
        }
    
    def discover_feed_url(self, blog_url: str) -> Optional[str]:
        """
        Try to discover the RSS/Atom feed URL for a blog.
        
        Args:
            blog_url: The main blog URL
            
        Returns:
            Feed URL if found, None otherwise
        """
        # Normalize URL
        if not blog_url.startswith(("http://", "https://")):
            blog_url = f"https://{blog_url}"
        
        blog_url = blog_url.rstrip("/")
        
        # First, try to find feed link in HTML
        try:
            response = requests.get(blog_url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                # Look for RSS/Atom link tags
                feed_patterns = [
                    r'<link[^>]+type=["\']application/rss\+xml["\'][^>]+href=["\']([^"\']+)["\']',
                    r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/rss\+xml["\']',
                    r'<link[^>]+type=["\']application/atom\+xml["\'][^>]+href=["\']([^"\']+)["\']',
                    r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/atom\+xml["\']',
                ]
                
                for pattern in feed_patterns:
                    match = re.search(pattern, response.text, re.IGNORECASE)
                    if match:
                        feed_url = match.group(1)
                        # Handle relative URLs
                        if feed_url.startswith("/"):
                            parsed = urlparse(blog_url)
                            feed_url = f"{parsed.scheme}://{parsed.netloc}{feed_url}"
                        return feed_url
        except:
            pass
        
        # Try common feed paths
        for path in self.FEED_PATHS:
            feed_url = f"{blog_url}{path}"
            try:
                response = requests.head(feed_url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    return feed_url
            except:
                continue
        
        return None
    
    def fetch_feed(self, feed_url: str, limit: int = 10) -> Dict[str, Any]:
        """
        Fetch and parse an RSS/Atom feed.
        
        Args:
            feed_url: Direct URL to the RSS/Atom feed
            limit: Max posts to return
            
        Returns:
            Dict with feed info and posts
        """
        result = {
            "feed_url": feed_url,
            "fetched_at": datetime.now().isoformat(),
            "title": None,
            "description": None,
            "posts": [],
            "fetch_status": "pending"
        }
        
        if not HAS_FEEDPARSER:
            result["fetch_status"] = "failed"
            result["error"] = "feedparser not installed"
            return result
        
        try:
            feed = feedparser.parse(feed_url)
            
            if feed.bozo and not feed.entries:
                result["fetch_status"] = "failed"
                result["error"] = "Invalid feed"
                return result
            
            # Feed metadata
            result["title"] = feed.feed.get("title")
            result["description"] = feed.feed.get("description") or feed.feed.get("subtitle")
            result["link"] = feed.feed.get("link")
            
            # Parse entries
            for entry in feed.entries[:limit]:
                # Parse date
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published = datetime(*entry.published_parsed[:6]).isoformat()
                    except:
                        pass
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    try:
                        published = datetime(*entry.updated_parsed[:6]).isoformat()
                    except:
                        pass
                
                # Get content preview
                content = ""
                if hasattr(entry, "content") and entry.content:
                    content = entry.content[0].get("value", "")
                elif hasattr(entry, "summary"):
                    content = entry.summary
                
                # Strip HTML tags for preview
                content_preview = re.sub(r'<[^>]+>', '', content)[:300]
                
                result["posts"].append({
                    "title": entry.get("title", "Untitled"),
                    "url": entry.get("link"),
                    "published": published,
                    "content_preview": content_preview,
                    "tags": [tag.get("term") for tag in entry.get("tags", [])]
                })
            
            result["fetch_status"] = "success"
            result["post_count"] = len(result["posts"])
            
        except Exception as e:
            result["fetch_status"] = "failed"
            result["error"] = str(e)
        
        return result
    
    def fetch_from_blog_url(self, blog_url: str, limit: int = 10) -> Dict[str, Any]:
        """
        Convenience method: discover feed and fetch posts.
        
        Args:
            blog_url: Main blog URL
            limit: Max posts to return
            
        Returns:
            Feed data dict
        """
        print(f"  → Discovering RSS feed for: {blog_url}")
        
        feed_url = self.discover_feed_url(blog_url)
        
        if not feed_url:
            print(f"    ✗ No RSS feed found")
            return {
                "blog_url": blog_url,
                "fetch_status": "failed",
                "error": "No RSS feed discovered"
            }
        
        print(f"    ✓ Found feed: {feed_url}")
        
        result = self.fetch_feed(feed_url, limit)
        result["blog_url"] = blog_url
        
        if result["fetch_status"] == "success":
            print(f"    ✓ Fetched {result['post_count']} posts")
        
        return result


class MediumFetcher:
    """
    Fetches Medium posts via RSS feed.
    Medium provides RSS at: medium.com/feed/@username
    """
    
    def __init__(self):
        self.blog_fetcher = BlogFetcher()
    
    def fetch_user_posts(self, username: str, limit: int = 10) -> Dict[str, Any]:
        """
        Fetch Medium posts for a user.
        
        Args:
            username: Medium username (with or without @)
            limit: Max posts
            
        Returns:
            Feed data dict
        """
        # Normalize username
        username = username.lstrip("@")
        feed_url = f"https://medium.com/feed/@{username}"
        
        print(f"  → Fetching Medium posts for: @{username}")
        
        result = self.blog_fetcher.fetch_feed(feed_url, limit)
        result["platform"] = "medium"
        result["username"] = username
        
        if result["fetch_status"] == "success":
            print(f"    ✓ Fetched {result.get('post_count', 0)} Medium posts")
        else:
            print(f"    ✗ Failed to fetch Medium posts")
        
        return result


# Test
if __name__ == "__main__":
    print("=" * 60)
    print("Blog/RSS Fetcher Test")
    print("=" * 60)
    
    fetcher = BlogFetcher()
    
    # Test with a known blog
    test_blogs = [
        "https://kentcdodds.com/blog",
        "https://overreacted.io",  # Dan Abramov's blog
    ]
    
    for blog in test_blogs:
        print(f"\nTesting: {blog}")
        result = fetcher.fetch_from_blog_url(blog, limit=3)
        
        if result["fetch_status"] == "success":
            print(f"  Blog Title: {result.get('title')}")
            for post in result["posts"][:3]:
                print(f"  - {post['title']}")
        else:
            print(f"  Error: {result.get('error')}")
