# Spotify Sync (`taste.sync.spotify`)

Music playback history is stored as standard ConsumptionSignal records in `signals.jsonl` with `domain: "music"` and `source: "play"`.

## Procedure

1. Verify valid Spotify token (skip if expired with no `refresh_token` — requires interactive re-auth).
2. Call Spotify MCP: `get_recently_played` (last 24h) and `get_top_items`.
3. Create ConsumptionSignals (`strength: 0.60`) and ItemRecords per track.
4. Deduplicate by track name + artist. Persist to JSONL files.
5. Update `music/spotify_sync_checkpoint.json`. Write journal.

See `references/api_auth.md` for Spotify MCP setup and env vars.
