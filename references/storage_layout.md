# Storage Layout

## Data directory

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
```

## Journal directory

```
{agent_root}/commons/journals/ocas-taste/
  YYYY-MM-DD/
    {run_id}.json
```

## Enrichment pipeline

```bash
python3 scripts/taste_full_enrich.py        # Full scan: styx + email + existing items
python3 scripts/taste_cleanup_and_enrich.py  # Dedup + retry failed items
```

## Name matching / rename patterns

Styx merchants frequently have messy names from Plaid. See `references/enrichment.md` for the full list of observed patterns and normalization rules. Key principle: cross-source dedup means same restaurant via email + calendar + styx = one entry. Normalize by lowercasing, stripping articles, location suffixes, and venue-type suffixes.

⚠️ LEGACY: An old data path may exist but is STALE. Active data is ONLY under `{agent_root}/commons/data/ocas-taste/`.
