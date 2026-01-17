"""
Extended GitHub Fetcher
Comprehensive data extraction from GitHub API for social profile consolidation.

Features:
- Full profile with followers/following/repos
- Recent commits (3 months) with recency weighting
- Issue comments and PR activity
- Contribution patterns and frequency
- Repository analysis (languages, stars, activity)
- Organization memberships
- Starred repos (interests)
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not required if GITHUB_TOKEN is set manually

# Import identity classes
from identity_node import IdentityNode, Platform, ActivityEvent, CrossReference


class ExtendedGitHubFetcher:
    """
    Fetches comprehensive GitHub data for a user.
    Extracts 3 months of activity with recency weighting metadata.
    """
    
    # Recency weight boundaries (for next pipeline stage)
    RECENCY_WEIGHTS = {
        "last_week": 1.0,       # Last 7 days
        "last_month": 0.8,      # 8-30 days
        "last_3_months": 0.5    # 31-90 days
    }
    
    def __init__(self, github_token: Optional[str] = None):
        self.base_url = "https://api.github.com"
        self.token = github_token or os.getenv('GITHUB_TOKEN')
        self.headers = {}
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
            self.headers['Accept'] = 'application/vnd.github.v3+json'
        
        # Date boundaries for activity extraction
        self.now = datetime.now()
        self.three_months_ago = self.now - timedelta(days=90)
        self.one_month_ago = self.now - timedelta(days=30)
        self.one_week_ago = self.now - timedelta(days=7)
    
    def fetch_full_profile(self, username: str) -> Dict[str, Any]:
        """
        Fetches comprehensive GitHub data for a user.
        
        Returns dict with:
        - profile: Basic user info
        - repositories: Top repos with stats
        - commits: Recent commit activity (3 months)
        - comments: Issue/PR comments
        - pull_requests: PR activity
        - contribution_patterns: Activity frequency
        - organizations: Org memberships
        - interests: Starred repos
        - cross_references: Detected social handles
        - recency_metadata: Weighting info for scoring stage
        """
        print(f"📊 Fetching comprehensive GitHub data for: {username}")
        
        result = {
            "username": username,
            "fetched_at": datetime.now().isoformat(),
            "profile": {},
            "repositories": [],
            "commits": [],
            "comments": [],
            "pull_requests": [],
            "contribution_patterns": {},
            "organizations": [],
            "interests": [],
            "cross_references": [],
            "recency_metadata": {
                "weights": self.RECENCY_WEIGHTS,
                "boundaries": {
                    "one_week_ago": self.one_week_ago.isoformat(),
                    "one_month_ago": self.one_month_ago.isoformat(),
                    "three_months_ago": self.three_months_ago.isoformat()
                },
                "activity_by_recency": {
                    "last_week": 0,
                    "last_month": 0,
                    "last_3_months": 0
                }
            },
            "fetch_status": "pending"
        }
        
        try:
            # 1. Basic profile
            print("  → Fetching profile...")
            result["profile"] = self._fetch_profile(username)
            
            # 2. Repositories
            print("  → Fetching repositories...")
            result["repositories"] = self._fetch_repositories(username)
            
            # 3. Recent events (commits, comments, PRs)
            print("  → Fetching recent activity...")
            events = self._fetch_events(username)
            result["commits"] = events["commits"]
            result["comments"] = events["comments"]
            result["pull_requests"] = events["pull_requests"]
            
            # 4. Additional comments from search API
            print("  → Fetching issue comments (last 3 months)...")
            additional_comments = self._fetch_issue_comments(username)
            result["comments"].extend(additional_comments)
            
            # 5. Contribution patterns
            print("  → Analyzing contribution patterns...")
            result["contribution_patterns"] = self._analyze_contribution_patterns(
                result["commits"], result["comments"], result["pull_requests"]
            )
            
            # 6. Organizations
            print("  → Fetching organizations...")
            result["organizations"] = self._fetch_organizations(username)
            
            # 7. Starred repos (interests)
            print("  → Fetching starred repos...")
            result["interests"] = self._fetch_starred_repos(username)
            
            # 8. Cross-references (auto-detect social handles)
            print("  → Extracting cross-references...")
            result["cross_references"] = self._extract_cross_references(result["profile"])
            
            # 9. Calculate recency metadata
            result["recency_metadata"]["activity_by_recency"] = self._count_by_recency(
                result["commits"] + result["comments"] + result["pull_requests"]
            )
            
            result["fetch_status"] = "success"
            print(f"✅ Successfully fetched GitHub data for {username}")
            
        except Exception as e:
            result["fetch_status"] = "failed"
            result["error"] = str(e)
            print(f"❌ Failed to fetch GitHub data: {e}")
        
        return result
    
    def _fetch_profile(self, username: str) -> Dict:
        """Fetch basic user profile"""
        url = f"{self.base_url}/users/{username}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch profile: HTTP {response.status_code}")
        
        return response.json()
    
    def _fetch_repositories(self, username: str, limit: int = 30) -> List[Dict]:
        """Fetch top repositories by activity and stars"""
        repos = []
        
        # Fetch repos sorted by recently pushed
        url = f"{self.base_url}/users/{username}/repos"
        params = {"sort": "pushed", "per_page": min(limit, 100)}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            for repo in response.json()[:limit]:
                repos.append({
                    "name": repo.get("name"),
                    "full_name": repo.get("full_name"),
                    "description": repo.get("description"),
                    "url": repo.get("html_url"),
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "watchers": repo.get("watchers_count", 0),
                    "open_issues": repo.get("open_issues_count", 0),
                    "is_fork": repo.get("fork", False),
                    "created_at": repo.get("created_at"),
                    "updated_at": repo.get("updated_at"),
                    "pushed_at": repo.get("pushed_at"),
                    "topics": repo.get("topics", [])
                })
        
        return repos
    
    def _fetch_events(self, username: str) -> Dict[str, List]:
        """Fetch recent public events (commits, comments, PRs)"""
        commits = []
        comments = []
        pull_requests = []
        
        # Fetch up to 300 events (3 pages)
        for page in range(1, 4):
            url = f"{self.base_url}/users/{username}/events/public"
            params = {"per_page": 100, "page": page}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                break
            
            events = response.json()
            if not events:
                break
            
            for event in events:
                created_at = datetime.fromisoformat(event["created_at"].replace("Z", "+00:00"))
                
                # Filter to last 3 months
                if created_at.replace(tzinfo=None) < self.three_months_ago:
                    continue
                
                recency = self._get_recency_bucket(created_at)
                event_type = event.get("type", "")
                
                if event_type == "PushEvent":
                    for commit in event.get("payload", {}).get("commits", []):
                        commits.append({
                            "sha": commit.get("sha"),
                            "message": commit.get("message"),
                            "timestamp": created_at.isoformat(),
                            "repo": event.get("repo", {}).get("name"),
                            "url": f"https://github.com/{event.get('repo', {}).get('name')}/commit/{commit.get('sha')}",
                            "recency_bucket": recency,
                            "recency_weight": self.RECENCY_WEIGHTS[recency]
                        })
                
                elif event_type == "IssueCommentEvent":
                    comment = event.get("payload", {}).get("comment", {})
                    comments.append({
                        "type": "issue_comment",
                        "body": comment.get("body", "")[:500],
                        "timestamp": created_at.isoformat(),
                        "url": comment.get("html_url"),
                        "repo": event.get("repo", {}).get("name"),
                        "recency_bucket": recency,
                        "recency_weight": self.RECENCY_WEIGHTS[recency]
                    })
                
                elif event_type == "PullRequestEvent":
                    pr = event.get("payload", {}).get("pull_request", {})
                    action = event.get("payload", {}).get("action")
                    pull_requests.append({
                        "action": action,
                        "title": pr.get("title"),
                        "timestamp": created_at.isoformat(),
                        "url": pr.get("html_url"),
                        "repo": event.get("repo", {}).get("name"),
                        "state": pr.get("state"),
                        "merged": pr.get("merged", False),
                        "recency_bucket": recency,
                        "recency_weight": self.RECENCY_WEIGHTS[recency]
                    })
                
                elif event_type == "PullRequestReviewEvent":
                    review = event.get("payload", {}).get("review", {})
                    pull_requests.append({
                        "action": "review",
                        "state": review.get("state"),
                        "timestamp": created_at.isoformat(),
                        "url": review.get("html_url"),
                        "repo": event.get("repo", {}).get("name"),
                        "recency_bucket": recency,
                        "recency_weight": self.RECENCY_WEIGHTS[recency]
                    })
        
        return {"commits": commits, "comments": comments, "pull_requests": pull_requests}
    
    def _fetch_issue_comments(self, username: str, limit: int = 50) -> List[Dict]:
        """Fetch issue comments via search API"""
        comments = []
        
        # Search for comments by user in last 3 months
        since = self.three_months_ago.strftime("%Y-%m-%d")
        url = f"{self.base_url}/search/issues"
        params = {
            "q": f"commenter:{username} updated:>={since}",
            "sort": "updated",
            "order": "desc",
            "per_page": min(limit, 100)
        }
        
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            issues = response.json().get("items", [])
            for issue in issues[:limit]:
                updated_at = datetime.fromisoformat(issue["updated_at"].replace("Z", "+00:00"))
                recency = self._get_recency_bucket(updated_at)
                
                comments.append({
                    "type": "issue_participation",
                    "title": issue.get("title"),
                    "timestamp": updated_at.isoformat(),
                    "url": issue.get("html_url"),
                    "repo": issue.get("repository_url", "").split("/")[-1] if issue.get("repository_url") else None,
                    "is_pull_request": "pull_request" in issue,
                    "state": issue.get("state"),
                    "recency_bucket": recency,
                    "recency_weight": self.RECENCY_WEIGHTS[recency]
                })
        
        return comments
    
    def _fetch_organizations(self, username: str) -> List[Dict]:
        """Fetch organization memberships"""
        orgs = []
        url = f"{self.base_url}/users/{username}/orgs"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 200:
            for org in response.json():
                orgs.append({
                    "login": org.get("login"),
                    "description": org.get("description"),
                    "url": f"https://github.com/{org.get('login')}"
                })
        
        return orgs
    
    def _fetch_starred_repos(self, username: str, limit: int = 20) -> List[Dict]:
        """Fetch starred repositories (indicates interests)"""
        starred = []
        url = f"{self.base_url}/users/{username}/starred"
        params = {"per_page": min(limit, 100)}
        response = requests.get(url, headers=self.headers, params=params)
        
        if response.status_code == 200:
            for repo in response.json()[:limit]:
                starred.append({
                    "name": repo.get("full_name"),
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "stars": repo.get("stargazers_count"),
                    "topics": repo.get("topics", [])
                })
        
        return starred
    
    def _extract_cross_references(self, profile: Dict) -> List[Dict]:
        """Extract cross-platform references from profile"""
        refs = []
        
        # Twitter username (built-in field)
        twitter = profile.get("twitter_username")
        if twitter:
            refs.append({
                "platform": "twitter",
                "identifier": twitter,
                "source": "twitter_username_field",
                "confidence": 1.0
            })
        
        # Blog URL
        blog = profile.get("blog")
        if blog:
            refs.append({
                "platform": "website",
                "identifier": blog,
                "source": "blog_field",
                "confidence": 1.0
            })
            
            # Check for known platforms in blog URL
            if "linkedin.com" in blog:
                linkedin_id = blog.rstrip("/").split("/")[-1]
                refs.append({
                    "platform": "linkedin",
                    "identifier": linkedin_id,
                    "source": "blog_field",
                    "confidence": 0.9
                })
            elif "twitter.com" in blog or "x.com" in blog:
                twitter_handle = blog.rstrip("/").split("/")[-1]
                refs.append({
                    "platform": "twitter",
                    "identifier": twitter_handle,
                    "source": "blog_field",
                    "confidence": 0.9
                })
            elif "dev.to" in blog:
                devto_user = blog.rstrip("/").split("/")[-1]
                refs.append({
                    "platform": "devto",
                    "identifier": devto_user,
                    "source": "blog_field",
                    "confidence": 0.9
                })
        
        # Bio parsing for @handles
        bio = profile.get("bio", "") or ""
        import re
        
        # Twitter handles (@username)
        handles = re.findall(r'@([A-Za-z0-9_]+)', bio)
        for handle in handles:
            if handle not in [r["identifier"] for r in refs if r["platform"] == "twitter"]:
                refs.append({
                    "platform": "twitter",
                    "identifier": handle,
                    "source": "bio",
                    "confidence": 0.7
                })
        
        # LinkedIn URLs in bio
        linkedin_matches = re.findall(r'linkedin\.com/in/([A-Za-z0-9_-]+)', bio)
        for match in linkedin_matches:
            refs.append({
                "platform": "linkedin",
                "identifier": match,
                "source": "bio",
                "confidence": 0.8
            })
        
        return refs
    
    def _analyze_contribution_patterns(
        self, 
        commits: List[Dict], 
        comments: List[Dict], 
        prs: List[Dict]
    ) -> Dict:
        """Analyze contribution patterns and frequency"""
        all_activities = commits + comments + prs
        
        # Daily activity count
        daily = defaultdict(int)
        weekly = defaultdict(int)  # 0=Monday, 6=Sunday
        hourly = defaultdict(int)
        
        for activity in all_activities:
            try:
                ts = datetime.fromisoformat(activity["timestamp"].replace("Z", "+00:00"))
                date_str = ts.strftime("%Y-%m-%d")
                daily[date_str] += 1
                weekly[ts.weekday()] += 1
                hourly[ts.hour] += 1
            except:
                continue
        
        # Find most active days/times
        most_active_days = sorted(daily.items(), key=lambda x: x[1], reverse=True)[:10]
        most_active_weekday = max(weekly.items(), key=lambda x: x[1]) if weekly else (0, 0)
        most_active_hour = max(hourly.items(), key=lambda x: x[1]) if hourly else (0, 0)
        
        # Language distribution from commits
        repo_languages = defaultdict(int)
        for commit in commits:
            repo = commit.get("repo", "")
            # Count as activity for that repo
            repo_languages[repo] += 1
        
        top_repos = sorted(repo_languages.items(), key=lambda x: x[1], reverse=True)[:10]
        
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        return {
            "total_activities": len(all_activities),
            "total_commits": len(commits),
            "total_comments": len(comments),
            "total_prs": len(prs),
            "daily_activity": dict(most_active_days),
            "most_active_weekday": {
                "day": weekday_names[most_active_weekday[0]] if weekly else None,
                "count": most_active_weekday[1]
            },
            "most_active_hour": {
                "hour": most_active_hour[0],
                "count": most_active_hour[1]
            },
            "top_contributed_repos": [{"repo": r, "count": c} for r, c in top_repos],
            "activity_streak": self._calculate_streak(daily)
        }
    
    def _calculate_streak(self, daily: Dict[str, int]) -> Dict:
        """Calculate current and longest activity streak"""
        if not daily:
            return {"current": 0, "longest": 0}
        
        dates = sorted([datetime.strptime(d, "%Y-%m-%d") for d in daily.keys()], reverse=True)
        
        # Current streak
        current_streak = 0
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i, date in enumerate(dates):
            expected = today - timedelta(days=i)
            if date.date() == expected.date():
                current_streak += 1
            else:
                break
        
        # Longest streak
        longest = 1
        current = 1
        for i in range(1, len(dates)):
            if (dates[i-1] - dates[i]).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        
        return {"current": current_streak, "longest": longest}
    
    def _get_recency_bucket(self, dt: datetime) -> str:
        """Determine which recency bucket a timestamp falls into"""
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
            counts[bucket] += 1
        
        return counts
    
    def to_identity_node(self, data: Dict) -> IdentityNode:
        """Convert fetched data to IdentityNode format"""
        node = IdentityNode(Platform.GITHUB, data["username"])
        node.data = data["profile"]
        node.fetch_status = data["fetch_status"]
        node.last_updated = datetime.now()
        node.confidence_score = 1.0 if data["fetch_status"] == "success" else 0.0
        
        # Add cross-references
        for ref in data.get("cross_references", []):
            try:
                platform = Platform(ref["platform"])
                node.add_cross_reference(platform, ref["identifier"], ref["source"])
            except ValueError:
                # Skip unknown platforms
                pass
        
        # Add activities
        for commit in data.get("commits", [])[:30]:
            activity = ActivityEvent(
                platform=Platform.GITHUB,
                event_type="commit",
                content=commit.get("message", ""),
                timestamp=datetime.fromisoformat(commit["timestamp"].replace("Z", "+00:00")),
                url=commit.get("url"),
                metadata={"sha": commit.get("sha"), "recency_weight": commit.get("recency_weight")}
            )
            node.add_activity(activity)
        
        for comment in data.get("comments", [])[:20]:
            activity = ActivityEvent(
                platform=Platform.GITHUB,
                event_type="comment",
                content=comment.get("body", comment.get("title", "")),
                timestamp=datetime.fromisoformat(comment["timestamp"].replace("Z", "+00:00")),
                url=comment.get("url"),
                metadata={"recency_weight": comment.get("recency_weight")}
            )
            node.add_activity(activity)
        
        return node


# Quick test
if __name__ == "__main__":
    import json
    
    fetcher = ExtendedGitHubFetcher()
    
    # Test with a user
    username = "kentcdodds"
    print(f"\n{'='*60}")
    print(f"Testing ExtendedGitHubFetcher with: {username}")
    print(f"{'='*60}\n")
    
    data = fetcher.fetch_full_profile(username)
    
    print(f"\n📋 Results Summary:")
    print(f"  • Profile: {data['profile'].get('name', 'N/A')}")
    print(f"  • Repos: {len(data['repositories'])}")
    print(f"  • Commits: {len(data['commits'])}")
    print(f"  • Comments: {len(data['comments'])}")
    print(f"  • PRs: {len(data['pull_requests'])}")
    print(f"  • Organizations: {len(data['organizations'])}")
    print(f"  • Cross-refs: {len(data['cross_references'])}")
    print(f"\n📊 Recency Breakdown:")
    for bucket, count in data['recency_metadata']['activity_by_recency'].items():
        weight = data['recency_metadata']['weights'][bucket]
        print(f"  • {bucket}: {count} activities (weight: {weight})")
    
    # Save sample output
    os.makedirs("social_profiles", exist_ok=True)
    with open(f"social_profiles/{username}_github_extended.json", "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"\n💾 Saved to: social_profiles/{username}_github_extended.json")
