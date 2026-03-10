# Taste Schemas

## ConsumptionSignal
```json
{"signal_id":"string","timestamp":"string","domain":"string — music|restaurant|book|movie|product|travel|event","item":{"name":"string","metadata":"object"},"strength":"number — 0.0 to 1.0","source":"string — purchase|visit|play|watch|stay|manual"}
```

## Recommendation
```json
{"item":{"name":"string","domain":"string","metadata":"object"},"confidence":"string — high|med|low","because":[{"consumed_item":"string","link":"string — why this connects","evidence_ref":"string — signal_id"}]}
```

## ItemRecord
```json
{"item_id":"string","name":"string","domain":"string","metadata":"object","first_seen":"string","last_seen":"string","signal_count":"number","enriched":"boolean"}
```

## LinkRecord
```json
{"link_id":"string","item_a_id":"string","item_b_id":"string","link_type":"string","strength":"number","evidence_refs":["string"]}
```

## ModelStatus
```json
{"timestamp":"string","total_signals":"number","domains_active":["string"],"staleness_summary":"object","top_items_by_domain":"object"}
```

## WeeklyReport
```json
{"report_id":"string","period_start":"string","period_end":"string","new_signals":"number","emerging_patterns":["string"],"recommendations_generated":"number"}
```
