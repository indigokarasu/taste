# Backup and Restore

## What's backed up

All taste and styx data is backed up to GitHub LFS (`/root/indigo-repo`):

| File | Source | Description |
|------|--------|-------------|
| `data/styx.db` | `/root/.hermes/data/styx.db` | Merchant database (162 food + 19 travel) |
| `data/transactions.db` | `/root/.hermes/data/transactions.db` | Plaid transaction history |
| `data/ocas-taste-signals.jsonl` | `/root/.hermes/commons/data/ocas-taste/signals.jsonl` | ~7,800 consumption signals |
| `data/ocas-taste-items.jsonl` | `/root/.hermes/commons/data/ocas-taste/items.jsonl` | ~980 enriched entities |
| `data/ocas-taste-extractions.jsonl` | `/root/.hermes/commons/data/ocas-taste/extractions.jsonl` | Raw email/calendar extractions |
| `data/ocas-taste-links.jsonl` | `/root/.hermes/commons/data/ocas-taste/links.jsonl` | Entity relationships |
| `data/ocas-taste-decisions.jsonl` | `/root/.hermes/commons/data/ocas-taste/decisions.jsonl` | Audit log |
| `data/ocas-taste-config.json` | `/root/.hermes/commons/data/ocas-taste/config.json` | Configuration |

## What's NOT backed up

- `state.db` (14G) — too large for GitHub LFS
- `/root/commons/data/ocas-taste/` — stale copy, removed

## Backup script

bash /root/indigo-repo/scripts/backup_all_hermes_data.sh

Runs daily at 03:00 via Backup Hermes Sessions to GitHub cron job.

## LFS tracking

Git LFS tracks: *.jsonl, *.db, *.lbug, *.sqlite3, *.tar.gz

## Restore from backup

cd /root/indigo-repo
git lfs pull
cp data/styx.db /root/.hermes/data/styx.db
cp data/ocas-taste-*.jsonl /root/.hermes/commons/data/ocas-taste/
cp data/transactions.db /root/.hermes/data/transactions.db

## Disk space management

- Old local backups in /root/backup/ are cleaned up automatically (keep 3 days)
- state.db (14G) is never backed up - it's session state that can be regenerated