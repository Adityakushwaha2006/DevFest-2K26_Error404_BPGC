"""
Google Custom Search Engine Integration
Discovers social profiles and relevant sites for a person.

Setup required:
1. Create a Programmable Search Engine at https://programmablesearchengine.google.com/
2. Get API key from Google Cloud Console
3. Set GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID in .env

Free tier: 100 queries/day
Paid: $5 per 1,000 queries
"""

import os
import re
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class GoogleSearchEngine:
    """
    Uses Google Custom Search JSON API to discover social profiles.
    """
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    # Platform patterns to identify social profiles
    PLATFORM_PATTERNS = {
        "github": r"github\.com/([A-Za-z0-9_-]+)",
        "twitter": r"(?:twitter\.com|x\.com)/([A-Za-z0-9_]+)",
        "linkedin": r"linkedin\.com/in/([A-Za-z0-9_-]+)",
        "devto": r"dev\.to/([A-Za-z0-9_]+)",
        "medium": r"medium\.com/@([A-Za-z0-9_.-]+)",
        "stackoverflow": r"stackoverflow\.com/users/(\d+)",
        "hackernews": r"news\.ycombinator\.com/user\?id=([A-Za-z0-9_]+)"
    }
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        search_engine_id: Optional[str] = None
    ):
        """
        Initialize Google Search Engine.
        
        Args:
            api_key: Google API key (or set GOOGLE_CSE_API_KEY env var)
            search_engine_id: Custom Search Engine ID (or set GOOGLE_CSE_ID env var)
        """
        self.api_key = (api_key or os.getenv("GOOGLE_CSE_API_KEY", "")).strip()
        self.search_engine_id = (search_engine_id or os.getenv("GOOGLE_CSE_ID", "")).strip()
        
        if not self.api_key or not self.search_engine_id:
            print("⚠️ Google CSE credentials not configured.")
            print("   Set GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID in .env")
    
    def is_configured(self) -> bool:
        """Check if API credentials are configured."""
        return bool(self.api_key and self.search_engine_id)
    
    def search(
        self, 
        query: str, 
        num_results: int = 10,
        site_restrict: Optional[str] = None
    ) -> List[Dict]:
        """
        Perform a Google search.
        """
        if not self.is_configured():
            return []
        
        # Build query with site restriction if provided
        if site_restrict:
            query = f"site:{site_restrict} {query}"
        
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10)
        }
        
        # Debug info (masked)
        masked_key = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
        print(f"   [DEBUG] Req: q='{query}', cx='{self.search_engine_id}', key='{masked_key}'")
        
        try:
            response = requests.get(self.BASE_URL, params=params)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                return [
                    {
                        "title": item.get("title"),
                        "url": item.get("link"),
                        "snippet": item.get("snippet"),
                        "display_link": item.get("displayLink")
                    }
                    for item in items
                ]
            else:
                error = response.json().get("error", {})
                print(f"Google Search API error: {error.get('message', response.status_code)}")
                return []
                
        except Exception as e:
            print(f"Error performing Google search: {e}")
            return []
    
    def discover_profiles(
        self, 
        name: str, 
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Discover social profiles for a person.
        
        Args:
            name: Person's name
            context: Additional context (company, location, role)
            
        Returns:
            Dict with discovered platforms and profiles
        """
        print(f"\n🔍 Discovering profiles for: {name}")
        if context:
            print(f"   Context: {context}")
        
        result = {
            "searched_at": datetime.now().isoformat(),
            "query": name,
            "context": context,
            "discovered_profiles": {},
            "raw_results": [],
            "search_status": "pending"
        }
        
        if not self.is_configured():
            result["search_status"] = "not_configured"
            result["error"] = "Google CSE API credentials not set"
            return result
        
        # Build search query - simpler approach without site restrictions
        query_parts = [f'"{name}"']
        if context:
            query_parts.append(context)
        
        base_query = ' '.join(query_parts)
        
        # Search each platform separately for better results
        platforms_to_search = [
            ("github", "github.com"),
            ("linkedin", "linkedin.com"),
            ("twitter", "twitter.com OR x.com"),
            ("devto", "dev.to"),
            ("stackoverflow", "stackoverflow.com"),
            ("medium", "medium.com"),
            ("hackernews", "news.ycombinator.com")
        ]
        
        for platform, site in platforms_to_search:
            print(f"   Searching {platform}...")
            query = f"{base_query} site:{site}"
            
            results = self.search(query, num_results=5)
            
            for search_result in results:
                url = search_result.get("url", "")
                pattern = self.PLATFORM_PATTERNS.get(platform)
                
                if pattern:
                    match = re.search(pattern, url, re.IGNORECASE)
                    if match and platform not in result["discovered_profiles"]:
                        identifier = match.group(1)
                        result["discovered_profiles"][platform] = {
                            "identifier": identifier,
                            "url": url,
                            "title": search_result.get("title"),
                            "snippet": search_result.get("snippet"),
                            "confidence": self._calculate_confidence(name, search_result, platform)
                        }
                        print(f"   ✓ {platform}: {identifier}")
                        break
        
        if not result["discovered_profiles"]:
            result["search_status"] = "no_results"
            return result
        
        result["search_status"] = "success"
        result["platforms_found"] = list(result["discovered_profiles"].keys())
        
        return result
    
    def _calculate_confidence(
        self, 
        name: str, 
        result: Dict, 
        platform: str
    ) -> float:
        """
        Calculate confidence score for a profile match.
        Higher if name appears in title/snippet.
        """
        confidence = 0.5  # Base confidence
        
        name_lower = name.lower()
        title_lower = (result.get("title") or "").lower()
        snippet_lower = (result.get("snippet") or "").lower()
        
        # Name in title
        if name_lower in title_lower:
            confidence += 0.3
        elif any(part in title_lower for part in name_lower.split()):
            confidence += 0.15
        
        # Name in snippet
        if name_lower in snippet_lower:
            confidence += 0.2
        elif any(part in snippet_lower for part in name_lower.split()):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def search_person_comprehensive(
        self,
        name: str,
        company: Optional[str] = None,
        role: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Comprehensive person search with multiple query strategies.
        
        Args:
            name: Person's name
            company: Company name
            role: Job role/title
            location: Geographic location
            
        Returns:
            Comprehensive discovery result
        """
        print("\n" + "=" * 60)
        print(f"🔎 COMPREHENSIVE PERSON SEARCH")
        print(f"   Name: {name}")
        if company:
            print(f"   Company: {company}")
        if role:
            print(f"   Role: {role}")
        if location:
            print(f"   Location: {location}")
        print("=" * 60)
        
        result = {
            "searched_at": datetime.now().isoformat(),
            "input": {
                "name": name,
                "company": company,
                "role": role,
                "location": location
            },
            "discovered_profiles": {},
            "all_searches": [],
            "search_status": "pending"
        }
        
        # Strategy 1: Name + context
        context_parts = [c for c in [company, role, location] if c]
        context = " ".join(context_parts) if context_parts else None
        
        search1 = self.discover_profiles(name, context)
        result["all_searches"].append({"strategy": "name_context", "result": search1})
        
        # Merge discovered profiles
        for platform, profile in search1.get("discovered_profiles", {}).items():
            if platform not in result["discovered_profiles"]:
                result["discovered_profiles"][platform] = profile
        
        # Strategy 2: Platform-specific searches (if we need more coverage)
        missing_platforms = set(["github", "linkedin"]) - set(result["discovered_profiles"].keys())
        
        for platform in missing_platforms:
            print(f"\n   Searching specifically on {platform}...")
            
            if platform == "github":
                # GitHub-specific search
                platform_results = self.search(f'"{name}" {company or ""}', site_restrict="github.com")
            elif platform == "linkedin":
                platform_results = self.search(f'"{name}" {company or ""}', site_restrict="linkedin.com")
            else:
                continue
            
            for pr in platform_results[:3]:
                url = pr.get("url", "")
                pattern = self.PLATFORM_PATTERNS.get(platform)
                if pattern:
                    match = re.search(pattern, url, re.IGNORECASE)
                    if match and platform not in result["discovered_profiles"]:
                        result["discovered_profiles"][platform] = {
                            "identifier": match.group(1),
                            "url": url,
                            "title": pr.get("title"),
                            "snippet": pr.get("snippet"),
                            "confidence": self._calculate_confidence(name, pr, platform)
                        }
                        print(f"   ✓ {platform}: {match.group(1)}")
                        break
        
        result["search_status"] = "success"
        result["platforms_found"] = list(result["discovered_profiles"].keys())
        
        print("\n" + "=" * 60)
        print(f"✅ SEARCH COMPLETE")
        print(f"   Platforms found: {', '.join(result['platforms_found']) or 'None'}")
        print("=" * 60 + "\n")
        
        return result


class MockProfileDiscovery:
    """
    Mock profile discovery for demo when Google CSE is not configured.
    Uses known mappings for common developers.
    """
    
    KNOWN_PROFILES = {
        "kent c. dodds": {
            "github": "kentcdodds",
            "twitter": "kentcdodds",
            "linkedin": "kentcdodds",
            "blog": "https://kentcdodds.com/blog"
        },
        "dan abramov": {
            "github": "gaearon",
            "twitter": "dan_abramov",
            "blog": "https://overreacted.io"
        },
        "linus torvalds": {
            "github": "torvalds",
            "linkedin": "linustorvalds"
        },
        "evan you": {
            "github": "yyx990803",
            "twitter": "youyuxi"
        },
        "sindre sorhus": {
            "github": "sindresorhus",
            "twitter": "sindresorhus",
            "blog": "https://sindresorhus.com"
        }
    }
    
    def discover_profiles(self, name: str) -> Dict[str, Any]:
        """
        Mock profile discovery using known mappings.
        """
        print(f"\n🔍 [MOCK] Discovering profiles for: {name}")
        
        name_lower = name.lower()
        profiles = self.KNOWN_PROFILES.get(name_lower, {})
        
        result = {
            "searched_at": datetime.now().isoformat(),
            "query": name,
            "discovered_profiles": {},
            "search_status": "mock",
            "note": "Using mock data - configure Google CSE for real search"
        }
        
        for platform, identifier in profiles.items():
            result["discovered_profiles"][platform] = {
                "identifier": identifier,
                "confidence": 1.0,
                "source": "known_mapping"
            }
            print(f"   ✓ {platform}: {identifier}")
        
        if not profiles:
            print(f"   ⚠️ No mock data for: {name}")
        
        result["platforms_found"] = list(result["discovered_profiles"].keys())
        
        return result


def get_search_engine(
    api_key: Optional[str] = None,
    search_engine_id: Optional[str] = None
) -> 'GoogleSearchEngine | MockProfileDiscovery':
    """
    Factory function to get appropriate search engine.
    Returns GoogleSearchEngine if configured, otherwise MockProfileDiscovery.
    """
    engine = GoogleSearchEngine(api_key, search_engine_id)
    
    if engine.is_configured():
        return engine
    else:
        print("⚠️ Google CSE not configured, using mock discovery")
        return MockProfileDiscovery()


# CLI
if __name__ == "__main__":
    import sys
    
    print("\n" + "=" * 60)
    print("NEXUS - Profile Discovery (Google CSE)")
    print("=" * 60)
    
    if len(sys.argv) < 2:
        print("\nUsage: python google_search.py <name> [options]")
        print("\nOptions:")
        print("  --company <company>   Company name")
        print("  --role <role>         Job role")
        print("  --location <location> Location")
        print("\nExamples:")
        print('  python google_search.py "Kent C. Dodds"')
        print('  python google_search.py "John Smith" --company Google --role Engineer')
        print("\nSetup:")
        print("  1. Create CSE at https://programmablesearchengine.google.com/")
        print("  2. Set GOOGLE_CSE_API_KEY and GOOGLE_CSE_ID in .env")
        sys.exit(0)
    
    # Parse arguments
    name = sys.argv[1]
    company = None
    role = None
    location = None
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--company" and i + 1 < len(sys.argv):
            company = sys.argv[i + 1]
            i += 2
        elif arg == "--role" and i + 1 < len(sys.argv):
            role = sys.argv[i + 1]
            i += 2
        elif arg == "--location" and i + 1 < len(sys.argv):
            location = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    
    # Get search engine (real or mock)
    search_engine = get_search_engine()
    
    if isinstance(search_engine, GoogleSearchEngine) and search_engine.is_configured():
        result = search_engine.search_person_comprehensive(
            name=name,
            company=company,
            role=role,
            location=location
        )
    else:
        result = search_engine.discover_profiles(name)
    
    print(f"\n📊 Discovered Profiles:")
    for platform, profile in result.get("discovered_profiles", {}).items():
        identifier = profile.get("identifier") if isinstance(profile, dict) else profile
        print(f"   {platform}: {identifier}")
