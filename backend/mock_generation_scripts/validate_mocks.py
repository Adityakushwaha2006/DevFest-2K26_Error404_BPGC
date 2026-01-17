"""
Validation Script for Mock Data
Verifies structure integrity and cross-reference correctness.
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from identity_node import IdentityNode, Platform



class MockDataValidator:
    """
    Validates mock data for structural integrity and cross-reference correctness.
    Run this after generating mocks to ensure nothing is broken.
    """
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_node(self, node: IdentityNode, platform_name: str) -> bool:
        """Validate a single IdentityNode"""
        self.errors = []
        self.warnings = []
        
        print(f"\n🔍 Validating {platform_name} node: {node.identifier}")
        print("-" * 50)
        
        # 1. Basic structure checks
        self._check_basic_structure(node)
        
        # 2. Platform-specific validation
        if node.platform == Platform.TWITTER:
            self._validate_twitter_node(node)
        elif node.platform == Platform.LINKEDIN:
            self._validate_linkedin_node(node)
        elif node.platform == Platform.GITHUB:
            self._validate_github_node(node)
        
        # 3. Cross-reference validation
        self._validate_cross_references(node)
        
        # 4. Activity validation
        self._validate_activities(node)
        
        # Print results
        self._print_results()
        
        return len(self.errors) == 0
    
    def validate_cross_platform_consistency(
        self, 
        github_node: IdentityNode,
        twitter_node: IdentityNode,
        linkedin_node: IdentityNode
    ) -> bool:
        """Validate that all nodes cross-reference correctly"""
        print("\n" + "=" * 60)
        print("🔗 CROSS-PLATFORM CONSISTENCY CHECK")
        print("=" * 60)
        
        self.errors = []
        self.warnings = []
        
        github_username = github_node.identifier
        
        # Check Twitter → GitHub reference
        twitter_refs_github = any(
            ref.platform == Platform.GITHUB and ref.identifier == github_username
            for ref in twitter_node.cross_references
        )
        
        if twitter_refs_github:
            print(f"✅ Twitter references GitHub ({github_username})")
        else:
            self.errors.append(f"Twitter does not reference GitHub username '{github_username}'")
        
        # Check LinkedIn → GitHub reference
        linkedin_refs_github = any(
            ref.platform == Platform.GITHUB and ref.identifier == github_username
            for ref in linkedin_node.cross_references
        )
        
        if linkedin_refs_github:
            print(f"✅ LinkedIn references GitHub ({github_username})")
        else:
            self.errors.append(f"LinkedIn does not reference GitHub username '{github_username}'")
        
        # Check name consistency
        names = [
            github_node.get_name(),
            twitter_node.get_name(),
            linkedin_node.get_name()
        ]
        
        # Filter out None values
        names = [n for n in names if n]
        
        if len(set(names)) == 1:
            print(f"✅ Names match across platforms: {names[0]}")
        elif len(names) > 0:
            self.warnings.append(f"Names differ across platforms: {names}")
        
        self._print_results()
        
        return len(self.errors) == 0
    
    def _check_basic_structure(self, node: IdentityNode):
        """Check basic required fields"""
        if not node.identifier:
            self.errors.append("Missing identifier")
        
        if not node.platform:
            self.errors.append("Missing platform")
        
        if node.fetch_status != "success":
            self.errors.append(f"Fetch status is not 'success': {node.fetch_status}")
        
        if not node.data:
            self.warnings.append("Node data is empty")
        
        if node.confidence_score < 0 or node.confidence_score > 1:
            self.errors.append(f"Invalid confidence score: {node.confidence_score}")
    
    def _validate_twitter_node(self, node: IdentityNode):
        """Twitter-specific validation"""
        data = node.data
        
        required_fields = ['name', 'bio', 'followers', 'following']
        for field in required_fields:
            if field not in data:
                self.warnings.append(f"Missing Twitter field: {field}")
        
        # Check follower/following are numbers
        if 'followers' in data and not isinstance(data['followers'], (int, float)):
            self.errors.append("followers should be a number")
        
        if 'following' in data and not isinstance(data['following'], (int, float)):
            self.errors.append("following should be a number")
        
        # Check bio length (Twitter limit)
        if 'bio' in data and len(str(data['bio'])) > 160:
            self.warnings.append(f"Twitter bio exceeds 160 chars: {len(data['bio'])} chars")
    
    def _validate_linkedin_node(self, node: IdentityNode):
        """LinkedIn-specific validation"""
        data = node.data
        
        required_fields = ['name', 'headline', 'location']
        for field in required_fields:
            if field not in data:
                self.warnings.append(f"Missing LinkedIn field: {field}")
        
        # Check for experience array
        if 'experience' not in data:
            self.warnings.append("Missing experience history")
        elif not isinstance(data['experience'], list):
            self.errors.append("experience should be a list")
        
        # Check for skills
        if 'skills' not in data:
            self.warnings.append("Missing skills")
    
    def _validate_github_node(self, node: IdentityNode):
        """GitHub-specific validation"""
        data = node.data
        
        required_fields = ['login', 'type']
        for field in required_fields:
            if field not in data:
                self.errors.append(f"Missing critical GitHub field: {field}")
    
    def _validate_cross_references(self, node: IdentityNode):
        """Validate cross-references"""
        if not node.cross_references:
            self.warnings.append("No cross-references found")
            return
        
        for ref in node.cross_references:
            if not ref.identifier:
                self.errors.append(f"Cross-reference to {ref.platform} missing identifier")
            
            if not ref.source_field:
                self.warnings.append(f"Cross-reference to {ref.platform} missing source_field")
    
    def _validate_activities(self, node: IdentityNode):
        """Validate activity events"""
        if not node.activities:
            self.warnings.append("No activities found")
            return
        
        for i, activity in enumerate(node.activities):
            if not activity.content:
                self.warnings.append(f"Activity {i} has empty content")
            
            if not activity.timestamp:
                self.errors.append(f"Activity {i} missing timestamp")
            
            if activity.timestamp and activity.timestamp > datetime.now():
                self.errors.append(f"Activity {i} has future timestamp: {activity.timestamp}")
    
    def _print_results(self):
        """Print validation results"""
        print()
        if self.errors:
            print(f"❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ All checks passed!")
        elif not self.errors:
            print(f"\n✅ Valid (with {len(self.warnings)} warnings)")
        else:
            print(f"\n❌ INVALID ({len(self.errors)} errors)")


def run_validation_suite(github_username: str = None):
    """Run full validation on generated mock data"""
    import os
    from platform_fetchers import get_fetcher
    from mock_generators import MockTwitterGenerator, MockLinkedInGenerator
    
    print("=" * 60)
    print("NEXUS - Mock Data Validation Suite")
    print("=" * 60)
    
    # Use default username if not provided
    if not github_username:
        github_username = "torvalds"
        print(f"Using default username: {github_username}")
    
    validator = MockDataValidator()
    
    # 1. Fetch real GitHub data
    print(f"\n📡 Fetching GitHub profile: {github_username}")
    github_fetcher = get_fetcher(Platform.GITHUB, github_token=os.getenv('GITHUB_TOKEN'))
    github_node = github_fetcher.fetch(github_username)
    
    if github_node.fetch_status != "success":
        print(f"❌ Failed to fetch GitHub: {github_node.error_message}")
        return False
    
    # Validate GitHub node
    github_valid = validator.validate_node(github_node, "GitHub")
    
    # 2. Generate and validate Twitter mock
    print(f"\n🐦 Generating Twitter mock...")
    twitter_gen = MockTwitterGenerator()
    twitter_node = twitter_gen.generate_from_github(github_node)
    twitter_valid = validator.validate_node(twitter_node, "Twitter")
    
    # 3. Generate and validate LinkedIn mock
    print(f"\n💼 Generating LinkedIn mock...")
    linkedin_gen = MockLinkedInGenerator()
    linkedin_node = linkedin_gen.generate_from_github(github_node)
    linkedin_valid = validator.validate_node(linkedin_node, "LinkedIn")
    
    # 4. Cross-platform consistency check
    cross_platform_valid = validator.validate_cross_platform_consistency(
        github_node, twitter_node, linkedin_node
    )
    
    # Final summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    print(f"GitHub:          {'✅ Valid' if github_valid else '❌ Invalid'}")
    print(f"Twitter Mock:    {'✅ Valid' if twitter_valid else '❌ Invalid'}")
    print(f"LinkedIn Mock:   {'✅ Valid' if linkedin_valid else '❌ Invalid'}")
    print(f"Cross-Platform:  {'✅ Valid' if cross_platform_valid else '❌ Invalid'}")
    print("=" * 60)
    
    all_valid = github_valid and twitter_valid and linkedin_valid and cross_platform_valid
    
    if all_valid:
        print("🎉 All validations passed!")
    else:
        print("⚠️  Some validations failed. Check output above.")
    
    return all_valid


if __name__ == "__main__":
    import sys
    
    username = sys.argv[1] if len(sys.argv) > 1 else None
    run_validation_suite(username)
