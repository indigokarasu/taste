# Token Repair Patterns

Two distinct failure modes require repair before running `taste_scan.py`. Both can occur in the same session.

## Failure Mode 1: Timezone Suffix in Expiry String

**Symptom:** `ValueError: unconverted data remains: +00:00` when loading token.

**Cause:** Google OAuth library writes `expiry: "2026-06-24T18:37:34+00:00"` but `google.oauth2.credentials.Credentials.from_authorized_user_file()` only accepts `%Y-%m-%dT%H:%M:%S`.

**Fix:**
```python
import json
path = '/root/.google_workspace_mcp/credentials/email.json'
with open(path) as f:
    d = json.load(f)
if '+' in d.get('expiry', '') or d.get('expiry', '').endswith('Z'):
    d['expiry'] = d['expiry'][:19]
with open(path, 'w') as f:
    json.dump(d, f, indent=2)
```

## Failure Mode 2: Expiry as Float (Unix Timestamp)

**Symptom:** `AttributeError: 'float' object has no attribute 'rstrip'` when loading token.

**Cause:** Some token files store `expiry` as a Unix timestamp float (e.g., `1782328557.213807`) instead of an ISO string. The Taste script calls string methods on it.

**Fix:**
```python
import json, time
path = '/root/.google_workspace_mcp/credentials/email.json'
with open(path) as f:
    d = json.load(f)
if isinstance(d.get('expiry'), float):
    d['expiry'] = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(time.time() + 3600))
with open(path, 'w') as f:
    json.dump(d, f, indent=2)
```

## Combined Repair Script (handles both)

Run this before every Taste scan to ensure tokens are valid:

```bash
python3 -c "
import json, time
from pathlib import Path

for email in ['jared.zimmerman@gmail.com', 'mx.indigo.karasu@gmail.com']:
    path = Path(f'/root/.google_workspace_mcp/credentials/{email}.json')
    if not path.exists():
        print(f'{email}: NO TOKEN FILE')
        continue
    with open(path) as f:
        d = json.load(f)
    expiry = d.get('expiry', 'MISSING')
    
    if isinstance(expiry, float):
        d['expiry'] = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(time.time() + 3600))
        print(f'{email}: Fixed float -> {d[\"expiry\"]}')
    elif isinstance(expiry, str) and ('+' in expiry or expiry.endswith('Z')):
        d['expiry'] = expiry[:19]
        print(f'{email}: Fixed suffix -> {d[\"expiry\"]}')
    else:
        print(f'{email}: OK ({repr(expiry)})')
        continue
    
    with open(path, 'w') as f:
        json.dump(d, f, indent=2)
"
```

## Re-Run After Repair: Duplicate Signal Risk

When a scan fails due to token format and tokens are repaired mid-session, the re-run scan will process the same emails again and create duplicate signals. The `taste_signals_dedup.py` script uses `(venue_name, event_date, extraction_source, domain)` as the dedup key, but the scan generates different `signal_id` UUIDs each run, so the dedup script may not catch them if the `event_date` precision differs (e.g., `2026-06-24T13:13:29` vs `2026-06-24T13:20:44.677614`).

**Confirmed 2026-06-24 dispatch #53:** First scan attempt failed with token error (stderr). Tokens repaired. Second scan succeeded, created 2 Lavash/DoorDash signals with different signal_ids and slightly different event_date precision. Dedup script found 0 duplicates.

**Mitigation after token repair:**
1. Record signal count BEFORE the scan: `wc -l signals.jsonl`
2. Record signal count AFTER the scan
3. If delta > 0 and the scan was a re-run after repair, check for same-venue + same-day duplicates manually:
   ```python
   python3 -c "
   import json
   from collections import Counter
   signals = [json.loads(l) for l in open('signals.jsonl') if l.strip()]
   key = lambda s: (s.get('venue_name',''), s.get('event_date','')[:10], s.get('extraction_source',''))
   counts = Counter(key(s) for s in signals)
   dupes = {k:v for k,v in counts.items() if v > 1}
   print(f'{len(dupes)} duplicate groups: {dupes}')
   "
   ```
4. If same-day same-venue duplicates exist with different signal_ids, keep the one with more precision (longer event_date) and remove the other.

## Failure Mode 3: Token Refresh Race (Repair → Refresh → Suffix Returns)

**Symptom:** Token repair succeeds (confirmed `expiry: "2026-06-25T03:40:37"`), but the subsequent scan immediately fails with `unconverted data remains: +00:00` — the expiry is back to `+00:00` format.

**Cause:** Between the repair `python3 -c` call and the scan script invocation, the Google OAuth library performs a token refresh (triggered by the scan's auth initialization). The refresh writes a new `expiry` field with the `+00:00` timezone suffix, overwriting the stripped version. This happens within seconds — it's not a stale token issue, it's a race between repair and the next auth init.

**Confirmed 2026-06-25 dispatch #62:** Both accounts repaired successfully (suffix stripped to `2026-06-25T03:40:37`). Seconds later, `taste_scan.py scan-incremental 24` failed with `+00:00` on both accounts. The OAuth library refreshed the token between the two `terminal()` calls.

**Fix: Combine repair and scan in a SINGLE `terminal()` call.** By running the repair and the scan back-to-back in one shell invocation, there's no window for the OAuth library to refresh the token between steps. The scan's auth init reads the freshly-repaired token before any refresh cycle can fire.

```bash
# CORRECT: repair + scan in one terminal() call (no race window)
python3 -c "
import json, time
from pathlib import Path
for email in ['jared.zimmerman@gmail.com', 'mx.indigo.karasu@gmail.com']:
    path = Path(f'/root/.google_workspace_mcp/credentials/{email}.json')
    with open(path) as f: d = json.load(f)
    expiry = d.get('expiry','')
    if isinstance(expiry, str) and ('+' in expiry or expiry.endswith('Z')):
        d['expiry'] = expiry[:19]
    elif isinstance(expiry, float):
        d['expiry'] = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(time.time()+3600))
    with open(path, 'w') as f: json.dump(d, f, indent=2)
" && cd /root/.hermes/profiles/indigo/commons/data/ocas-taste && /usr/bin/python3 /root/.hermes/profiles/indigo/skills/ocas-taste/scripts/taste_scan.py scan-incremental 24
```

**Why this works:** The token file is repaired in the same process invocation that immediately launches the scan. The scan's `google_auth.py` helper reads the token file via `from_authorized_user_file()` before any refresh trigger can rewrite it. The refresh only happens if the token is expired or nearly-expired — a freshly-repaired token with a future expiry won't trigger a refresh on the same init call.

**When NOT to use this pattern:** If the token is genuinely expired (not just suffix-corrupted), the refresh WILL fire and may re-introduce the suffix. In that case, run the repair twice: once to check, and once immediately before the scan. If the expiry keeps reverting, the token may need full re-auth (`google_oauth_init.py`).

## Mandatory Every-Scan Pattern (Confirmed 2026-06-25)

As of dispatch #68 (2026-06-25), token repair has been required on **every single Taste scan** without exception. Five consecutive dispatches (#68, #71, #73, #74, ~#80) all required timezone suffix stripping on both accounts. This is now the expected default — not a reactive fix, but a **mandatory pre-scan step**.

**Why:** The OAuth library refreshes the token on every `google_auth.py` initialization, and each refresh re-adds the `+00:00` suffix. Even if a scan succeeded 1 hour ago, the token has been refreshed since and will have the suffix again.

**Rule:** Always run the combined repair script immediately before `taste_scan.py`, chained in a single `terminal()` call. Never skip repair, never assume the token is still clean from a prior scan. As of dispatch #130, this has held true for 15+ consecutive scans across 9+ hours on 2026-06-25.

## Confirmed Incidents

- **2026-06-25 (dispatch #130):** Both accounts Mode 1 again (`+00:00`). 10th+ consecutive scan on 2026-06-25 requiring repair. Combined repair+scan in single terminal() call succeeded. 1 signal created (Next Level VG/DoorDash).
- **2026-06-25 (dispatch #62):** Token refresh race confirmed. Repair wrote `2026-06-25T03:40:37` (no suffix), but scan seconds later saw `2026-06-25T03:40:37+00:00`. OAuth library refreshed the token between two separate `terminal()` calls. Fix: combine repair + scan in one call.
- **2026-06-24 (dispatch wave 20:34Z):** Both accounts Mode 1 again (`+00:00`). Fixed with combined repair script. Taste scan then succeeded (1 signal: Lavash/DoorDash). This is a **recurring pattern** — the OAuth library periodically rewrites the token file with timezone suffix after token refresh. If a scan fails with "unconverted data remains," always run the combined repair before retrying.
- **2026-06-24 (dispatch #53):** Both accounts Mode 1. Token repair mid-session. Re-run created 2 Lavash/DoorDash signals (same venue, same day, different signal_id, different event_date precision). Dedup script missed them (different `event_date` string). Manual dedup key `(venue_name, event_date[:10], extraction_source)` caught them.
- **2026-06-24 (dispatch #486):** Both accounts Mode 1 (timezone suffix `+00:00`). Fixed, scan created 1 signal (Lavash/DoorDash).
- **2026-06-24 (dispatch #485):** mx.indigo Mode 1 (`+00:00`), jared Mode 2 (float). Fixed, scan created 1 signal (Lavash/DoorDash).
- **2026-06-23:** Mode 1 on jared token. Fixed, scan processed 599 messages and created 142 signals.
