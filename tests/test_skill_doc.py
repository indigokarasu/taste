#!/usr/bin/env python3
"""Doc-integrity tests for the ocas-taste skill.

Guards the SKILL.md contract: frontmatter parses, the file stays inside the
context budget (approx tokens = chars / 4), and every references/ or scripts/
path it cites exists on disk. A stale pointer in SKILL.md is a dead reference
that silently wastes a run.
"""
import re
import unittest
from pathlib import Path

try:
    import yaml
except ImportError:  # keep the suite runnable on stdlib-only interpreters
    yaml = None

SKILL_DIR = Path(__file__).resolve().parent.parent
SKILL_MD = SKILL_DIR / "SKILL.md"

MAX_CHARS = 14000  # D3 budget: len(content) / 4 must stay <= 3500 tokens
MAX_LINES = 300


class SkillDocTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SKILL_MD.read_text(encoding="utf-8")

    def test_frontmatter_parses(self):
        if yaml is None:
            self.skipTest("PyYAML unavailable")
        parts = self.text.split("---")
        self.assertGreaterEqual(len(parts), 3, "frontmatter block missing")
        fm = yaml.safe_load(parts[1])
        self.assertIsInstance(fm, dict, "frontmatter is not a mapping")
        for key in ("name", "description", "triggers"):
            self.assertTrue(fm.get(key), "frontmatter missing %r" % key)
        self.assertEqual(fm["name"], "ocas-taste")

    def test_within_context_budget(self):
        self.assertLessEqual(
            len(self.text), MAX_CHARS,
            "SKILL.md is %d chars; keep it <= %d (token budget)" % (len(self.text), MAX_CHARS),
        )
        self.assertLessEqual(len(self.text.splitlines()), MAX_LINES)

    def test_cited_support_files_exist(self):
        missing = []
        refs = set(re.findall(r"references/[\w./-]+\.md", self.text))
        scripts = set(re.findall(r"(?<![/\w-])scripts/[\w.-]+\.py", self.text))
        for ref in sorted(refs | scripts):
            if not (SKILL_DIR / ref).exists():
                missing.append(ref)
        self.assertEqual(missing, [], "SKILL.md cites missing files: %s" % missing)


if __name__ == "__main__":
    unittest.main()
