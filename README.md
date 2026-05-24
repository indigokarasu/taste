# 🎯 Taste

> **Personalized recommendation engine — builds taste models from real consumption signals.**

## Why Taste?

Most recommendation engines use collaborative filtering or editorial lists. Taste is different: it builds a model from YOUR actual behavior — restaurant visits, food delivery orders, hotel stays, purchases, music plays, movie watches. Every recommendation names the specific purchases and patterns that justify it, and it only suggests places you haven't been.

Skill packages follow the [agentskills.io](https://agentskills.io/specification) open standard and are compatible with OpenClaw, Hermes Agent, Claude, and any agentskills.io-compliant client.

## Quick Start

```
# Get recommendations
"Where should I eat tonight?"

# Scan for new signals
"Scan my email for recent restaurant visits"

# Check model status
"What does my taste model look like?"
```

Taste auto-initializes on first use.

## What It Does

Taste extracts consumption signals from email and calendar data (DoorDash, Instacart, Tock, OpenTable, Amazon, hotel bookings, and more), deduplicates across confirmation/reminder/cancellation chains, and enriches venue entities with taste-relevant attributes via Google Maps. Every recommendation is grounded in real behavior, only suggests new places, and respects dietary restrictions. Signals decay over time using a configurable half-life.

## Commands

| Command | Description |
|---|---|
| `taste.scan` | Scan email and calendar for consumption signals |
| `taste.scan.report` | Summarize last scan |
| `taste.ingest.signal` | Manually record a consumption signal |
| `taste.enrich.item` | Enrich an item with attributes via Google Maps |
| `taste.query.recommend` | Generate discovery recommendations |
| `taste.query.serendipity` | Find novel cross-domain connections |
| `taste.model.status` | Model state: signal count, domains, coverage |
| `taste.report.weekly` | Weekly taste pattern summary |
| `taste.journal` | Write journal |
| `taste.update` | Self-update |

## Dependencies

- [Sift](https://github.com/indigokarasu/sift) — additional item enrichment via web research
- [Elephas](https://github.com/indigokarasu/elephas) — Chronicle entity context (read-only)
- User's email account, Google Calendar, Google Maps

## Scheduled Tasks

| Job | Schedule | Command |
|---|---|---|
| `taste:update` | `0 0 * * *` | Self-update |

## Changelog

### v3.5.2 — April 26, 2026
- Removed stale Spotify sync variants

### v3.5.1 — April 26, 2026
- Security: Spotify credentials now read from env vars

### v3.0.1 — March 27, 2026
- Self-update command and schedule

---

*Taste is part of the [OCAS Agent Suite](https://github.com/indigokarasu).*