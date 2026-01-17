"""
Demo: Full Mock Generation Pipeline with Checkpoint Support
Shows the complete flow from GitHub → Mock Twitter/LinkedIn with resumption capability
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from identity_node import IdentityGraph, Platform
from platform_fetchers import get_fetcher
from scoring_engine import WinProbabilityCalculator
from mock_generators import (
    MockTwitterGenerator, 
    MockLinkedInGenerator, 
    CheckpointManager,
    RateLimitError,
    generate_mock_profiles_batch
)


def demo_single_user(github_username: str):
    """
    Demonstrate the complete pipeline for a single user with checkpoint support.
    """
    print("=" * 70)
    print("NEXUS - Mock Generation Pipeline (with Checkpoints)")
    print("=" * 70)
    print(f"\n🎯 Target: {github_username}\n")
    
    # Initialize checkpoint manager
    checkpoint_mgr = CheckpointManager()
    
    # Check pending work
    pending = checkpoint_mgr.get_pending_platforms(github_username, ["twitter", "linkedin"])
    if pending:
        print(f"📋 Pending platforms: {pending}")
    else:
        print(f"✅ All platforms already checkpointed for {github_username}")
        print("   Use --force to regenerate")
    
    # Initialize graph
    graph = IdentityGraph()
    
    # ================================================================
    # STEP 1: Fetch Real GitHub Data
    # ================================================================
    print("\n📡 Step 1: Fetching real GitHub data...")
    print("-" * 70)
    
    github_fetcher = get_fetcher(Platform.GITHUB, github_token=os.getenv('GITHUB_TOKEN'))
    github_node = github_fetcher.fetch(github_username)
    
    if github_node.fetch_status != "success":
        print(f"❌ Failed: {github_node.error_message}")
        return
    
    print(f"✅ GitHub Profile:")
    print(f"   Name: {github_node.get_name()}")
    print(f"   Bio: {(github_node.get_bio() or 'N/A')[:80]}...")
    print(f"   Location: {github_node.get_location() or 'Unknown'}")
    print(f"   Company: {github_node.get_company() or 'N/A'}")
    print(f"   Activities: {len(github_node.activities)} events")
    
    graph.add_node(github_node)
    
    # ================================================================
    # STEP 2: Generate Mock Twitter (with checkpoint)
    # ================================================================
    print(f"\n🐦 Step 2: Generating mock Twitter profile...")
    print("-" * 70)
    
    try:
        twitter_gen = MockTwitterGenerator(checkpoint_manager=checkpoint_mgr)
        twitter_node = twitter_gen.generate_from_github(github_node)
        
        print(f"✅ Twitter Profile:")
        print(f"   Name: {twitter_node.data.get('name', 'N/A')}")
        print(f"   Bio: {str(twitter_node.data.get('bio', 'N/A'))[:80]}...")
        print(f"   Followers: {twitter_node.data.get('followers', 0):,}")
        print(f"   Tweets generated: {len(twitter_node.activities)}")
        
        if twitter_node.activities:
            print(f"\n   📝 Sample Tweets:")
            for tweet in twitter_node.activities[:3]:
                print(f"      • {tweet.content[:70]}...")
                print(f"        ❤️ {tweet.metadata.get('likes', 0)} | 🔄 {tweet.metadata.get('retweets', 0)}")
        
        graph.add_node(twitter_node)
        
    except RateLimitError:
        print("\n⚠️ Rate limit hit during Twitter generation")
        print("💡 Switch API key and re-run to continue from checkpoint")
        return
    
    # ================================================================
    # STEP 3: Generate Mock LinkedIn (with checkpoint)
    # ================================================================
    print(f"\n💼 Step 3: Generating mock LinkedIn profile...")
    print("-" * 70)
    
    try:
        linkedin_gen = MockLinkedInGenerator(checkpoint_manager=checkpoint_mgr)
        linkedin_node = linkedin_gen.generate_from_github(github_node)
        
        print(f"✅ LinkedIn Profile:")
        print(f"   Name: {linkedin_node.data.get('name', 'N/A')}")
        print(f"   Headline: {linkedin_node.data.get('headline', 'N/A')}")
        print(f"   Location: {linkedin_node.data.get('location', 'N/A')}")
        print(f"   Connections: {linkedin_node.data.get('connections', 0):,}")
        
        experience = linkedin_node.data.get('experience', [])
        if experience:
            print(f"\n   💼 Experience:")
            for job in experience[:2]:
                if isinstance(job, dict):
                    print(f"      • {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
        
        skills = linkedin_node.data.get('skills', [])
        if skills:
            skill_names = [s.get('name', s) if isinstance(s, dict) else s for s in skills[:5]]
            print(f"\n   🎯 Skills: {', '.join(skill_names)}")
        
        graph.add_node(linkedin_node)
        
    except RateLimitError:
        print("\n⚠️ Rate limit hit during LinkedIn generation")
        print("💡 Switch API key and re-run to continue from checkpoint")
        return
    
    # ================================================================
    # STEP 4: Cross-Validation & Scoring
    # ================================================================
    print(f"\n🔗 Step 4: Cross-platform validation...")
    print("-" * 70)
    
    confidence = graph.calculate_cross_validation_score()
    print(f"📊 Cross-Validation: {confidence:.2%} confidence")
    
    # Scoring
    print(f"\n📈 Step 5: Calculating win probability...")
    print("-" * 70)
    
    calculator = WinProbabilityCalculator()
    
    all_activities = []
    for node in graph.nodes.values():
        all_activities.extend(node.activities)
    
    combined_node = github_node
    combined_node.activities = all_activities
    
    result = calculator.calculate_win_probability(combined_node, context_similarity=0.7)
    
    print(f"🎲 Win Probability: {result['probability']:.1f}%")
    print(f"   Momentum: {result['momentum_score']:.1f}/100")
    print(f"   Intent: {result['intent_score']:.1f}/100")
    print(f"   💡 {result['recommendation']}")
    
    # ================================================================
    # STEP 6: Export to simulated_data folder
    # ================================================================
    print(f"\n📦 Step 6: Exporting to simulated_data/...")
    print("-" * 70)
    
    from simulated_data_export import SimulatedDataExporter, SimulatedDataValidator
    
    # Save GitHub checkpoint first
    github_checkpoint_data = {
        "profile": github_node.data,
        "activities": [
            {
                "type": act.event_type,
                "content": act.content,
                "timestamp": act.timestamp.isoformat() if act.timestamp else None,
                "url": act.url,
                "metadata": act.metadata
            }
            for act in github_node.activities
        ]
    }
    checkpoint_mgr.save_checkpoint(github_username, "github", github_checkpoint_data)
    
    # Export to simulated_data
    exporter = SimulatedDataExporter()
    files = exporter.export_complete_profile(github_node, twitter_node, linkedin_node)
    
    # ================================================================
    # STEP 7: Validate exported data
    # ================================================================
    print(f"\n🔍 Step 7: Validating exported data...")
    print("-" * 70)
    
    validator = SimulatedDataValidator()
    valid = validator.validate_all()
    
    # ================================================================
    # FINAL: Summary
    # ================================================================
    print(f"\n" + "=" * 70)
    print("✅ GENERATION COMPLETE")
    print("=" * 70)
    print(f"\n📁 Checkpoints: checkpoints/")
    print(f"   - {github_username}_github.json")
    print(f"   - {github_username}_twitter.json")
    print(f"   - {github_username}_linkedin.json")
    print(f"\n📁 Exported data: simulated_data/")
    for platform, filename in files.items():
        print(f"   - {filename}")
    
    if valid:
        print(f"\n✅ All data validated successfully!")
    else:
        print(f"\n⚠️ Validation found issues (see above)")
    
    return graph


def demo_batch(usernames: list):
    """Process multiple users with checkpoint support"""
    print("=" * 70)
    print("NEXUS - Batch Mock Generation")
    print("=" * 70)
    print(f"\n📋 Users to process: {usernames}\n")
    
    results = generate_mock_profiles_batch(usernames)
    
    print("\n" + "=" * 70)
    print("BATCH SUMMARY")
    print("=" * 70)
    
    for username, data in results.items():
        platforms = [p for p in data.keys() if p != "github"]
        print(f"  {username}: {', '.join(platforms) if platforms else 'pending'}")


def run_export():
    """Export all completed checkpoints to simulated_data"""
    from checkpoint_recovery import CheckpointRecovery
    
    recovery = CheckpointRecovery()
    status = recovery.get_status()
    
    if status["complete_profiles"]:
        print(f"📦 Exporting {len(status['complete_profiles'])} complete profiles...")
        finalized = recovery.finalize_complete_profiles()
        print(f"✅ Exported: {finalized}")
    else:
        print("No complete profiles to export")


def run_recover():
    """Run checkpoint recovery procedure"""
    from checkpoint_recovery import recovery_procedure
    recovery_procedure()


def run_validate():
    """Validate simulated data"""
    from simulated_data_export import validate_simulated_data
    validate_simulated_data()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--batch":
            usernames = sys.argv[2:] if len(sys.argv) > 2 else ["torvalds", "gaearon"]
            demo_batch(usernames)
        elif sys.argv[1] == "--clear":
            mgr = CheckpointManager()
            if len(sys.argv) > 2:
                mgr.clear_checkpoints(sys.argv[2])
            else:
                mgr.clear_checkpoints()
        elif sys.argv[1] == "--export":
            run_export()
        elif sys.argv[1] == "--recover":
            run_recover()
        elif sys.argv[1] == "--validate":
            run_validate()
        else:
            demo_single_user(sys.argv[1])
    else:
        print("Usage:")
        print("  python demo_mock_generation.py <github_username>  # Generate profiles")
        print("  python demo_mock_generation.py --batch user1 user2 # Batch mode")
        print("  python demo_mock_generation.py --export            # Export completed")
        print("  python demo_mock_generation.py --recover           # Recovery procedure")
        print("  python demo_mock_generation.py --validate          # Validate exports")
        print("  python demo_mock_generation.py --clear [username]  # Clear checkpoints")
        print()
        demo_single_user("kentcdodds")
