# 🎯 Taste

Taste builds a personalized taste model from real consumption signals -- restaurant visits, food delivery orders, hotel stays, purchases, music plays, and movie watches. It scans the user's email and calendar to automatically extract these signals, enriches venue entities with taste-relevant attributes (cuisine, price point, neighborhood, vibe) via Google Maps, and generates discovery-focused recommendations that only suggest new places and respect dietary restrictions.


Skill packages follow the [agentskills.io](https://agentskills.io/specification) open standard and are compatible with OpenClaw, Hermes Agent, and any agentskills.io-compliant client.

---

## Overview

Taste is a recommendation engine grounded entirely in real consumption behavior -- not editorial lists, not collaborative filtering, not popularity signals. It automatically extracts consumption signals from email and calendar data (DoorDash, Instacart, Tock, OpenTable, Amazon, hotel bookings, and more), deduplicates across confirmation/reminder/cancellation chains, and enriches venue entities with taste-relevant attributes via Google Maps and web search. Every recommendation names the specific purchases, visits, and frequency patterns that justify it, only suggests places the user hasn't been, and respects stated dietary restrictions. Signals decay over time using a configurable half-life so that stale history loses influence unless reinforced by fresh behavior.

## Commands

| Command | Description |
|---|---|
| `taste.scan` | Scan user's email and calendar for consumption signals; extract, deduplicate, promote |
| `taste.scan.report` | Summarize last scan: extractions, signals created, cancellations, pending dedup matches |
| `taste.ingest.signal` | Manually record a consumption signal (purchase, visit, play, watch, stay) |
| `taste.enrich.item` | Enrich an item with taste-relevant attributes via Google Maps + web search |
| `taste.query.recommend` | Generate discovery recommendations grounded in consumption history and enriched attributes |
| `taste.query.serendipity` | Find novel but defensible cross-domain connections |
| `taste.model.status` | Model state: signal count, domains active, enrichment coverage, staleness |
| `taste.report.weekly` | Generate a weekly taste pattern summary |
| `taste.journal` | Write journal for the current run |
| `taste.update` | Pull latest from GitHub source (preserves journals and data) |

## Setup

`taste.init` runs automatically on first invocation and creates all required directories, config.json, and JSONL files. No manual setup is required for day-to-day operation — it also registers the `taste:update` cron job (midnight daily) for automatic self-updates.

## Installation

One-time host setup for running Taste under Hermes Agent.

### Python virtual environment

On Debian/Ubuntu with PEP 668 (externally managed Python), packages cannot be installed system-wide. Create a venv inside the skill's data directory:

```bash
# Install venv package if missing
apt update && apt install -y python3.13-venv

# Create virtual environment in skill data directory
cd {agent_root}/commons/data/ocas-taste
python3 -m venv venv
source venv/bin/activate
pip install spotipy google-api-python-client
```

### Spotify MCP configuration

Add to `config.yaml` under `mcp_servers`:

```yaml
mcp_servers:
  spotify:
    command: node
    args:
      - /root/.hermes/node/lib/node_modules/@darrenjaws/spotify-mcp/build/bin.js
    env:
      SPOTIFY_CLIENT_ID: ${SPOTIFY_CLIENT_ID}
      SPOTIFY_CLIENT_SECRET: ${SPOTIFY_CLIENT_SECRET}
      SPOTIFY_REDIRECT_URI: http://localhost:8888/callback
```

MCP environment variables in `.env` do NOT propagate to MCP stdio commands. They must be declared under `mcp_servers.spotify.env` in `config.yaml`.

### Cron registration

```bash
# Email/calendar scan (daily)
hermes cron create --name taste:scan --skill ocas-taste "0 6 * * *" \
  "scan email and calendar for consumption signals from the last 24 hours"

# Spotify sync (daily at midnight)
hermes cron create --name taste:sync-spotify --skill ocas-taste "0 0 * * *" \
  "sync Spotify recently played tracks"
```

## Dependencies

**OCAS Skills**
- [Sift](https://github.com/indigokarasu/sift) -- additional item enrichment via web research
- [Elephas](https://github.com/indigokarasu/elephas) -- Chronicle entity context (read-only)
- [Thread](https://github.com/indigokarasu/thread) -- may use thread signals to detect emerging taste patterns

**External**
- User's email account -- for scanning transactional emails
- User's Google Calendar -- for restaurant/hotel reservation data
- Google Maps -- for entity enrichment (cuisine, price, neighborhood, ratings)
- Web search -- backup enrichment source

## Scheduled Tasks

| Job | Mechanism | Schedule | Command |
|---|---|---|---|
| `taste:update` | cron | `0 0 * * *` (midnight daily) | Self-update from GitHub source |

## Changelog

### v3.4.4 — April 12, 2026
- Switch Spotify sync from spotify-history skill to Spotify MCP

### v3.2.0 -- April 2, 2026
- Structured entity observations in journal payloads (`entities_observed`, `relationships_observed`, `preferences_observed`)
- `user_relevance` tagging on journal observations (default `user` for preference-relevant entities)
- Elephas journal cooperation in skill cooperation section
- Concept/Idea, Entity/Person added to ontology types

### v3.0.0 -- March 27, 2026
- Email and calendar scanning: automatic extraction of consumption signals from transactional emails (DoorDash, Instacart, Good Eggs, Tock, OpenTable, Yelp, Amazon, hotel bookings) and Google Calendar
- Deduplication engine: handles confirmation/reminder/cancellation chains with composite dedup keys
- Entity enrichment: enriches venues and items with taste-relevant attributes (cuisine, price level, neighborhood, vibe) via Google Maps and web search
- Strength model: frequency bonuses, recency bonuses, and extraction confidence thresholds
- Recommendation rules: discovery-only (never recommend visited places, except seasonal menu changes), dietary restriction enforcement, enrichment-aware pattern reasoning
- User preferences: dietary restrictions, dietary preferences, and cuisine dislikes in config
- New schemas: ExtractionRecord, extended ConsumptionSignal, extended ItemRecord with enrichment fields
- New reference docs: strength_model.md, email_extraction.md, enrichment.md
- New OKRs: email_extraction_coverage, dedup_accuracy, enrichment_coverage

### v3.0.1 -- March 27, 2026
- Added `taste.update` command and midnight cron for automatic version-checked self-updates

### v2.2.0 -- March 22, 2026
- Routing improvements

### v2.1.0 -- March 22, 2026
- Journal documentation and initialization with storage setup

### v2.0.0 -- March 18, 2026
- Initial release as part of the unified OCAS skill suite
---

*Taste is part of the [OCAS Agent Suite](https://github.com/indigokarasu) -- a collection of interconnected skills for personal intelligence, autonomous research, and continuous self-improvement. Each skill owns a narrow responsibility and communicates with others through structured signal files, shared journals, and Chronicle, a long-term knowledge graph that accumulates verified facts over time.*
