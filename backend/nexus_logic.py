"""
NEXUS Logic Layer
Consolidated module for data processing, orchestration, and aggregation logic.

Includes:
1. ProfileConsolidator
2. MiscConsolidator
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# Import from the consolidated fetcher module
from nexus_fetch import (
    IdentityNode, IdentityGraph, Platform, ActivityEvent,
    ExtendedGitHubFetcher,
    SimulatedDataFetcher,
    StackOverflowFetcher,
    BlogFetcher, MediumFetcher,
    HackerNewsFetcher
)

# ==================================================================================
# 1. PROFILE CONSOLIDATOR
# ==================================================================================

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
        """
        print("\n" + "=" * 60)
        print(f"[*] PROFILE CONSOLIDATION PIPELINE")
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
        print("\n[>] Step 1: Fetching GitHub data...")
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
            print("[x] Failed to fetch GitHub data")
            result["meta"]["errors"] = ["github_fetch_failed"]
        
        # Step 2: Auto-detect social handles
        print("\n[>] Step 2: Detecting social handles...")
        detected_twitter, detected_linkedin = self._detect_handles(github_data)
        
        twitter_handle = twitter_handle or detected_twitter
        linkedin_id = linkedin_id or detected_linkedin
        
        if twitter_handle:
            print(f"  + Twitter: @{twitter_handle}")
        if linkedin_id:
            print(f"  + LinkedIn: {linkedin_id}")
        
        # Store cross-references
        if github_data:
            result["identity"]["cross_references"] = github_data.get("cross_references", [])
        
        # Step 3: Fetch Twitter data (simulated)
        print("\n[>] Step 3: Fetching Twitter data...")
        twitter_data = self._fetch_twitter(twitter_handle or github_username)
        
        if twitter_data:
            result["profiles"]["twitter"] = twitter_data
            result["meta"]["data_sources"].append("twitter_simulated")
            result["identity"]["verified_platforms"].append("twitter")
            result["recency_summary"]["twitter"] = twitter_data.get("recency_metadata", {}).get("activity_by_recency", {})
        
        # Step 4: Fetch LinkedIn data (simulated)
        print("\n[>] Step 4: Fetching LinkedIn data...")
        linkedin_data = self._fetch_linkedin(linkedin_id or github_username)
        
        if linkedin_data:
            result["profiles"]["linkedin"] = linkedin_data
            result["meta"]["data_sources"].append("linkedin_simulated")
            result["identity"]["verified_platforms"].append("linkedin")
            result["recency_summary"]["linkedin"] = linkedin_data.get("recency_metadata", {}).get("activity_by_recency", {})
        
        # Step 5: Build identity graph and calculate confidence
        print("\n[>] Step 5: Building identity graph...")
        identity_graph = self._build_identity_graph(github_data, twitter_data, linkedin_data)
        confidence = identity_graph.calculate_cross_validation_score()
        
        result["identity"]["confidence_score"] = round(confidence, 3)
        print(f"  + Identity confidence: {confidence:.1%}")
        
        # Step 6: Aggregate activity timeline
        print("\n[>] Step 6: Aggregating activity timeline...")
        result["activity_timeline"] = self._aggregate_activities(
            github_data, twitter_data, linkedin_data
        )
        print(f"  + Total activities: {len(result['activity_timeline'])}")
        
        # Step 7: Calculate engagement metrics
        print("\n[>] Step 7: Calculating engagement metrics...")
        result["engagement_metrics"] = self._calculate_engagement_metrics(
            github_data, twitter_data, linkedin_data
        )
        
        # Step 8: Generate summary
        print("\n[>] Step 8: Generating summary...")
        result["summary"] = self._generate_summary(github_data, twitter_data, linkedin_data)
        
        # Step 9: Save to file
        output_filename = output_file or f"{github_username}_consolidated.json"
        output_path = self.output_dir / output_filename
        
        print(f"\n[S] Saving to: {output_path}")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        
        print("\n" + "=" * 60)
        print("[OK] CONSOLIDATION COMPLETE")
        print(f"   * Platforms: {', '.join(result['identity']['verified_platforms'])}")
        print(f"   * Confidence: {confidence:.1%}")
        print(f"   * Activities: {len(result['activity_timeline'])}")
        print(f"   * Output: {output_path}")
        print("=" * 60 + "\n")
        
        return result
    
    def _fetch_github(self, username: str, use_simulated: bool = False) -> Optional[Dict]:
        if use_simulated:
            return self.simulated_fetcher.fetch_github(username)
        return self.github_fetcher.fetch_full_profile(username)
    
    def _fetch_twitter(self, handle: str) -> Optional[Dict]:
        return self.simulated_fetcher.fetch_twitter(handle)
    
    def _fetch_linkedin(self, identifier: str) -> Optional[Dict]:
        return self.simulated_fetcher.fetch_linkedin(identifier)
    
    def _detect_handles(self, github_data: Optional[Dict]) -> Tuple[Optional[str], Optional[str]]:
        twitter = None
        linkedin = None
        
        if not github_data:
            return twitter, linkedin
        
        twitter = github_data.get("profile", {}).get("twitter_username")
        
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
        activities = []
        
        if github_data:
            for commit in github_data.get("commits", []):
                activities.append({
                    "platform": "github",
                    "type": "commit",
                    "content": commit.get("message", "")[:200],
                    "timestamp": commit.get("timestamp"),
                    "url": commit.get("url"),
                })
        
        if twitter_data:
            for tweet in twitter_data.get("tweets", []):
                activities.append({
                    "platform": "twitter",
                    "type": "tweet",
                    "content": tweet.get("content", "")[:280],
                    "timestamp": tweet.get("timestamp"),
                })
        
        if linkedin_data:
            for post in linkedin_data.get("posts", []):
                activities.append({
                    "platform": "linkedin",
                    "type": "post",
                    "content": post.get("content", "")[:500],
                    "timestamp": post.get("timestamp"),
                })
        
        activities.sort(
            key=lambda x: x.get("timestamp") or "1970-01-01",
            reverse=True
        )
        return activities[:limit]
    
    def _calculate_engagement_metrics(self, github, twitter, linkedin) -> Dict:
        # Simplified for consolidated storage
        return {"combined": {}}
    
    def _generate_summary(self, github, twitter, linkedin) -> Dict:
        summary = {
            "name": None, "bio": None, "location": None,
            "company": None, "top_languages": [], "top_repos": []
        }
        if github:
            p = github.get("profile", {})
            summary.update({
                "name": p.get("name"), "bio": p.get("bio"),
                "location": p.get("location"), "company": p.get("company")
            })
        return summary


# ==================================================================================
# 2. MISC CONSOLIDATOR
# ==================================================================================

class MiscConsolidator:
    """
    Consolidates data from miscellaneous (non-social) sources
    into a unified misc_profile.json.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent / "social_profiles"
        self.output_dir.mkdir(exist_ok=True)
        
        self.stackoverflow = StackOverflowFetcher()
        self.blog = BlogFetcher()
        self.medium = MediumFetcher()
        self.hackernews = HackerNewsFetcher()
    
    def consolidate(
        self,
        name: str,
        stackoverflow_name: Optional[str] = None,
        blog_url: Optional[str] = None,
        medium_username: Optional[str] = None,
        hackernews_username: Optional[str] = None,
        output_file: Optional[str] = None
    ) -> Dict[str, Any]:
        
        print("\n" + "=" * 60)
        print("[*] MISC DATA CONSOLIDATION")
        print(f"   Target: {name}")
        print("=" * 60)
        
        result = {
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "target_name": name,
                "sources_attempted": [],
                "sources_successful": []
            },
            "stack_overflow": None,
            "blog": None,
            "medium": None,
            "hackernews": None,
            "expertise_summary": {},
            "content_summary": {}
        }
        
        # Stack Overflow
        print("\n[>] Stack Overflow...")
        result["meta"]["sources_attempted"].append("stack_overflow")
        so_name = stackoverflow_name or name
        so_data = self.stackoverflow.search_and_fetch(so_name)
        
        if so_data and so_data.get("fetch_status") == "success":
            result["stack_overflow"] = so_data
            result["meta"]["sources_successful"].append("stack_overflow")
        else:
             print("   [x] No Stack Overflow profile found")
             
        # Personal Blog
        if blog_url:
            print("\n[>] Personal Blog...")
            result["meta"]["sources_attempted"].append("blog")
            blog_data = self.blog.fetch_from_blog_url(blog_url)
            
            if blog_data.get("fetch_status") == "success":
                result["blog"] = blog_data
                result["meta"]["sources_successful"].append("blog")
        
        # Medium
        if medium_username:
            print("\n[>] Medium...")
            result["meta"]["sources_attempted"].append("medium")
            medium_data = self.medium.fetch_user_posts(medium_username)
            
            if medium_data.get("fetch_status") == "success":
                result["medium"] = medium_data
                result["meta"]["sources_successful"].append("medium")
        
        # Hacker News
        if hackernews_username:
            print("\n[>] Hacker News...")
            result["meta"]["sources_attempted"].append("hackernews")
            hn_data = self.hackernews.fetch_full_profile(hackernews_username)
            
            if hn_data.get("fetch_status") == "success":
                result["hackernews"] = hn_data
                result["meta"]["sources_successful"].append("hackernews")
        
        # Generate summaries
        print("\n[>] Generating summaries...")
        result["expertise_summary"] = self._generate_expertise_summary(result)
        result["content_summary"] = self._generate_content_summary(result)
        
        # Save to file
        safe_name = name.lower().replace(" ", "_").replace(".", "")
        output_filename = output_file or f"{safe_name}_misc.json"
        output_path = self.output_dir / output_filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        
        print("\n" + "=" * 60)
        print("[OK] MISC CONSOLIDATION COMPLETE")
        print(f"   Output: {output_path}")
        print("=" * 60 + "\n")
        
        return result

    def _generate_expertise_summary(self, data: Dict) -> Dict:
        """Generate summary of technical expertise."""
        summary = {"top_technologies": [], "expertise_indicators": []}
        # Simplified implementation
        if data.get("stack_overflow"):
             summary["expertise_indicators"].append("Stack Overflow User")
        return summary

    def _generate_content_summary(self, data: Dict) -> Dict:
        """Generate summary of content created."""
        summary = {"total_blog_posts": 0, "total_so_answers": 0, "total_hn_submissions": 0}
        if data.get("blog"): summary["total_blog_posts"] += len(data["blog"].get("posts", []))
        if data.get("medium"): summary["total_blog_posts"] += len(data["medium"].get("posts", []))
        if data.get("hackernews"): summary["total_hn_submissions"] = data["hackernews"]["profile"].get("total_submissions", 0)
        return summary
