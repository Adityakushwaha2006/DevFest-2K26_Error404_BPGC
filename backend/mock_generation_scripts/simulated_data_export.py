"""
Simulated Data Export System
Exports generated profiles to structured JSON files with cross-links.

Output Structure:
  simulated_data/
    ├── {name}_github.json
    ├── {name}_twitter.json
    ├── {name}_linkedin.json
    └── manifest.json  (index of all profiles)
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from identity_node import IdentityNode, Platform



class SimulatedDataExporter:
    """
    Exports generated mock data to structured JSON files.
    Each platform gets its own file with cross-links to other platforms.
    """
    
    def __init__(self, output_dir: str = "simulated_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.manifest: Dict[str, Any] = self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        """Load or create manifest file"""
        manifest_path = self.output_dir / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "profiles": {}
        }
    
    def _save_manifest(self):
        """Save manifest file"""
        self.manifest["updated_at"] = datetime.now().isoformat()
        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.manifest, f, indent=2)
    
    def _get_safe_name(self, name: str) -> str:
        """Convert name to safe filename"""
        return name.lower().replace(" ", "_").replace(".", "_")[:50]
    
    def export_github(self, node: IdentityNode) -> str:
        """Export GitHub profile to JSON"""
        safe_name = self._get_safe_name(node.identifier)
        filename = f"{safe_name}_github.json"
        
        # Build structured data with timestamps
        activities = []
        for act in node.activities:
            activities.append({
                "type": act.event_type,
                "content": act.content,
                "timestamp": act.timestamp.isoformat() if act.timestamp else None,
                "date": act.timestamp.strftime("%Y-%m-%d") if act.timestamp else None,
                "time": act.timestamp.strftime("%H:%M:%S") if act.timestamp else None,
                "url": act.url,
                "metadata": act.metadata
            })
        
        export_data = {
            "platform": "github",
            "identifier": node.identifier,
            "profile": node.data,
            "activities": activities,
            "cross_references": {
                "twitter": f"{safe_name}_twitter.json",
                "linkedin": f"{safe_name}_linkedin.json"
            },
            "confidence_score": node.confidence_score,
            "exported_at": datetime.now().isoformat(),
            "fetch_status": node.fetch_status
        }
        
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Exported: {filename}")
        return filename
    
    def export_twitter(self, node: IdentityNode) -> str:
        """Export Twitter profile to JSON"""
        safe_name = self._get_safe_name(node.identifier)
        filename = f"{safe_name}_twitter.json"
        
        # Build structured tweets with full timestamps
        tweets = []
        for act in node.activities:
            tweets.append({
                "type": act.event_type,
                "content": act.content,
                "timestamp": act.timestamp.isoformat() if act.timestamp else None,
                "date": act.timestamp.strftime("%Y-%m-%d") if act.timestamp else None,
                "time": act.timestamp.strftime("%H:%M:%S") if act.timestamp else None,
                "day_of_week": act.timestamp.strftime("%A") if act.timestamp else None,
                "url": act.url,
                "engagement": {
                    "likes": act.metadata.get("likes", 0),
                    "retweets": act.metadata.get("retweets", 0),
                    "replies": act.metadata.get("replies", 0)
                }
            })
        
        export_data = {
            "platform": "twitter",
            "identifier": node.identifier,
            "profile": node.data,
            "tweets": tweets,
            "tweet_count": len(tweets),
            "cross_references": {
                "github": f"{safe_name}_github.json",
                "linkedin": f"{safe_name}_linkedin.json"
            },
            "confidence_score": node.confidence_score,
            "exported_at": datetime.now().isoformat(),
            "is_simulated": True
        }
        
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Exported: {filename}")
        return filename
    
    def export_linkedin(self, node: IdentityNode) -> str:
        """Export LinkedIn profile to JSON"""
        safe_name = self._get_safe_name(node.identifier)
        filename = f"{safe_name}_linkedin.json"
        
        # Build structured posts with timestamps
        posts = []
        for act in node.activities:
            posts.append({
                "type": act.event_type,
                "content": act.content,
                "timestamp": act.timestamp.isoformat() if act.timestamp else None,
                "date": act.timestamp.strftime("%Y-%m-%d") if act.timestamp else None,
                "time": act.timestamp.strftime("%H:%M:%S") if act.timestamp else None,
                "day_of_week": act.timestamp.strftime("%A") if act.timestamp else None,
                "url": act.url,
                "engagement": {
                    "likes": act.metadata.get("likes", 0),
                    "comments": act.metadata.get("comments", 0)
                }
            })
        
        export_data = {
            "platform": "linkedin",
            "identifier": node.identifier,
            "profile": node.data,
            "posts": posts,
            "post_count": len(posts),
            "cross_references": {
                "github": f"{safe_name}_github.json",
                "twitter": f"{safe_name}_twitter.json"
            },
            "confidence_score": node.confidence_score,
            "exported_at": datetime.now().isoformat(),
            "is_simulated": True
        }
        
        filepath = self.output_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Exported: {filename}")
        return filename
    
    def export_complete_profile(
        self,
        github_node: IdentityNode,
        twitter_node: IdentityNode,
        linkedin_node: IdentityNode
    ) -> Dict[str, str]:
        """
        Export all three platform profiles for a user.
        Returns dict of platform -> filename mappings.
        """
        print(f"\n📦 Exporting complete profile: {github_node.identifier}")
        print("-" * 50)
        
        files = {}
        files["github"] = self.export_github(github_node)
        files["twitter"] = self.export_twitter(twitter_node)
        files["linkedin"] = self.export_linkedin(linkedin_node)
        
        # Update manifest
        safe_name = self._get_safe_name(github_node.identifier)
        self.manifest["profiles"][safe_name] = {
            "name": github_node.get_name() or github_node.identifier,
            "github_username": github_node.identifier,
            "files": files,
            "exported_at": datetime.now().isoformat(),
            "platforms": ["github", "twitter", "linkedin"]
        }
        self._save_manifest()
        
        print(f"✅ Profile exported successfully!")
        return files
    
    def list_exported_profiles(self) -> List[str]:
        """List all exported profile names"""
        return list(self.manifest.get("profiles", {}).keys())


class SimulatedDataValidator:
    """
    Validates exported simulated data for:
    - File existence
    - JSON structure
    - Cross-reference integrity
    - Timestamp validity
    """
    
    def __init__(self, data_dir: str = "simulated_data"):
        self.data_dir = Path(data_dir)
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self) -> bool:
        """Validate all exported profiles"""
        print("=" * 60)
        print("SIMULATED DATA VALIDATION")
        print("=" * 60)
        
        manifest_path = self.data_dir / "manifest.json"
        if not manifest_path.exists():
            self.errors.append("manifest.json not found")
            self._print_results()
            return False
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        profiles = manifest.get("profiles", {})
        
        if not profiles:
            self.warnings.append("No profiles found in manifest")
            self._print_results()
            return True
        
        all_valid = True
        for profile_name, profile_info in profiles.items():
            print(f"\n🔍 Validating: {profile_name}")
            print("-" * 40)
            
            if not self._validate_profile(profile_name, profile_info):
                all_valid = False
        
        self._print_results()
        return all_valid and len(self.errors) == 0
    
    def _validate_profile(self, name: str, info: Dict) -> bool:
        """Validate a single profile"""
        files = info.get("files", {})
        valid = True
        
        # Check all files exist
        for platform, filename in files.items():
            filepath = self.data_dir / filename
            if not filepath.exists():
                self.errors.append(f"Missing file: {filename}")
                valid = False
                continue
            
            # Validate file content
            if not self._validate_file(filepath, platform):
                valid = False
        
        # Validate cross-references
        if valid:
            if not self._validate_cross_references(files):
                valid = False
        
        return valid
    
    def _validate_file(self, filepath: Path, platform: str) -> bool:
        """Validate a single JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in {filepath.name}: {e}")
            return False
        
        # Check required fields
        required = ["platform", "identifier", "profile", "cross_references", "exported_at"]
        for field in required:
            if field not in data:
                self.errors.append(f"{filepath.name}: Missing required field '{field}'")
                return False
        
        # Validate platform matches
        if data["platform"] != platform:
            self.errors.append(f"{filepath.name}: Platform mismatch (expected {platform}, got {data['platform']})")
            return False
        
        # Validate timestamps in activities
        if not self._validate_timestamps(data, filepath.name):
            return False
        
        print(f"  ✅ {filepath.name}")
        return True
    
    def _validate_timestamps(self, data: Dict, filename: str) -> bool:
        """Validate all timestamps in activities/tweets/posts"""
        valid = True
        
        # Check tweets
        for i, tweet in enumerate(data.get("tweets", [])):
            if not tweet.get("timestamp"):
                self.warnings.append(f"{filename}: Tweet {i} missing timestamp")
            elif not tweet.get("date"):
                self.warnings.append(f"{filename}: Tweet {i} missing date field")
        
        # Check posts
        for i, post in enumerate(data.get("posts", [])):
            if not post.get("timestamp"):
                self.warnings.append(f"{filename}: Post {i} missing timestamp")
            elif not post.get("date"):
                self.warnings.append(f"{filename}: Post {i} missing date field")
        
        # Check activities
        for i, act in enumerate(data.get("activities", [])):
            if not act.get("timestamp"):
                self.warnings.append(f"{filename}: Activity {i} missing timestamp")
        
        return valid
    
    def _validate_cross_references(self, files: Dict[str, str]) -> bool:
        """Validate cross-references between files are consistent"""
        valid = True
        
        for platform, filename in files.items():
            filepath = self.data_dir / filename
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cross_refs = data.get("cross_references", {})
            
            # Check each cross-reference points to existing file
            for ref_platform, ref_filename in cross_refs.items():
                ref_path = self.data_dir / ref_filename
                if not ref_path.exists():
                    self.errors.append(
                        f"{filename}: Cross-reference to {ref_filename} but file doesn't exist"
                    )
                    valid = False
                else:
                    # Verify the referenced file links back
                    with open(ref_path, 'r', encoding='utf-8') as rf:
                        ref_data = json.load(rf)
                    
                    back_refs = ref_data.get("cross_references", {})
                    expected_back = files.get(platform)
                    actual_back = back_refs.get(platform)
                    
                    if actual_back != expected_back:
                        self.warnings.append(
                            f"{ref_filename}: Back-reference to {platform} is '{actual_back}', expected '{expected_back}'"
                        )
        
        if valid:
            print(f"  ✅ Cross-references valid")
        
        return valid
    
    def _print_results(self):
        """Print validation results"""
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"   • {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"   • {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All validations passed!")
        elif not self.errors:
            print(f"\n✅ Valid (with {len(self.warnings)} warnings)")
        else:
            print(f"\n❌ INVALID ({len(self.errors)} errors)")


def validate_simulated_data():
    """Run validation on simulated data directory"""
    validator = SimulatedDataValidator()
    return validator.validate_all()


if __name__ == "__main__":
    validate_simulated_data()
