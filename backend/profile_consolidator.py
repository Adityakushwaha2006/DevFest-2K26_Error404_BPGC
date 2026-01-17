"""
Profile Consolidator Pipeline
Main entry point for social profile consolidation.

Pipeline:
1. Fetch extended GitHub data (live)
2. Auto-detect social handles from cross-references
3. Load simulated Twitter/LinkedIn data
4. Build IdentityGraph with all nodes
5. Calculate cross-validation confidence
6. Aggregate all data into comprehensive JSON
7. Save to social_profiles folder

Output is ready for the next pipeline stage (scoring by context/intent/timing).
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from identity_node import IdentityNode, IdentityGraph, Platform, ActivityEvent
from extended_github_fetcher import ExtendedGitHubFetcher
from simulated_data_fetcher import SimulatedDataFetcher


class ProfileConsolidator:
    """
    Main pipeline: Fetches from all sources, validates identity,
    and consolidates into comprehensive JSON.
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        github_token: Optional[str] = None
    ):
        """
        Initialize the consolidator.
        
        Args:
            output_dir: Where to save consolidated profiles. Default: backend/social_profiles/
            github_token: GitHub API token for higher rate limits
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent / "social_profiles"
        
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize fetchers
        self.github_fetcher = ExtendedGitHubFetcher(github_token=github_token)
        self.simulated_fetcher = SimulatedDataFetcher()
    
    def consolidate(
        self,
        github_username: str,
        twitter_handle: Optional[str] = None,
        linkedin_id: Optional[str] = None,
        output_file: Optional[str] = None,
        use_simulated_github: bool = False
    ) -> Dict[str, Any]:
        """
        Run the full consolidation pipeline.
        
        Args:
            github_username: Primary identifier - GitHub username
            twitter_handle: Optional Twitter handle (auto-detected if None)
            linkedin_id: Optional LinkedIn ID (auto-detected if None)
            output_file: Custom output filename (default: {username}_consolidated.json)
            use_simulated_github: If True, use simulated GitHub instead of live API
        
        Returns:
            Comprehensive consolidated profile dict
        """
        print("\n" + "=" * 60)
        print(f"🔄 PROFILE CONSOLIDATION PIPELINE")
        print(f"   Target: {github_username}")
        print("=" * 60)
        
        result = {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "pipeline_version": "1.0",
                "primary_identifier": github_username,
                "data_sources": []
            },
            "identity": {
                "primary_name": None,
                "confidence_score": 0.0,
                "verified_platforms": [],
                "cross_references": []
            },
            "profiles": {},
            "activity_timeline": [],
            "contribution_patterns": {},
            "engagement_metrics": {},
            "recency_summary": {},
            "summary": {}
        }
        
        # Step 1: Fetch GitHub data
        print("\n📊 Step 1: Fetching GitHub data...")
        github_data = self._fetch_github(github_username, use_simulated=use_simulated_github)
        
        if github_data and github_data.get("fetch_status") == "success":
            result["profiles"]["github"] = github_data
            result["meta"]["data_sources"].append("github_live" if not use_simulated_github else "github_simulated")
            result["identity"]["verified_platforms"].append("github")
            result["identity"]["primary_name"] = github_data.get("profile", {}).get("name")
            
            # Store contribution patterns from GitHub
            result["contribution_patterns"] = github_data.get("contribution_patterns", {})
            result["recency_summary"]["github"] = github_data.get("recency_metadata", {}).get("activity_by_recency", {})
        else:
            print("❌ Failed to fetch GitHub data")
            result["meta"]["errors"] = ["github_fetch_failed"]
        
        # Step 2: Auto-detect social handles
        print("\n🔍 Step 2: Detecting social handles...")
        detected_twitter, detected_linkedin = self._detect_handles(github_data)
        
        twitter_handle = twitter_handle or detected_twitter
        linkedin_id = linkedin_id or detected_linkedin
        
        if twitter_handle:
            print(f"  ✓ Twitter: @{twitter_handle}")
        if linkedin_id:
            print(f"  ✓ LinkedIn: {linkedin_id}")
        
        # Store cross-references
        if github_data:
            result["identity"]["cross_references"] = github_data.get("cross_references", [])
        
        # Step 3: Fetch Twitter data (simulated)
        print("\n🐦 Step 3: Fetching Twitter data...")
        twitter_data = self._fetch_twitter(twitter_handle or github_username)
        
        if twitter_data:
            result["profiles"]["twitter"] = twitter_data
            result["meta"]["data_sources"].append("twitter_simulated")
            result["identity"]["verified_platforms"].append("twitter")
            result["recency_summary"]["twitter"] = twitter_data.get("recency_metadata", {}).get("activity_by_recency", {})
        
        # Step 4: Fetch LinkedIn data (simulated)
        print("\n💼 Step 4: Fetching LinkedIn data...")
        linkedin_data = self._fetch_linkedin(linkedin_id or github_username)
        
        if linkedin_data:
            result["profiles"]["linkedin"] = linkedin_data
            result["meta"]["data_sources"].append("linkedin_simulated")
            result["identity"]["verified_platforms"].append("linkedin")
            result["recency_summary"]["linkedin"] = linkedin_data.get("recency_metadata", {}).get("activity_by_recency", {})
        
        # Step 5: Build identity graph and calculate confidence
        print("\n🔗 Step 5: Building identity graph...")
        identity_graph = self._build_identity_graph(github_data, twitter_data, linkedin_data)
        confidence = identity_graph.calculate_cross_validation_score()
        
        result["identity"]["confidence_score"] = round(confidence, 3)
        print(f"  ✓ Identity confidence: {confidence:.1%}")
        
        # Step 6: Aggregate activity timeline
        print("\n📅 Step 6: Aggregating activity timeline...")
        result["activity_timeline"] = self._aggregate_activities(
            github_data, twitter_data, linkedin_data
        )
        print(f"  ✓ Total activities: {len(result['activity_timeline'])}")
        
        # Step 7: Calculate engagement metrics
        print("\n📈 Step 7: Calculating engagement metrics...")
        result["engagement_metrics"] = self._calculate_engagement_metrics(
            github_data, twitter_data, linkedin_data
        )
        
        # Step 8: Generate summary
        print("\n📋 Step 8: Generating summary...")
        result["summary"] = self._generate_summary(github_data, twitter_data, linkedin_data)
        
        # Step 9: Save to file
        output_filename = output_file or f"{github_username}_consolidated.json"
        output_path = self.output_dir / output_filename
        
        print(f"\n💾 Saving to: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        
        print("\n" + "=" * 60)
        print("✅ CONSOLIDATION COMPLETE")
        print(f"   • Platforms: {', '.join(result['identity']['verified_platforms'])}")
        print(f"   • Confidence: {confidence:.1%}")
        print(f"   • Activities: {len(result['activity_timeline'])}")
        print(f"   • Output: {output_path}")
        print("=" * 60 + "\n")
        
        return result
    
    def _fetch_github(self, username: str, use_simulated: bool = False) -> Optional[Dict]:
        """Fetch GitHub data (live or simulated)"""
        if use_simulated:
            return self.simulated_fetcher.fetch_github(username)
        return self.github_fetcher.fetch_full_profile(username)
    
    def _fetch_twitter(self, handle: str) -> Optional[Dict]:
        """Fetch Twitter data (simulated)"""
        return self.simulated_fetcher.fetch_twitter(handle)
    
    def _fetch_linkedin(self, identifier: str) -> Optional[Dict]:
        """Fetch LinkedIn data (simulated)"""
        return self.simulated_fetcher.fetch_linkedin(identifier)
    
    def _detect_handles(self, github_data: Optional[Dict]) -> Tuple[Optional[str], Optional[str]]:
        """
        Auto-detect Twitter and LinkedIn handles from GitHub cross-references.
        
        Returns: (twitter_handle, linkedin_id)
        """
        twitter = None
        linkedin = None
        
        if not github_data:
            return twitter, linkedin
        
        # Check profile for direct twitter_username
        twitter = github_data.get("profile", {}).get("twitter_username")
        
        # Check cross-references
        for ref in github_data.get("cross_references", []):
            platform = ref.get("platform", "").lower()
            identifier = ref.get("identifier")
            
            if platform == "twitter" and not twitter:
                twitter = identifier
            elif platform == "linkedin" and not linkedin:
                linkedin = identifier
        
        return twitter, linkedin
    
    def _build_identity_graph(
        self,
        github_data: Optional[Dict],
        twitter_data: Optional[Dict],
        linkedin_data: Optional[Dict]
    ) -> IdentityGraph:
        """Build IdentityGraph from all platform data"""
        graph = IdentityGraph()
        
        if github_data and github_data.get("fetch_status") == "success":
            node = self.github_fetcher.to_identity_node(github_data)
            graph.add_node(node)
        
        if twitter_data:
            node = self.simulated_fetcher.to_twitter_node(twitter_data)
            graph.add_node(node)
        
        if linkedin_data:
            node = self.simulated_fetcher.to_linkedin_node(linkedin_data)
            graph.add_node(node)
        
        return graph
    
    def _aggregate_activities(
        self,
        github_data: Optional[Dict],
        twitter_data: Optional[Dict],
        linkedin_data: Optional[Dict],
        limit: int = 100
    ) -> List[Dict]:
        """Aggregate all activities chronologically with recency weights"""
        activities = []
        
        # GitHub activities
        if github_data:
            for commit in github_data.get("commits", []):
                activities.append({
                    "platform": "github",
                    "type": "commit",
                    "content": commit.get("message", "")[:200],
                    "timestamp": commit.get("timestamp"),
                    "url": commit.get("url"),
                    "recency_bucket": commit.get("recency_bucket"),
                    "recency_weight": commit.get("recency_weight")
                })
            
            for comment in github_data.get("comments", []):
                activities.append({
                    "platform": "github",
                    "type": comment.get("type", "comment"),
                    "content": comment.get("body", comment.get("title", ""))[:200],
                    "timestamp": comment.get("timestamp"),
                    "url": comment.get("url"),
                    "recency_bucket": comment.get("recency_bucket"),
                    "recency_weight": comment.get("recency_weight")
                })
            
            for pr in github_data.get("pull_requests", []):
                activities.append({
                    "platform": "github",
                    "type": f"pr_{pr.get('action', 'activity')}",
                    "content": pr.get("title", "Pull Request"),
                    "timestamp": pr.get("timestamp"),
                    "url": pr.get("url"),
                    "recency_bucket": pr.get("recency_bucket"),
                    "recency_weight": pr.get("recency_weight")
                })
        
        # Twitter activities
        if twitter_data:
            for tweet in twitter_data.get("tweets", []):
                activities.append({
                    "platform": "twitter",
                    "type": "tweet",
                    "content": tweet.get("content", "")[:280],
                    "timestamp": tweet.get("timestamp"),
                    "url": tweet.get("url"),
                    "recency_bucket": tweet.get("recency_bucket"),
                    "recency_weight": tweet.get("recency_weight"),
                    "engagement": tweet.get("engagement", {})
                })
        
        # LinkedIn activities
        if linkedin_data:
            for post in linkedin_data.get("posts", []):
                activities.append({
                    "platform": "linkedin",
                    "type": "post",
                    "content": post.get("content", "")[:500],
                    "timestamp": post.get("timestamp"),
                    "url": post.get("url"),
                    "recency_bucket": post.get("recency_bucket"),
                    "recency_weight": post.get("recency_weight")
                })
        
        # Sort by timestamp (most recent first)
        activities.sort(
            key=lambda x: x.get("timestamp") or "1970-01-01",
            reverse=True
        )
        
        return activities[:limit]
    
    def _calculate_engagement_metrics(
        self,
        github_data: Optional[Dict],
        twitter_data: Optional[Dict],
        linkedin_data: Optional[Dict]
    ) -> Dict:
        """Calculate aggregate engagement metrics"""
        metrics = {
            "github": {},
            "twitter": {},
            "linkedin": {},
            "combined": {}
        }
        
        # GitHub metrics
        if github_data:
            profile = github_data.get("profile", {})
            metrics["github"] = {
                "followers": profile.get("followers", 0),
                "following": profile.get("following", 0),
                "public_repos": profile.get("public_repos", 0),
                "total_commits_3m": len(github_data.get("commits", [])),
                "total_comments_3m": len(github_data.get("comments", [])),
                "total_prs_3m": len(github_data.get("pull_requests", []))
            }
        
        # Twitter metrics
        if twitter_data:
            profile = twitter_data.get("profile", {})
            tweets = twitter_data.get("tweets", [])
            
            total_likes = sum(t.get("engagement", {}).get("likes", 0) for t in tweets)
            total_retweets = sum(t.get("engagement", {}).get("retweets", 0) for t in tweets)
            
            metrics["twitter"] = {
                "followers": profile.get("followers", 0),
                "following": profile.get("following", 0),
                "tweets_count": profile.get("tweets_count", 0),
                "avg_likes_per_tweet": round(total_likes / len(tweets), 1) if tweets else 0,
                "avg_retweets_per_tweet": round(total_retweets / len(tweets), 1) if tweets else 0
            }
        
        # LinkedIn metrics
        if linkedin_data:
            profile = linkedin_data.get("profile", {})
            metrics["linkedin"] = {
                "connections": profile.get("connections_count", 0),
                "headline": profile.get("headline")
            }
        
        # Combined metrics
        total_followers = (
            metrics["github"].get("followers", 0) +
            metrics["twitter"].get("followers", 0) +
            metrics["linkedin"].get("connections", 0)
        )
        
        metrics["combined"] = {
            "total_social_reach": total_followers,
            "platforms_active": len([p for p in [github_data, twitter_data, linkedin_data] if p])
        }
        
        return metrics
    
    def _generate_summary(
        self,
        github_data: Optional[Dict],
        twitter_data: Optional[Dict],
        linkedin_data: Optional[Dict]
    ) -> Dict:
        """Generate high-level profile summary"""
        summary = {
            "name": None,
            "bio": None,
            "location": None,
            "company": None,
            "top_languages": [],
            "top_repos": [],
            "primary_interests": [],
            "professional_focus": None
        }
        
        if github_data:
            profile = github_data.get("profile", {})
            summary["name"] = profile.get("name")
            summary["bio"] = profile.get("bio")
            summary["location"] = profile.get("location")
            summary["company"] = profile.get("company")
            
            # Extract top languages from repos
            languages = {}
            for repo in github_data.get("repositories", []):
                lang = repo.get("language")
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
            
            summary["top_languages"] = sorted(languages.keys(), key=lambda x: languages[x], reverse=True)[:5]
            
            # Top repos by stars
            repos = sorted(
                github_data.get("repositories", []),
                key=lambda r: r.get("stars", 0),
                reverse=True
            )[:5]
            summary["top_repos"] = [
                {"name": r.get("name"), "stars": r.get("stars")}
                for r in repos
            ]
            
            # Primary interests from starred repos
            topics = {}
            for repo in github_data.get("interests", []):
                for topic in repo.get("topics", []):
                    topics[topic] = topics.get(topic, 0) + 1
            
            summary["primary_interests"] = sorted(topics.keys(), key=lambda x: topics[x], reverse=True)[:10]
        
        # Use Twitter bio as fallback
        if not summary["bio"] and twitter_data:
            summary["bio"] = twitter_data.get("profile", {}).get("bio")
        
        # Professional focus from LinkedIn
        if linkedin_data:
            summary["professional_focus"] = linkedin_data.get("profile", {}).get("headline")
        
        return summary


# CLI interface
if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("NEXUS - Social Profile Consolidator")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage: python profile_consolidator.py <github_username> [options]")
        print("\nOptions:")
        print("  --twitter <handle>     Specify Twitter handle (optional)")
        print("  --linkedin <id>        Specify LinkedIn ID (optional)")
        print("  --output <filename>    Custom output filename")
        print("  --simulated            Use simulated GitHub data instead of live")
        print("\nExamples:")
        print("  python profile_consolidator.py kentcdodds")
        print("  python profile_consolidator.py torvalds --output linus.json")
        sys.exit(0)
    
    # Parse arguments
    github_username = sys.argv[1]
    twitter_handle = None
    linkedin_id = None
    output_file = None
    use_simulated = False
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--twitter" and i + 1 < len(sys.argv):
            twitter_handle = sys.argv[i + 1]
            i += 2
        elif arg == "--linkedin" and i + 1 < len(sys.argv):
            linkedin_id = sys.argv[i + 1]
            i += 2
        elif arg == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        elif arg == "--simulated":
            use_simulated = True
            i += 1
        else:
            i += 1
    
    # Run consolidation
    consolidator = ProfileConsolidator()
    result = consolidator.consolidate(
        github_username=github_username,
        twitter_handle=twitter_handle,
        linkedin_id=linkedin_id,
        output_file=output_file,
        use_simulated_github=use_simulated
    )
    
    print(f"\n✅ Profile consolidation complete!")
    print(f"   Identity confidence: {result['identity']['confidence_score']:.1%}")
