---
name: ocas-taste
description: >
  Behavior-driven taste model. Builds personalized recommendations from real
  consumption signals with evidence-backed explanations. Supports cross-domain
  discovery and periodic taste reports.
---

# Taste

Taste turns real consumption behavior into auditable, evidence-linked discovery recommendations and serendipity connections.

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

## Core promise

Every recommendation cites specific consumed items as evidence. First-party consumption signals are the highest priority source. No vague flattery or trend-chasing filler.

## Commands

- `taste.ingest.signal` — record a consumption signal (purchase, visit, play, watch, stay)
- `taste.enrich.item` — optional: enrich an item with metadata from external sources
- `taste.query.recommend` — generate recommendations grounded in consumption history
- `taste.query.serendipity` — find novel but defensible cross-domain connections
- `taste.model.status` — return model state: signal count, domains active, staleness
- `taste.report.weekly` — optional: generate a weekly taste pattern summary

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

## Signal weighting and decay

Signal strength and recency both matter. Config: `decay.halflife_days`. Stale signals weaken unless reinforced. Newer identical signals outweigh older ones.

## Support file map

- `references/schemas.md` — ConsumptionSignal, Recommendation, ItemRecord, LinkRecord, ModelStatus, WeeklyReport
- `references/signal_policy.md` — decay, reinforcement, domain gating, provenance rules
- `references/recommendation_style.md` — explanation quality, voice, anti-salesy output rules

## Storage layout

```
.taste/
  config.json
  signals.jsonl
  items.jsonl
  links.jsonl
  decisions.jsonl
  reports/
```

## Validation rules

- Every recommendation contains at least one evidence-backed explanation
- Stale signals contribute less than recent identical signals
- Disabled domains do not appear in results
- Serendipity output is novel but evidence-linked
