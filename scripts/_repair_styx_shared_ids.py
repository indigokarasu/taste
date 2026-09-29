#!/usr/bin/env python3
"""Repair two remaining Styx duplication classes in signals.jsonl.

Class 1 -- shared signal_id: two signals carry the SAME signal_id because a
single Plaid transaction_id was linked to two merchant aliases. One purchase,
two names. Keep one signal per signal_id, preferring the one whose venue name
is not a raw/truncated alias and whose item_id resolves.

Class 2 -- same-day multi-charge at one merchant: a merchant with N distinct
Plaid transactions on the same day but only one signal. These are REAL repeat
visits, not duplicates; add the missing signals from the transactions table.

Usage: repair_styx_shared_ids.py <data-dir> [--apply]
"""
import json
import shutil
import sqlite3
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path

STYX_DB = '/root/.hermes/data/styx.db'
TXN_DB = '/root/.hermes/data/transactions.db'


def norm(x):
    return ''.join(ch for ch in str(x or '').lower() if ch.isalnum())


def main():
    data_dir = Path(sys.argv[1])
    apply = '--apply' in sys.argv
    sig_path = data_dir / 'signals.jsonl'

    signals = [json.loads(l) for l in open(sig_path) if l.strip()]
    items = [json.loads(l) for l in open(data_dir / 'items.jsonl') if l.strip()]
    item_ids = {i.get('item_id') for i in items}
    item_by_norm = {}
    for i in items:
        n = norm(i.get('name'))
        if n:
            item_by_norm.setdefault(n, i)

    # ---- Class 1: one signal per signal_id -------------------------------
    by_sid = defaultdict(list)
    for s in signals:
        if s.get('signal_id'):
            by_sid[s['signal_id']].append(s)

    def rank(s):
        venue = str(s.get('venue_name') or '')
        resolvable = 0 if (s.get('item_id') and s['item_id'] in item_ids) else 1
        # a name with spaces/punctuation is a cleaned display name, not a raw alias
        aliasish = 1 if (norm(venue) == venue.lower() and ' ' in venue) else 0
        return (aliasish, resolvable, str(s.get('created_at') or ''))

    drop_sid = set()
    for sid, members in by_sid.items():
        if len(members) < 2:
            continue
        keep = sorted(members, key=rank)[0]
        for s in members:
            if s is not keep:
                drop_sid.add(id(s))

    # ---- Class 2: real same-day repeat visits ----------------------------
    conn = sqlite3.connect(STYX_DB)
    conn.execute(f"ATTACH DATABASE '{TXN_DB}' AS txndb")
    rows = conn.execute('''
        SELECT t.transaction_id, t.amount, t.date, m.name, m.category, m.city, tm.confidence
        FROM transaction_merchants tm
        JOIN merchants m ON tm.merchant_id = m.id
        JOIN txndb.transactions t ON tm.transaction_id = t.transaction_id
        WHERE (m.category IN ('restaurant','cafe','bar','food')
           OR t.personal_finance_category = 'FOOD_AND_DRINK')
          AND tm.confidence >= 0.7
    ''').fetchall()
    conn.close()

    # one row per real transaction (an alias join can duplicate a txn)
    seen_txn = {}
    for r in rows:
        seen_txn.setdefault(r[0], r)
    txn_rows = list(seen_txn.values())

    have = defaultdict(set)
    have_txn = defaultdict(set)
    for s in signals:
        if s.get('source') == 'styx':
            p = (s.get('dedup_key') or '').split(':')
            if len(p) >= 3:
                # receipt-schema signals (2026-09-24 batch) store amount=None at
                # the top level and the real figure in metadata.amount -- without
                # this fallback every repeat visit looks missing and is re-added.
                a = s.get('amount')
                if a is None:
                    a = (s.get('metadata') or {}).get('amount')
                have[(norm(p[1]), p[2])].add(round(float(a), 2) if a is not None else None)
                tid = (s.get('metadata') or {}).get('transaction_id')
                if tid:
                    have_txn[(norm(p[1]), p[2])].add(tid)

    additions = []
    for txn_id, amount, date, merchant, cat, city, conf in txn_rows:
        key = (norm(merchant), str(date)[:10])
        amt = round(float(amount), 2) if amount is not None else None
        if amt is None or amt in have[key]:
            continue
        # only when a signal already exists for this venue+day (a real repeat)
        if not have.get(key):
            continue
        # never re-add a transaction_id that is already ingested under an alias
        if txn_id in have_txn[key]:
            continue
        item = item_by_norm.get(key[0])
        additions.append({
            'signal_id': f'sig-styx-{uuid.uuid4().hex[:28]}',
            'item_id': item.get('item_id') if item else None,
            'dedup_key': f"styx:{str(merchant).lower().strip()}:{str(date)[:10]}",
            'domain': 'food',
            'source': 'styx',
            'signal_type': 'purchase',
            'venue_name': merchant,
            'merchant_name': merchant,
            'amount': amt,
            'date': str(date)[:10],
            'event_date': str(date)[:10],
            'confidence': conf,
            'metadata': {'transaction_id': txn_id, 'category': cat, 'city': city,
                         'ingested_by': 'repair_styx_shared_ids'},
            'created_at': time.strftime('%Y-%m-%dT%H:%M:%S+00:00', time.gmtime()),
        })
        have[key].add(amt)

    kept = [s for s in signals if id(s) not in drop_sid] + additions
    print(f"signals before: {len(signals)}  after: {len(kept)}")
    print(f"  shared-signal_id dupes removed: {len(drop_sid)}")
    print(f"  real same-day repeat visits added: {len(additions)}")
    for a in additions:
        print(f"    + {a['dedup_key']} ${a['amount']}")
    if not apply:
        print("DRY RUN -- pass --apply to write")
        return 0

    stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    shutil.copy2(sig_path, data_dir / f'signals.jsonl.bak-sharedid-{stamp}')
    with open(sig_path, 'w') as f:
        for s in kept:
            f.write(json.dumps(s) + '\n')
    print(f"wrote signals; backup signals.jsonl.bak-sharedid-{stamp}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
