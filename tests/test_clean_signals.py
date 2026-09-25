#!/usr/bin/env python3
"""Unit tests for clean_signals.py — generic-meal filtering and same-day dedup.

The date-bug era taught the hard way that calendar rows titled "Dinner" are not
venues, and that the same venue can appear twice per day via two sources. These
tests pin that behaviour with a temp copy of signals.jsonl (never the live file).
"""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / ("%s.py" % name))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cs = _load("clean_signals")


class CleanSignalsTest(unittest.TestCase):
    def test_generic_meal_detection(self):
        for name in ("Dinner", "breakfast", "Lunch / M", "Brunch"):
            self.assertTrue(cs._is_generic_meal(name), name)
        for name in ("Taco Bell", "Sidewalk Juice", "Dinner House"):
            self.assertFalse(cs._is_generic_meal(name), name)

    def test_clean_drops_junk_and_dedups_same_day(self):
        recs = [
            {"venue_name": "Dinner", "event_date": "2026-07-01", "extraction_source": "calendar", "domain": "food"},
            {"venue_name": "", "event_date": "2026-07-01", "extraction_source": "email", "domain": "food"},
            {"venue_name": "Taco Bell", "event_date": "2026-07-01T12:00:00", "extraction_source": "styx", "domain": "food"},
            {"venue_name": "Taco Bell", "event_date": "2026-07-01T19:00:00", "extraction_source": "styx", "domain": "food"},
            {"venue_name": "Taco Bell", "event_date": "2026-07-02", "extraction_source": "styx", "domain": "food"},
        ]
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "signals.jsonl"
            p.write_text("\n".join(json.dumps(r) for r in recs) + "\n", encoding="utf-8")
            before, after = cs.clean(p)
            kept = [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(before, 5)
        # "Dinner" and empty venue dropped; two same-day Taco Bell rows collapse to one;
        # the next-day Taco Bell row survives.
        self.assertEqual(after, 2)
        self.assertEqual(sorted(s["event_date"][:10] for s in kept), ["2026-07-01", "2026-07-02"])


if __name__ == "__main__":
    unittest.main()
