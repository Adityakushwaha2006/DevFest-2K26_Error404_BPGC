"""
Demo: Scoring Engine - Momentum, Readiness, Win Probability
The "WHEN to connect" magic!
"""

import os
from platform_fetchers import get_fetcher
from identity_node import Platform
from scoring_engine import MomentumScorer, ReadinessScorer, WinProbabilityCalculator


def demo_momentum_scoring(username: str):
    """Demo: Calculate momentum score for a user"""
    print("=" * 70)
    print("NEXUS - Momentum Scoring Demo")
    print("=" * 70)
    print(f"\n🎯 Analyzing: @{username}\n")
    
    # Fetch user
    github_token = os.getenv('GITHUB_TOKEN')
    fetcher = get_fetcher(Platform.GITHUB, github_token=github_token)
    node = fetcher.fetch(username)
    
    if node.fetch_status != 'success':
        print(f"❌ Error: {node.error_message}")
        return
    
    print(f"✅ Profile: {node.get_name() or username}")
    print(f"   Bio: {(node.get_bio() or 'No bio')[:80]}...")
    print(f"   Activities fetched: {len(node.activities)}")
    print()
    
    # Calculate momentum
    scorer = MomentumScorer(decay_factor=0.8)
    momentum = scorer.calculate_momentum(node.activities)
    
    print("📊 MOMENTUM ANALYSIS")
    print("-" * 70)
    print(f"Momentum Score: {momentum}/100")
    print()
    
    if momentum >= 70:
        print("✅ Status: VERY ACTIVE")
        print("   This person is highly engaged right now!")
    elif momentum >= 40:
        print("⚡ Status: MODERATELY ACTIVE")
        print("   Good baseline activity level")
    else:
        print("⏸️  Status: LOW ACTIVITY")
        print("   Consider waiting for higher engagement")
    
    # Get activity bursts
    bursts = scorer.get_activity_burst_periods(node.activities)
    
    if bursts:
        print(f"\n🔥 Activity Bursts (Last 30 days):")
        for i, burst in enumerate(bursts[:5], 1):
            print(f"   {i}. {burst['date']}: {burst['activity_count']} events ({burst['intensity']} intensity)")
    else:
        print("\n   No significant activity bursts detected")
    
    print("\n" + "=" * 70)


def demo_win_probability(username: str):
    """Demo: Full win probability calculation"""
    print("\n" + "=" * 70)
    print("NEXUS - Win Probability Calculator")
    print("=" * 70)
    print(f"\n🎯 Target: @{username}\n")
    
    # Fetch user
    github_token = os.getenv('GITHUB_TOKEN')
    fetcher = get_fetcher(Platform.GITHUB, github_token=github_token)
    node = fetcher.fetch(username)
    
    if node.fetch_status != 'success':
        print(f"❌ Error: {node.error_message}")
        return
    
    print(f"✅ Profile: {node.get_name() or username}")
    print()
    
    # Calculate win probability
    calculator = WinProbabilityCalculator()
    result = calculator.calculate_win_probability(
        node,
        context_similarity=0.75  # Simulating 75% profile match
    )
    
    print("🎲 WIN PROBABILITY ANALYSIS")
    print("=" * 70)
    print(f"\n📊 Overall Success Probability: {result['probability']:.1f}%")
    print()
    print(f"📈 Component Scores:")
    print(f"   • Context Match:    {result['context_score']:.1f}/100")
    print(f"   • Timing/Momentum:  {result['momentum_score']:.1f}/100")
    print(f"   • Intent Signals:   {result['intent_score']:.1f}/100")
    print()
    print(f"💡 Recommendation: {result['recommendation']}")
    print(f"📝 Reasoning: {result['reasoning']}")
    
    # Predict best time
    best_time = calculator.predict_best_time(node)
    if best_time:
        if best_time == "now":
            print(f"\n⏰ Best Time to Connect: RIGHT NOW")
        else:
            print(f"\n⏰ Suggested Contact Date: {best_time}")
    
    print("\n" + "=" * 70)


def demo_comparison(username1: str, username2: str):
    """Demo: Compare two candidates"""
    print("\n" + "=" * 70)
    print("NEXUS - Candidate Comparison")
    print("=" * 70)
    print()
    
    github_token = os.getenv('GITHUB_TOKEN')
    fetcher = get_fetcher(Platform.GITHUB, github_token=github_token)
    calculator = WinProbabilityCalculator()
    
    # Fetch both users
    print(f"📡 Fetching profiles...")
    node1 = fetcher.fetch(username1)
    node2 = fetcher.fetch(username2)
    
    if node1.fetch_status != 'success' or node2.fetch_status != 'success':
        print("❌ Error fetching one or both profiles")
        return
    
    # Calculate scores
    result1 = calculator.calculate_win_probability(node1, context_similarity=0.7)
    result2 = calculator.calculate_win_probability(node2, context_similarity=0.7)
    
    # Display comparison
    print("\n" + "=" * 70)
    print(f"👤 Candidate 1: @{username1}")
    print("-" * 70)
    print(f"Win Probability: {result1['probability']:.1f}%")
    print(f"Momentum: {result1['momentum_score']:.1f}/100")
    print(f"Recommendation: {result1['recommendation']}")
    
    print("\n" + "=" * 70)
    print(f"👤 Candidate 2: @{username2}")
    print("-" * 70)
    print(f"Win Probability: {result2['probability']:.1f}%")
    print(f"Momentum: {result2['momentum_score']:.1f}/100")
    print(f"Recommendation: {result2['recommendation']}")
    
    print("\n" + "=" * 70)
    print("🏆 VERDICT")
    print("=" * 70)
    
    if result1['probability'] > result2['probability']:
        diff = result1['probability'] - result2['probability']
        print(f"✅ Contact @{username1} first ({diff:.1f}% higher win probability)")
    elif result2['probability'] > result1['probability']:
        diff = result2['probability'] - result1['probability']
        print(f"✅ Contact @{username2} first ({diff:.1f}% higher win probability)")
    else:
        print("🤝 Equal probability - contact either one!")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python demo_scoring.py momentum <username>")
        print("  python demo_scoring.py probability <username>")
        print("  python demo_scoring.py compare <username1> <username2>")
        print()
        print("Examples:")
        print("  python demo_scoring.py momentum torvalds")
        print("  python demo_scoring.py probability kentcdodds")
        print("  python demo_scoring.py compare torvalds kentcdodds")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "momentum" and len(sys.argv) >= 3:
        demo_momentum_scoring(sys.argv[2])
    
    elif command == "probability" and len(sys.argv) >= 3:
        demo_win_probability(sys.argv[2])
    
    elif command == "compare" and len(sys.argv) >= 4:
        demo_comparison(sys.argv[2], sys.argv[3])
    
    else:
        print("Invalid command or missing arguments")
