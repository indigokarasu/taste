# Support File Index

Full index of every bundled file that SKILL.md does not cover inline. The `When to read`
column is the trigger — read the file before assuming a tool, rule, or schema does not
exist, and before running the workflow it belongs to.

| File | When to read |
|---|---|
| `references/api_auth.md` | Before Gmail/Calendar/Spotify API calls — OAuth patterns, credential paths, token pitfalls |
| `references/api_specifics.md` | During a scan or enrichment run — API-specific query syntax and rate limits |
| `references/automation.md` | When troubleshooting cron jobs, schedules, or backup failures |
| `references/backup.md` | Before backup/restore work; LFS tracking and disk-space management |
| `references/chronicle_linkage.md` | When a Taste place must also exist in Chronicle (bidirectional linkage rules) |
| `references/config.default.json` | On `taste.init` — template for a fresh `config.json` |
| `references/cron_failure.md` | When a scan hits `invalid_grant` or a 0-byte token — full fallback procedure |
| `references/cron_pipeline_pattern.md` | For daily cron runs — pipeline order, Places API key location, dedup key format, rate limiting |
| `references/dedup_match.md` | Before dedup work — venue-name normalization pitfalls (24h-window matching) |
| `references/dispatch-triggered-scan.md` | When the dispatcher fires `taste_new_data` — incremental scan + safe dedup procedure |
| `references/dispatch_dedup_styx_corruption.md` | Before ever running `dispatch_taste_dedup.py` — it deletes Styx signals; incident + recovery recipe |
| `references/email_extraction.md` | Before `taste.scan` — sender allowlist (8 services) and extraction/normalization rules |
| `references/enrichment.md` | Before `taste.enrich.item` — attributes per domain, false-positive filtering, re-enrichment |
| `references/gotchas.md` | Before any scan, Styx delta, enrichment, or backfill; when a run succeeds but data looks wrong |
| `references/historical_scan_auth.md` | Before historical email or calendar scans — auth staging for backfills |
| `references/initialization.md` | On first invocation of any Taste command (`taste.init`) |
| `references/interactive-menu.md` | When invoked interactively — menu structure and response parsing |
| `references/journal.md` | Before `taste.journal` / at the end of every run — journal format and required fields |
| `references/multilocation_merge.md` | When merging chain / multi-location venues (locations as metadata) |
| `references/okrs.md` | During performance review or model-status reporting |
| `references/plans/preference-scan.plan.md` | Before a multi-step preference-scan workflow (ingest recent activity → update model) |
| `references/receipt_product_ingestion.md` | When itemized receipts are available — product-level signals |
| `references/recommendation_analysis.md` | During recommendation work — strength code, visited-set build, pattern identification, candidate cross-ref |
| `references/recommendation_style.md` | Before formatting a recommendation or report — output rules |
| `references/recovery.md` | On every wake — gap detection and degraded-mode logic |
| `references/scan_execution_patterns.md` | When choosing a scan command — concrete patterns + OAuth account table |
| `references/scan_historical_date_bug.md` | Before any historical scan — `scan-historical` stamps signals with scan time; root cause, patch, revert recipe |
| `references/schemas.md` | Before creating signals, items, links, extractions, or recommendations |
| `references/script_inventory.md` | When choosing which script to run — purpose, auth needs, runtime, key distinctions |
| `references/signal_dedup.md` | After enrichment runs — same-day cross-source signal dedup and source priority |
| `references/signal_policy.md` | Before decay calculations or domain gating — half-life policy |
| `references/signal_weighting.md` | Before computing signal strength or temporal decay |
| `references/spotify_oauth_fix.md` | When `taste.sync.spotify` reports DEGRADED / missing `SPOTIFY_REFRESH_TOKEN` |
| `references/spotify_sync.md` | Before `taste.sync.spotify` — music playback history procedure |
| `references/storage_layout.md` | When debugging data paths or the two-store (signals/items) architecture |
| `references/strength_model.md` | Before computing item strength or ranking items — full model |
| `references/styx_delta.md` | During Styx→Taste delta ingestion — SQL query, enrichment, dedup, schemas |
| `references/styx_delta_placeid_dedup.md` | After a `place_id`-sibling duplicate incident (2026-07-15) — canonical rule + reconciliation recipe |
| `references/styx_truncation_fix.md` | When merging truncated Styx variants; signal-item linkage repair recipe |
| `references/support-file-map.md` | When locating any bundled file or script (this index) |
| `references/taste_scan_env_fix.md` | When `taste_scan.py` cannot find its environment / venv |
| `references/token-repair.md` | **Before every scan** — five token failure modes and the combined repair script |
| `references/venue_name_corruption_fix.md` | When `venue_name` contains email-subject fragments ("… is confirmed") — corruption fix |
| `references/session-20260625-dispatch-066-taste.md` | Historical session record — token repair + 2 signals (2026-06-25) |
| `references/session-20260625-dispatch-1846-taste.md` | Historical session record — taste scan + Styx enrichment (2026-06-25) |
| `references/session-20260626-dispatch-taste.md` | Historical session record — mixed dispatch wave (2026-06-26) |
| `references/session-20260626-dispatch-taste-1657.md` | Historical session record — clean sweep + taste signal (2026-06-26) |
| `scripts/apply_spotify_token_to_env.py` | After `spotify_auth_helper.py` — bridges the token file into `.env` as `SPOTIFY_REFRESH_TOKEN` |
| `scripts/clean_signals.py` | After enrichment — removes generic meal titles and dedups on `(venue_name, event_date, extraction_source, domain)` |
| `scripts/dispatch_taste_dedup.py` | Dispatch-wave dedup — **never on the daily Styx delta** (deletes Styx signals); use `safe_taste_dedup.py` instead |
| `scripts/email_scan.py` | Standalone email scanner (lazy auth import; `--help` safe without deps) |
| `scripts/run_historical_scans.py` | Historical email + calendar backfill orchestrator (lazy auth import) |
| `scripts/safe_taste_dedup.py` | **Styx-safe** dedup — keys on `(venue_name, (event_date or date)[:10], extraction_source)`, backs up, refuses to write if Styx count drops. `--dry-run` supported |
| `scripts/spotify_auth_helper.py` | One-time interactive Spotify OAuth (auto or `--manual`); writes `music/spotify_token.json` |
| `scripts/spotify_history_puller.py` | Pulls recent Spotify plays via the API (needs `SPOTIFY_REFRESH_TOKEN`; lazy `requests` import) |
| `scripts/spotify_sync_mcp.py` | Alternative Spotify sync via MCP (music signals) |
| `scripts/styx_delta_corrected.py` | **Corrected daily Styx delta** — dedups candidates by `(name,date)`, links by `place_id`/name, self-heals orphans; never chain `dispatch_taste_dedup.py` onto it |
| `scripts/taste_cleanup_and_enrich.py` | Recovery — cross-source dedup + retry failed enrichments |
| `scripts/taste_enrich_fix.py` | Fixes enrichment persistence — re-enriches and sets `enriched: true` (supports `--dry-run`, `--limit`) |
| `scripts/taste_full_enrich.py` | Full Styx→Taste pipeline (has schema drift — see `references/gotchas.md`; prefer inline enrichment for cron) |
| `scripts/taste_menu_monitor.py` | Scrapes restaurant menus, diffs against the last snapshot, reports new dishes |
| `scripts/taste_scan.py` | Main CLI entry point (scan/incremental/historical/calendar); must run with `/usr/bin/python3` |
| `scripts/verify_taste_delta.py` | **Run after every Styx delta write** — asserts zero `place_id` collisions, `item_id` dupes, orphaned signals, `(merchant,date)` styx dupes; pass `--data-dir` |
| `evals/evals.json` | When running or updating the skill's evaluation cases |
| `tests/test_skill_doc.py` | Before editing SKILL.md — doc-integrity guards (frontmatter parses, char budget, every cited file exists) |
| `tests/test_script_help.py` | Before shipping a script — asserts every script answers `--help` with no deps, auth, or network |
| `tests/test_safe_dedup.py` | Before changing dedup keys — pins the Styx-safety invariant (2026-07-22 incident) |
| `tests/test_clean_signals.py` | Before changing generic-meal filtering or same-day dedup |
| `.github/workflows/test.yml` | CI on push/PR — compileall + `unittest discover -s tests` |
