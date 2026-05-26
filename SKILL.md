---
name: ocas-taste
description: 'Taste: behavior-driven taste model built from real consumption signals.
  Scans user''s email and calendar for consumption data (restaurant reservations,
  food delivery, hotel bookings, purchases), enriches entities with taste-relevant
  attributes via Google Maps, and generates discovery-focused recommendations that
  respect dietary restrictions. Trigger phrases: ''recommend'', ''what would I like'',
  ''based on what I''ve liked'', ''suggest something similar'', ''my taste'', ''what
  should I try'', ''scan my email'', ''what have I been eating'', ''restaurant recommendations'',
  ''update taste''. Do not use for generic search, editorial top-10 lists, or ad-copy
  generation.

  '
license: MIT
metadata:
  author: Indigo Karasu
  version: 3.6.1
source: https://github.com/indigokarasu/taste
includes:
  - references/**
  - evals/**
---

Taste builds a personalized taste model from real consumption signals — purchases, restaurant visits, food delivery orders, hotel stays, music plays, and movie watches. It scans the user's email and calendar to automatically extract these signals, enriches venue entities with taste-relevant attributes (cuisine, price point, neighborhood, vibe) via Google Maps and web search, and uses temporal decay so recent behavior outweighs stale history. Every recommendation names the specific prior consumption that justifies it, respects dietary restrictions, and only suggests places the user hasn't been.

## When to Use

- Scanning email and calendar for consumption signals (restaurant bookings, delivery orders, hotel stays, purchases)
- Personalized recommendations grounded in real prior behavior
- Cross-domain discovery based on actual taste signals
- "What else would I like" reasoning with named evidence
- Enriching venue/item entities with taste-relevant attributes
- Taste model status check
- Weekly or periodic taste pattern summary

## When NOT to Use

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

## Implementation

The taste skill runs as agent-driven cron jobs. All Google access goes through the MCP server. See `references/api_auth.md` for credential paths, OAuth patterns, and the `google_auth` helper usage. See `references/api_specifics.md` for Gmail, Calendar, and Places API details.

## Cron failure fallback

See `references/cron_failure.md` for the full fallback procedure. Key point: when `invalid_grant` occurs, full re-auth is required — no retry will help.

## Operating invariants

- Evidence-first: recommendations must reference specific consumed items
- Discovery-only: never recommend places the user has already been (exception: seasonal menu changes)
- Dietary safety: never recommend venues that conflict with stated dietary restrictions
- Signal decay: older signals degrade unless reinforced; frequency matters: repeat visits are a strong signal
- No speculative identity inference from taste signals
- Explainability: every recommendation explains the link to prior consumption
- First-party signals outrank enriched metadata
- Confidence reflects actual evidence strength, not rhetorical certainty
- Always use the user's email account, never the agent's account

## Workflows

All workflows follow a consistent pattern: **extract → dedup → enrich → recommend**.

### Email/calendar scan (`taste.scan`)

**Purpose:** Extract consumption signals from email and calendar, deduplicate, and queue for enrichment.

**Pre-flight:**
1. Load Google OAuth credentials per `references/api_auth.md`. Use the user profile for email; fall back to agent profile only for calendar.
2. If token fails with `invalid_grant`, follow `references/cron_failure.md` — don't silently skip.

**Extract:**
3. Build Gmail query per configured service. Correct form: `({sender_query}) after:{date_str}` — wrong form returns every email after the date.
4. Enumerate writable calendars via `calendarList().list()` (not just `primary`). Filter `accessRole in ('owner', 'writer')`.
5. Extract structured data into ExtractionRecords. Validate: drop records with empty `venue_name` or `from` addresses not matching configured `sender_patterns`.

**Normalize:**
6. Strip `Reservation at ` prefix and city suffixes (` - San Francisco`, ` - SF`, etc.).
7. Apply venue-detection heuristics: exclude medical/video calls/generic meetings; include meal keywords, hotel brands, event types.
8. Classify email_type: confirmation, reminder, update, cancellation, receipt.

**Dedup & persist:**
9. Cross-calendar dedup key: `{service}:{normalized_venue}:{event_date[:10]}`. Same venue on different dates = separate signals.
10. Exclude cancelled events. Promote valid extractions to ConsumptionSignals.
11. Create/update ItemRecords, queue unenriched items.
12. Write journal.

**Edge cases:**
- Empty scan (no new signals): still write evidence record with `not_activity_reason: no_new_signals`.
- Partial parse failure: log error, continue with successfully parsed records.
- Calendar API returns empty: check `accessRole` filter isn't too restrictive; fall back to `primary` only if needed.

See `references/email_extraction.md` for sender allowlist and extraction rules.

### Enrichment (`taste.enrich.item`)

**Purpose:** Add taste-relevant attributes (cuisine, price, neighborhood, vibe) to items via Google Maps.

1. Look up unenriched items on Google Maps via Styx (`styx_places_enrich.py`).
2. Extract attributes per `references/enrichment.md`.
3. Use web search (Sift) to fill gaps if Google Maps data is insufficient.
4. Update ItemRecord metadata, set `enriched: true` and `enriched_at`.
5. Create LinkRecords between items sharing attributes. Persist.

**⚠️ CRITICAL:** Dedup check uses `venue_name`, not `name`. Verify when modifying item schema.

**Edge cases:**
- Google Maps returns no results: fall back to web search, mark with lower confidence.
- Duplicate venue names after normalization: merge only if same normalized name AND same date range.

Bulk enrich: `python {skill_root}/scripts/styx_places_enrich.py --limit 200`

### Signal ingestion (`taste.ingest.signal`)

1. Receive/normalize input signal. Validate domain and structure.
2. Persist signal, create/update ItemRecord, queue for enrichment if new. Write journal.

### Recommendation (`taste.query.recommend`)

**Purpose:** Generate personalized restaurant/venue recommendations grounded in proven consumption history.

1. Load active signals, apply temporal decay (see `references/signal_policy.md`).
2. Compute effective item strength with frequency and recency bonuses (see `references/strength_model.md`).
3. Rank items by strength within each domain. Identify taste patterns from enriched attributes.
4. Generate recommendations for *new* venues matching identified patterns.
5. Verify against dietary restrictions and that user hasn't visited.
6. Include evidence-linked explanation citing specific consumed items. Write journal.

**Edge cases:**
- No enriched items available: explain to user that recommendations need enrichment first, trigger a scan.
- All matching venues already visited: expand search radius or relax pattern constraints, explain trade-off to user.
- Dietary restriction matches zero venues: report honestly, don't suggest violating restrictions.

## Signal weighting and decay

See `references/signal_weighting.md` and `references/strength_model.md` for full model.

## Recovery Behavior

See `references/recovery.md` for the full recovery contract.

## Storage layout

See `references/storage_layout.md` for data directory structure and enrichment pipeline.

## Spotify sync (`taste.sync.spotify`)

See `references/spotify_sync.md` for the full sync procedure.

## OKRs

See `references/okrs.md` for the full OKR table.

## Optional skill cooperation

- **Google Maps** — entity enrichment (cuisine, price level, neighborhood, vibe, rating)
- **SearchX (local SearXNG)** — backup enrichment when Google Maps data is insufficient
- Sift — additional item enrichment via web research
- Elephas — read Chronicle for entity context; journal entity observations for Chronicle ingestion
- Thread — may use Thread signals to detect emerging taste patterns

## Journal outputs

See `references/journal.md` for journal format. All signal ingestion, scan, enrichment, query, and report runs write observation journals.

Taste entities default to `user` relevance since they reflect actual preferences and consumption patterns.

## Initialization

See `references/initialization.md` for the full `taste.init` procedure.

## Automation

See `references/automation.md` for cron job schedule and backup details.

## Self-Update

`taste:update` runs daily at midnight, pulling the latest package from the `source:` URL. Full procedure in `references/self_update.md`.

## Gotchas

- **`invalid_grant` means full re-auth required** — When the Gmail/Calendar OAuth token fails with `invalid_grant`, no retry will help. Full re-authorization via `access_type=offline&prompt=consent` is required. Always output the re-auth URL in the scan report.
- **Legacy data path is stale** — An old data path may exist but is STALE. Active data is ONLY under `{agent_root}/commons/data/ocas-taste/`. Scripts referencing the old path will read outdated data.
- **Dedup key includes service + venue + date** — The cross-calendar dedup key is `{service}:{normalized_venue}:{event_date[:10]}`. Two extractions from different sources for the same venue on the same day are correctly deduplicated, but the same venue on different dates creates separate signals.
- **Enrichment script dedup uses `venue_name`, not `name`** — The enrichment pipeline's dedup check looks at `venue_name`, not the generic `name` field. Verify dedup logic when modifying the item schema.
- **Calendar scan enumerates writable calendars** — The scan calls `calendarList().list()` and filters for `accessRole in ('owner', 'writer')`, not just `primary`. Some consumption signals may come from shared or secondary calendars the user didn't expect.


## Self-update

`taste.update` pulls the latest package from GitHub. Runs silently — no output unless the version changed or an error occurred.

1. Read `source:` from frontmatter
2. Read local version from SKILL.md frontmatter `metadata.version`
3. Fetch remote version via gh CLI
4. If versions match → stop silently
5. Download and install updated package
6. On failure → retry once, then report error
7. Output: `I updated taste from version {old} to {new}`

## Support File Map

| File | When to read |
|---|---|
| `references/api_specifics.md` | During scan or enrichment; API-specific query syntax and rate limits |
| `references/api_auth.md` | Before Gmail/Calendar/Spotify API calls; OAuth patterns and token pitfalls |
| `references/automation.md` | When troubleshooting cron jobs or backup failures |
| `references/backup.md` | Backup/restore procedures, LFS tracking, disk space management |
| `references/config.default.json` | On `taste.init`; template for a fresh config.json |
| `references/cron_failure.md` | When Gmail/Calendar OAuth token fails with `invalid_grant` |
| `references/email_extraction.md` | Before running taste.scan; sender allowlist and dedup rules |
| `references/enrichment.md` | Before running taste.enrich.item; what to extract per domain, false-positive filtering, dedup |
| `references/historical_scan_auth.md` | Before running historical email or calendar scans |
| `references/initialization.md` | On first invocation of any Taste command |
| `references/journal.md` | Before taste.journal; at end of every run |
| `references/okrs.md` | During performance review or model status reporting |
| `references/recommendation_style.md` | Before generating recommendations or reports |
| `references/recovery.md` | On every wake; gap detection and degraded mode logic |
| `references/schemas.md` | Before creating signals, items, links, extractions, or recommendations |
| `references/self_update.md` | Before `taste.update`; full pull/install procedure |
| `references/signal_dedup.md` | After enrichment runs to dedup same-day signals from multiple sources |
| `references/signal_policy.md` | Before decay calculations or domain gating |
| `references/signal_weighting.md` | Before computing signal strength or computing temporal decay |
| `references/spotify_sync.md` | Before `taste.sync.spotify`; music playback history procedure |
| `references/storage_layout.md` | When debugging data path issues or managing disk |
| `references/strength_model.md` | Before computing signal strength or ranking items |
| `scripts/taste_full_enrich.py` | Full pipeline: styx + email + existing unenriched items |
| `scripts/taste_cleanup_and_enrich.py` | Cross-source dedup + retry failed enrichments |
