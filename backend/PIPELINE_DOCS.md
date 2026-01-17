# NEXUS Data Fetching Pipeline Documentation

## Overview

The NEXUS pipeline fetches and consolidates identity data from multiple platforms into a unified JSON profile. **Scoring is NOT part of this pipeline** - this module only handles data fetching and aggregation.

---

## Architecture

```
nexus_main.py         # CLI & Orchestrator (entry point)
    |
    +-- nexus_search.py   # Discovery (Google CSE / Mock)
    +-- nexus_logic.py    # Consolidation logic
            |
            +-- nexus_fetch.py  # Individual platform fetchers
```

---

## File Descriptions

### `nexus_main.py` - Entry Point & Orchestrator

**Purpose**: Main CLI that runs the full pipeline.

**Input**: A person's name and optional platform handles.

**Pipeline Steps**:
1. **Discovery**: Find social profiles from a name (optional)
2. **Social**: Fetch GitHub, Twitter, LinkedIn data
3. **Misc**: Fetch Stack Overflow, Blog, Hacker News data
4. **Unified**: Merge all data into a single JSON

**Fault Tolerance**: Each step is wrapped in try/except. If any step fails, the pipeline continues with partial data.

---

### `nexus_search.py` - Discovery Engine

**Purpose**: Discovers platform handles from a name.

| Class | Description |
|-------|-------------|
| `GoogleSearchEngine` | Uses Google Custom Search API |
| `MockProfileDiscovery` | Uses local `data/known_profiles.json` |
| `get_search_engine()` | Factory function (returns configured engine) |

**Error Points**:
- Google CSE: Requires `GOOGLE_CSE_API_KEY` and `GOOGLE_CSE_ID` env vars
- Mock: Requires `data/known_profiles.json` to exist

---

### `nexus_logic.py` - Business Logic

**Purpose**: Orchestrates fetching from each platform group.

| Class | Description |
|-------|-------------|
| `ProfileConsolidator` | Handles GitHub, Twitter, LinkedIn |
| `MiscConsolidator` | Handles SO, Blog, Medium, Hacker News |

**Error Points**:
- Simulated data requires files in `simulated_data/` directory
- Network failures are caught and logged

---

### `nexus_fetch.py` - Platform Fetchers

**Purpose**: Individual fetchers for each platform.

| Class | API Used | Auth Required |
|-------|----------|--------------|
| `ExtendedGitHubFetcher` | GitHub REST API | Optional (`GITHUB_TOKEN`) |
| `SimulatedDataFetcher` | Local JSON files | No |
| `StackOverflowFetcher` | Stack Exchange API | No |
| `BlogFetcher` | RSS/Atom feeds | No |
| `MediumFetcher` | Medium RSS | No |
| `HackerNewsFetcher` | HN Firebase API | No |

**Error Points**:
- GitHub: Rate limits (60/hr unauthenticated, 5000/hr with token)
- Stack Overflow: API throttling
- Blog/Medium: RSS feed not found
- All: Network timeouts

---

## CLI Usage

### Basic Usage (Name Only)
```bash
python nexus_main.py "Aditya"
```
- Uses auto-discovery if name is in `known_profiles.json`
- Falls back to searching with name

### With GitHub Username
```bash
python nexus_main.py "Aditya" --github aditya123
```
- Skips discovery since GitHub is provided
- Fetches live GitHub data

### With Misc Platforms
```bash
python nexus_main.py "Paul Graham" --hn pg
```
- Fetches Hacker News data for user "pg"

### All Options
```bash
python nexus_main.py "Name" \
  --github <username> \
  --twitter <handle> \
  --linkedin <id> \
  --so <display_name> \
  --blog <url> \
  --hn <username> \
  --company <name> \
  --role <role> \
  --no-discover
```

---

## Scenarios

| Scenario | Works? | Notes |
|----------|--------|-------|
| Name only | Yes | Uses discovery or searches with name |
| Name + GitHub | Yes | Skips discovery, fetches real GitHub |
| Name + any social | Yes | Uses provided handles |
| Name + misc only (--hn, --so) | Yes | Skips social, runs misc |
| GitHub fails | Yes | Continues with Twitter/LinkedIn |
| All social fails | Yes | Continues to misc step |
| All misc fails | Yes | Produces unified with only social |
| Everything fails | Yes | Returns empty unified profile |

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_CSE_API_KEY` | Optional | Google Custom Search API key |
| `GOOGLE_CSE_ID` | Optional | Custom Search Engine ID |
| `GITHUB_TOKEN` | Optional | GitHub personal access token |

---

## Output Files

All output is saved to `backend/social_profiles/`:

- `<username>_social.json` - Social platform data
- `<username>_misc.json` - Miscellaneous platform data
- `<username>_unified.json` - Merged profile (final output)
