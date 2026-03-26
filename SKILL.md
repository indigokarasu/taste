---
name: ocas-taste
source: https://github.com/indigokarasu/taste
install: openclaw skill install https://github.com/indigokarasu/taste
description: Use when generating personalized recommendations grounded in real consumption signals (purchases, visits, plays, watches), exploring cross-domain discovery based on actual behavior, checking taste model status, or producing periodic taste pattern reports. Trigger phrases: 'recommend', 'what would I like', 'based on what I've liked', 'suggest something similar', 'my taste', 'what should I try'. Do not use for generic search, editorial top-10 lists, or ad-copy generation.
metadata: {"openclaw":{"emoji":"🎯"}}
---

# Taste

Taste builds a personalized taste model from real consumption signals — purchases, restaurant visits, music plays, movie watches, and travel stays — using temporal decay so recent behavior outweighs stale history. Every recommendation it generates names the specific prior consumption that justifies it, making the reasoning auditable rather than opaque, and serendipity queries explicitly cross domain boundaries to surface novel but defensible connections.

## When to use

- Personalized recommendations grounded in real prior behavior
- Cross-domain discovery based on actual taste signals
- "What else would I like" reasoning with named evidence
- Taste model status check
- Weekly or periodic taste pattern summary

## Do not use

- Generic web research — use Sift
- Editorial/top-10 style recommendations without personalization
- Ad-copy or sales-oriented product suggestions
- Inference of sensitive identity traits from behavior

## Responsibility boundary

Taste owns behavior-driven preference modeling and evidence-backed recommendations.

Taste does not own: web research (Sift), social graph (Weave), knowledge graph (Elephas), pattern analysis (Corvus), browsing interpretation (Thread).

## Commands

- `taste.ingest.signal` — record a consumption signal (purchase, visit, play, watch, stay)
- `taste.enrich.item` — optional: enrich an item with metadata from external sources
- `taste.query.recommend` — generate recommendations grounded in consumption history
- `taste.query.serendipity` — find novel but defensible cross-domain connections
- `taste.model.status` — return model state: signal count, domains active, staleness
- `taste.report.weekly` — optional: generate a weekly taste pattern summary
- `taste.journal` — write journal for the current run; called at end of every run

## Operating invariants

- Evidence-first: recommendations must reference specific consumed items
- Signal decay: older signals degrade unless reinforced
- No speculative identity inference from taste signals
- Explainability: every recommendation explains the link to prior consumption
- First-party signals outrank enriched metadata
- Disabled domains do not appear in recommendations
- Confidence reflects actual evidence strength, not rhetorical certainty

## Taste-model workflow

1. Receive or normalize input signal
2. Validate domain and signal structure
3. Persist signal
4. Optionally enrich referenced item
5. Update item/link understanding from concrete evidence
6. Apply signal weighting and temporal decay
7. Answer query or generate report
8. Ensure output includes evidence-linked explanation
9. Persist material model updates
10. Write journal via `taste.journal`

## Signal weighting and decay

Signal strength and recency both matter. Config: `decay.halflife_days`. Stale signals weaken unless reinforced. Newer identical signals outweigh older ones.

## Storage layout

```
~/openclaw/data/ocas-taste/
  config.json
  signals.jsonl
  items.jsonl
  links.jsonl
  decisions.jsonl
  reports/

~/openclaw/journals/ocas-taste/
  YYYY-MM-DD/
    {run_id}.json
```


Default config.json:
```json
{
  "skill_id": "ocas-taste",
  "skill_version": "2.2.0",
  "config_version": "1",
  "created_at": "",
  "updated_at": "",
  "domains": {
    "enabled": ["music", "restaurant", "book", "movie", "product", "travel", "event"]
  },
  "decay": {
    "halflife_days": 180
  },
  "retention": {
    "days": 0,
    "max_records": 10000
  }
}
```

## OKRs

Universal OKRs from spec-ocas-journal.md apply to all runs.

```yaml
skill_okrs:
  - name: recommendation_evidence_rate
    metric: fraction of recommendations citing at least one consumed item
    direction: maximize
    target: 1.0
    evaluation_window: 30_runs
  - name: serendipity_novelty
    metric: fraction of serendipity results crossing domain boundaries
    direction: maximize
    target: 0.80
    evaluation_window: 30_runs
  - name: signal_freshness
    metric: fraction of active signals within decay half-life
    direction: maximize
    target: 0.60
    evaluation_window: 30_runs
```

## Optional skill cooperation

- Sift — item enrichment via web research
- Elephas — read Chronicle (read-only) for entity context
- Thread — may use Thread signals to detect emerging taste patterns

## Journal outputs

Observation Journal — all signal ingestion, query, and report runs.

## Initialization

On first invocation of any Taste command, run `taste.init`:

1. Create `~/openclaw/data/ocas-taste/` and subdirectories (`reports/`)
2. Write default `config.json` with ConfigBase fields if absent
3. Create empty JSONL files: `signals.jsonl`, `items.jsonl`, `links.jsonl`, `decisions.jsonl`
4. Create `~/openclaw/journals/ocas-taste/`
5. Log initialization as a DecisionRecord in `decisions.jsonl`

Taste is purely reactive. No cron jobs or heartbeat entries.

## Visibility

public

## Support file map

| File | When to read |
|---|---|
| `references/schemas.md` | Before creating signals, items, links, or recommendations |
| `references/signal_policy.md` | Before decay calculations or domain gating |
| `references/recommendation_style.md` | Before generating recommendations or reports |
| `references/journal.md` | Before taste.journal; at end of every run |
