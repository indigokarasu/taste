# Scan execution patterns

Concrete command patterns for running taste scans, verified 2026-06-23.

## Historical email scan (365 days)

```bash
# Pre-flight: validate token (see "Pre-scan token repair checklist" section)
cd /root/.hermes/commons/data/ocas-taste && \
  /root/hermes-agent/.venv/bin/python3.13 \
  /root/.hermes/profiles/indigo/skills/ocas-taste/scripts/taste_scan.py \
  scan-historical 365 2>&1
```

**Output:** JSON to stdout with `signals_created`, `cancellations`, `services_scanned`, `total_messages_processed`.

**Post-run verification:**
```bash
wc -l /root/.hermes/commons/data/ocas-taste/signals.jsonl
```

**Confirmed 2026-06-23:** 599 messages processed, 142 signals created, 2 cancellations. Services: doordash, instacart, good_eggs, tock, opentable, yelp, amazon, hotels.

**Note:** `scan-historical` is email-only. For the full pipeline (Styx delta + enrichment), use `taste_full_enrich.py`. Use `scan-historical` when the user explicitly wants broad historical email coverage, or when OAuth for calendar is broken but Gmail works.

## Historical calendar scan

```bash
/root/hermes-agent/.venv/bin/python3.13 \
  /root/.hermes/profiles/indigo/skills/ocas-taste/scripts/taste_scan.py \
  scan-calendar 365 2>&1
```

## Incremental daily scan (24h)

```bash
/root/hermes-agent/.venv/bin/python3.13 \
  /root/.hermes/profiles/indigo/skills/ocas-taste/scripts/taste_scan.py \
  scan-incremental 24 2>&1
```

## OAuth token accounts

| Account | File | Used for |
|---|---|---|
| Jared | `/root/.google_workspace_mcp/credentials/jared.zimmerman@gmail.com.json` | Gmail, Calendar (primary) |
| Indigo | `/root/.google_workspace_mcp/credentials/mx.indigo.karasu@gmail.com.json` | Fallback (no consumption emails) |

Always verify Jared's token was loaded. A 0-byte token or `+00:00` suffix causes silent fallback to Indigo's account → 0 results.
