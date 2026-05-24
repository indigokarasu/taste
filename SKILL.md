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
includes:
  - references/**
  - evals/**
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

## Implementation

The taste skill runs as agent-driven cron jobs. All Google access goes through the MCP server. See `references/api_auth.md` for credential paths, OAuth patterns, and the `google_auth` helper usage.

### API specifics

**Gmail API:**
- Query syntax: space = AND, OR must be uppercase, date filters use `after:` not `since:`.
- The `from:` operator matches partial domains: `from:@opentable.com` matches all OpenTable emails.
- Rate limit: 250 quota units per user per second. A `messages().list()` costs 5 units, `messages().get()` costs 1 unit.
- Pagination: always check `nextPageToken` — a single query can return hundreds of results.

**Google Calendar API:**
- `calendarList().list()` returns all calendars the user has access to, including shared ones.
- `events().list()` requires `singleEvents=true` to expand recurring events into individual instances.
- Time format: RFC 3339 (`2024-01-15T00:00:00-08:00`). Always include timezone offset.
- The `accessRole` field determines write access: `owner` and `writer` can create events; `reader` and `freeBusyReader` cannot.

**Google Places API (via Styx):**
- Text search endpoint: `places:searchText` — best for natural language queries like "Italian restaurant in Mission District".
- Nearby search: `places:searchNearby` — best when you have coordinates.
- Rate limit: 100 requests/second on the free tier.
- Response includes `displayName`, `formattedAddress`, `priceLevel`, `rating`, and `types` — map these to taste attributes per `references/enrichment.md`.

## Cron failure fallback

When a taste cron job runs and the Gmail/Calendar OAuth token is revoked (all refresh attempts return `invalid_grant`):

1. **Don't SILENT-fail.** Always output a report containing: auth failure diagnosis, OAuth re-authorization URL, current taste model state, and any data quality issues.
2. **Check credentials.** All Google credentials are centralized in the agent's credential directory (typically `~/.google_workspace_mcp/credentials/`). If refresh fails with `invalid_grant`, full re-auth is required — no retry will help. See `references/api_auth.md` for paths and patterns.
3. **Generate the auth URL** using the re-auth procedure in `infrastructure/google-workspace-auth` skill.
4. **Report existing data quality.** Even when scan fails, analyze existing `signals.jsonl` and `items.jsonl` for: enrichment coverage (target: 90%), signal freshness (fraction within 180-day half-life), calendar noise, duplicate venue names.

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
2. If token fails with `invalid_grant`, follow the cron failure fallback section above — don't silently skip.

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

### Enrichment (`taste.enrich.item`)

**Purpose:** Add taste-relevant attributes (cuisine, price, neighborhood, vibe) to items via Google Maps.

**Steps:**
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

**Steps:**
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

See `references/strength_model.md` for full model. Key points:
- Config: `decay.halflife_days` (default 180)
- Frequency bonus: +0.05 per repeat visit, capped at +0.15
- Recency bonus: +0.05 if last signal within 30 days

## Recovery Behavior

Implements the recovery contract from `spec-ocas-recovery.md`.

- **Evidence**: Every run writes to `evidence.jsonl`, including no-op runs (mandatory `not_activity_reason` field).
- **Gap detection**: On every wake, checks evidence log. If gap exceeds cadence (24h), logs `gap_detected`.
- **Degraded mode**: When Gmail/Calendar API tokens fail, implements fallback per cron failure pattern above. Logs `degraded: <api>`.
- **Log compaction**: Evidence/decision logs older than 30 days (no-op) or 90 days (error/gap) compacted. Last 7 days retained.

## Storage layout

```
{agent_root}/commons/data/ocas-taste/
  config.json
  signals.jsonl       ← consumption signals
  items.jsonl         ← entities (restaurants, venues, media items)
  links.jsonl         ← entity relationship links
  decisions.jsonl     ← audit log
  extractions.jsonl   ← raw email/calendar extractions
  intents.jsonl       ← intent tracking for scan/enrich/recommend operations
  evidence.jsonl      ← evidence records for recovery contract
  scripts/            ← taste_full_enrich.py, taste_cleanup_and_enrich.py
  music/
    spotify_sync_checkpoint.json

{agent_root}/commons/journals/ocas-taste/
  YYYY-MM-DD/
    {run_id}.json
```

Enrichment pipeline:
```bash
python3 scripts/taste_full_enrich.py        # Full scan: styx + email + existing items
python3 scripts/taste_cleanup_and_enrich.py  # Dedup + retry failed items
```

Name matching / rename patterns for enrichment: Styx merchants frequently have messy names from Plaid. See `references/enrichment.md` for the full list of observed patterns and normalization rules. Key principle: cross-source dedup means same restaurant via email + calendar + styx = one entry. Normalize by lowercasing, stripping articles, location suffixes, and venue-type suffixes.

⚠️ LEGACY: An old data path may exist but is STALE. Active data is ONLY under `{agent_root}/commons/data/ocas-taste/`.

### Spotify sync (`taste.sync.spotify`)

Music playback history is stored as standard ConsumptionSignal records in `signals.jsonl` with `domain: "music"` and `source: "play"`.

1. Verify valid Spotify token (skip if expired with no `refresh_token` — requires interactive re-auth).
2. Call Spotify MCP: `get_recently_played` (last 24h) and `get_top_items`.
3. Create ConsumptionSignals (`strength: 0.60`) and ItemRecords per track.
4. Deduplicate by track name + artist. Persist to JSONL files.
5. Update `music/spotify_sync_checkpoint.json`. Write journal.

See `references/api_auth.md` for Spotify MCP setup and env vars.

## OKRs

Universal OKRs from spec-ocas-journal.md apply. All OKRs maximize against a 30-run evaluation window.

| Name | Metric | Target |
|---|---|---|
| `recommendation_evidence_rate` | fraction of recommendations citing at least one consumed item | 1.0 |
| `serendipity_novelty` | fraction of serendipity results crossing domain boundaries | 0.80 |
| `signal_freshness` | fraction of active signals within decay half-life | 0.60 |
| `email_extraction_coverage` | fraction of transactional emails extracted with confidence >= threshold | 0.90 |
| `dedup_accuracy` | fraction of dedup groupings not corrected by manual review | 0.95 |
| `enrichment_coverage` | fraction of items with enriched = true | 0.90 |
| `schedule_adherence` | fraction of cron runs completing within scheduled hour | 0.95 |
| `data_integrity` | fraction of signals/items passing schema validation on read | 0.99 |

## Optional skill cooperation

- **Google Maps** — entity enrichment (cuisine, price level, neighborhood, vibe, rating)
- **SearchX (local SearXNG)** — backup enrichment when Google Maps data is insufficient
- Sift — additional item enrichment via web research
- Elephas — read Chronicle for entity context; journal entity observations for Chronicle ingestion
- Thread — may use Thread signals to detect emerging taste patterns

## Journal outputs

All signal ingestion, scan, enrichment, query, and report runs write observation journals. When entities are encountered, include in `decision.payload`:

- `entities_observed` — list of entities (type, name, `user_relevance`: `user`, `agent_only`, or `unknown`)
- `relationships_observed` — relationships between entities encountered
- `preferences_observed` — user preferences linked to entities

Taste entities default to `user` relevance since they reflect actual preferences and consumption patterns.

## Initialization

On first invocation of any Taste command, run `taste.init`:

1. Create `{agent_root}/commons/data/ocas-taste/` and subdirectories
2. Write default `config.json` if absent (from `references/config.default.json`)
3. Create empty JSONL files: `signals.jsonl`, `items.jsonl`, `links.jsonl`, `decisions.jsonl`, `extractions.jsonl`, `intents.jsonl`, `evidence.jsonl`
4. Create `{agent_root}/commons/journals/ocas-taste/`
5. Register cron job `taste:update` if not already present
6. Log initialization as a DecisionRecord in `decisions.jsonl`

## Automation

### Daily cron jobs

| Job | Time | What |
|-----|------|------|
| `plaid-transaction-sync` | 07:00 | Pulls new bank transactions into styx.db |
| `styx:enrich-new-transactions` | 07:30 | Enriches new styx merchants via Google Places |
| `taste:daily-styx-enrichment` | 08:00 | Full pipeline: styx_places_enrich → taste_full_enrich → taste_signals_dedup |
| `taste:historical-email` | 09:02 | Scans email for restaurant reservations/deliveries |
| `taste:historical-calendar` | 10:10 | Scans calendar for restaurant/hotel events |
| `taste:scan` | 13:12 | Daily email/calendar scan + Styx→Taste delta ingestion |
| `Backup Hermes Sessions to GitHub` | 03:00 | Backs up all DBs + taste flatfiles to GitHub LFS |

### Backup

All taste and styx data is backed up to GitHub LFS (`indigo-repo`): `data/styx.db`, `data/ocas-taste-*.jsonl`, `data/chronicle.lbug`, `data/weave.lbug`, `data/transactions.db`, `data/chroma.sqlite3`. LFS tracks: `*.jsonl`, `*.db`, `*.lbug`, `*.sqlite3`, `*.tar.gz`.

⚠️ `state.db` is SKIPPed in backup — too large for GitHub.

### Self-update

`taste:update` runs daily at midnight, pulling the latest package from the `source:` URL. Full procedure in `references/self_update.md`.

## Visibility

public

## Gotchas

- **`invalid_grant` means full re-auth required** — When the Gmail/Calendar OAuth token fails with `invalid_grant`, no retry will help. Full re-authorization via `access_type=offline&prompt=consent` is required. Always output the re-auth URL in the scan report.
- **Legacy data path is stale** — An old data path may exist but is STALE. Active data is ONLY under `{agent_root}/commons/data/ocas-taste/`. Scripts referencing the old path will read outdated data.
- **Dedup key includes service + venue + date** — The cross-calendar dedup key is `{service}:{normalized_venue}:{event_date[:10]}`. Two extractions from different sources for the same venue on the same day are correctly deduplicated, but the same venue on different dates creates separate signals.
- **Enrichment script dedup uses `venue_name`, not `name`** — The enrichment pipeline's dedup check looks at `venue_name`, not the generic `name` field. Verify dedup logic when modifying the item schema.
- **Calendar scan enumerates writable calendars** — The scan calls `calendarList().list()` and filters for `accessRole in ('owner', 'writer')`, not just `primary`. Some consumption signals may come from shared or secondary calendars the user didn't expect.

## Support file map

| File | When to read |
|---|---|
| `references/schemas.md` | Before creating signals, items, links, extractions, or recommendations |
| `references/signal_policy.md` | Before decay calculations or domain gating |
| `references/strength_model.md` | Before computing signal strength or ranking items |
| `references/email_extraction.md` | Before running taste.scan; sender allowlist and dedup rules |
| `references/enrichment.md` | Before running taste.enrich.item; what to extract per domain, false-positive filtering, dedup |
| `references/recommendation_style.md` | Before generating recommendations or reports |
| `references/journal.md` | Before taste.journal; at end of every run |
| `references/api_auth.md` | Before Gmail/Calendar/Spotify API calls; OAuth patterns and token pitfalls |
| `references/config.default.json` | On `taste.init`; template for a fresh config.json |
| `references/self_update.md` | Before `taste.update`; full pull/install procedure |
| `references/signal_dedup.md` | After enrichment runs to dedup same-day signals from multiple sources |
| `references/backup.md` | Backup/restore procedures, LFS tracking, disk space management |
| `scripts/taste_full_enrich.py` | Full pipeline: styx + email + existing unenriched items |
| `scripts/taste_cleanup_and_enrich.py` | Cross-source dedup + retry failed enrichments |
| `scripts/taste_signals_dedup.py` | Dedup signals by (venue, date) — priority: styx > calendar > email |
