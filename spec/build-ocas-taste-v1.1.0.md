# Build Spec — `ocas-taste` v1.1.0

## Purpose
Build a complete, ready-to-install Agent Skill package named `ocas-taste` that creates and maintains a private, behavior-driven taste model from concrete consumption signals, enriches items when useful, mines specific cross-item and cross-domain links, answers recommendation and serendipity queries with named evidence, and can optionally generate periodic taste reports.

## Skill identity
- Skill package name: `ocas-taste`
- Version: `1.1.0`
- Author: `Indigo Karasu`
- Email: `mx.indigo.karasu@gmail.com`
- Skill type: `system`

## Build rules
The coder must follow these rules:
- Build a real Agent Skill package, not a planning memo.
- Preserve all functionality from the prior `build.ocas-taste.v1.0.0.md`; do not remove capabilities, commands, invariants, storage, or optional reporting/enrichment behaviors.
- Keep `SKILL.md` lean and routing-aware, but do not compress away required behavior. Move secondary detail into `references/` where appropriate.
- Define all required schemas locally inside the package.
- Optimize for concrete use, not generic prose.
- Keep recommendations specific, evidence-based, and non-salesy.
- Do not infer sensitive traits or protected-category identity from taste signals.
- Treat first-party consumption evidence as the highest-priority signal source.
- Support operation as a standalone skill even if no other skills are installed.

## Responsibility Boundary

Taste stores persistent user preferences derived from behavioral signals.

Corvus observes behavior patterns and generates signals.

Corvus does not store preference data directly.

---

## One sharp promise
This skill exists to turn real consumption behavior into auditable, evidence-linked discovery recommendations and serendipity connections.

## Required output
Produce a complete package with this structure:

```text
ocas-taste/
  skill.json
  SKILL.md
  references/
    schemas.md
    signal_policy.md
    recommendation_style.md
```

Do not add `scripts/` or `assets/` unless required to implement a concrete capability defined below. The current package should work without them.

## Package specification

### 1) `skill.json`
Create a valid `skill.json` for the target Agent Skill runtime.

Required fields:
- `name`: `ocas-taste`
- `version`: `1.0.1`
- `author`: `Indigo Karasu`
- `email`: `mx.indigo.karasu@gmail.com`
- `description`: routing-optimized text

### Description requirements
The description must clearly say that the skill:
- builds a private taste model from what the user actually consumes
- uses signals like purchases, visits, plays, watches, stays, and similar concrete behavior
- answers recommendation and serendipity-style discovery requests
- explains recommendations by citing named prior items
- can optionally enrich items and generate reports

The description should trigger on requests like:
- “Based on what I like, what else should I try?”
- “Recommend something similar to these restaurants/books/movies/hotels.”
- “Find surprising connections across my tastes.”
- “Use my actual purchase/visit history to suggest new things.”

The description should not over-trigger on:
- generic search with no taste-model need
- one-off factual lookups
- pure ranking tasks with no user-preference grounding
- generic shopping queries that do not ask for behavior-based personalization

## 2) `SKILL.md`
`SKILL.md` must be the operational surface. It must tell the agent:
- when to use the skill
- what inputs it accepts
- how the internal taste-model loop works
- what commands and outputs exist
- what invariants must never be violated
- when to read each reference file

### Required `SKILL.md` sections
Use exactly these top-level sections:
1. `# Taste (ocas-taste)`
2. `## When to use`
3. `## Do not use`
4. `## Core promise`
5. `## Accepted inputs`
6. `## Commands`
7. `## Operating invariants`
8. `## Taste-model workflow`
9. `## Signal weighting and decay`
10. `## Enrichment policy`
11. `## Recommendation and serendipity behavior`
12. `## Output requirements`
13. `## Storage model`
14. `## Reference files`
15. `## Validation rules`

### `SKILL.md` required content by section

#### `## When to use`
State trigger conditions clearly. Include both explicit and implicit trigger patterns, such as:
- the user wants personalized recommendations grounded in real prior behavior
- the user wants cross-domain discovery based on actual taste signals
- the user wants “what else would I like” reasoning with named evidence
- the user wants a status check on the current taste model
- the user wants a weekly or periodic summary of evolving taste patterns

#### `## Do not use`
List nearby non-trigger cases, such as:
- generic web research with no taste personalization
- purely editorial/top-10 style recommendation generation
- ad-copy or sales-oriented product suggestion writing
- inference of sensitive identity traits from behavior
- unsupported autonomous monitoring or alerting beyond the explicit report command

#### `## Core promise`
State the skill’s one sharp promise in plain language.

#### `## Accepted inputs`
Define the main accepted input classes:
- explicit `ConsumptionSignal`
- item metadata for optional enrichment
- direct recommendation queries
- direct serendipity queries
- model status request
- optional report-generation request

Also state supported domains from the original spec:
- `music`
- `restaurant`
- `book`
- `movie`
- `product`
- `travel`
- `event`

Allow the skill to ignore unsupported domains cleanly.

#### `## Commands`
Preserve all original commands and define what each one does:
- `taste.ingest.signal`
- `taste.enrich.item` (optional)
- `taste.query.recommend`
- `taste.query.serendipity`
- `taste.model.status`
- `taste.report.weekly` (optional)

For each command, state:
- purpose
- minimum required input
- expected output shape
- side effects, if any

#### `## Operating invariants`
Preserve and expand the original invariants:
- Evidence-first: recommendations must reference specific consumed items.
- Signal decay: older signals degrade unless reinforced.
- No speculative identity inference: do not infer sensitive traits from taste signals.
- Explainability: every recommendation explains the link to prior consumption.

Add the following operational invariants because they are consistent with the original skill intent:
- First-party signals outrank enriched or inferred metadata.
- Cross-domain links are allowed only when the explanation is concrete.
- Disabled domains must not appear in recommendations.
- Recommendations must avoid vague flattery, trend-chasing filler, or generic marketing language.
- Confidence must reflect actual evidence strength, not rhetorical certainty.

#### `## Taste-model workflow`
Define the ordered internal loop:
1. receive or normalize input
2. validate domain and signal structure
3. persist signal or query context
4. optionally enrich the referenced item if enrichment is enabled and useful
5. update item/link understanding using concrete evidence only
6. apply signal weighting and temporal decay
7. answer the query or generate the requested report
8. ensure output includes evidence-linked explanation
9. persist any material model update or decision artifact

Keep this as a behavior loop, not as hidden implementation prose.

#### `## Signal weighting and decay`
State that `strength` and recency both matter.
The build must preserve the original config field:
- `decay.halflife_days`

Also preserve:
- stale signals weaken over time unless reinforced by new matching or adjacent signals
- newer identical signals should outweigh older identical signals
- report and status views should reflect current weighted influence, not raw counts only

#### `## Enrichment policy`
Preserve optional enrichment behavior from the original skill.
State that enrichment:
- is optional
- should add provenance-aware metadata when helpful
- must not override first-party behavior evidence
- should be skipped when it adds little value or introduces speculative drift

#### `## Recommendation and serendipity behavior`
Differentiate the two main discovery modes:
- Recommendation mode: find likely-fit items close to demonstrated preferences.
- Serendipity mode: find novel but defensible links that stretch slightly beyond the current comfort zone without becoming random.

State that both modes must:
- anchor explanations to named consumed items
- prefer concrete, auditable links
- avoid generic similarity claims with no evidence trail
- support both broad and narrow inferences when evidence supports them
- allow cross-domain discovery when the explanation is specific enough to be persuasive without sounding salesy

#### `## Output requirements`
State that every recommendation output must include:
- candidate item
- confidence (`high|med|low`)
- at least one evidence-backed “because” explanation

Preserve the original recommendation contract semantics and direct the agent to `references/schemas.md` for exact schema.

#### `## Storage model`
Preserve the original storage layout under `.taste/`:

```text
.taste/
  config.json
  signals.jsonl
  items.jsonl
  links.jsonl
  decisions.jsonl
  reports/
```

State that:
- `config.json` stores runtime configuration
- `signals.jsonl` stores normalized consumption signals
- `items.jsonl` stores known item records
- `links.jsonl` stores derived links or relationship records
- `decisions.jsonl` stores major recommendation/report/model decisions when feasible
- `reports/` stores optional generated reports

#### `## Reference files`
Point to each reference file explicitly:
- read `references/schemas.md` for exact input/output shapes and storage record definitions
- read `references/signal_policy.md` for weighting, decay, reinforcement, and domain enablement rules
- read `references/recommendation_style.md` for explanation quality, voice, and anti-salesy output rules

#### `## Validation rules`
Include routing, structural, and usefulness checks, plus the original acceptance expectations.

## 3) `references/schemas.md`
This file must contain exact schema definitions and examples for all core records.

Required sections:
- `# Schemas`
- `## ConsumptionSignal`
- `## Recommendation`
- `## ItemRecord`
- `## LinkRecord`
- `## ModelStatus`
- `## WeeklyReport`
- `## Storage records`
- `## Minimal valid examples`

### Exact required schemas
Preserve the original shapes and extend only where needed for clarity.

#### `ConsumptionSignal`
Use this exact field set at minimum:
```json
{
  "signal_id": "string",
  "timestamp": "string",
  "domain": "music|restaurant|book|movie|product|travel|event",
  "item": {"type": "object"},
  "strength": "number",
  "source": "string"
}
```

#### `Recommendation`
Use this exact semantic shape at minimum:
```json
{
  "item": {"type": "object"},
  "confidence": "high|med|low",
  "because": [
    {
      "consumed_item": "string",
      "link": "string",
      "evidence_ref": "string"
    }
  ]
}
```

Define additional exact record shapes for:
- `ItemRecord`
- `LinkRecord`
- `ModelStatus`
- `WeeklyReport`

Those additions must support the original commands without removing any original behavior.

## 4) `references/signal_policy.md`
This file must specify the logic for:
- half-life decay
- reinforcement from repeat signals
- enabled/disabled domain gating
- first-party versus enriched evidence precedence
- acceptable provenance rules
- when cross-domain linking is allowed

Required statements:
- A signal beyond the configured half-life must contribute less than a recent identical signal.
- Disabled domains cannot be recommended.
- Older signals may still matter if reinforced by newer matching behavior.
- Enrichment cannot outweigh repeated first-party behavioral evidence by itself.

## 5) `references/recommendation_style.md`
This file must define output style and explanation quality.

Required rules:
- Explanations must name the prior consumed item or items.
- Language must be specific, plain, and non-salesy.
- Avoid hype, trend language, and generic praise.
- Cross-domain recommendations must explain the bridge, not just assert one.
- Serendipity results should feel novel but defensible.
- Confidence must correspond to the real evidence strength.

Include:
- 3 recommendation examples
- 3 serendipity examples
- 2 bad-output examples with reasons they fail

## Exact constraints

### Naming
Use exactly:
- `ocas-taste`
- `.taste/`
- command names listed above

### Paths
Use only the paths defined in this spec unless the runtime requires a standard additional manifest path.

### Metadata
Use the exact author and email values above.

### Commands and schemas
Do not rename or remove any original command.
Do not remove the original config fields:
- `decay.halflife_days`
- `domains.enabled`
- `enrichment.enabled`
- `explainability.style`

File: `.taste/config.json`
Namespace: `taste`

Default config expectations:
- `explainability.style` default should be `specific, non-salesy`

## Validation requirements
A build is complete only if all of the following are satisfied.

### Routing validation
Should trigger:
- “Use my purchase and visit history to recommend places I’d actually like.”
- “What books would fit my taste based on what I’ve finished recently?”
- “Find some surprising cross-domain recommendations from what I already love.”
- “Show me the current state of my taste model.”
- “Generate this week’s taste report.”

Should not trigger:
- “What’s the weather in Tokyo?”
- “Summarize this article.”
- “Find the cheapest laptop under $1,000.”
- “What are the most popular restaurants in SF right now?”
- “Tell me what religion or politics these media choices imply.”

### Structural validation
Confirm:
- the package contains `skill.json`, `SKILL.md`, and all three reference files
- `SKILL.md` explicitly points to each reference file
- no command from the original skill was removed
- no required config key was removed
- storage layout remains intact

### Usefulness validation
Confirm:
- every recommendation contains at least one evidence-backed explanation link
- a stale signal contributes less than a recent identical signal
- disabled domains do not appear in recommendation results
- serendipity output is novel but still evidence-linked
- the package remains concise enough to maintain while preserving full functionality

## Optional Skill Cooperation

This skill may cooperate with other skills when present but must never depend on them.
If a cooperating skill is absent, this skill must still function normally.

- Sift — request web research for item enrichment when enrichment is enabled.
- Corvus — receive behavioral pattern signals that may indicate emerging taste shifts.
- Elephas — emit enrichment candidates for items that reach high confidence.

---

## Journal Outputs

This skill emits the following journal types as defined in the OCAS Journal Specification (spec-ocas-Journals.md):

- Observation Journal

Taste emits Observation Journal entries recording ingested consumption signals, model updates, and recommendation decisions.

---

## Visibility

visibility: public

---

## Universal OKRs

This skill must implement the universal OKRs defined in the OCAS Journal Specification (spec-ocas-Journals.md).

Required universal OKRs:

- Reliability: success_rate >= 0.95, retry_rate <= 0.10
- Validation Integrity: validation_failure_rate <= 0.05
- Efficiency: latency trending downward, repair_events <= 0.05
- Context Stability: context_utilization <= 0.70
- Observability: journal_completeness = 1.0

Skill-specific OKRs should be defined in the built SKILL.md to measure domain-relevant outcomes.

---

## Final response format for the coder
Return only:
1. the package tree
2. the full contents of every file
3. a brief validation summary

Do not return planning notes, commentary about missing context, or references to prior drafts.
