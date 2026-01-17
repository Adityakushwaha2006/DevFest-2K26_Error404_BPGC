"""
Bulk Profile Generator for NEXUS
Generates social profile data for 200 real GitHub users with rate limiting.

Features:
- Reads GitHub usernames from people_names.txt
- Rate limiting: checks every 10 iterations, sleeps if < 60 seconds elapsed
- Progress counter with percentage
- Full error handling with error message output
- Overwrites enabled for simulated_data folder
- Generates complete profiles: GitHub + Twitter + LinkedIn
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

load_dotenv()

from identity_node import IdentityGraph, Platform
from platform_fetchers import get_fetcher
from mock_generators import (
    MockTwitterGenerator,
    MockLinkedInGenerator,
    CheckpointManager,
    RateLimitError
)
from simulated_data_export import SimulatedDataExporter



class BulkProfileGenerator:
    """
    Generates social profiles for a large number of GitHub users
    with intelligent rate limiting and progress tracking.
    """
    
    def __init__(
        self,
        names_file: str = "people_names.txt",
        output_dir: str = None,
        checkpoint_dir: str = "checkpoints"
    ):
        self.script_dir = Path(__file__).parent
        self.names_file = self.script_dir / names_file
        
        # Output to backend/simulated_data (same location as before)
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = self.script_dir.parent / "simulated_data"
        
        self.checkpoint_dir = self.script_dir / checkpoint_dir
        
        # Rate limiting config
        self.check_interval = 10  # Check timer every N iterations
        self.min_time_window = 60  # Minimum seconds between checks
        self.buffer_time = 5  # Extra buffer seconds to be safe
        
        # Progress tracking
        self.total_count = 0
        self.completed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.errors: List[dict] = []
        
        # Initialize components
        self.checkpoint_mgr = CheckpointManager(str(self.checkpoint_dir))
        self.exporter = SimulatedDataExporter(str(self.output_dir))
        
        # Generators
        self.twitter_gen = None
        self.linkedin_gen = None
        self.github_fetcher = None
    
    def load_names(self) -> List[str]:
        """Load GitHub usernames from the names file."""
        names = []
        
        if not self.names_file.exists():
            raise FileNotFoundError(f"Names file not found: {self.names_file}")
        
        with open(self.names_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    names.append(line)
        
        return names
    
    def _init_generators(self):
        """Initialize API clients and generators."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        github_token = os.getenv('GITHUB_TOKEN')
        
        self.twitter_gen = MockTwitterGenerator(
            api_key=api_key,
            checkpoint_manager=self.checkpoint_mgr
        )
        self.linkedin_gen = MockLinkedInGenerator(
            api_key=api_key,
            checkpoint_manager=self.checkpoint_mgr
        )
        self.github_fetcher = get_fetcher(Platform.GITHUB, github_token=github_token)
    
    def _print_progress(self, current: int, total: int, username: str, status: str):
        """Print progress bar and status."""
        percent = (current / total) * 100
        bar_length = 30
        filled = int(bar_length * current / total)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r[{bar}] {percent:5.1f}% | {current}/{total} | {username}: {status}", end='', flush=True)
    
    def _print_stats(self):
        """Print current statistics."""
        print(f"\n{'='*60}")
        print(f"📊 PROGRESS STATS")
        print(f"{'='*60}")
        print(f"   ✅ Completed: {self.completed_count}")
        print(f"   ⏭️  Skipped (cached): {self.skipped_count}")
        print(f"   ❌ Failed: {self.failed_count}")
        print(f"   📋 Remaining: {self.total_count - self.completed_count - self.skipped_count - self.failed_count}")
        print(f"{'='*60}\n")
    
    def generate_single_profile(self, username: str, force_overwrite: bool = True) -> bool:
        """
        Generate complete profile (GitHub + Twitter + LinkedIn) for a single user.
        
        Args:
            username: GitHub username to process
            force_overwrite: If True, regenerates even if data exists
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if already fully processed and not forcing overwrite
            if not force_overwrite:
                github_file = self.output_dir / f"{username}_github.json"
                twitter_file = self.output_dir / f"{username}_twitter.json" 
                linkedin_file = self.output_dir / f"{username}_linkedin.json"
                
                if all(f.exists() for f in [github_file, twitter_file, linkedin_file]):
                    return True  # Already complete
            
            # Fetch GitHub data
            github_node = self.github_fetcher.fetch(username)
            
            if github_node.fetch_status != "success":
                error_msg = github_node.error_message or "Unknown GitHub fetch error"
                self.errors.append({
                    "username": username,
                    "platform": "github",
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                })
                print(f"\n❌ GitHub fetch failed for {username}: {error_msg}")
                return False
            
            # Generate Twitter profile
            twitter_node = self.twitter_gen.generate_from_github(
                github_node,
                skip_if_checkpointed=not force_overwrite
            )
            
            # Generate LinkedIn profile
            linkedin_node = self.linkedin_gen.generate_from_github(
                github_node,
                skip_if_checkpointed=not force_overwrite
            )
            
            # Export to simulated_data (with overwrite)
            self.exporter.export_complete_profile(
                github_node,
                twitter_node,
                linkedin_node
            )
            
            # Save GitHub checkpoint
            github_data = {
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
            self.checkpoint_mgr.save_checkpoint(username, "github", github_data)
            
            return True
            
        except RateLimitError as e:
            self.errors.append({
                "username": username,
                "platform": "gemini",
                "error": f"Rate limit: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })
            raise  # Re-raise to trigger pause
            
        except Exception as e:
            self.errors.append({
                "username": username,
                "platform": "unknown",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            print(f"\n❌ Error processing {username}: {str(e)}")
            return False
    
    def run(
        self,
        limit: Optional[int] = None,
        force_overwrite: bool = True,
        resume_from: Optional[str] = None
    ):
        """
        Run bulk generation for all names in the file.
        
        Args:
            limit: Optional limit on number of users to process
            force_overwrite: If True, regenerates all data even if exists
            resume_from: Optional username to resume from
        """
        print("="*60)
        print("🚀 NEXUS BULK PROFILE GENERATOR")
        print("="*60)
        
        # Load names
        names = self.load_names()
        self.total_count = len(names)
        
        if limit:
            names = names[:limit]
            self.total_count = len(names)
        
        # Resume from specific username if specified
        if resume_from:
            try:
                start_idx = names.index(resume_from)
                names = names[start_idx:]
                print(f"📌 Resuming from: {resume_from}")
            except ValueError:
                print(f"⚠️ Username '{resume_from}' not found, starting from beginning")
        
        print(f"\n📋 Total users to process: {self.total_count}")
        print(f"📁 Output directory: {self.output_dir}")
        print(f"⏱️  Rate limiting: check every {self.check_interval} iterations")
        print(f"   Min time window: {self.min_time_window}s + {self.buffer_time}s buffer")
        print(f"{'='*60}\n")
        
        # Initialize generators
        self._init_generators()
        
        # Rate limiting state
        iteration_count = 0
        last_check_time = time.time()
        start_time = time.time()
        
        try:
            for i, username in enumerate(names, 1):
                self._print_progress(i, len(names), username, "Processing...")
                
                # Check if user already has complete data
                github_file = self.output_dir / f"{username}_github.json"
                
                if github_file.exists() and not force_overwrite:
                    self.skipped_count += 1
                    self._print_progress(i, len(names), username, "Skipped (cached)")
                    continue
                
                # Generate profile
                success = self.generate_single_profile(username, force_overwrite)
                
                if success:
                    self.completed_count += 1
                    self._print_progress(i, len(names), username, "✓ Complete")
                else:
                    self.failed_count += 1
                
                print()  # New line after progress
                
                # Rate limiting check every N iterations
                iteration_count += 1
                if iteration_count % self.check_interval == 0:
                    elapsed = time.time() - last_check_time
                    
                    if elapsed < self.min_time_window:
                        sleep_time = self.min_time_window - elapsed + self.buffer_time
                        print(f"\n⏳ Rate limiting: sleeping {sleep_time:.1f}s to avoid API limits...")
                        time.sleep(sleep_time)
                    
                    last_check_time = time.time()
                    self._print_stats()
        
        except RateLimitError:
            print("\n" + "="*60)
            print("⚠️ RATE LIMIT HIT - Generation paused")
            print("="*60)
            print("To resume:")
            print("1. Wait for rate limit to reset (usually 1-15 minutes)")
            print("2. Or switch to a different API key")
            print(f"3. Resume: python bulk_generate.py --resume {username}")
            self._save_error_log()
            return
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Generation interrupted by user")
            self._save_error_log()
            return
        
        # Final summary
        total_time = time.time() - start_time
        self._print_final_summary(total_time)
        self._save_error_log()
    
    def _print_final_summary(self, total_time: float):
        """Print final generation summary."""
        print("\n" + "="*60)
        print("✅ BULK GENERATION COMPLETE")
        print("="*60)
        print(f"\n📊 Final Statistics:")
        print(f"   ✅ Successfully generated: {self.completed_count}")
        print(f"   ⏭️  Skipped (already cached): {self.skipped_count}")
        print(f"   ❌ Failed: {self.failed_count}")
        print(f"   ⏱️  Total time: {total_time/60:.1f} minutes")
        print(f"\n📁 Output location: {self.output_dir}")
        
        if self.errors:
            print(f"\n⚠️ {len(self.errors)} errors occurred (see errors.json)")
    
    def _save_error_log(self):
        """Save error log to file."""
        if self.errors:
            error_file = self.script_dir / "generation_errors.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "generated_at": datetime.now().isoformat(),
                    "total_errors": len(self.errors),
                    "errors": self.errors
                }, f, indent=2)
            print(f"📝 Error log saved: {error_file}")


def main():
    """Main entry point for bulk generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk Profile Generator for NEXUS")
    parser.add_argument("--limit", type=int, help="Limit number of users to process")
    parser.add_argument("--resume", type=str, help="Resume from specific username")
    parser.add_argument("--no-overwrite", action="store_true", help="Skip existing profiles")
    parser.add_argument("--test", action="store_true", help="Test mode with 3 users")
    
    args = parser.parse_args()
    
    generator = BulkProfileGenerator()
    
    # Test mode
    limit = args.limit
    if args.test:
        limit = 3
        print("🧪 TEST MODE - Processing only 3 users")
    
    generator.run(
        limit=limit,
        force_overwrite=not args.no_overwrite,
        resume_from=args.resume
    )


if __name__ == "__main__":
    main()
