#!/usr/bin/env python3
"""Unit tests for safe_taste_dedup.py keying — the Styx-safety invariant.

Incident 2026-07-22: dispatch_taste_dedup.py keyed on event_date[:10] alone.
Styx signals carry `date`, not `event_date`, so they all collapsed into one
group per venue and all-but-one were deleted (47 of 49 lost). keyfn() here
must fall back to `date` so every (venue, day) survives.
"""
import importlib.util
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / ("%s.py" % name))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sd = _load("safe_taste_dedup")


class StyxSafetyTest(unittest.TestCase):
    def test_date10_prefers_event_date_then_date(self):
        self.assertEqual(sd.date10({"event_date": "2026-07-22T09:00:00"}), "2026-07-22")
        self.assertEqual(sd.date10({"date": "2026-07-22"}), "2026-07-22")
        self.assertEqual(sd.date10({}), "")

    def test_styx_signals_do_not_collapse_across_days(self):
        styx = [
            {"venue_name": "Cafe X", "date": "2026-07-20", "extraction_source": "styx"},
            {"venue_name": "Cafe X", "date": "2026-07-21", "extraction_source": "styx"},
            {"venue_name": "Cafe X", "date": "2026-07-22", "extraction_source": "styx"},
        ]
        keys = {sd.keyfn(s) for s in styx}
        self.assertEqual(len(keys), 3, "Styx visits collapsed - real visits would be deleted")

    def test_same_venue_same_day_different_sources_survive(self):
        a = {"venue_name": "Cafe X", "event_date": "2026-07-22T11:00:00", "extraction_source": "styx"}
        b = {"venue_name": "Cafe X", "event_date": "2026-07-22", "extraction_source": "email"}
        self.assertNotEqual(sd.keyfn(a), sd.keyfn(b))

    def test_same_key_still_dedups_exact_duplicates(self):
        a = {"venue_name": "Cafe X", "event_date": "2026-07-22T11:00:00", "extraction_source": "email"}
        b = {"venue_name": "Cafe X", "event_date": "2026-07-22T18:00:00", "extraction_source": "email"}
        self.assertEqual(sd.keyfn(a), sd.keyfn(b))


if __name__ == "__main__":
    unittest.main()
