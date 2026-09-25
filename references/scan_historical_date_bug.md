# scan-historical date-extraction bug

**Severity:** CRITICAL — defeats the purpose of historical scans.
**Discovered:** 2026-07-07, ocas-taste `scan-historical 365` run (cron).

## Symptom
`scan-historical` produces signals whose `event_date` is the scan timestamp, not the
real email/consumption date. A 365-day run on 2026-07-07 emitted 141 signals; **137 had
`event_date = 2026-07-07T09:06:23.xxx`** (microsecond-spaced — impossible for real
emails spread across a year; a year of history cannot all be sent at 09:06:23).

## Root cause
`scripts/taste_scan.py`, `_extract_from_email` (lines ~340-346):
```python
date_str = headers.get('Date', '')
try:
    email_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
except:
    email_date = datetime.now()   # fallback fires for (almost) every email
```
The single rigid format doesn't match the varied `Date` headers Gmail returns, so the
`except` branch fires and stamps every signal "now".

## Why it matters
- Temporal decay (the model's core mechanism) is corrupted: everything looks recent.
- It **maximizes recency bias** — the opposite of "scan all history to avoid recency bias".
- Combined with the dedup incompatibility below, re-running over a populated dataset
  silently pollutes it with un-dedupable, mis-dated signals.

## Fix (apply in taste_scan.py)
Replace the rigid strptime with the stdlib robust parser:
```python
from email.utils import parsedate_to_datetime
date_str = headers.get('Date', '')
try:
    email_date = parsedate_to_datetime(date_str)
    if email_date is None:
        email_date = datetime.now(timezone.utc)
except Exception:
    email_date = datetime.now(timezone.utc)
```
`parsedate_to_datetime` handles RFC-2822 variants, non-zero-padded fields, and most
tz formats. After fixing, re-run `scan-historical` cleanly.

## Dedup incompatibility (related)
Any dedup key that reads `name`/`normalized_name` skips scan signals (they use
`venue_name`), so it reports a false "0 dupes" on `--dry-run`. Use the
schema-aware tools instead: `clean_signals.py` keys on
`(venue_name, event_date[:10], extraction_source, domain)` and
`safe_taste_dedup.py` keys on `(extraction_source, venue_name, event_date or date)`.
Never trust a "0 dupes" count from a key that reads fields scan signals don't have.

## If you already ran a bad scan (revert recipe)
The scan **appends** new signals to the end of `signals.jsonl`. To revert:
1. Snapshot first: `cp signals.jsonl signals.jsonl.<tag>.bak`
2. Note the pre-scan line count (cron `wc -l` baseline, or a just-before count).
3. Keep only the pre-scan lines:
   `head -n <PRE_COUNT> signals.jsonl > signals.jsonl.tmp && mv -f signals.jsonl.tmp signals.jsonl`
4. Validate: every line `json.loads` ok, no scan-time-dated signals remain.
5. `items.jsonl` minor inflation (signal_count +1, one spurious visit_date per touched
   item) is low-impact; recommendations key off `signals.jsonl`. Leave unless scrubbing.

## Preferred path for historical coverage
No bundled backfill script ships with this skill. The supported path is:
1. Patch the parse above (`email.utils.parsedate_to_datetime()`) in `taste_scan.py`.
2. Run `taste_scan.py scan-historical N` (email) / `taste_scan.py scan-calendar N`
   (calendar) in bounded chunks, with food/venue filtering for calendar events.
3. Dedup with `scripts/safe_taste_dedup.py` (Styx-safe) and verify counts directly —
   never trust a tool's "0 dupes" line alone.