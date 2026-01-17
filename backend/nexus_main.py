"""
NEXUS Main Entry Point
Master controller that runs the full pipeline:
1. Search-to-Sites: Discover platforms from name (via nexus_search)
2. Social-to-JSON: Fetch from GitHub, Twitter, LinkedIn (via nexus_logic)
3. Misc-to-JSON: Fetch from Stack Overflow, blogs, HN (via nexus_logic)
4. Unified Profile: Merge and prepare for downstream use

NOTE: Scoring is NOT part of this pipeline. This only handles data fetching.

Usage:
  python nexus_main.py "Name" [options]
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import consolidated components
from nexus_search import GoogleSearchEngine, MockProfileDiscovery, get_search_engine
from nexus_logic import ProfileConsolidator, MiscConsolidator


class NexusOrchestrator:
    """
    Master pipeline orchestrator.
    Coordinates all data fetching and consolidation.
    Each step is wrapped in try/except for fault tolerance.
    """
    
    def __init__(
        self,
        output_dir: Optional[str] = None,
        google_api_key: Optional[str] = None,
        google_cse_id: Optional[str] = None,
        github_token: Optional[str] = None,
        enable_fallback: bool = True
    ):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent / "social_profiles"
        
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.search_engine = get_search_engine(
            google_api_key, 
            google_cse_id,
            enable_fallback=enable_fallback
        )
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
        """Process a person through the full NEXUS pipeline."""
        
        print("\n" + "=" * 60)
        print("  NEXUS UNIFIED PIPELINE v2.1 (Fault-Tolerant)")
        print(f"  Target: {name}")
        print("=" * 60)
        
        result = {
            "meta": {
                "pipeline_version": "2.1",
                "processed_at": datetime.now().isoformat(),
                "input": {
                    "name": name,
                    "company": company,
                    "role": role
                },
                "errors": []
            },
            "discovery": None,
            "social_profile": None,
            "misc_profile": None,
            "unified_profile": None,
            "pipeline_status": "running"
        }
        
        # ===================================================================
        # STEP 1: SEARCH TO SITES (Discovery)
        # ===================================================================
        if auto_discover and not github_username:
            print("\n" + "-" * 40)
            print("STEP 1: SEARCH TO SITES")
            print("-" * 40)
            
            try:
                if isinstance(self.search_engine, GoogleSearchEngine) and self.search_engine.is_configured():
                    discovery = self.search_engine.search_person_comprehensive(
                        name=name, company=company, role=role
                    )
                else:
                    discovery = self.search_engine.discover_profiles(name)
                
                result["discovery"] = discovery
                
                # Extract discovered profiles
                profiles = discovery.get("discovered_profiles", {})
                if not github_username and "github" in profiles:
                    github_username = profiles["github"].get("identifier")
                    print(f"   > Auto-discovered GitHub: {github_username}")
                if not twitter_handle and "twitter" in profiles:
                    twitter_handle = profiles["twitter"].get("identifier")
                    print(f"   > Auto-discovered Twitter: {twitter_handle}")
                if not linkedin_id and "linkedin" in profiles:
                    linkedin_id = profiles["linkedin"].get("identifier")
                    print(f"   > Auto-discovered LinkedIn: {linkedin_id}")
                if not blog_url and "blog" in profiles:
                    blog_url = profiles.get("blog", {}).get("identifier")
                    
            except Exception as e:
                print(f"[!] Discovery failed: {e}")
                result["meta"]["errors"].append(f"discovery_failed: {str(e)}")
                result["discovery"] = {"search_status": "error", "error": str(e)}
        else:
            print("\n   [Skipping discovery - profiles provided or disabled]")
        
        # ===================================================================
        # STEP 2: SOCIAL TO JSON
        # ===================================================================
        if github_username:
            print("\n" + "-" * 40)
            print("STEP 2: SOCIAL TO JSON")
            print("-" * 40)
            
            try:
                social_profile = self.social_consolidator.consolidate(
                    github_username=github_username,
                    twitter_handle=twitter_handle,
                    linkedin_id=linkedin_id,
                    output_file=f"{github_username}_social.json"
                )
                result["social_profile"] = social_profile
            except Exception as e:
                print(f"[!] Social consolidation failed: {e}")
                result["meta"]["errors"].append(f"social_failed: {str(e)}")
                result["social_profile"] = None
        else:
            print("\n[!] No GitHub username - skipping social consolidation")
        
        # ===================================================================
        # STEP 3: MISC TO JSON
        # ===================================================================
        print("\n" + "-" * 40)
        print("STEP 3: MISC TO JSON")
        print("-" * 40)
        
        try:
            misc_profile = self.misc_consolidator.consolidate(
                name=name,
                stackoverflow_name=stackoverflow_name or name,
                blog_url=blog_url,
                hackernews_username=hackernews_username,
                output_file=f"{github_username or name.lower().replace(' ', '_')}_misc.json"
            )
            result["misc_profile"] = misc_profile
        except Exception as e:
            print(f"[!] Misc consolidation failed: {e}")
            result["meta"]["errors"].append(f"misc_failed: {str(e)}")
            result["misc_profile"] = None
        
        # ===================================================================
        # STEP 4: UNIFIED PROFILE
        # ===================================================================
        print("\n" + "-" * 40)
        print("STEP 4: UNIFIED PROFILE")
        print("-" * 40)
        
        try:
            result["unified_profile"] = self._merge_profiles(
                name=name,
                social=result.get("social_profile"),
                misc=result.get("misc_profile"),
                discovery=result.get("discovery")
            )
            
            # Save unified profile
            safe_name = github_username or name.lower().replace(" ", "_").replace(".", "")
            output_path = self.output_dir / f"{safe_name}_unified.json"
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result["unified_profile"], f, indent=2, default=str)
            
            print(f"\n[+] Saved unified profile to: {output_path}")
        except Exception as e:
            print(f"[!] Unified profile generation failed: {e}")
            result["meta"]["errors"].append(f"unified_failed: {str(e)}")
        
        # Final status
        if result["meta"]["errors"]:
            result["pipeline_status"] = "partial_success"
        else:
            result["pipeline_status"] = "complete"
        
        self._print_summary(result)
        return result
    
    def _merge_profiles(self, name, social, misc, discovery) -> Dict:
        """Merge social and misc profiles into unified profile."""
        unified = {
            "name": name,
            "generated_at": datetime.now().isoformat(),
            "identity": {},
            "platforms": {},
            "expertise": {},
            "content": {},
            "activity_timeline": [],
            "recency_weighting": {}
        }
        
        if social:
            unified["identity"] = social.get("identity", {})
            unified["platforms"].update(social.get("profiles", {}))
            unified["activity_timeline"].extend(social.get("activity_timeline", []))
            unified["recency_weighting"]["social"] = social.get("recency_summary", {})
            unified["name"] = social.get("summary", {}).get("name") or name
        
        if misc:
            if misc.get("stack_overflow"): unified["platforms"]["stackoverflow"] = misc["stack_overflow"]
            if misc.get("blog"): unified["platforms"]["blog"] = misc["blog"]
            if misc.get("hackernews"): unified["platforms"]["hackernews"] = misc["hackernews"]
            unified["expertise"] = misc.get("expertise_summary", {})
            unified["content"] = misc.get("content_summary", {})
        
        if discovery:
            unified["discovery_metadata"] = {
                "platforms_discovered": discovery.get("platforms_found", []),
                "search_status": discovery.get("search_status")
            }
        
        # Sort and limit timeline
        unified["activity_timeline"].sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        unified["activity_timeline"] = unified["activity_timeline"][:100]
        
        return unified

    def _print_summary(self, result: Dict):
        print("\n" + "*" * 30)
        if result["pipeline_status"] == "complete":
            print("  PIPELINE COMPLETE")
        else:
            print("  PIPELINE PARTIAL SUCCESS")
            print(f"  Errors: {len(result['meta']['errors'])}")
        print("*" * 30)
        
        if result.get("discovery"):
            platforms = result["discovery"].get("platforms_found", [])
            print(f"\n[?] Discovery: {len(platforms)} platforms found")
        
        if result.get("social_profile"):
            conf = result["social_profile"].get("identity", {}).get("confidence_score", 0)
            print(f"\n[#] Social: Identity Confidence {conf:.1%}")
            
        print("\n" + "=" * 60)


if __name__ == "__main__":
    
    print("\n" + "=" * 60)
    print("NEXUS - Unified Pipeline Orchestrator")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage: python nexus_main.py <name> [options]")
        print("\nOptions:")
        print("  --github <username>   GitHub username (skips discovery)")
        print("  --twitter <handle>    Twitter handle")
        print("  --linkedin <id>       LinkedIn ID")
        print("  --so <name>           Stack Overflow display name")
        print("  --blog <url>          Blog URL")
        print("  --hn <username>       Hacker News username")
        print("  --company <name>      Company (for search context)")
        print("  --role <role>         Role (for search context)")
        print("  --no-discover         Skip auto-discovery")
        print("\nExamples:")
        print('  python nexus_main.py "Aditya"                     # Name only (uses discovery)')
        print('  python nexus_main.py "Aditya" --github adityauser # With GitHub')
        print('  python nexus_main.py "pg" --hn pg                 # With Hacker News')
        sys.exit(0)
    
    # Simple argument parsing
    name = sys.argv[1]
    args = {}
    i = 2
    while i < len(sys.argv):
        if sys.argv[i].startswith("--"):
            key = sys.argv[i].lstrip("-")
            if key == "no-discover":
                args["auto_discover"] = False
                i += 1
            elif i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
                args[key] = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        else:
            i += 1

    orchestrator = NexusOrchestrator(enable_fallback=True)
    orchestrator.process_person(
        name=name,
        github_username=args.get("github"),
        twitter_handle=args.get("twitter"),
        linkedin_id=args.get("linkedin"),
        stackoverflow_name=args.get("so"),
        blog_url=args.get("blog"),
        hackernews_username=args.get("hn"),
        company=args.get("company"),
        role=args.get("role"),
        auto_discover=args.get("auto_discover", True)
    )
