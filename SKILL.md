---
name: ocas-taste
description: >
  Taste: behavior-driven taste model built from real consumption signals.
  Scans user's email and calendar for consumption data (restaurant
  reservations, food delivery, hotel bookings, purchases), enriches entities
  with taste-relevant attributes via Google Maps, and generates
  discovery-focused recommendations that respect dietary restrictions. Trigger
  phrases: 'recommend', 'what would I like', 'based on what I've liked',
  'suggest something similar', 'my taste', 'what should I try', 'scan my
  email', 'what have I been eating', 'restaurant recommendations', 'update
  taste'. Do not use for generic search, editorial top-10 lists, or ad-copy
  generation.
metadata:
  author: Indigo Karasu
  email: mx.indigo.karasu@gmail.com
  version: "3.5.0"
  hermes:
    tags: [preferences, recommendations, food]
    category: preference
    cron:
      - name: "taste:update"
        schedule: "25 7 * * *"
        command: "taste.update"
      - name: "taste:sync-spotify"
        schedule: "10 7 * * *"
        command: "taste.sync.spotify"
      - name: "taste:historical-email"
        schedule: "0 9 * * *"
        command: "taste.historical.email"
      - name: "taste:historical-calendar"
        schedule: "10 10 * * *"
        command: "taste.historical.calendar"
      - name: "taste:scan"
        schedule: "10 13 * * *"
        command: "taste.scan"
  openclaw:
    skill_type: system
    filesystem:
      read:
        - "{agent_root}/commons/data/ocas-taste/"
        - "{agent_root}/commons/journals/ocas-taste/"
      write:
        - "{agent_root}/commons/data/ocas-taste/"
        - "{agent_root}/commons/journals/ocas-taste/"
    self_update:
      source: "https://github.com/indigokarasu/taste"
      mechanism: "version-checked tarball from GitHub via gh CLI"
      command: "taste.update"
      requires_binaries: [gh, tar, python3]
    cron:
      - name: "taste:update"
        schedule: "25 7 * * *"
        command: "taste.update"
      - name: "taste:sync-spotify"
        schedule: "10 7 * * *"
        command: "taste.sync.spotify"
      - name: "taste:historical-email"
        schedule: "0 9 * * *"
        command: "taste.historical.email"
      - name: "taste:historical-calendar"
        schedule: "10 10 * * *"
        command: "taste.historical.calendar"
      - name: "taste:scan"
        schedule: "10 13 * * *"
        command: "taste.scan"
---

Taste builds a personalized taste model from real consumption signals — purchases, restaurant visits, food delivery orders, hotel stays, music plays, and movie watches. It scans the user's email and calendar to automatically extract these signals, enriches venue entities with taste-relevant attributes (cuisine, price point, neighborhood, vibe) via Google Maps and web search, and uses temporal decay so recent behavior outweighs stale history. Every recommendation names the specific prior consumption that justifies it, respects dietary restrictions, and only suggests places the user hasn't been.

## When to use

- Scanning email and calendar for consumption signals (restaurant bookings, delivery orders, hotel stays, purchases)
- Personalized recommendations grounded in real prior behavior
- Cross-domain discovery based on actual taste signals
- "What else would I like" reasoning with named evidence
- Enriching venue/item entities with taste-relevant attributes
- Taste model status check
- Weekly or periodic taste pattern summary

## Do not use

- Generic web research — use Sift
- Editorial/top-10 style recommendations without personalization
- Ad-copy or sales-oriented product suggestions
- Inference of sensitive identity traits from behavior

## Responsibility boundary

Taste owns behavior-driven preference modeling, consumption signal extraction from email/calendar, entity enrichment for taste profiling, and evidence-backed recommendations.

Taste does not own: web research (Sift), social graph (Weave), knowledge graph (Elephas), pattern analysis (Corvus), browsing interpretation (Thread).

## Ontology types

Taste works with these types from `spec-ocas-ontology.md`:

- **Place** — venues (restaurants, cafes, bars, retail, entertainment spaces). Extracted from consumption events; enriched via Google Maps or Sift.
- **Thing/DigitalArtifact** — consumed media items (articles, videos, podcasts, books, albums). Stored as ItemRecords.
- **Concept/Action** — behavioral actions (consumed, saved, skipped, dismissed, rated). Used as signal types in ConsumptionSignal.
- **Concept/Idea** — cuisines, genres, categories, and other taste dimensions.
- **Entity/Person** — chefs, artists, creators, and other individuals the user likes or follows.

Taste maintains its own preference model in `{agent_root}/commons/data/ocas-taste/`. See `spec-ocas-shared-schemas.md` for ConsumptionSignal and ItemRecord schemas.

## Commands

- `taste.scan` — scan the user's email and calendar for consumption signals; extract, deduplicate, and promote to signals; queue new items for enrichment
- `taste.scan.report` — summarize last scan: extractions processed, signals created, cancellations, dedup matches pending review
- `taste.ingest.signal` — manually record a consumption signal (purchase, visit, play, watch, stay)
- `taste.enrich.item` — enrich an item with taste-relevant attributes via Google Maps lookup and web search
- `taste.query.recommend` — generate recommendations grounded in consumption history, enriched attributes, and frequency patterns; respects dietary restrictions; only suggests new places
- `taste.query.serendipity` — find novel but defensible cross-domain connections
- `taste.model.status` — return model state: signal count, domains active, enrichment coverage, staleness
- `taste.report.weekly` — generate a weekly taste pattern summary
- `taste.journal` — write journal for the current run; called at end of every run
- `taste.update` — pull latest from GitHub source; preserves journals and data
- `taste.sync.spotify` — pull recent Spotify listening history via Spotify MCP; creates/updates music ConsumptionSignals; runs daily via scheduled task

## Operating invariants

- Evidence-first: recommendations must reference specific consumed items
- Discovery-only: never recommend places the user has already been (exception: seasonal menu changes)
- Dietary safety: never recommend venues that conflict with stated dietary restrictions or preferences
- Signal decay: older signals degrade unless reinforced
- Frequency matters: repeat visits/orders are a strong signal and must be tracked and weighted
- No speculative identity inference from taste signals
- Explainability: every recommendation explains the link to prior consumption
- First-party signals outrank enriched metadata
- Disabled domains do not appear in recommendations
- Confidence reflects actual evidence strength, not rhetorical certainty
- Always use the user's email account, never the agent's account

## Workflows

### Email/calendar scan workflow (`taste.scan`)

Gmail and Calendar access uses direct Google API clients with OAuth credentials loaded via the multi-profile discovery pattern in `references/api_auth.md`. <!-- TODO: migrate OAuth to ocas-auth skill -->

1. Load Google OAuth credentials per `references/api_auth.md`. Use the user profile for email (the agent profile has no consumption emails); fall back to the agent profile only for calendar.
2. Build the Gmail query for each configured service. Use OR between terms, AND across clauses — Gmail API treats space as AND by default, so sender terms must be grouped in parentheses before the date clause. Wrong form `from:a OR from:b OR after:YYYY/MM/DD` returns every email after the date; correct form is:
   ```python
   sender_query = " OR ".join(f"from:{p}" for p in sender_patterns)
   query = f"({sender_query}) after:{date_str}"
   ```
3. For each matching message, extract structured data into an ExtractionRecord. After extraction, validate: drop records with `venue_name` in (None, "Unknown", "") and drop records whose `from` address does not match the configured `sender_patterns` for the service (wildcard patterns like `*@exploretock.com` are partial matches and will otherwise pull in unrelated mail).
4. Enumerate writable calendars, not just `primary`. Scanning only `calendarId='primary'` misses shared calendars where reservation and hotel events typically live; in practice this is the difference between 2 events found and 130 venue extractions across 980 events. Call `calendarList().list()`, filter `accessRole in ('owner', 'writer')`, and call `events().list()` for each.
5. Normalize venue names pulled from calendar summaries before dedup. Strip leading `Reservation at ` and trailing city suffixes (` - San Francisco`, ` – Daly City`, ` - Oakland`, ` - SF`).
6. Apply venue-detection heuristics to event titles:
   - Exclude: medical (doctor, dr., one medical, telehealth), video calls (zoom.us, teams.microsoft, google meet), generic meetings (standup, 1:1, sync, interview, therapy, dentist).
   - Include: meal keywords plus venue indicators in location (st, ave, blvd, drive, road), named hotel brands (fairmont, marriott, hilton, hyatt), event types (omakase, chef, tasting, winery, brewery).
7. Classify email_type: confirmation, reminder, update, cancellation, receipt.
8. Compute dedup_key and run dedup pass (see `references/email_extraction.md`). Events often appear in multiple calendars, so use a cross-calendar dedup key of `{service}:{normalized_venue}:{event_date[:10]}` and skip any extraction whose key was already seen in this run.
9. Exclude cancelled events from promotion.
10. Promote valid, non-duplicate extractions to ConsumptionSignals.
11. Create or update ItemRecords (increment signal_count, append to visit_dates).
12. Queue unenriched items for enrichment.
13. Persist all records. If signals.jsonl contains legacy garbage (signals with no real venue or duplicates across the key in step 8), run `scripts/clean_signals.py` against it.
14. Write journal.

### Enrichment workflow (`taste.enrich.item`)

1. For items with `enriched: false`, look up the venue/item on Google Maps
2. Extract taste-relevant attributes: cuisine, price level, neighborhood, vibe, rating (see `references/enrichment.md`)
3. If Google Maps data is insufficient, use web search to fill gaps
4. Update ItemRecord metadata with enriched attributes
5. Set `enriched: true` and `enriched_at`
6. Evaluate and create LinkRecords between items sharing attributes
7. Persist updates

### Signal ingestion workflow (`taste.ingest.signal`)

1. Receive or normalize input signal
2. Validate domain and signal structure
3. Persist signal
4. Create or update ItemRecord
5. Queue for enrichment if new item
6. Write journal

### Recommendation workflow (`taste.query.recommend`)

1. Load all active signals, apply temporal decay (see `references/signal_policy.md`)
2. Compute effective item strength with frequency and recency bonuses (see `references/strength_model.md`)
3. Rank items by effective strength within each domain
4. Identify taste patterns from enriched attributes (cuisine clusters, price preferences, neighborhood tendencies)
5. Generate recommendations for *new* venues that match identified patterns
6. Verify each recommendation against dietary restrictions (`config.json` → `user_preferences`)
7. Verify each recommendation is not a place the user has visited (check signals/items)
8. Include evidence-linked explanation citing specific consumed items and frequency
9. Write journal

## Signal weighting and decay

Signal strength and recency both matter. See `references/strength_model.md` for full model. Key points:
- Config: `decay.halflife_days` (default 180)
- Stale signals weaken unless reinforced by repeat consumption
- Frequency bonus: +0.05 per repeat visit, capped at +0.15
- Recency bonus: +0.05 if last signal within 30 days

## Storage layout

```
{agent_root}/commons/data/ocas-taste/
  config.json
  signals.jsonl
  items.jsonl
  links.jsonl
  decisions.jsonl
  extractions.jsonl
  reports/
  
{agent_root}/commons/data/ocas-taste/music/
  spotify_sync_checkpoint.json — last sync timestamp
  
{agent_root}/commons/journals/ocas-taste/
  YYYY-MM-DD/
    {run_id}.json
```

Music playback history from Spotify is stored as standard ConsumptionSignal records in `signals.jsonl` with `domain: "music"` and `source: "play"`.

### taste.sync.spotify workflow

Authentication and Spotipy client setup are covered in `references/api_auth.md`. <!-- TODO: migrate OAuth to ocas-auth skill -->

1. Before running, verify a valid Spotify token is available. If the cached token is expired and has no `refresh_token`, skip the run — Spotify's user-data endpoints require interactive browser login to re-authorize (`npx @darrenjaws/spotify-mcp setup`), which cron cannot do headlessly.
2. Call Spotify MCP tools: `get_recently_played` for the last 24h of plays and `get_top_items` for recent favorites.
3. Parse MCP output to extract track names and artists.
4. For each track, create a ConsumptionSignal with `domain: "music"`, `source: "play"`, `strength: 0.60`.
5. For each track, create or update an ItemRecord with play counts and visit_dates.
6. Deduplicate by track name + artist against existing signals.
7. Write new signals to `signals.jsonl` and items to `items.jsonl`.
8. Update `music/spotify_sync_checkpoint.json` with last sync timestamp.
9. Write journal with entity observations for Elephas ingestion.

**Spotify MCP prerequisites** (install-time setup lives in `README.md`):
- MCP server: `@darrenjaws/spotify-mcp`
- Environment variables: `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`
- Run setup once: `npx @darrenjaws/spotify-mcp setup`

Default config.json is written from `references/config.default.json` on init. Key sections: `domains.enabled`, `decay.halflife_days`, `email_scan` (thresholds and last_scan_timestamp), `email_sources` (per-service sender_patterns / domain / source_type), `strength` (base weights plus frequency and recency bonuses), `user_preferences` (dietary_restrictions, dietary_preferences, cuisine_dislikes, notes).

## OKRs

Universal OKRs from spec-ocas-journal.md apply to all runs.

All OKRs maximize against a 30-run evaluation window.

| Name | Metric | Target |
|---|---|---|
| `recommendation_evidence_rate` | fraction of recommendations citing at least one consumed item | 1.0 |
| `serendipity_novelty` | fraction of serendipity results crossing domain boundaries | 0.80 |
| `signal_freshness` | fraction of active signals within decay half-life | 0.60 |
| `email_extraction_coverage` | fraction of transactional emails successfully extracted with confidence >= threshold | 0.90 |
| `dedup_accuracy` | fraction of dedup groupings not subsequently corrected by manual review | 0.95 |
| `enrichment_coverage` | fraction of items with enriched = true | 0.90 |

## Optional skill cooperation

- **Google Maps** — entity enrichment (cuisine, price level, neighborhood, vibe, rating)
- **SearchX (local SearXNG)** — backup enrichment when Google Maps data is insufficient, replacing all external paid search APIs.
- Sift — additional item enrichment via web research
- Elephas — read Chronicle (read-only) for entity context
- Elephas — journal entity observations consumed during Chronicle ingestion
- Thread — may use Thread signals to detect emerging taste patterns

## Journal outputs

Observation Journal — all signal ingestion, scan, enrichment, query, and report runs.

When entities are encountered during a run, journals should include the following fields in `decision.payload`:

- `entities_observed` — list of entities encountered (Place for restaurants and venues, Concept/Idea for cuisines and genres, Entity/Person for chefs and creators). Each entry includes type, name/identifier, and a `user_relevance` field (`user`, `agent_only`, or `unknown`).
- `relationships_observed` — list of relationships between entities encountered during the run (e.g., chef-to-restaurant, cuisine-to-venue).
- `preferences_observed` — list of user preferences linked to entities encountered during the run (e.g., frequency of visits, ratings, dietary notes).

All entity observations must include a `user_relevance` field: `user` if the entity is directly related to the user's world, `agent_only` if encountered incidentally, `unknown` if unclear. Taste entities default to `user` since they reflect the user's actual preferences and consumption patterns.

## Initialization

On first invocation of any Taste command, run `taste.init`:

1. Create `{agent_root}/commons/data/ocas-taste/` and subdirectories (`reports/`)
2. Write default `config.json` with all fields if absent
3. Create empty JSONL files: `signals.jsonl`, `items.jsonl`, `links.jsonl`, `decisions.jsonl`, `extractions.jsonl`
4. Create `{agent_root}/commons/journals/ocas-taste/`
5. Register cron job `taste:update` if not already present (check the platform scheduling registry first)
6. Log initialization as a DecisionRecord in `decisions.jsonl`

## Background tasks and self-update

Cron schedule lives in frontmatter `metadata.{platform}.cron`. `taste:update` runs daily at midnight and invokes `taste.update`, which pulls the latest package from the `source:` URL silently unless the version changed. Full procedure in `references/self_update.md`.

## Visibility

public

## Support file map

| File | When to read |
|---|---|
| `references/schemas.md` | Before creating signals, items, links, extractions, or recommendations |
| `references/signal_policy.md` | Before decay calculations or domain gating |
| `references/strength_model.md` | Before computing signal strength or ranking items |
| `references/email_extraction.md` | Before running taste.scan; sender allowlist and dedup rules |
| `references/enrichment.md` | Before running taste.enrich.item; what to look up and extract per domain |
| `references/recommendation_style.md` | Before generating recommendations or reports |
| `references/journal.md` | Before taste.journal; at end of every run |
| `references/api_auth.md` | Before Gmail/Calendar/Spotify API calls; OAuth patterns and known token pitfalls |
| `references/config.default.json` | On `taste.init`; template for a fresh config.json |
| `references/self_update.md` | Before `taste.update`; full pull/install procedure |
