"""
Checkpoint Recovery System
Provides procedures to recover from interrupted generation and resume with new API keys.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()



class CheckpointRecovery:
    """
    Handles recovery from interrupted mock data generation.
    
    Recovery Procedure:
    1. Scan checkpoint directory for partial work
    2. Identify incomplete profiles
    3. Resume generation with new API key
    4. Move completed profiles to simulated_data
    """
    
    def __init__(
        self, 
        checkpoint_dir: str = "checkpoints",
        output_dir: str = "simulated_data"
    ):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.output_dir = Path(output_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def get_status(self) -> Dict[str, any]:
        """
        Get current recovery status.
        Returns summary of completed vs pending work.
        """
        status = {
            "checkpoints_found": 0,
            "complete_profiles": [],
            "partial_profiles": [],
            "pending_platforms": {}
        }
        
        # Scan checkpoints
        checkpoints = list(self.checkpoint_dir.glob("*.json"))
        status["checkpoints_found"] = len(checkpoints)
        
        # Group by username
        users = {}
        for cp in checkpoints:
            if cp.name == "current_session.json":
                continue
            
            parts = cp.stem.rsplit("_", 1)
            if len(parts) == 2:
                username, platform = parts
                if username not in users:
                    users[username] = set()
                users[username].add(platform)
        
        # Categorize
        required_platforms = {"github", "twitter", "linkedin"}
        
        for username, platforms in users.items():
            # Remove partial checkpoints from consideration
            actual = {p for p in platforms if not p.endswith("_partial")}
            
            if required_platforms.issubset(actual):
                status["complete_profiles"].append(username)
            else:
                status["partial_profiles"].append(username)
                missing = required_platforms - actual
                status["pending_platforms"][username] = list(missing)
        
        return status
    
    def print_status(self):
        """Print human-readable recovery status"""
        status = self.get_status()
        
        print("=" * 60)
        print("CHECKPOINT RECOVERY STATUS")
        print("=" * 60)
        print(f"\n📁 Checkpoint files found: {status['checkpoints_found']}")
        
        if status["complete_profiles"]:
            print(f"\n✅ COMPLETE PROFILES ({len(status['complete_profiles'])}):")
            for user in status["complete_profiles"]:
                print(f"   • {user}")
        
        if status["partial_profiles"]:
            print(f"\n⚠️  PARTIAL PROFILES ({len(status['partial_profiles'])}):")
            for user in status["partial_profiles"]:
                pending = status["pending_platforms"].get(user, [])
                print(f"   • {user}: needs {pending}")
        
        if not status["complete_profiles"] and not status["partial_profiles"]:
            print("\n📭 No checkpoints found. Run generation first.")
        
        print("=" * 60)
        
        return status
    
    def recover_and_resume(self, new_api_key: Optional[str] = None) -> Dict:
        """
        Resume generation from where it left off.
        
        Args:
            new_api_key: New Gemini API key (or uses env var)
        
        Returns:
            Results dict with completed profiles
        """
        from platform_fetchers import get_fetcher
        from mock_generators import (
            MockTwitterGenerator, 
            MockLinkedInGenerator, 
            CheckpointManager,
            RateLimitError
        )
        from identity_node import Platform
        
        status = self.get_status()
        
        if not status["partial_profiles"]:
            print("✅ No incomplete profiles to resume")
            return {}
        
        print(f"\n🔄 Resuming generation for {len(status['partial_profiles'])} profiles...")
        
        # Initialize generators with new key
        api_key = new_api_key or os.getenv('GEMINI_API_KEY')
        checkpoint_mgr = CheckpointManager(str(self.checkpoint_dir))
        
        twitter_gen = MockTwitterGenerator(api_key=api_key, checkpoint_manager=checkpoint_mgr)
        linkedin_gen = MockLinkedInGenerator(api_key=api_key, checkpoint_manager=checkpoint_mgr)
        github_fetcher = get_fetcher(Platform.GITHUB, github_token=os.getenv('GITHUB_TOKEN'))
        
        results = {}
        
        for username in status["partial_profiles"]:
            pending = status["pending_platforms"].get(username, [])
            print(f"\n📋 Resuming {username}: generating {pending}")
            
            try:
                # Fetch GitHub (always needed as base)
                github_node = github_fetcher.fetch(username)
                if github_node.fetch_status != "success":
                    print(f"❌ Failed to fetch GitHub for {username}")
                    continue
                
                results[username] = {"github": github_node}
                
                # Generate pending platforms
                if "twitter" in pending:
                    twitter_node = twitter_gen.generate_from_github(github_node, skip_if_checkpointed=False)
                    results[username]["twitter"] = twitter_node
                    print(f"  ✅ Twitter complete")
                
                if "linkedin" in pending:
                    linkedin_node = linkedin_gen.generate_from_github(github_node, skip_if_checkpointed=False)
                    results[username]["linkedin"] = linkedin_node
                    print(f"  ✅ LinkedIn complete")
                
            except RateLimitError:
                print(f"\n⚠️ Rate limit hit again. Update API key and retry.")
                print(f"   Progress saved for {username}")
                break
        
        return results
    
    def finalize_complete_profiles(self) -> List[str]:
        """
        Move all complete profiles to simulated_data folder.
        Returns list of finalized usernames.
        """
        from simulated_data_export import SimulatedDataExporter
        from mock_generators import CheckpointManager
        
        status = self.get_status()
        finalized = []
        
        if not status["complete_profiles"]:
            print("No complete profiles to finalize")
            return finalized
        
        exporter = SimulatedDataExporter(str(self.output_dir))
        checkpoint_mgr = CheckpointManager(str(self.checkpoint_dir))
        
        for username in status["complete_profiles"]:
            print(f"\n📦 Finalizing: {username}")
            
            try:
                # Load checkpoint data
                github_data = checkpoint_mgr.load_checkpoint(username, "github")
                twitter_data = checkpoint_mgr.load_checkpoint(username, "twitter")
                linkedin_data = checkpoint_mgr.load_checkpoint(username, "linkedin")
                
                if not all([github_data, twitter_data, linkedin_data]):
                    print(f"  ⚠️ Missing checkpoint data for {username}")
                    continue
                
                # Reconstruct nodes from checkpoints
                from identity_node import IdentityNode, Platform
                from mock_generators import MockTwitterGenerator, MockLinkedInGenerator
                
                # GitHub node (from checkpoint)
                github_node = self._rebuild_github_node(username, github_data)
                
                # Twitter node (from checkpoint)
                twitter_gen = MockTwitterGenerator.__new__(MockTwitterGenerator)
                twitter_gen.checkpoint_manager = checkpoint_mgr
                twitter_node = twitter_gen._build_node_from_data(username, twitter_data)
                
                # LinkedIn node (from checkpoint)
                linkedin_gen = MockLinkedInGenerator.__new__(MockLinkedInGenerator)
                linkedin_gen.checkpoint_manager = checkpoint_mgr
                linkedin_node = linkedin_gen._build_node_from_data(username, linkedin_data)
                
                # Export to simulated_data
                exporter.export_complete_profile(github_node, twitter_node, linkedin_node)
                finalized.append(username)
                
            except Exception as e:
                print(f"  ❌ Error finalizing {username}: {e}")
        
        return finalized
    
    def _rebuild_github_node(self, username: str, data: Dict) -> 'IdentityNode':
        """Rebuild GitHub IdentityNode from checkpoint data"""
        from identity_node import IdentityNode, Platform, ActivityEvent
        from datetime import datetime
        
        node = IdentityNode(Platform.GITHUB, username)
        node.data = data.get("profile", data)
        node.fetch_status = "success"
        node.confidence_score = 0.9
        
        # Rebuild activities
        for act_data in data.get("activities", []):
            timestamp = act_data.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            activity = ActivityEvent(
                platform=Platform.GITHUB,
                event_type=act_data.get("type", "commit"),
                content=act_data.get("content", ""),
                timestamp=timestamp,
                url=act_data.get("url"),
                metadata=act_data.get("metadata", {})
            )
            node.add_activity(activity)
        
        return node
    
    def cleanup_checkpoints(self, username: Optional[str] = None):
        """
        Clean up checkpoint files after successful export.
        """
        if username:
            for f in self.checkpoint_dir.glob(f"{username}_*.json"):
                f.unlink()
            print(f"🗑️ Cleaned up checkpoints for: {username}")
        else:
            for f in self.checkpoint_dir.glob("*.json"):
                if f.name != "current_session.json":
                    f.unlink()
            print("🗑️ Cleaned up all checkpoint files")


def recovery_procedure():
    """
    Full recovery procedure - run this after hitting rate limit.
    
    Steps:
    1. Check status of checkpoints
    2. Resume generation with new API key
    3. Finalize complete profiles to simulated_data
    4. Validate exported data
    """
    print("=" * 60)
    print("NEXUS - CHECKPOINT RECOVERY PROCEDURE")
    print("=" * 60)
    
    recovery = CheckpointRecovery()
    
    # Step 1: Check status
    print("\n📋 Step 1: Checking checkpoint status...")
    status = recovery.print_status()
    
    # Step 2: Resume if needed
    if status["partial_profiles"]:
        print("\n🔄 Step 2: Resuming incomplete profiles...")
        print("   (Make sure GEMINI_API_KEY is updated in .env)")
        
        input("\nPress Enter to continue with recovery, or Ctrl+C to abort...")
        
        try:
            recovery.recover_and_resume()
        except Exception as e:
            print(f"\n❌ Recovery failed: {e}")
            print("   Save your progress and try again with a new API key")
            return False
    else:
        print("\n✅ Step 2: No incomplete profiles")
    
    # Step 3: Finalize complete profiles
    print("\n📦 Step 3: Finalizing complete profiles...")
    status = recovery.get_status()  # Refresh status
    
    if status["complete_profiles"]:
        finalized = recovery.finalize_complete_profiles()
        print(f"   Finalized {len(finalized)} profiles")
    else:
        print("   No complete profiles to finalize")
    
    # Step 4: Validate
    print("\n🔍 Step 4: Validating exported data...")
    from simulated_data_export import validate_simulated_data
    valid = validate_simulated_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("RECOVERY COMPLETE")
    print("=" * 60)
    
    if valid:
        print("✅ All data exported and validated successfully!")
        print(f"📁 Output: simulated_data/")
    else:
        print("⚠️ Some validation issues found. Check output above.")
    
    return valid


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            recovery = CheckpointRecovery()
            recovery.print_status()
        elif sys.argv[1] == "--finalize":
            recovery = CheckpointRecovery()
            recovery.finalize_complete_profiles()
        elif sys.argv[1] == "--cleanup":
            recovery = CheckpointRecovery()
            if len(sys.argv) > 2:
                recovery.cleanup_checkpoints(sys.argv[2])
            else:
                recovery.cleanup_checkpoints()
        else:
            print("Usage:")
            print("  python checkpoint_recovery.py          # Full recovery")
            print("  python checkpoint_recovery.py --status # Check status")
            print("  python checkpoint_recovery.py --finalize # Export complete profiles")
            print("  python checkpoint_recovery.py --cleanup [username]")
    else:
        recovery_procedure()
