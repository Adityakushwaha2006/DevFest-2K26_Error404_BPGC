"""
NEXUS End-to-End Pipeline Test
Demonstrates the complete pipeline: Name → Discovery → Social + Misc → Unified JSON

Usage:
    python run_pipeline.py "Person Name" --company "Company" --role "Role"
    
Examples:
    python run_pipeline.py "Kent C. Dodds"
    python run_pipeline.py "Dan Abramov" --company "Meta"
    python run_pipeline.py "Evan You" --role "Creator of Vue.js"
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline_orchestrator import NexusOrchestrator


def run_full_pipeline(
    name: str,
    company: str = None,
    role: str = None,
    github: str = None,
    blog: str = None,
    hn: str = None
):
    """
    Run the complete NEXUS pipeline.
    
    Flow:
    1. SEARCH: Google CSE discovers social profiles from name
    2. SOCIAL: Fetch GitHub, Twitter, LinkedIn data  
    3. MISC: Fetch Stack Overflow, Blog, Hacker News data
    4. UNIFIED: Merge into single JSON ready for scoring
    """
    
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "NEXUS PIPELINE v2.0" + " " * 24 + "║")
    print("║" + " " * 10 + "Social Profile Intelligence System" + " " * 13 + "║")
    print("╚" + "═" * 58 + "╝")
    
    print(f"\n📋 INPUT:")
    print(f"   Name: {name}")
    if company:
        print(f"   Company: {company}")
    if role:
        print(f"   Role: {role}")
    if github:
        print(f"   GitHub (provided): {github}")
    if blog:
        print(f"   Blog (provided): {blog}")
    
    print("\n" + "─" * 60)
    
    # Initialize orchestrator
    orchestrator = NexusOrchestrator()
    
    # Run the full pipeline
    result = orchestrator.process_person(
        name=name,
        company=company,
        role=role,
        github_username=github,
        blog_url=blog,
        hackernews_username=hn,
        auto_discover=True  # Use Google CSE
    )
    
    # Output summary
    print("\n" + "═" * 60)
    print("📊 FINAL OUTPUT SUMMARY")
    print("═" * 60)
    
    unified = result.get("unified_profile", {})
    
    # Identity
    print(f"\n🪪 IDENTITY:")
    print(f"   Name: {unified.get('name', 'Unknown')}")
    social = result.get("social_profile") or {}
    identity = social.get("identity") or {}
    print(f"   Confidence: {identity.get('confidence_score', 0):.1%}")
    
    # Platforms discovered
    discovery = result.get("discovery") or {}
    platforms_found = discovery.get("platforms_found", [])
    print(f"\n🔍 DISCOVERY:")
    print(f"   Platforms found: {', '.join(platforms_found) if platforms_found else 'None (used provided handles)'}")
    
    # Social data
    if social:
        print(f"\n📱 SOCIAL DATA:")
        profiles = social.get("profiles") or {}
        gh = profiles.get("github") or {}
        if gh:
            profile = gh.get("profile") or {}
            print(f"   GitHub: {profile.get('login')} ({profile.get('followers', 0):,} followers)")
        tw = profiles.get("twitter")
        if tw:
            tw_profile = tw.get("profile") or {}
            print(f"   Twitter: @{tw_profile.get('username', 'N/A')}")
        li = profiles.get("linkedin")
        if li:
            li_profile = li.get("profile") or {}
            print(f"   LinkedIn: {li_profile.get('name', 'N/A')}")
    
    # Misc data
    misc = result.get("misc_profile") or {}
    if misc:
        print(f"\n📚 MISC DATA:")
        so = misc.get("stack_overflow")
        if so and so.get("fetch_status") == "success":
            rep = so.get("profile", {}).get("reputation", 0)
            tags = so.get("top_tags", [])[:3]
            tag_names = [t["tag_name"] for t in tags]
            print(f"   Stack Overflow: {rep:,} reputation | Top: {', '.join(tag_names)}")
        
        blog_data = misc.get("blog")
        if blog_data and blog_data.get("fetch_status") == "success":
            print(f"   Blog: {blog_data.get('post_count', 0)} recent posts")
        
        hn = misc.get("hackernews")
        if hn and hn.get("fetch_status") == "success":
            karma = hn.get("profile", {}).get("karma", 0)
            print(f"   Hacker News: {karma:,} karma")
    
    # Expertise
    expertise = unified.get("expertise", {})
    if expertise.get("top_technologies"):
        print(f"\n💡 EXPERTISE:")
        print(f"   Top Technologies: {', '.join(expertise['top_technologies'][:5])}")
    
    # Activity
    activity = unified.get("activity_timeline", [])
    print(f"\n📅 ACTIVITY:")
    print(f"   Total activities captured: {len(activity)}")
    
    # Output file
    safe_name = github or name.lower().replace(" ", "_").replace(".", "")
    output_path = Path(__file__).parent / "social_profiles" / f"{safe_name}_unified.json"
    
    print(f"\n💾 OUTPUT FILES:")
    print(f"   Unified: {output_path}")
    
    print("\n" + "═" * 60)
    print("✅ PIPELINE COMPLETE - Ready for Scoring Stage")
    print("═" * 60 + "\n")
    
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nQuick test examples:")
        print('  python run_pipeline.py "Kent C. Dodds"')
        print('  python run_pipeline.py "Linus Torvalds"')
        print('  python run_pipeline.py "Dan Abramov" --company Meta')
        sys.exit(0)
    
    # Parse arguments
    name = sys.argv[1]
    company = None
    role = None
    github = None
    blog = None
    hn = None
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--company" and i + 1 < len(sys.argv):
            company = sys.argv[i + 1]
            i += 2
        elif arg == "--role" and i + 1 < len(sys.argv):
            role = sys.argv[i + 1]
            i += 2
        elif arg == "--github" and i + 1 < len(sys.argv):
            github = sys.argv[i + 1]
            i += 2
        elif arg == "--blog" and i + 1 < len(sys.argv):
            blog = sys.argv[i + 1]
            i += 2
        elif arg == "--hn" and i + 1 < len(sys.argv):
            hn = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # Run the pipeline
    run_full_pipeline(
        name=name,
        company=company,
        role=role,
        github=github,
        blog=blog,
        hn=hn
    )
