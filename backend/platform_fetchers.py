"""
Platform-specific data fetchers for identity nodes
"""

import requests
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any
from identity_node import IdentityNode, Platform, ActivityEvent, CrossReference


class PlatformFetcher(ABC):
    """Abstract base class for platform data fetchers"""
    
    @abstractmethod
    def fetch(self, identifier: str) -> IdentityNode:
        """Fetch data for the given identifier and return an IdentityNode"""
        pass
    
    @abstractmethod
    def extract_cross_references(self, node: IdentityNode) -> List[CrossReference]:
        """Extract cross-platform references from node data"""
        pass


class GitHubFetcher(PlatformFetcher):
    """Fetches data from GitHub API"""
    
    def __init__(self, github_token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.headers = {}
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
    
    def fetch(self, username: str) -> IdentityNode:
        """Fetch GitHub user profile and recent activity"""
        node = IdentityNode(Platform.GITHUB, username)
        
        try:
            # Fetch user profile
            profile_url = f"{self.base_url}/users/{username}"
            response = requests.get(profile_url, headers=self.headers)
            
            if response.status_code != 200:
                node.fetch_status = "failed"
                node.error_message = f"HTTP {response.status_code}"
                return node
            
            profile_data = response.json()
            node.data = profile_data
            
            # Fetch recent events (activity)
            events_url = f"{self.base_url}/users/{username}/events/public"
            events_response = requests.get(events_url, headers=self.headers)
            
            if events_response.status_code == 200:
                events = events_response.json()
                self._parse_events(node, events)
            
            # Extract cross-references
            self.extract_cross_references(node)
            
            node.fetch_status = "success"
            node.last_updated = datetime.now()
            node.confidence_score = 1.0  # Primary source, highest confidence
            
        except Exception as e:
            node.fetch_status = "failed"
            node.error_message = str(e)
        
        return node
    
    def _parse_events(self, node: IdentityNode, events: List[Dict]):
        """Parse GitHub events into ActivityEvent objects"""
        for event in events[:30]:  # Limit to last 30 events
            event_type = event.get('type', '')
            created_at = datetime.fromisoformat(event['created_at'].replace('Z', '+00:00'))
            
            # Only track certain event types
            if event_type == 'PushEvent':
                commits = event.get('payload', {}).get('commits', [])
                for commit in commits:
                    activity = ActivityEvent(
                        platform=Platform.GITHUB,
                        event_type='commit',
                        content=commit.get('message', 'No message'),
                        timestamp=created_at,
                        url=f"https://github.com/{node.identifier}",
                        metadata={'sha': commit.get('sha')}
                    )
                    node.add_activity(activity)
            
            elif event_type == 'CreateEvent':
                ref_type = event.get('payload', {}).get('ref_type')
                activity = ActivityEvent(
                    platform=Platform.GITHUB,
                    event_type=f'create_{ref_type}',
                    content=f"Created {ref_type}: {event.get('payload', {}).get('ref', '')}",
                    timestamp=created_at,
                    url=f"https://github.com/{node.identifier}"
                )
                node.add_activity(activity)
            
            elif event_type == 'IssueCommentEvent':
                comment = event.get('payload', {}).get('comment', {})
                activity = ActivityEvent(
                    platform=Platform.GITHUB,
                    event_type='comment',
                    content=comment.get('body', '')[:200],  # Truncate long comments
                    timestamp=created_at,
                    url=comment.get('html_url')
                )
                node.add_activity(activity)
    
    def extract_cross_references(self, node: IdentityNode) -> List[CrossReference]:
        """Extract Twitter, blog, email from GitHub profile"""
        cross_refs = []
        
        # Twitter username (built-in field)
        twitter_username = node.data.get('twitter_username')
        if twitter_username:
            node.add_cross_reference(Platform.TWITTER, twitter_username, 'twitter_username')
            cross_refs.append(CrossReference(Platform.TWITTER, twitter_username, 'twitter_username'))
        
        # Bio parsing for handles
        bio = node.data.get('bio', '')
        if bio:
            # Look for Twitter handles in bio
            twitter_matches = re.findall(r'@([A-Za-z0-9_]+)', bio)
            for handle in twitter_matches:
                if handle not in [ref.identifier for ref in cross_refs]:
                    node.add_cross_reference(Platform.TWITTER, handle, 'bio')
                    cross_refs.append(CrossReference(Platform.TWITTER, handle, 'bio'))
        
        # Blog/website
        blog_url = node.data.get('blog')
        if blog_url:
            # Check if it's a known platform
            if 'dev.to' in blog_url:
                dev_username = blog_url.split('/')[-1]
                node.add_cross_reference(Platform.DEVTO, dev_username, 'blog')
                cross_refs.append(CrossReference(Platform.DEVTO, dev_username, 'blog'))
            elif 'hashnode.dev' in blog_url:
                hashnode_username = blog_url.split('//')[-1].split('.')[0]
                node.add_cross_reference(Platform.HASHNODE, hashnode_username, 'blog')
                cross_refs.append(CrossReference(Platform.HASHNODE, hashnode_username, 'blog'))
        
        return cross_refs


class DevToFetcher(PlatformFetcher):
    """Fetches data from Dev.to API (no auth required)"""
    
    def __init__(self):
        self.base_url = "https://dev.to/api"
    
    def fetch(self, username: str) -> IdentityNode:
        """Fetch Dev.to user profile and articles"""
        node = IdentityNode(Platform.DEVTO, username)
        
        try:
            # Fetch user profile
            profile_url = f"{self.base_url}/users/by_username?url={username}"
            response = requests.get(profile_url)
            
            if response.status_code != 200:
                node.fetch_status = "failed"
                node.error_message = f"HTTP {response.status_code}"
                return node
            
            profile_data = response.json()
            node.data = profile_data
            
            # Fetch articles
            user_id = profile_data.get('id')
            if user_id:
                articles_url = f"{self.base_url}/articles?username={username}"
                articles_response = requests.get(articles_url)
                
                if articles_response.status_code == 200:
                    articles = articles_response.json()
                    self._parse_articles(node, articles)
            
            # Extract cross-references
            self.extract_cross_references(node)
            
            node.fetch_status = "success"
            node.last_updated = datetime.now()
            node.confidence_score = 0.8  # Secondary source
            
        except Exception as e:
            node.fetch_status = "failed"
            node.error_message = str(e)
        
        return node
    
    def _parse_articles(self, node: IdentityNode, articles: List[Dict]):
        """Parse Dev.to articles into ActivityEvent objects"""
        for article in articles[:20]:  # Limit to 20 most recent
            published_at = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
            
            activity = ActivityEvent(
                platform=Platform.DEVTO,
                event_type='article',
                content=article.get('title', ''),
                timestamp=published_at,
                url=article.get('url'),
                metadata={
                    'tags': article.get('tag_list', []),
                    'reactions': article.get('public_reactions_count', 0),
                    'comments': article.get('comments_count', 0)
                }
            )
            node.add_activity(activity)
    
    def extract_cross_references(self, node: IdentityNode) -> List[CrossReference]:
        """Extract GitHub/Twitter from Dev.to profile"""
        cross_refs = []
        
        # Dev.to provides GitHub username
        github_username = node.data.get('github_username')
        if github_username:
            node.add_cross_reference(Platform.GITHUB, github_username, 'github_username')
            cross_refs.append(CrossReference(Platform.GITHUB, github_username, 'github_username'))
        
        # Twitter username
        twitter_username = node.data.get('twitter_username')
        if twitter_username:
            node.add_cross_reference(Platform.TWITTER, twitter_username, 'twitter_username')
            cross_refs.append(CrossReference(Platform.TWITTER, twitter_username, 'twitter_username'))
        
        return cross_refs



class MockLinkedInFetcher(PlatformFetcher):
    """
    Mock LinkedIn fetcher for hackathon demo.
    Returns simulated data based on a template.
    """
    
    def __init__(self, mock_data_path: Optional[str] = None):
        self.mock_data_path = mock_data_path
        self.mock_profiles = self._load_mock_data()
    
    def _load_mock_data(self) -> Dict[str, Dict]:
        """Load mock LinkedIn profiles from JSON file"""
        # For now, return a hardcoded template
        # In production, this would load from a JSON file
        return {
            'default': {
                'name': 'Professional User',
                'headline': 'Software Engineer',
                'location': 'San Francisco, CA',
                'company': 'Tech Company',
                'summary': 'Experienced software engineer...',
                'connections': 500
            }
        }
    
    def fetch(self, profile_url: str) -> IdentityNode:
        """Create a mock LinkedIn node"""
        # Extract identifier from URL (last part)
        identifier = profile_url.split('/')[-1] if '/' in profile_url else profile_url
        
        node = IdentityNode(Platform.LINKEDIN, identifier)
        
        # Use mock data
        node.data = self.mock_profiles.get(identifier, self.mock_profiles['default'])
        node.fetch_status = "success"
        node.last_updated = datetime.now()
        node.confidence_score = 0.5  # Lower confidence for mock data
        
        return node
    
    def extract_cross_references(self, node: IdentityNode) -> List[CrossReference]:
        """Mock cross-references (could be in profile summary)"""
        # In a real implementation, this would parse the summary/bio
        return []


# Factory function to get appropriate fetcher
def get_fetcher(platform: Platform, **kwargs) -> PlatformFetcher:
    """Factory function to instantiate the correct fetcher"""
    if platform == Platform.GITHUB:
        return GitHubFetcher(kwargs.get('github_token'))
    elif platform == Platform.DEVTO:
        return DevToFetcher()
    elif platform == Platform.LINKEDIN:
        return MockLinkedInFetcher(kwargs.get('mock_data_path'))
    else:
        raise ValueError(f"Unsupported platform: {platform}")
