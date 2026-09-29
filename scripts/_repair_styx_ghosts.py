#!/usr/bin/env python3
"""Remove the amount=None receipt-schema GHOST duplicate of an already-ingested
Styx purchase.

The 2026-09-24 receipt batch re-emitted ~129 purchases already in the model.
Each ghost has amount=None at the top level (the figure lives in
metadata.amount) and shares its Plaid transaction_id with the real signal for
the same normalized merchant + date. Grouping on amount alone misses them --
every ghost group looks "distinct" -- so this keys on transaction_id.

Only removes a signal when its group (normalized merchant, date) contains a
sibling that (a) shares the same transaction_id and (b) carries a real
top-level amount. A group is never collapsed if the amounts differ, since
same merchant + same day + different amount is two genuine visits.

Usage: repair_styx_ghosts.py <data-dir> [--apply]
"""
import json
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path


def norm(x):
    return ''.join(ch for ch in str(x or '').lower() if ch.isalnum())


def main():
    data_dir = Path(sys.argv[1])
    apply = '--apply' in sys.argv
    sig_path = data_dir / 'signals.jsonl'

    signals = [json.loads(l) for l in open(sig_path) if l.strip()]
    items = [json.loads(l) for l in open(data_dir / 'items.jsonl') if l.strip()]
    item_ids = {i.get('item_id') for i in items}

    groups = defaultdict(list)
    for s in signals:
        if s.get('source') != 'styx':
            continue
        p = (s.get('dedup_key') or '').split(':')
        if len(p) >= 3:
            groups[(norm(p[1]), p[2])].append(s)

    drop = set()
    for key, members in groups.items():
        if len(members) < 2:
            continue
        def amt(s):
            a = s.get('amount')
            if a is None:
                a = (s.get('metadata') or {}).get('amount')
            return None if a is None else round(float(a), 2)
        amounts = [amt(s) for s in members]
        if len(set(amounts)) != 1:
            continue  # genuinely different charges -> keep every signal
        tids = {(s.get('metadata') or {}).get('transaction_id') for s in members}
        tids.discard(None)
        if len(tids) != 1:
            continue  # no shared transaction -> can't prove they're one purchase
        # keep the member with a real top-level amount whose item resolves
        ranked = sorted(members, key=lambda s: (
            s.get('amount') is None,
            0 if (s.get('item_id') in item_ids) else 1,
            str(s.get('created_at') or '')))
        keep = ranked[0]
        for s in members:
            if s is not keep:
                drop.add(id(s))

    kept = [s for s in signals if id(s) not in drop]
    print(f"signals before: {len(signals)}  after: {len(kept)}  ghosts removed: {len(drop)}")
    ghosts_amt_none = sum(1 for s in signals if id(s) in drop and s.get('amount') is None)
    print(f"  of which amount=None ghosts: {ghosts_amt_none}")
    if not apply:
        print("DRY RUN -- pass --apply to write")
        return 0
    if not drop:
        print("nothing to remove")
        return 0
    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    shutil.copy2(sig_path, data_dir / f'signals.jsonl.bak-ghostfix-{stamp}')
    with open(sig_path, 'w') as f:
        for s in kept:
            f.write(json.dumps(s) + '\n')
    print(f"wrote signals; backup signals.jsonl.bak-ghostfix-{stamp}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
