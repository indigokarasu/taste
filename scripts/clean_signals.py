"""Garbage signal cleanup helper.

Removes signals with no real venue and deduplicates across
(venue_name, event_date, extraction_source, domain). Writes the cleaned
set back to the same JSONL file.

Usage:
    python scripts/clean_signals.py /path/to/signals.jsonl
"""

import json
import sys
from pathlib import Path


def clean(signals_path: Path) -> tuple[int, int]:
    with signals_path.open() as fh:
        signals = [json.loads(line) for line in fh if line.strip()]

    total = len(signals)
    clean_signals = [
        s for s in signals
        if s.get("venue_name") not in (None, "Unknown", "")
    ]

    seen: set[tuple[str, str, str, str]] = set()
    unique: list[dict] = []
    for s in clean_signals:
        key = (
            s.get("venue_name", ""),
            s.get("event_date", "")[:10],
            s.get("extraction_source", ""),
            s.get("domain", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(s)

    with signals_path.open("w") as fh:
        for s in unique:
            fh.write(json.dumps(s) + "\n")

    return total, len(unique)


if __name__ == "__main__":
    path = Path(sys.argv[1])
    before, after = clean(path)
    print(f"cleaned {path}: {before} -> {after}")
