"""
Demo: GitHub Search & Discovery Engine
Find people you don't know yet!
"""

import os
from search_engine import GitHubSearchEngine, DiscoveryEngine
from platform_fetchers import get_fetcher
from identity_node import Platform


def demo_user_search():
    """Demo: Search for developers by criteria"""
    print("=" * 70)
    print("NEXUS - GitHub Discovery Demo")
    print("=" * 70)
    print()
    
    # Initialize search engine
    github_token = os.getenv('GITHUB_TOKEN')
    search = GitHubSearchEngine(github_token)
    
    # Example 1: Find blockchain engineers
    print("🔍 Example 1: Find blockchain engineers in San Francisco")
    print("-" * 70)
    
    users = search.search_users(
        query="blockchain",
        location="San Francisco",
        min_followers=50,
        max_results=10
    )
    
    print(f"Found {len(users)} developers:\n")
    for i, user in enumerate(users[:5], 1):
        print(f"{i}. @{user['username']}")
        print(f"   Profile: {user['profile_url']}")
        print(f"   Match Score: {user['score']:.1f}")
        print()
    
    # Example 2: Find Python developers
    print("\n" + "=" * 70)
    print("🔍 Example 2: Find Python developers with 100+ followers")
    print("-" * 70)
    
    users = search.search_users(
        query="python developer",
        language="python",
        min_followers=100,
        max_results=10
    )
    
    print(f"Found {len(users)} developers:\n")
    for i, user in enumerate(users[:5], 1):
        print(f"{i}. @{user['username']} - {user['profile_url']}")
    
    # Example 3: Find machine learning researchers
    print("\n" + "=" * 70)
    print("🔍 Example 3: Find machine learning researchers")
    print("-" * 70)
    
    users = search.search_users(
        query="machine learning research",
        min_followers=200,
        min_repos=5,
        max_results=10
    )
    
    print(f"Found {len(users)} researchers:\n")
    for i, user in enumerate(users[:5], 1):
        print(f"{i}. @{user['username']}")
    
    print("\n" + "=" * 70)
    print("✅ Discovery Demo Complete!")
    print("=" * 70)


def demo_project_contributors():
    """Demo: Find contributors to popular projects"""
    print("\n" + "=" * 70)
    print("NEXUS - Project Contributors Discovery")
    print("=" * 70)
    print()
    
    github_token = os.getenv('GITHUB_TOKEN')
    search = GitHubSearchEngine(github_token)
    
    # Find React contributors
    print("🔍 Finding React ecosystem contributors...")
    print("-" * 70)
    
    repos = search.search_repositories(
        query="react",
        language="javascript",
        min_stars=1000,
        max_results=5
    )
    
    print(f"Top React projects:\n")
    for i, repo in enumerate(repos[:3], 1):
        print(f"{i}. {repo['full_name']} ⭐ {repo['stars']:,}")
        print(f"   {repo['description'][:60]}...")
        print()
    
    # Get contributors from top repo
    if repos:
        top_repo = repos[0]
        print(f"\n📊 Top contributors to {top_repo['full_name']}:\n")
        
        contributors = search.get_repo_contributors(
            top_repo['full_name'],
            max_contributors=10
        )
        
        for i, username in enumerate(contributors[:10], 1):
            print(f"{i}. @{username}")
    
    print("\n" + "=" * 70)
    print("✅ Contributors Discovery Complete!")
    print("=" * 70)


def demo_full_discovery_pipeline():
    """Demo: Search → Identity Resolution → Scoring"""
    print("\n" + "=" * 70)
    print("NEXUS - Full Discovery Pipeline")
    print("=" * 70)
    print()
    
    github_token = os.getenv('GITHUB_TOKEN')
    search = GitHubSearchEngine(github_token)
    github_fetcher = get_fetcher(Platform.GITHUB, github_token=github_token)
    
    # Step 1: Search
    print("Step 1: 🔍 Searching for 'web developers' in NYC...")
    print("-" * 70)
    
    users = search.search_users(
        query="web developer",
        location="NYC",
        min_followers=50,
        max_results=5
    )
    
    print(f"Found {len(users)} candidates\n")
    
    # Step 2: Fetch full profiles for top 3
    print("Step 2: 📡 Fetching detailed profiles...")
    print("-" * 70)
    
    for user in users[:3]:
        print(f"\nFetching @{user['username']}...")
        node = github_fetcher.fetch(user['username'])
        
        if node.fetch_status == 'success':
            print(f"  ✅ {node.get_name() or user['username']}")
            print(f"     Bio: {(node.get_bio() or 'No bio')[:60]}...")
            print(f"     Location: {node.get_location() or 'Unknown'}")
            print(f"     Activities: {len(node.activities)} events")
        else:
            print(f"  ⚠️  Failed: {node.error_message}")
    
    print("\n" + "=" * 70)
    print("✅ Full Pipeline Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    import sys
    
    choice = sys.argv[1] if len(sys.argv) > 1 else "1"
    
    if choice == "1":
        demo_user_search()
    elif choice == "2":
        demo_project_contributors()
    elif choice == "3":
        demo_full_discovery_pipeline()
    else:
        print("Usage:")
        print("  python demo_search.py 1  # User search demo")
        print("  python demo_search.py 2  # Project contributors demo")
        print("  python demo_search.py 3  # Full pipeline demo")
