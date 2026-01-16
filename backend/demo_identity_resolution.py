"""
Demo script showing the node-based identity resolution system in action.
Run this to test the multi-platform data aggregation.
"""

import os
from datetime import datetime
from identity_node import IdentityGraph, Platform
from platform_fetchers import get_fetcher


def demo_identity_resolution(seed_username: str, seed_platform: Platform = Platform.GITHUB):
    """
    Demonstration of identity resolution starting from a single seed.
    
    Args:
        seed_username: The initial username/handle to start from
        seed_platform: Which platform the seed is from
    """
    print("=" * 60)
    print("NEXUS - Node-Based Identity Resolution Demo")
    print("=" * 60)
    print(f"\n🌱 Seed: {seed_platform.value}/{seed_username}\n")
    
    # Initialize identity graph
    graph = IdentityGraph()
    
    # Step 1: Fetch seed node
    print(f"📡 Step 1: Fetching {seed_platform.value} profile...")
    fetcher = get_fetcher(seed_platform, github_token=os.getenv('GITHUB_TOKEN'))
    seed_node = fetcher.fetch(seed_username)
    
    if seed_node.fetch_status != "success":
        print(f"❌ Failed to fetch seed node: {seed_node.error_message}")
        return
    
    print(f"✅ Fetched: {seed_node.get_name() or seed_username}")
    print(f"   Bio: {seed_node.get_bio()[:100] if seed_node.get_bio() else 'N/A'}...")
    print(f"   Activities: {len(seed_node.activities)} events")
    
    graph.add_node(seed_node)
    
    # Step 2: Discover cross-references
    print(f"\n🔍 Step 2: Discovering cross-platform references...")
    print(f"   Found {len(seed_node.cross_references)} cross-references:")
    
    for ref in seed_node.cross_references:
        print(f"      → {ref.platform.value}: {ref.identifier} (from {ref.source_field})")
    
    # Step 3: Fetch cross-referenced nodes
    print(f"\n📡 Step 3: Fetching cross-referenced profiles...")
    
    for cross_ref in seed_node.cross_references:
        try:
            print(f"   Fetching {cross_ref.platform.value}/{cross_ref.identifier}...")
            
            # Try to get fetcher - will raise ValueError if platform not supported
            try:
                ref_fetcher = get_fetcher(cross_ref.platform)
            except ValueError as e:
                print(f"   ⏭️  Skipped: Platform {cross_ref.platform.value} not currently supported")
                continue
            
            ref_node = ref_fetcher.fetch(cross_ref.identifier)
            
            if ref_node.fetch_status == "success":
                print(f"   ✅ Success: {ref_node.get_name() or cross_ref.identifier}")
                graph.add_node(ref_node)
            else:
                print(f"   ⚠️  Failed: {ref_node.error_message}")
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Step 4: Calculate cross-validation
    print(f"\n🎯 Step 4: Cross-validation analysis...")
    confidence = graph.calculate_cross_validation_score()
    print(f"   Overall Identity Confidence: {confidence:.2%}")
    
    if confidence > 0.7:
        print("   ✅ HIGH CONFIDENCE - Identity validated across platforms")
    elif confidence > 0.4:
        print("   ⚠️  MEDIUM CONFIDENCE - Partial validation")
    else:
        print("   ❌ LOW CONFIDENCE - Insufficient cross-validation")
    
    # Step 5: Synthesize unified profile
    print(f"\n🔨 Step 5: Synthesizing unified profile...")
    unified = graph.synthesize_profile()
    
    print(f"\n{'=' * 60}")
    print("UNIFIED PROFILE")
    print("=" * 60)
    print(f"Name: {unified.get('name')}")
    print(f"Location: {unified.get('location')}")
    print(f"Company: {unified.get('company')}")
    print(f"Confidence: {unified.get('overall_confidence', 0):.2%}")
    
    print(f"\nPlatforms Connected:")
    for platform, data in unified.get('platforms', {}).items():
        print(f"   • {platform}: {data['identifier']} (conf: {data['confidence']:.2f})")
    
    print(f"\nRecent Activity (Last 10 events):")
    for i, activity in enumerate(unified.get('aggregated_activity', [])[:10], 1):
        timestamp = datetime.fromisoformat(activity['timestamp'])
        print(f"   {i}. [{activity['platform']}] {activity['event_type']}: {activity['content'][:50]}...")
        print(f"      ⏱  {timestamp.strftime('%Y-%m-%d %H:%M')}")
    
    print(f"\n{'=' * 60}")
    print("Demo Complete!")
    print("=" * 60)
    
    return graph


def demo_github_to_multiplatform(github_username: str):
    """Convenience function for GitHub-seeded resolution"""
    return demo_identity_resolution(github_username, Platform.GITHUB)


if __name__ == "__main__":
    import sys
    
    # Example usage
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        # Default demo username (change this to test with real profiles)
        username = "torvalds"  # Linus Torvalds as example
        print("💡 No username provided, using demo: 'torvalds'")
        print("   Run with: python demo_identity_resolution.py <github_username>\n")
    
    try:
        graph = demo_github_to_multiplatform(username)
        
        # Optional: Save to JSON
        print("\n💾 Saving unified profile to 'unified_profile.json'...")
        import json
        with open('unified_profile.json', 'w') as f:
            json.dump(graph.to_dict(), f, indent=2)
        print("✅ Saved!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
