# Cron Failure Fallback

When a taste cron job runs and the Gmail/Calendar OAuth token is revoked (all refresh attempts return `invalid_grant`):

1. **Don't SILENT-fail.** Always output a report containing: auth failure diagnosis, OAuth re-authorization URL, current taste model state, and any data quality issues.
2. **Check credentials.** All Google credentials are centralized in the agent's credential directory (typically `~/.google_workspace_mcp/credentials/`). If refresh fails with `invalid_grant`, full re-auth is required — no retry will help. See `references/api_auth.md` for paths and patterns.
3. **Generate the auth URL** using the re-auth procedure in `infrastructure/google-workspace-auth` skill.
4. **Report existing data quality.** Even when scan fails, analyze existing `signals.jsonl` and `items.jsonl` for: enrichment coverage (target: 90%), signal freshness (fraction within 180-day half-life), calendar noise, duplicate venue names.
