"""
Misc-to-JSON Consolidator
Aggregates supplementary data from non-social platforms.

Sources:
- Stack Overflow (reputation, badges, expertise)
- Personal blogs (RSS posts)
- Hacker News (karma, submissions)
- Medium (articles)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from stackoverflow_fetcher import StackOverflowFetcher
from blog_fetcher import BlogFetcher, MediumFetcher
from hackernews_fetcher import HackerNewsFetcher


class MiscConsolidator:
    """
    Consolidates data from miscellaneous (non-social) sources
    into a unified misc_profile.json.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize consolidator.
        
        Args:
            output_dir: Where to save output files. Default: backend/social_profiles/
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent / "social_profiles"
        
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize fetchers
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
        """
        Consolidate data from all miscellaneous sources.
        
        Args:
            name: Person's name (used for SO search if stackoverflow_name not provided)
            stackoverflow_name: Stack Overflow display name (optional)
            blog_url: Personal blog URL (optional)
            medium_username: Medium username (optional)
            hackernews_username: Hacker News username (optional)
            output_file: Custom output filename
            
        Returns:
            Consolidated misc profile dict
        """
        print("\n" + "=" * 60)
        print("📚 MISC DATA CONSOLIDATION")
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
        print("\n📊 Stack Overflow...")
        result["meta"]["sources_attempted"].append("stack_overflow")
        so_name = stackoverflow_name or name
        so_data = self.stackoverflow.search_and_fetch(so_name)
        
        if so_data and so_data.get("fetch_status") == "success":
            result["stack_overflow"] = so_data
            result["meta"]["sources_successful"].append("stack_overflow")
        
        # Personal Blog
        if blog_url:
            print("\n📝 Personal Blog...")
            result["meta"]["sources_attempted"].append("blog")
            blog_data = self.blog.fetch_from_blog_url(blog_url)
            
            if blog_data.get("fetch_status") == "success":
                result["blog"] = blog_data
                result["meta"]["sources_successful"].append("blog")
        
        # Medium
        if medium_username:
            print("\n📰 Medium...")
            result["meta"]["sources_attempted"].append("medium")
            medium_data = self.medium.fetch_user_posts(medium_username)
            
            if medium_data.get("fetch_status") == "success":
                result["medium"] = medium_data
                result["meta"]["sources_successful"].append("medium")
        
        # Hacker News
        if hackernews_username:
            print("\n🔶 Hacker News...")
            result["meta"]["sources_attempted"].append("hackernews")
            hn_data = self.hackernews.fetch_full_profile(hackernews_username)
            
            if hn_data.get("fetch_status") == "success":
                result["hackernews"] = hn_data
                result["meta"]["sources_successful"].append("hackernews")
        
        # Generate summaries
        print("\n📋 Generating summaries...")
        result["expertise_summary"] = self._generate_expertise_summary(result)
        result["content_summary"] = self._generate_content_summary(result)
        
        # Save to file
        safe_name = name.lower().replace(" ", "_").replace(".", "")
        output_filename = output_file or f"{safe_name}_misc.json"
        output_path = self.output_dir / output_filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, default=str)
        
        print("\n" + "=" * 60)
        print("✅ MISC CONSOLIDATION COMPLETE")
        print(f"   Sources: {len(result['meta']['sources_successful'])}/{len(result['meta']['sources_attempted'])}")
        print(f"   Output: {output_path}")
        print("=" * 60 + "\n")
        
        return result
    
    def _generate_expertise_summary(self, data: Dict) -> Dict:
        """Generate summary of technical expertise from all sources."""
        summary = {
            "top_technologies": [],
            "expertise_indicators": []
        }
        
        # From Stack Overflow
        if data.get("stack_overflow") and data["stack_overflow"].get("top_tags"):
            so_tags = [tag["tag_name"] for tag in data["stack_overflow"]["top_tags"][:10]]
            summary["top_technologies"].extend(so_tags)
            
            # Expertise level from reputation
            rep = data["stack_overflow"].get("profile", {}).get("reputation", 0)
            if rep > 100000:
                summary["expertise_indicators"].append("Stack Overflow Top Contributor (100k+ rep)")
            elif rep > 10000:
                summary["expertise_indicators"].append("Stack Overflow Expert (10k+ rep)")
            elif rep > 1000:
                summary["expertise_indicators"].append("Active Stack Overflow contributor")
        
        # From Hacker News
        if data.get("hackernews") and data["hackernews"].get("profile"):
            karma = data["hackernews"]["profile"].get("karma", 0)
            if karma > 10000:
                summary["expertise_indicators"].append("Hacker News veteran (10k+ karma)")
            elif karma > 1000:
                summary["expertise_indicators"].append("Active Hacker News community member")
        
        # Deduplicate technologies
        summary["top_technologies"] = list(dict.fromkeys(summary["top_technologies"]))
        
        return summary
    
    def _generate_content_summary(self, data: Dict) -> Dict:
        """Generate summary of content created."""
        summary = {
            "total_blog_posts": 0,
            "total_so_answers": 0,
            "total_hn_submissions": 0,
            "recent_topics": []
        }
        
        # Blog posts
        if data.get("blog") and data["blog"].get("posts"):
            summary["total_blog_posts"] = len(data["blog"]["posts"])
            # Extract topics from post titles
            for post in data["blog"]["posts"][:5]:
                if post.get("title"):
                    summary["recent_topics"].append(post["title"])
        
        # Medium posts
        if data.get("medium") and data["medium"].get("posts"):
            summary["total_blog_posts"] += len(data["medium"]["posts"])
        
        # Stack Overflow answers
        if data.get("stack_overflow") and data["stack_overflow"].get("profile"):
            summary["total_so_answers"] = data["stack_overflow"]["profile"].get("answer_count", 0)
        
        # HN submissions
        if data.get("hackernews") and data["hackernews"].get("profile"):
            summary["total_hn_submissions"] = data["hackernews"]["profile"].get("total_submissions", 0)
        
        return summary


# CLI
if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("NEXUS - Misc Data Consolidator")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage: python misc_consolidator.py <name> [options]")
        print("\nOptions:")
        print("  --so <name>          Stack Overflow display name")
        print("  --blog <url>         Personal blog URL")
        print("  --medium <username>  Medium username")
        print("  --hn <username>      Hacker News username")
        print("  --output <filename>  Custom output filename")
        print("\nExamples:")
        print('  python misc_consolidator.py "Kent C. Dodds" --blog https://kentcdodds.com/blog')
        print('  python misc_consolidator.py "Dan Abramov" --hn dan_abramov --blog https://overreacted.io')
        sys.exit(0)
    
    # Parse arguments
    name = sys.argv[1]
    so_name = None
    blog_url = None
    medium_username = None
    hn_username = None
    output_file = None
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--so" and i + 1 < len(sys.argv):
            so_name = sys.argv[i + 1]
            i += 2
        elif arg == "--blog" and i + 1 < len(sys.argv):
            blog_url = sys.argv[i + 1]
            i += 2
        elif arg == "--medium" and i + 1 < len(sys.argv):
            medium_username = sys.argv[i + 1]
            i += 2
        elif arg == "--hn" and i + 1 < len(sys.argv):
            hn_username = sys.argv[i + 1]
            i += 2
        elif arg == "--output" and i + 1 < len(sys.argv):
            output_file = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # Run consolidation
    consolidator = MiscConsolidator()
    result = consolidator.consolidate(
        name=name,
        stackoverflow_name=so_name,
        blog_url=blog_url,
        medium_username=medium_username,
        hackernews_username=hn_username,
        output_file=output_file
    )
