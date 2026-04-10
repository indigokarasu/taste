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
  version: "3.4.2"
  hermes:
    tags: [preferences, recommendations, food]
    category: preference
    cron:
      - name: "taste:update"
        schedule: "0 0 * * *"
        command: "taste.update"
      - name: "taste:sync-spotify"
        schedule: "0 0 * * *"
        command: "taste.sync.spotify"
  openclaw:
    skill_type: system
    visibility: public
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
        schedule: "0 0 * * *"
        command: "taste.update"
      - name: "taste:sync-spotify"
        schedule: "0 0 * * *"
        command: "taste.sync.spotify"
---

# Taste

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
- `taste.sync.spotify` — pull recent Spotify listening history via spotify-history skill; creates/updates music ConsumptionSignals; runs daily via scheduled task

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

1. Access the user's email and search for transactional messages from known services (see `references/email_extraction.md` for sender allowlist)
2. Access the user's Google Calendar for restaurant reservations and hotel bookings
3. For each matching message/event, extract structured data into an ExtractionRecord
4. Classify email_type: confirmation, reminder, update, cancellation, receipt
5. Compute dedup_key and run dedup pass (see `references/email_extraction.md`)
6. Exclude cancelled events from promotion
7. Promote valid, non-duplicate extractions to ConsumptionSignals
8. Create or update ItemRecords (increment signal_count, append to visit_dates)
9. Queue unenriched items for enrichment
10. Persist all records
11. Write journal

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

1. Call spotify-history skill's `recent` command to get last 24 hours of plays
2. Call spotify-history skill's `top-tracks short_term` for recent favorites
3. For each track: create a ConsumptionSignal with `domain: "music"`, `source: "play"`, `strength: 0.60`
4. For each track: create or update an ItemRecord with play counts and visit_dates
5. Deduplicate by track_id + timestamp against existing signals
6. Write new signals to `signals.jsonl` and items to `items.jsonl`
7. Update `music/spotify_sync_checkpoint.json` with last sync timestamp
8. Write journal with entity observations for Elephas ingestion

No external scripts required — spotify-history provides the Spotify API access.

Default config.json:
```json
{
  "skill_id": "ocas-taste",
  "skill_version": "3.0.0",
  "config_version": "2",
  "created_at": "",
  "updated_at": "",
  "domains": {
    "enabled": ["music", "restaurant", "book", "movie", "product", "travel", "event"]
  },
  "decay": {
    "halflife_days": 180
  },
  "retention": {
    "days": 0,
    "max_records": 10000
  },
  "email_scan": {
    "enabled": true,
    "last_scan_timestamp": null,
    "extraction_confidence_threshold": 0.6,
    "auto_promote_threshold": 0.8
  },
  "email_sources": {
    "doordash": { "sender_patterns": ["no-reply@doordash.com", "orders@doordash.com"], "domain": "restaurant", "source_type": "purchase" },
    "instacart": { "sender_patterns": ["no-reply@instacart.com"], "domain": "product", "source_type": "purchase" },
    "good_eggs": { "sender_patterns": ["*@goodeggs.com"], "domain": "product", "source_type": "purchase" },
    "tock": { "sender_patterns": ["*@exploretock.com"], "domain": "restaurant", "source_type": "visit" },
    "opentable": { "sender_patterns": ["*@opentable.com"], "domain": "restaurant", "source_type": "visit" },
    "yelp": { "sender_patterns": ["no-reply@yelp.com"], "domain": "restaurant", "source_type": "visit" },
    "amazon": { "sender_patterns": ["auto-confirm@amazon.com", "ship-confirm@amazon.com"], "domain": "product", "source_type": "purchase" },
    "hotels": { "sender_patterns": ["*@booking.com", "*@hotels.com", "*@marriott.com", "*@hilton.com", "*@hyatt.com", "*@ihg.com", "*@airbnb.com"], "domain": "travel", "source_type": "stay" }
  },
  "strength": {
    "base_purchase": 0.80,
    "base_visit": 0.70,
    "base_stay": 0.75,
    "base_play": 0.60,
    "base_watch": 0.60,
    "base_manual": 0.60,
    "frequency_bonus_per_visit": 0.05,
    "frequency_bonus_cap": 0.15,
    "recency_bonus_days": 30,
    "recency_bonus_value": 0.05
  },
  "user_preferences": {
    "dietary_restrictions": [],
    "dietary_preferences": [],
    "cuisine_dislikes": [],
    "notes": ""
  }
}
```

## OKRs

Universal OKRs from spec-ocas-journal.md apply to all runs.

```yaml
skill_okrs:
  - name: recommendation_evidence_rate
    metric: fraction of recommendations citing at least one consumed item
    direction: maximize
    target: 1.0
    evaluation_window: 30_runs
  - name: serendipity_novelty
    metric: fraction of serendipity results crossing domain boundaries
    direction: maximize
    target: 0.80
    evaluation_window: 30_runs
  - name: signal_freshness
    metric: fraction of active signals within decay half-life
    direction: maximize
    target: 0.60
    evaluation_window: 30_runs
  - name: email_extraction_coverage
    metric: fraction of transactional emails successfully extracted with confidence >= threshold
    direction: maximize
    target: 0.90
    evaluation_window: 30_runs
  - name: dedup_accuracy
    metric: fraction of dedup groupings not subsequently corrected by manual review
    direction: maximize
    target: 0.95
    evaluation_window: 30_runs
  - name: enrichment_coverage
    metric: fraction of items with enriched = true
    direction: maximize
    target: 0.90
    evaluation_window: 30_runs
```

## Optional skill cooperation

- Google Maps — entity enrichment (cuisine, price level, neighborhood, vibe, rating)
- Web search — backup enrichment when Google Maps data is insufficient
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

## Background tasks

| Job name | Mechanism | Schedule | Command |
|---|---|---|---|
| `taste:update` | cron | `0 0 * * *` (midnight daily) | `taste.update` |

```
# Task declared in SKILL.md frontmatter metadata.{platform}.cron
```


## Self-update

`taste.update` pulls the latest package from the `source:` URL in this file's frontmatter. Runs silently — no output unless the version changed or an error occurred.

1. Read `source:` from frontmatter → extract `{owner}/{repo}` from URL
2. Read local version from `skill.json`
3. Fetch remote version: `gh api "repos/{owner}/{repo}/contents/skill.json" --jq '.content' | base64 -d | python3 -c "import sys,json;print(json.load(sys.stdin)['version'])"`
4. If remote version equals local version → stop silently
5. Download and install:
   ```bash
   TMPDIR=$(mktemp -d)
   gh api "repos/{owner}/{repo}/tarball/main" > "$TMPDIR/archive.tar.gz"
   mkdir "$TMPDIR/extracted"
   tar xzf "$TMPDIR/archive.tar.gz" -C "$TMPDIR/extracted" --strip-components=1
   cp -R "$TMPDIR/extracted/"* ./
   rm -rf "$TMPDIR"
   ```
6. On failure → retry once. If second attempt fails, report the error and stop.
7. Output exactly: `I updated Taste from version {old} to {new}`

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

## Update command

This skill self-updates every 24 hours via:

```bash
taste.update
```

This pulls the latest version from GitHub and restarts the skill's background tasks if applicable.
