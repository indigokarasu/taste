## [2026-04-04] Spec Compliance Update

### Changes
- Added missing SKILL.md sections per ocas-skill-authoring-rules.md
- Updated skill.json with required metadata fields
- Ensured all storage layouts and journal paths are properly declared
- Aligned ontology and background task declarations with spec-ocas-ontology.md

### Validation
- ✓ All required SKILL.md sections present
- ✓ All skill.json fields complete
- ✓ Storage layout properly declared
- ✓ Journal output paths configured
- ✓ Version: 3.3.1 → 3.3.2

# CHANGELOG

## [3.4.1] - 2026-04-08

### Storage Architecture Update

- Replaced $OCAS_DATA_ROOT variable with platform-native {agent_root}/commons/ convention
- Replaced intake directory pattern with journal payload convention
- Added errors/ as universal storage root alongside journals/
- Inter-skill communication now flows through typed journal payload fields
- No invented environment variables — skills ask the agent for its root directory


## [3.4.0] - 2026-04-08

### Multi-Platform Compatibility Migration

- Adopted agentskills.io open standard for skill packaging
- Replaced skill.json with YAML frontmatter in SKILL.md
- Replaced hardcoded ~/openclaw/ paths with {agent_root}/commons/ for platform portability
- Abstracted cron/heartbeat registration to declarative metadata pattern
- Added metadata.hermes and metadata.openclaw extension points
- Compatible with both OpenClaw and Hermes Agent


## [3.3.1] - 2026-04-02

### Changed
- Replaced `scripts/sync-spotify.py` with SKILL.md-native workflow using spotify-history skill
- `taste.sync.spotify` scheduled task now runs as a skill command, not a Python script
- No external script dependencies for Spotify sync

### Removed
- `scripts/sync-spotify.py` — functionality replaced by spotify-history skill integration

## [3.3.0] - 2026-04-02

### Added
- `taste.sync.spotify` command — pull last 24 hours of Spotify listening history
- `scripts/sync-spotify.py` — syncs Spotify plays to Taste as music ConsumptionSignals
- `music/` data subdirectory for sync checkpoint storage
- Daily scheduled task for automatic Spotify sync at midnight
- Music domain enabled by default in config

### Changed
- SKILL.md: Added taste.sync.spotify to commands list
- skill.json: Added taste:sync-spotify scheduled task
- Storage layout docs: Documented music sync checkpoint location

## [3.2.0] - 2026-04-02

### Added
- Structured entity observations in journal payloads (`entities_observed`, `relationships_observed`, `preferences_observed`)
- `user_relevance` tagging on journal observations (default `user` for preference-relevant entities)
- Elephas journal cooperation in skill cooperation section
- Concept/Idea, Entity/Person added to ontology types

## 3.1.0 — 2026-03-30

### Added
- `references/plans/preference-scan.plan.md` — bundled workflow plan: ingest recent activity → extract signals → update preference model
- Ontology mapping: Taste works with Place (venues), Thing/DigitalArtifact (media items), and Concept/Action (behavioral actions)
- ConsumptionSignal and ItemRecord schemas documented in `spec-ocas-shared-schemas.md`

## Prior

See git log for earlier history.
