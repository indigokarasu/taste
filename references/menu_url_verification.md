# Restaurant Menu URL Verification

Before enabling or re-running `taste_menu_monitor.py`, verify every URL in `menu_monitor.json` returns 200 for a direct fetch. The scraper uses `urllib` (no browser, no JS execution) — URLs that redirect, require login, or serve JS-rendered shells return 404/403/empty and silently produce zero dishes.

## When to read
Before any menu-monitor run, after adding a restaurant, or when `changes=[]` persists across runs.

## Procedure

1. **Spot-check each URL:** `curl -sI <url>` or `python3 -c "import urllib.request; print(urllib.request.urlopen('<url>').status)"` — expect 200, not 404/403/redirect.
2. **Confirm scrape type:** Use `dom` for static HTML menu pages; use `pdf_page` for sites that link PDF menus (the scraper extracts PDF links and parses them).
3. **Validate content:** Fetch the URL and check the returned HTML contains food keywords — not a login wall, cookie banner, or "enable JavaScript" shell.
4. **Disable unverified:** Set `"enabled": false` for any restaurant whose URL isn't confirmed live. Re-enable after verification.
5. **Re-enable all verified:** Once every URL returns 200 with real menu content, set all `"enabled": true` and resume the cron job.

## Pitfall — 404s are silent failures

The monitor reports `HTTP Error 404: Not Found` per restaurant but continues — no alert, no escalation, just `changes=[]`. A month of 404s looks like "no new dishes" but means "nothing was ever checked." Always verify URLs before trusting an empty result.