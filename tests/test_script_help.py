#!/usr/bin/env python3
"""Every bundled script must answer --help WITHOUT third-party imports, auth, or
network access. This pins the lazy-import contract: --help is the first thing a
fresh agent runs, and it must never trigger a Google/Spotify login or traceback
on a machine without googleapiclient installed.
"""
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


class HelpContractTest(unittest.TestCase):
    def test_every_script_answers_help(self):
        scripts = sorted(SCRIPTS.glob("*.py"))
        self.assertTrue(scripts, "no scripts found under scripts/")
        failures = []
        for sp in scripts:
            try:
                r = subprocess.run(
                    [sys.executable, str(sp), "--help"],
                    capture_output=True, text=True, timeout=30,
                )
            except subprocess.TimeoutExpired:
                failures.append("%s: --help timed out" % sp.name)
                continue
            if r.returncode != 0:
                failures.append("%s: rc=%s %s" % (sp.name, r.returncode, (r.stderr or "").strip()[:80]))
            elif not (r.stdout.strip() or r.stderr.strip()):
                failures.append("%s: --help produced no output" % sp.name)
        self.assertEqual(failures, [], "scripts failing the --help contract: %s" % failures)


if __name__ == "__main__":
    unittest.main()
