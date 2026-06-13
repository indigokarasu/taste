# Script Inventory

Quick reference for what each script in `scripts/` does and when to use it.

| Script | Purpose | Full pipeline? | Needs OAuth? | Needs GOOGLE_PLACES_API_KEY? |
|---|---|---|---|---|
| `taste_scan.py` | Email/calendar scan + CLI entry point | Email-only | Yes (Gmail/Calendar) | No |
| `taste_full_enrich.py` | Styx delta + cross-source dedup + enrichment | Yes | No | Yes |
| `taste_cleanup_and_enrich.py` | Cross-source dedup + retry failed enrichments | Recovery only | No | Yes |
| `email_scan.py` | Standalone email scanner | Email-only | Yes | No |
| `run_historical_scans.py` | Orchestrator for historical email + calendar scans | Email/calendar only | Yes | No |

## Key Distinction

**`taste_scan.py scan-historical N`** scans Gmail only. It fails entirely if OAuth is broken.

**`taste_full_enrich.py [--limit N]`** runs the full Styx-to-Taste pipeline:
1. Queries styx.db for food merchants not yet in taste
2. Scans email extractions for restaurants not in taste
3. Cross-source dedup
4. Enriches all unenriched items via Google Places
5. Works without OAuth -- uses `GOOGLE_PLACES_API_KEY` from `/root/.hermes/secrets/plaid.env`

## When OAuth is Broken

What still works:
- `taste_full_enrich.py` (Styx delta + enrichment)
- Manual signal ingestion
- `taste_cleanup_and_enrich.py` (dedup + retry)
- Enrichment via Places API

What fails:
- `taste_scan.py scan-historical` (email) — **unless** the `invalid_scope` fix is applied (see gotchas: read scopes from token file instead of hardcoding)
- `taste_scan.py scan-calendar` (calendar) — same fix applies
- Any MCP-based Gmail/Calendar access
- Spotify sync (separate auth issue)

**Note:** `invalid_scope: Bad Request` is different from `invalid_grant`. The scope mismatch is fixable without re-auth — patch `taste_scan.py` to use token file scopes.

## Invocation

All scripts use the taste venv Python:
```
/root/.hermes/commons/data/ocas-taste/venv/bin/python3 /root/.hermes/skills/ocas-taste/scripts/<script>.py [args]
```
