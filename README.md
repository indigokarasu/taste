# 🎯 Taste

Behavior-driven taste model built from real consumption signals.

**Skill name:** `ocas-taste`
**Version:** 2.2.0
**Type:** system
**Layer:** Preference
**Author:** Indigo Karasu

---

## Files

| File | Purpose |
|---|---|
| `skill.json` | Package metadata and routing description |
| `SKILL.md` | Operational instructions for the agent |
| `references/` | Support files referenced by SKILL.md |

---

## Changelog

### 2.2.0 (2026-03-22)

- Added short-name routing aliases to skill.json description and SKILL.md frontmatter for natural invocation ('Scout', 'Sift', etc.)
- Added trigger phrases to descriptions for improved routing accuracy
- Cross-skill references in descriptions now use 'use X' format for routing clarity

### 2.1.0 (2026-03-22)

- Added explicit journal write as final workflow step (step 10)
- Added Initialization section with storage bootstrap
- Removed non-conformant OCAS_ROOT environment variable reference

### 2.0.0 (2026-03-18)

- Initial build of all OCAS skills as a unified suite
