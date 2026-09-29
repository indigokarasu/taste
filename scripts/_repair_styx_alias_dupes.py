#!/usr/bin/env python3
"""Remove Styx alias-duplicate signals (same normalized merchant + date + amount).

Only removes a signal when a sibling in the same group carries an IDENTICAL
amount -- i.e. a Plaid merchant-rename re-emission of one already-ingested
purchase. Groups where amounts genuinely differ (two real same-day visits) are
left untouched, as are the amount=None receipt-schema signals from the
2026-09-24 batch (different ingestion pipeline -- flagged, not deleted).

Usage: repair_styx_alias_dupes.py <data-dir> [--apply]
"""
import json
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path



def _usage():
    """--help must not touch the data dir.

    tests/test_script_help.py runs every scripts/*.py with --help and requires
    exit 0. main() reads sys.argv[1] as the data dir, so --help was consumed as
    a path and the script died on open('--help/signals.jsonl') before printing
    anything. The contract this pins is that a fresh agent can ask for help
    without a data dir and without a traceback.
    """
    print(__doc__.strip())
    print("\nusage: %s <data-dir> [--apply]\n" % __file__.rsplit("/", 1)[-1])
    return 0

def norm(x):
    return ''.join(ch for ch in str(x or '').lower() if ch.isalnum())


def main():
    if any(a in ('-h', '--help') for a in sys.argv[1:]):
        return _usage()
    if len(sys.argv) < 2:
        print(__doc__.strip())
        print("\nusage: %s <data-dir> [--apply]\n" % __file__.rsplit('/', 1)[-1])
        return 2
    data_dir = Path(sys.argv[1])
    apply = '--apply' in sys.argv
    sig_path = data_dir / 'signals.jsonl'
    item_path = data_dir / 'items.jsonl'

    signals = [json.loads(l) for l in open(sig_path) if l.strip()]
    items = [json.loads(l) for l in open(item_path) if l.strip()]
    item_ids = {i.get('item_id') for i in items}

    styx = [s for s in signals if s.get('source') == 'styx']
    groups = defaultdict(list)
    for s in styx:
        parts = (s.get('dedup_key') or '').split(':')
        if len(parts) >= 3:
            groups[(norm(parts[1]), parts[2])].append(s)

    def amt(s):
        a = s.get('amount')
        return None if a is None else round(float(a), 2)

    drop = []
    for key, members in groups.items():
        if len(members) < 2:
            continue
        amounts = [amt(s) for s in members]
        if len(set(amounts)) != 1 or amounts[0] is None:
            continue  # differing amounts (2 real visits) or an amount=None ghost
        # keep the earliest-created member whose item_id resolves; else earliest
        members_sorted = sorted(members, key=lambda s: str(s.get('created_at') or ''))
        keep = None
        for cand in members_sorted:
            if not cand.get('item_id') or cand.get('item_id') in item_ids:
                keep = cand
                break
        if keep is None:
            keep = members_sorted[0]
        for s in members:
            if s is not keep:
                drop.append(s)

    drop_ids = {id(s) for s in drop}
    kept = [s for s in signals if id(s) not in drop_ids]

    # items that would lose their only referencing signal
    ref = defaultdict(int)
    for s in kept:
        if s.get('item_id'):
            ref[s['item_id']] += 1
    newly_orphaned_items = [
        i for i in items
        if i.get('item_id') not in ref and any(s.get('item_id') == i.get('item_id') for s in drop)
    ]

    print(f"signals before: {len(signals)}  after: {len(kept)}  removed: {len(drop)}")
    print(f"items becoming unreferenced: {len(newly_orphaned_items)} (left in place)")
    if not apply:
        print("DRY RUN -- pass --apply to write")
        return 0

    if not drop:
        print("nothing to remove")
        return 0

    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    shutil.copy2(sig_path, data_dir / f'signals.jsonl.bak-aliasdedup-{stamp}')
    with open(sig_path, 'w') as f:
        for s in kept:
            f.write(json.dumps(s) + '\n')
    print(f"wrote {sig_path}; backup signals.jsonl.bak-aliasdedup-{stamp}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
