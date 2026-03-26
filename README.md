# 🎯 Taste

Taste builds a personalized taste model from real consumption signals -- purchases, restaurant visits, music plays, movie watches, and travel stays -- using temporal decay so recent behavior outweighs stale history. Every recommendation it generates names the specific prior consumption that justifies it, making the reasoning auditable rather than opaque, and serendipity queries explicitly cross domain boundaries to surface novel but defensible connections.

---

## Overview

Taste is a recommendation engine grounded entirely in real consumption behavior -- not editorial lists, not collaborative filtering, not popularity signals. Every recommendation it generates names the specific purchases, visits, plays, or watches that justify it, making the reasoning visible and auditable. Signals decay over time using a configurable half-life so that stale history loses influence unless reinforced by fresh behavior. Serendipity queries explicitly cross domain boundaries to surface novel but defensible cross-domain connections. First-party signals always outrank enriched metadata.

## Commands

| Command | Description |
|---|---|
| `taste.ingest.signal` | Record a consumption signal (purchase, visit, play, watch, stay) |
| `taste.enrich.item` | Enrich an item with metadata from external sources (optional) |
| `taste.query.recommend` | Generate recommendations grounded in consumption history |
| `taste.query.serendipity` | Find novel but defensible cross-domain connections |
| `taste.model.status` | Model state: signal count, domains active, staleness |
| `taste.report.weekly` | Generate a weekly taste pattern summary (optional) |
| `taste.journal` | Write journal for the current run |

## Setup

`taste.init` runs automatically on first invocation and creates all required directories, config.json, and JSONL files. No manual setup is required. Taste is purely reactive -- no scheduled tasks.

## Dependencies

**OCAS Skills**
- [Sift](https://github.com/indigokarasu/sift) -- item enrichment via web research
- [Elephas](https://github.com/indigokarasu/elephas) -- Chronicle entity context (read-only)
- [Thread](https://github.com/indigokarasu/thread) -- may use thread signals to detect emerging taste patterns

**External**
- None

## Scheduled Tasks

This skill is purely reactive. No scheduled tasks.

## Changelog

### v2.2.0 -- March 22, 2026
- Routing improvements

### v2.1.0 -- March 22, 2026
- Journal documentation and initialization with storage setup

### v2.0.0 -- March 18, 2026
- Initial release as part of the unified OCAS skill suite
---

*Taste is part of the [OpenClaw Agent Suite](https://github.com/indigokarasu) -- a collection of interconnected skills for personal intelligence, autonomous research, and continuous self-improvement. Each skill owns a narrow responsibility and communicates with others through structured signal files, shared journals, and Chronicle, a long-term knowledge graph that accumulates verified facts over time.*
