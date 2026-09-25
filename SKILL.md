---
description: Behavior-driven taste model built from real consumption signals. Scans
  email and calendar for consumption data (reservations, delivery orders, hotel
  stays, purchases), enriches entities with taste-relevant attributes via Google
  Maps, and generates discovery-focused recommendations that respect dietary
  restrictions. Not for generic search, editorial top-10 lists, or ad-copy.
includes:
- references/**
- evals/**
- scripts/**
license: MIT
metadata:
  author: Indigo Karasu (indigokarasu)
  version: "3.7.0"
  hermes:
    category: data-science
    config:
      - key: SPOTIFY_REFRESH_TOKEN
        description: OAuth refresh token for Spotify listening-history sync
        default: ""
      - key: GOOGLE_PLACES_API_KEY
        description: Google Places API key used by Styx delta ingestion (no OAuth)
        default: ""
      - key: GOOGLE_MCP_CREDENTIALS
        description: Directory containing Google OAuth token JSON files
        default: ~/.google_workspace_mcp/credentials
    tags:
    - preferences
    - recommendations
    - consumption-signals
    - OCAS-core
name: ocas-taste
source: https://github.com/<agent-handle>/taste
tags:
- preferences
- recommendations
- behavior
- consumption
- OCAS-core
triggers:
- taste model
- consumption signals
- user preferences
- behavioral taste
- preference profile
---

Taste builds a personalized taste model from real consumption signals — purchases, restaurant visits, food delivery orders, hotel stays, music plays, movie watches. It scans email and calendar to extract them, enriches venue entities with taste-relevant attributes, and applies temporal decay so recent behavior outweighs stale history. Every recommendation names the prior consumption that justifies it, respects dietary restrictions, and only suggests places the user hasn't been.

**Support files:** `references/support-file-map.md` indexes every bundled file with a `When to read` trigger — check it before working from assumptions about what is (not) available.

## Interactive Menu

Interactively: present the two-level menu in `references/interactive-menu.md`.

## When to Use

- Scanning email and calendar for consumption signals (bookings, delivery orders, hotel stays, purchases)
- Personalized recommendations grounded in real prior behavior (example: "You liked X, try Y because...")
- Cross-domain discovery and "What else would I like" reasoning with named evidence
- Enriching venue/item entities with taste-relevant attributes
- Taste model status checks; weekly taste pattern summaries
- Styx→Taste delta ingestion (new restaurant transactions from bank data)

## When NOT to Use

- Generic web research — use Sift
- Editorial/top-10 style recommendations without personalization
- Ad-copy or sales-oriented product suggestions
- Inference of sensitive identity traits from behavior

## Responsibility boundary

Taste owns behavior-driven preference modeling, signal extraction, entity enrichment, and evidence-backed recommendations. It does not own: web research (Sift), social graph (Weave), pattern analysis, browsing interpretation (Thread).

## Ontology types

**Place** (venues), **Thing/DigitalArtifact** (consumed media → ItemRecords), **Concept/Action** (signal types), **Concept/Idea** (cuisines, genres), **Entity/Person** (chefs, artists). Types: `spec-ocas-ontology.md`; schemas: `references/schemas.md`. The model lives in `{agent_root}/commons/data/ocas-taste/`.

## Commands

- `taste.scan` — email + calendar scan; extract, dedup, promote, queue enrichment
- `taste.scan.calendar` — calendar-only scan; historical backfill
- `taste.scan.report` — summarize last scan (extractions, signals, cancellations, dedup matches)
- `taste.ingest.signal` — record a signal by hand (purchase, visit, play, watch, stay)
- `taste.enrich.item` — enrich an item via Google Maps + web search
- `taste.query.recommend` — grounded recommendations; restrictions respected; new places only
- `taste.query.serendipity` — novel cross-domain connections
- `taste.model.status` — counts, domains, enrichment coverage, staleness
- `taste.report.weekly` — weekly taste pattern summary
- `taste.journal` — write the run journal (end of every run)
- `taste.sync.spotify` — Spotify history via `scripts/spotify_history_puller.py`; needs `SPOTIFY_REFRESH_TOKEN`

`taste.update` is retired: updates run fleet-wide from the centralized `skills:update-fleet` cron (`scripts/update_skill.sh`) — never `git pull` this skill in place.

## Scripts and runtime

Run taste scripts with `/usr/bin/python3` (system Python — has `googleapiclient`), never the ocas-taste venv. Scripts: `scripts/` under `<hermes-home>/profiles/indigo/skills/ocas-taste/`; data: `<hermes-home>/commons/data/ocas-taste/`. Every script supports `--help`. Key entry points: `taste_scan.py` (scan/incremental/historical/calendar), `taste_full_enrich.py` (Styx→Taste pipeline), `styx_delta_corrected.py` (daily delta), `verify_taste_delta.py` (post-write integrity), `safe_taste_dedup.py` (Styx-safe dedup), `taste_enrich_fix.py` (persist `enriched: true`). Full matrix: `references/script_inventory.md`.

## Workflows

All workflows follow **extract → dedup → enrich → recommend**.

### Email/calendar scan (`taste.scan`)

**Pre-flight:**
- [ ] Load Google OAuth credentials per `references/api_auth.md` — user profile for email, agent profile only as calendar fallback.
- [ ] Repair token expiry immediately before the scan; 0-byte token or `invalid_grant` → `references/cron_failure.md`, report it, don't skip silently.

**Extract / normalize / persist:**
- [ ] Gmail query form `({sender_query}) after:{date_str}`; enumerate writable calendars (`accessRole in ('owner','writer')`), not just `primary`.
- [ ] Drop records with empty `venue_name`; strip `Reservation at ` prefixes and city suffixes; classify email_type.
- [ ] Dedup key `{service}:{normalized_venue}:{event_date[:10]}`; exclude cancellations; promote to ConsumptionSignals; update ItemRecords; write journal.
- [ ] Empty scan still writes an evidence record (`not_activity_reason: no_new_signals`); partial parse failures log and continue.

Sender allowlist + extraction rules: `references/email_extraction.md`.

### Styx delta ingestion (`taste.styx.delta`)

Pull new Styx transactions not yet in Taste, enrich via Google Places, persist. **Standalone — no Google OAuth** (`GOOGLE_PLACES_API_KEY`); works when email/calendar auth is broken. Full procedure: `references/styx_delta.md`.

**⚠️ CRITICAL — dedup by canonical `place_id`, NOT by name (incident 2026-07-15):** near-names like "Taco Bell" vs "Taco Bell Cantina" share one `place_id`; a name-only check silently creates duplicates. If the `place_id` exists, **LINK** the signal to that item (bump `visit_count`, append `visit_dates`, recompute `avg_amount`); otherwise create exactly one canonical item. **Then run `scripts/verify_taste_delta.py --data-dir <real-path>`** — "N created" is testimony, not proof. Recipe: `references/styx_delta_placeid_dedup.md`.

### Enrichment (`taste.enrich.item`)

1. Look up unenriched items via Google Maps / `ocas-styx/scripts/styx_places_enrich.py`; extract attributes per `references/enrichment.md`.
2. Fill gaps with web search (Sift `--format=concise` if available; else local SearXNG `http://localhost:8888` or plain search — never fail over a missing Sift).
3. Update ItemRecord metadata, set `enriched: true` + `enriched_at`, create LinkRecords, persist.

**⚠️ Dedup uses `venue_name`, not `name`.** `taste_full_enrich.py` does NOT persist `enriched: true` — verify by counting `not i.get('enriched',False)`; if unchanged, use `taste_enrich_fix.py`.

### Signal ingestion (`taste.ingest.signal`)

Normalize input, validate domain/structure, persist signal, create/update ItemRecord, queue enrichment if new, write journal.

### Recommendation (`taste.query.recommend`)

1. Load active signals; apply temporal decay (`references/signal_policy.md`) and strength bonuses (`references/strength_model.md`); rank and identify patterns.
2. Search external sources (Eater SF, Michelin, local guides) for candidates matching patterns (`references/recommendation_analysis.md`).
3. Cross-reference every candidate against the visited set — never recommend a venue in signal history; verify dietary restrictions.
4. Format per `references/recommendation_style.md`; cite specific consumed items; write journal.

Edge cases: no enriched items → scan first; all candidates visited → widen radius and say so; zero venues fit restrictions → report honestly.

## Cron fallback

Full fallback procedure: `references/cron_failure.md`. Key points: `invalid_grant` → full re-auth required, no retry helps; 0-byte token → MCP tools fail visibly (`ACTION REQUIRED`) while standalone `google_auth.py` silently falls back to the wrong account; always output the re-auth URL in the scan report; **Styx delta still runs** when auth fails (separate API key).

## Operating invariants

- Evidence-first: recommendations cite specific consumed items
- Discovery-only: never recommend places already visited (exception: seasonal menu changes)
- Dietary safety: never recommend venues that conflict with stated dietary restrictions
- Signal decay: older signals degrade unless reinforced; repeats are strong
- No speculative identity inference from taste signals
- Explainability: every recommendation links to prior consumption
- First-party signals outrank enriched metadata
- Confidence reflects actual evidence strength, not rhetorical certainty
- Always use the user's email account, never the agent's account

## Model internals

- **Weighting/decay:** `references/signal_weighting.md` + `references/strength_model.md`
- **Recovery:** `references/recovery.md` (gap detection, degraded mode)
- **Storage layout:** `references/storage_layout.md` (two-store signals/items architecture)
- **Initialization:** `references/initialization.md` (`taste.init`, first invocation)
- **Journal:** `references/journal.md` — all runs write observation journals

## Historical Backfill

For gap-filling historical consumption signals:

- Patch the `scan-historical` date bug FIRST (`parsedate_to_datetime()`; `references/scan_historical_date_bug.md`) — unpatched, every signal gets the scan time.
- Run `taste_scan.py scan-historical N` / `scan-calendar N` in bounded chunks; filter calendar results aggressively (positive: restaurant/dinner/lunch; negative: appointment/meeting/zoom) — otherwise ~70% are noise. Neither runs Styx delta or enrichment.
- Dedup after: `safe_taste_dedup.py --dry-run`, then apply; verify with `wc -l`.

The 13:12 `taste:scan` job runs the full pipeline (scan → Styx delta → enrichment → journal); email/calendar steps can fail on OAuth while Styx delta succeeds.

## Dispatch-triggered scan (cron/dispatch)

When the dispatcher fires `taste_new_data` (or a cron triggers a taste scan):

1. **Repair tokens first**, chained with the scan in a SINGLE `terminal()` call — see Pre-Scan Token Repair.
2. **Run `taste_scan.py scan-incremental 24`** (email-only; NOT `taste_full_enrich.py`/`scan-historical`), then **`safe_taste_dedup.py --dry-run`** — confirm it opens `signals.jsonl` (`Total signals: N`); if not, the applied run no-ops and `dedup_removed` lies.
3. **Never chain `dispatch_taste_dedup.py` onto the daily Styx delta** — it keys on `event_date[:10]` (absent on Styx signals) and deletes all-but-one Styx signal per venue (2026-07-22); `safe_taste_dedup.py` is Styx-safe.
4. **Verify counts** — `wc -l signals.jsonl items.jsonl` (`taste_scan.py status` can report 0 outside the venv).

Full procedure: `references/dispatch-triggered-scan.md`.

## Pre-Scan Token Repair (REQUIRED)

Repair token expiry format before ANY scan — five failure modes (timezone suffix, float expiry, microsecond suffix, numeric-string expiry, microsecond+Z), each needing a different transform. Use `references/token-repair.md`; no partial fixes.

**⚠️ RACE CONDITION:** every `google_auth.py` init re-adds the `+00:00` suffix, so repair and scan MUST be chained in one `terminal()` call: `python3 -c "<repair>" && cd <data-dir> && /usr/bin/python3 <skill>/scripts/taste_scan.py scan-incremental 24`. Two separate calls WILL fail.

## Error Handling

| Failure | Detection | Response |
|---|---|---|
| Token `invalid_grant` / 0-byte file | Scan error; `wc -c` | Full re-auth (`references/cron_failure.md`); report the URL |
| Expiry format broken | `unconverted data remains` / float `rstrip` | Combined repair script, chained with the scan |
| Scan reports 0 signals, no error | `config.json` missing `email_sources` | Restore the config; calendar scan is independent |
| Enrichment "succeeds", items stay unenriched | Count `not i.get('enriched',False)` | `taste_enrich_fix.py` or inline enrichment |
| Styx delta reports "N created" | `verify_taste_delta.py --data-dir <real-path>` | Reconcile per `references/styx_delta_placeid_dedup.md` |

## Gotchas

Full incident list: `references/gotchas.md` — read before any scan, delta, enrichment, or backfill. Highest-stakes rules:

- **`scan-historical` DATE BUG (CRITICAL):** stamps every signal with the scan time; patch `parsedate_to_datetime()` first.
- **Wrong-account fallback:** 0-byte/invalid tokens silently fall back to the agent's account; verify the `Initialized Gmail and Calendar with <file>` line.
- **`place_id` dedup:** compare canonical `place_id`, never normalized name/item_id.
- **`taste_full_enrich.py` schema drift** (`item-{safe_name}` ids, `strength` not `signal_type`, `domain: 'restaurant'`) — prefer inline enrichment.
- **`taste_scan.py status` lies outside the venv:** use `wc -l`; cron mode blocks `execute_code` — use `terminal()` heredocs.
- **Never chain `dispatch_taste_dedup.py` onto the daily Styx delta.** A literal `<hermes-home>` path in an error = placeholder bug; patch to resolve `AGENT_ROOT`.
