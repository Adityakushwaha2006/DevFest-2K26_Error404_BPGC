"""
GitHub Search Engine for discovering developers
"""

import requests
from typing import List, Dict, Optional, Any
from datetime import datetime


class GitHubSearchEngine:
    """
    Search for developers on GitHub using advanced search queries.
    Enables discovery of people you don't already know about.
    """
    
    def __init__(self, github_token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.headers = {}
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
    
    def search_users(
        self,
        query: str,
        location: Optional[str] = None,
        language: Optional[str] = None,
        min_followers: int = 0,
        min_repos: int = 0,
        max_results: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search for GitHub users with various filters.
        
        Args:
            query: Main search term (e.g., "blockchain", "machine learning")
            location: Geographic location (e.g., "San Francisco", "NYC", "India")
            language: Programming language (e.g., "python", "javascript")
            min_followers: Minimum follower count
            min_repos: Minimum public repository count
            max_results: Maximum number of results to return (max 100)
        
        Returns:
            List of user dictionaries with basic info
        
        Examples:
            # Find blockchain engineers in SF with 100+ followers
            search_users("blockchain", location="San Francisco", min_followers=100)
            
            # Find Python developers
            search_users("developer", language="python", min_repos=5)
            
            # Find ML researchers
            search_users("machine learning research", min_followers=50)
        """
        # Build search query - use spaces, requests lib handles encoding
        search_parts = [query]
        
        if location:
            search_parts.append(f"location:{location}")
        
        if language:
            search_parts.append(f"language:{language}")
        
        if min_followers > 0:
            search_parts.append(f"followers:>={min_followers}")
        
        if min_repos > 0:
            search_parts.append(f"repos:>={min_repos}")
        
        search_query = " ".join(search_parts)  # Use spaces, not +
        
        # Make API request
        url = f"{self.base_url}/search/users"
        params = {
            'q': search_query,
            'per_page': min(max_results, 100),
            'sort': 'followers',  # Sort by most followers first
            'order': 'desc'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                users = data.get('items', [])
                
                # Return simplified user info
                return [
                    {
                        'username': user['login'],
                        'profile_url': user['html_url'],
                        'avatar_url': user['avatar_url'],
                        'type': user['type'],
                        'score': user.get('score', 0)
                    }
                    for user in users
                ]
            else:
                print(f"GitHub Search API error: {response.status_code}")
                return []
        
        except Exception as e:
            print(f"Error searching GitHub: {str(e)}")
            return []
    
    def search_repositories(
        self,
        query: str,
        language: Optional[str] = None,
        min_stars: int = 0,
        max_results: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Search for repositories (useful for finding project contributors).
        
        Args:
            query: Search term (e.g., "blockchain", "react hooks")
            language: Programming language filter
            min_stars: Minimum star count
            max_results: Maximum results
        
        Returns:
            List of repository dictionaries
        """
        search_parts = [query]
        
        if language:
            search_parts.append(f"language:{language}")
        
        if min_stars > 0:
            search_parts.append(f"stars:>={min_stars}")
        
        search_query = "+".join(search_parts)
        
        url = f"{self.base_url}/search/repositories"
        params = {
            'q': search_query,
            'per_page': min(max_results, 100),
            'sort': 'stars',
            'order': 'desc'
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                repos = data.get('items', [])
                
                return [
                    {
                        'name': repo['name'],
                        'full_name': repo['full_name'],
                        'owner': repo['owner']['login'],
                        'description': repo.get('description', ''),
                        'stars': repo['stargazers_count'],
                        'language': repo.get('language', 'Unknown'),
                        'url': repo['html_url']
                    }
                    for repo in repos
                ]
            else:
                return []
        
        except Exception as e:
            print(f"Error searching repositories: {str(e)}")
            return []
    
    def get_repo_contributors(
        self,
        repo_full_name: str,
        max_contributors: int = 30
    ) -> List[str]:
        """
        Get contributors for a specific repository.
        Useful for finding active developers in a specific domain.
        
        Args:
            repo_full_name: Format "owner/repo" (e.g., "facebook/react")
            max_contributors: Maximum number of contributors
        
        Returns:
            List of GitHub usernames
        """
        url = f"{self.base_url}/repos/{repo_full_name}/contributors"
        params = {'per_page': min(max_contributors, 100)}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                contributors = response.json()
                return [c['login'] for c in contributors if c['type'] == 'User']
            else:
                return []
        
        except Exception as e:
            print(f"Error fetching contributors: {str(e)}")
            return []


class DiscoveryEngine:
    """
    High-level discovery interface combining search with identity resolution.
    """
    
    def __init__(self, search_engine: GitHubSearchEngine, identity_fetcher):
        self.search = search_engine
        self.fetcher = identity_fetcher
    
    def discover_people(
        self,
        goal: str,
        location: Optional[str] = None,
        min_activity: int = 10,
        max_people: int = 20
    ) -> List[Dict[str, Any]]:
        """
        High-level discovery: find people matching a goal.
        
        Args:
            goal: What you're looking for (e.g., "blockchain engineer", "React developer")
            location: Optional location filter
            min_activity: Minimum followers to filter noise
            max_people: Maximum results
        
        Returns:
            List of discovered people with basic profiles
        """
        print(f"🔍 Discovering: {goal}" + (f" in {location}" if location else ""))
        
        # Search GitHub
        users = self.search.search_users(
            query=goal,
            location=location,
            min_followers=min_activity,
            max_results=max_people
        )
        
        if not users:
            print("   No users found")
            return []
        
        print(f"   Found {len(users)} candidates")
        
        # Fetch basic profiles (just usernames for now)
        discovered = []
        for user in users:
            discovered.append({
                'username': user['username'],
                'profile_url': user['profile_url'],
                'avatar_url': user['avatar_url'],
                'search_score': user['score']
            })
        
        return discovered
    
    def discover_by_project(
        self,
        project_name: str,
        language: Optional[str] = None,
        max_people: int = 20
    ) -> List[str]:
        """
        Find people who work on similar projects.
        
        Args:
            project_name: Project/technology name
            language: Optional language filter
            max_people: Maximum contributors to return
        
        Returns:
            List of GitHub usernames
        """
        print(f"🔍 Finding {project_name} contributors...")
        
        # Search for repos
        repos = self.search.search_repositories(
            query=project_name,
            language=language,
            min_stars=50,
            max_results=5
        )
        
        if not repos:
            return []
        
        # Get contributors from top repos
        all_contributors = []
        for repo in repos[:3]:  # Top 3 repos
            contributors = self.search.get_repo_contributors(
                repo['full_name'],
                max_contributors=10
            )
            all_contributors.extend(contributors)
        
        # Remove duplicates and limit
        unique_contributors = list(set(all_contributors))[:max_people]
        
        print(f"   Found {len(unique_contributors)} contributors")
        return unique_contributors
