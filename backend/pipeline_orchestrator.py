"""
NEXUS Pipeline Orchestrator
Master controller that runs the full pipeline:
1. Search-to-Sites: Discover platforms from name
2. Social-to-JSON: Fetch from GitHub, Twitter, LinkedIn
3. Misc-to-JSON: Fetch from Stack Overflow, blogs, HN
4. Unified Profile: Merge and prepare for scoring

This is the main entry point for the NEXUS data pipeline.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import pipeline components
from google_search import GoogleSearchEngine, MockProfileDiscovery, get_search_engine
from profile_consolidator import ProfileConsolidator
from misc_consolidator import MiscConsolidator


class NexusOrchestrator:
    """
    Master pipeline orchestrator.
    Coordinates all data fetching and consolidation.
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        google_api_key: Optional[str] = None,
        google_cse_id: Optional[str] = None,
        github_token: Optional[str] = None
    ):
        """
        Initialize orchestrator.
        
        Args:
            output_dir: Where to save output files
            google_api_key: Google CSE API key
            google_cse_id: Google CSE ID
            github_token: GitHub API token
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent / "social_profiles"
        
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.search_engine = get_search_engine(google_api_key, google_cse_id)
        self.social_consolidator = ProfileConsolidator(
            output_dir=str(self.output_dir),
            github_token=github_token
        )
        self.misc_consolidator = MiscConsolidator(output_dir=str(self.output_dir))
    
    def process_person(
        self,
        name: str,
        github_username: Optional[str] = None,
        twitter_handle: Optional[str] = None,
        linkedin_id: Optional[str] = None,
        stackoverflow_name: Optional[str] = None,
        blog_url: Optional[str] = None,
        hackernews_username: Optional[str] = None,
        company: Optional[str] = None,
        role: Optional[str] = None,
        auto_discover: bool = True
    ) -> Dict[str, Any]:
        """
        Process a person through the full NEXUS pipeline.
        
        Args:
            name: Person's full name
            github_username: Known GitHub username (optional)
            twitter_handle: Known Twitter handle (optional)
            linkedin_id: Known LinkedIn ID (optional)
            stackoverflow_name: SO display name (optional, defaults to name)
            blog_url: Personal blog URL (optional)
            hackernews_username: HN username (optional)
            company: Company for search context (optional)
            role: Role for search context (optional)
            auto_discover: Whether to use search to discover profiles
            
        Returns:
            Unified profile dict ready for scoring
        """
        print("\n" + "🌐" * 30)
        print("\n  NEXUS UNIFIED PIPELINE")
        print(f"  Target: {name}")
        print("\n" + "🌐" * 30)
        
        result = {
            "meta": {
                "pipeline_version": "2.0",
                "processed_at": datetime.now().isoformat(),
                "input": {
                    "name": name,
                    "company": company,
                    "role": role
                }
            },
            "discovery": None,
            "social_profile": None,
            "misc_profile": None,
            "unified_profile": None,
            "pipeline_status": "running"
        }
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 1: SEARCH TO SITES
        # ═══════════════════════════════════════════════════════════════
        if auto_discover and not github_username:
            print("\n" + "═" * 60)
            print("📍 STEP 1: SEARCH TO SITES")
            print("═" * 60)
            
            if isinstance(self.search_engine, GoogleSearchEngine) and self.search_engine.is_configured():
                discovery = self.search_engine.search_person_comprehensive(
                    name=name,
                    company=company,
                    role=role
                )
            else:
                discovery = self.search_engine.discover_profiles(name)
            
            result["discovery"] = discovery
            
            # Extract discovered profiles
            profiles = discovery.get("discovered_profiles", {})
            
            if not github_username and "github" in profiles:
                github_username = profiles["github"].get("identifier")
                print(f"   → Auto-discovered GitHub: {github_username}")
            
            if not twitter_handle and "twitter" in profiles:
                twitter_handle = profiles["twitter"].get("identifier")
                print(f"   → Auto-discovered Twitter: {twitter_handle}")
            
            if not linkedin_id and "linkedin" in profiles:
                linkedin_id = profiles["linkedin"].get("identifier")
                print(f"   → Auto-discovered LinkedIn: {linkedin_id}")
            
            if not blog_url and "blog" in profiles:
                blog_url = profiles["blog"].get("identifier")
                print(f"   → Auto-discovered Blog: {blog_url}")
        else:
            print("\n   [Skipping discovery - profiles provided]")
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 2: SOCIAL TO JSON
        # ═══════════════════════════════════════════════════════════════
        if github_username:
            print("\n" + "═" * 60)
            print("📱 STEP 2: SOCIAL TO JSON")
            print("═" * 60)
            
            social_profile = self.social_consolidator.consolidate(
                github_username=github_username,
                twitter_handle=twitter_handle,
                linkedin_id=linkedin_id,
                output_file=f"{github_username}_social.json"
            )
            
            result["social_profile"] = social_profile
        else:
            print("\n⚠️ No GitHub username - skipping social consolidation")
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 3: MISC TO JSON
        # ═══════════════════════════════════════════════════════════════
        print("\n" + "═" * 60)
        print("📚 STEP 3: MISC TO JSON")
        print("═" * 60)
        
        misc_profile = self.misc_consolidator.consolidate(
            name=name,
            stackoverflow_name=stackoverflow_name or name,
            blog_url=blog_url,
            hackernews_username=hackernews_username,
            output_file=f"{github_username or name.lower().replace(' ', '_')}_misc.json"
        )
        
        result["misc_profile"] = misc_profile
        
        # ═══════════════════════════════════════════════════════════════
        # STEP 4: UNIFIED PROFILE
        # ═══════════════════════════════════════════════════════════════
        print("\n" + "═" * 60)
        print("🔗 STEP 4: UNIFIED PROFILE")
        print("═" * 60)
        
        result["unified_profile"] = self._merge_profiles(
            name=name,
            social=result.get("social_profile"),
            misc=result.get("misc_profile"),
            discovery=result.get("discovery")
        )
        
        result["pipeline_status"] = "complete"
        
        # Save unified profile
        safe_name = github_username or name.lower().replace(" ", "_").replace(".", "")
        output_path = self.output_dir / f"{safe_name}_unified.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result["unified_profile"], f, indent=2, default=str)
        
        print(f"\n💾 Saved unified profile to: {output_path}")
        
        # Print summary
        self._print_summary(result)
        
        return result
    
    def _merge_profiles(
        self,
        name: str,
        social: Optional[Dict],
        misc: Optional[Dict],
        discovery: Optional[Dict]
    ) -> Dict[str, Any]:
        """Merge social and misc profiles into unified profile."""
        
        unified = {
            "name": name,
            "generated_at": datetime.now().isoformat(),
            "identity": {},
            "platforms": {},
            "expertise": {},
            "content": {},
            "activity_timeline": [],
            "recency_weighting": {},
            "scoring_ready": True
        }
        
        # From social profile
        if social:
            unified["identity"] = social.get("identity", {})
            unified["platforms"]["github"] = social.get("profiles", {}).get("github")
            unified["platforms"]["twitter"] = social.get("profiles", {}).get("twitter")
            unified["platforms"]["linkedin"] = social.get("profiles", {}).get("linkedin")
            unified["activity_timeline"].extend(social.get("activity_timeline", []))
            unified["recency_weighting"]["social"] = social.get("recency_summary", {})
            unified["name"] = social.get("summary", {}).get("name") or name
        
        # From misc profile
        if misc:
            unified["platforms"]["stackoverflow"] = misc.get("stack_overflow")
            unified["platforms"]["blog"] = misc.get("blog")
            unified["platforms"]["hackernews"] = misc.get("hackernews")
            unified["expertise"] = misc.get("expertise_summary", {})
            unified["content"] = misc.get("content_summary", {})
        
        # From discovery
        if discovery:
            unified["discovery_metadata"] = {
                "platforms_discovered": discovery.get("platforms_found", []),
                "search_status": discovery.get("search_status")
            }
        
        # Sort activity timeline
        unified["activity_timeline"].sort(
            key=lambda x: x.get("timestamp") or "",
            reverse=True
        )
        
        # Limit timeline
        unified["activity_timeline"] = unified["activity_timeline"][:100]
        
        return unified
    
    def _print_summary(self, result: Dict):
        """Print pipeline summary."""
        print("\n" + "🌐" * 30)
        print("\n  PIPELINE COMPLETE")
        print("\n" + "🌐" * 30)
        
        # Discovery summary
        if result.get("discovery"):
            platforms = result["discovery"].get("platforms_found", [])
            print(f"\n📍 Discovery: {len(platforms)} platforms found")
            for p in platforms:
                print(f"   • {p}")
        
        # Social summary
        if result.get("social_profile"):
            sp = result["social_profile"]
            confidence = sp.get("identity", {}).get("confidence_score", 0)
            print(f"\n📱 Social Profile:")
            print(f"   • Confidence: {confidence:.1%}")
            print(f"   • Activities: {len(sp.get('activity_timeline', []))}")
        
        # Misc summary
        if result.get("misc_profile"):
            mp = result["misc_profile"]
            sources = mp.get("meta", {}).get("sources_successful", [])
            print(f"\n📚 Misc Profile:")
            print(f"   • Sources: {', '.join(sources) or 'None'}")
            if mp.get("expertise_summary", {}).get("top_technologies"):
                techs = mp["expertise_summary"]["top_technologies"][:5]
                print(f"   • Top Tech: {', '.join(techs)}")
        
        # Unified summary
        if result.get("unified_profile"):
            up = result["unified_profile"]
            print(f"\n🔗 Unified Profile:")
            print(f"   • Ready for scoring: ✅")
            print(f"   • Total activities: {len(up.get('activity_timeline', []))}")
        
        print("\n" + "═" * 60)


# CLI
if __name__ == "__main__":
    import sys
    
    print("\n" + "═" * 60)
    print("NEXUS - Unified Pipeline Orchestrator")
    print("═" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage: python pipeline_orchestrator.py <name> [options]")
        print("\nOptions:")
        print("  --github <username>   GitHub username (skips discovery)")
        print("  --twitter <handle>    Twitter handle")
        print("  --linkedin <id>       LinkedIn ID")
        print("  --blog <url>          Blog URL")
        print("  --hn <username>       Hacker News username")
        print("  --company <name>      Company (for search context)")
        print("  --role <role>         Role (for search context)")
        print("  --no-discover         Skip auto-discovery")
        print("\nExamples:")
        print('  python pipeline_orchestrator.py "Kent C. Dodds"')
        print('  python pipeline_orchestrator.py "Kent C. Dodds" --github kentcdodds --blog https://kentcdodds.com/blog')
        print('  python pipeline_orchestrator.py "John Smith" --company Google --role Engineer')
        sys.exit(0)
    
    # Parse arguments
    name = sys.argv[1]
    github_username = None
    twitter_handle = None
    linkedin_id = None
    blog_url = None
    hn_username = None
    company = None
    role = None
    auto_discover = True
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--github" and i + 1 < len(sys.argv):
            github_username = sys.argv[i + 1]
            i += 2
        elif arg == "--twitter" and i + 1 < len(sys.argv):
            twitter_handle = sys.argv[i + 1]
            i += 2
        elif arg == "--linkedin" and i + 1 < len(sys.argv):
            linkedin_id = sys.argv[i + 1]
            i += 2
        elif arg == "--blog" and i + 1 < len(sys.argv):
            blog_url = sys.argv[i + 1]
            i += 2
        elif arg == "--hn" and i + 1 < len(sys.argv):
            hn_username = sys.argv[i + 1]
            i += 2
        elif arg == "--company" and i + 1 < len(sys.argv):
            company = sys.argv[i + 1]
            i += 2
        elif arg == "--role" and i + 1 < len(sys.argv):
            role = sys.argv[i + 1]
            i += 2
        elif arg == "--no-discover":
            auto_discover = False
            i += 1
        else:
            i += 1
    
    # Run pipeline
    orchestrator = NexusOrchestrator()
    result = orchestrator.process_person(
        name=name,
        github_username=github_username,
        twitter_handle=twitter_handle,
        linkedin_id=linkedin_id,
        blog_url=blog_url,
        hackernews_username=hn_username,
        company=company,
        role=role,
        auto_discover=auto_discover
    )
