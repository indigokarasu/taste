#!/usr/bin/env python3
"""
Taste: Spotify Sync — Pull last 24 hours of listening history

Pulls recent plays from Spotify and adds them to Taste signals.
Handles deduplication by track+timestamp.

Usage:
    python3 scripts/sync-spotify.py [--dry-run]

Environment:
    Requires spotify-history skill credentials at ~/.openclaw/skills/spotify-history/credentials/spotify.json
    or SPOTIFY_CLIENT_ID/SPOTIFY_CLIENT_SECRET env vars.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Paths
TASTE_DATA_DIR = Path.home() / "openclaw" / "data" / "ocas-taste"
TASTE_SIGNALS_FILE = TASTE_DATA_DIR / "signals.jsonl"
TASTE_ITEMS_FILE = TASTE_DATA_DIR / "items.jsonl"
SPOTIFY_TOKEN_FILE = Path.home() / ".config" / "spotify-clawd" / "token.json"
SPOTIFY_HISTORY_DIR = Path.home() / ".openclaw" / "skills" / "spotify-history"

def load_spotify_token():
    """Load Spotify access token from spotify-history."""
    if not SPOTIFY_TOKEN_FILE.exists():
        print("Error: No Spotify token found. Run spotify-history auth first.")
        sys.exit(1)
    
    with open(SPOTIFY_TOKEN_FILE) as f:
        token_data = json.load(f)
    
    return token_data.get("access_token")

def get_recent_plays(access_token, hours=24):
    """Fetch last N hours of plays from Spotify API."""
    import urllib.request
    
    # Calculate timestamp for 24 hours ago
    after_ms = int((datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp() * 1000)
    
    url = f"https://api.spotify.com/v1/me/player/recently-played?limit=50&after={after_ms}"
    
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
            return data.get("items", [])
    except urllib.error.HTTPError as e:
        print(f"Error fetching Spotify data: {e.code}")
        if e.code == 401:
            print("Token expired. Re-authenticate with spotify-history.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def load_existing_sigs():
    """Load existing signal IDs for deduplication."""
    sig_ids = set()
    if TASTE_SIGNALS_FILE.exists():
        with open(TASTE_SIGNALS_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    sig = json.loads(line)
                    sig_ids.add(sig.get("signal_id", ""))
                except json.JSONDecodeError:
                    continue
    return sig_ids

def make_signal_id(track, played_at):
    """Generate unique signal ID from track and timestamp."""
    track_id = track.get("id", "unknown")
    ts = played_at.replace(":", "_").replace("+", "_")
    return f"spotify-play-{track_id}-{ts}"

def normalize_track(track_item):
    """Convert Spotify track to Taste ConsumptionSignal format."""
    track = track_item.get("track", {})
    played_at = track_item.get("played_at", "")
    
    track_id = track.get("id", "")
    track_name = track.get("name", "Unknown Track")
    artists = [a.get("name", "") for a in track.get("artists", [])]
    artist_name = artists[0] if artists else "Unknown Artist"
    album = track.get("album", {})
    album_name = album.get("name", "")
    
    # Parse timestamp
    try:
        played_dt = datetime.fromisoformat(played_at.replace("Z", "+00:00"))
    except:
        played_dt = datetime.now(timezone.utc)
    
    signal_id = make_signal_id(track, played_at)
    
    return {
        "signal_id": signal_id,
        "timestamp": played_dt.isoformat(),
        "domain": "music",
        "item": {
            "name": f"{track_name} by {artist_name}",
            "metadata": {
                "track_name": track_name,
                "artist": artist_name,
                "artists": artists,
                "album": album_name,
                "spotify_track_id": track_id,
                "spotify_url": track.get("external_urls", {}).get("spotify", ""),
                "duration_ms": track.get("duration_ms", 0),
                "explicit": track.get("explicit", False),
                "popularity": track.get("popularity", 0),
                "event_date": played_dt.isoformat()
            }
        },
        "strength": 0.60,  # base_play per Taste strength model
        "source": "play",
        "source_extraction_id": None
    }

def append_signal(signal):
    """Append signal to taste signals.jsonl."""
    TASTE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(TASTE_SIGNALS_FILE, "a") as f:
        f.write(json.dumps(signal, default=str) + "\n")

def append_item(signal):
    """Create/update item record matching Taste schema."""
    # Parse visit date from signal
    played_at = signal["item"]["metadata"].get("event_date", signal["timestamp"])
    
    item_record = {
        "item_id": signal["item"]["metadata"]["spotify_track_id"],
        "item_type": "music_track",
        "display_name": signal["item"]["name"],
        "domain": "music",
        "signal_count": 1,
        "first_signal_at": played_at,
        "last_signal_at": played_at,
        "visit_dates": [played_at],
        "metadata": signal["item"]["metadata"],
        "enriched": False,
        "enriched_at": None
    }
    
    # Load existing items
    items = []
    if TASTE_ITEMS_FILE.exists():
        with open(TASTE_ITEMS_FILE) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    # Update existing or append new
    item_id = item_record["item_id"]
    existing_idx = None
    for i, it in enumerate(items):
        if it.get("item_id") == item_id:
            existing_idx = i
            break
    
    if existing_idx is not None:
        items[existing_idx]["signal_count"] += 1
        items[existing_idx]["last_signal_at"] = played_at
        items[existing_idx]["visit_dates"].append(played_at)
    else:
        items.append(item_record)
    
    # Rewrite items file
    with open(TASTE_ITEMS_FILE, "w") as f:
        for it in items:
            f.write(json.dumps(it, default=str) + "\n")

def main():
    dry_run = "--dry-run" in sys.argv
    
    print("Taste: Spotify Sync")
    print("=" * 40)
    
    # Load token
    access_token = load_spotify_token()
    print("✓ Spotify token loaded")
    
    # Load existing signals for dedup
    existing_sigs = load_existing_sigs()
    print(f"✓ Loaded {len(existing_sigs)} existing signal IDs")
    
    # Fetch recent plays
    print("\nFetching last 24 hours of plays...")
    plays = get_recent_plays(access_token, hours=24)
    print(f"✓ Retrieved {len(plays)} plays from Spotify")
    
    # Process and filter
    new_signals = []
    duplicates = 0
    
    for play in plays:
        signal = normalize_track(play)
        
        if signal["signal_id"] in existing_sigs:
            duplicates += 1
            continue
        
        new_signals.append(signal)
    
    print(f"\nResults:")
    print(f"  Total plays: {len(plays)}")
    print(f"  Duplicates (skipped): {duplicates}")
    print(f"  New signals: {len(new_signals)}")
    
    if dry_run:
        print("\n[DRY RUN] Would add:")
        for sig in new_signals[:5]:
            print(f"  - {sig['item_name']}")
        if len(new_signals) > 5:
            print(f"  ... and {len(new_signals) - 5} more")
        return
    
    # Append new signals
    added = 0
    for signal in new_signals:
        append_signal(signal)
        append_item(signal)
        added += 1
    
    print(f"\n✓ Added {added} new signals to Taste")
    print(f"✓ Data stored in: {TASTE_DATA_DIR}")
    
    # Write journal entry
    from uuid import uuid4
    run_id = f"taste-sync-spotify-{uuid4().hex[:8]}"
    journal_entry = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill_id": "ocas-taste",
        "skill_version": "3.2.0",
        "task_type": "sync",
        "command": "taste.sync.spotify",
        "status": "success",
        "input": {"hours": 24, "source": "spotify"},
        "output": {
            "plays_retrieved": len(plays),
            "duplicates": duplicates,
            "new_signals_added": added
        },
        "observations": [
            {
                "type": "entity",
                "entity_type": "ConsumptionSignal",
                "entity_id": sig["signal_id"],
                "operation": "created",
                "user_relevance": "user"
            }
            for sig in new_signals
        ]
    }
    
    journal_dir = Path.home() / "openclaw" / "journals" / "ocas-taste" / datetime.now().strftime("%Y-%m-%d")
    journal_dir.mkdir(parents=True, exist_ok=True)
    
    journal_file = journal_dir / f"{run_id}.json"
    with open(journal_file, "w") as f:
        json.dump(journal_entry, f, indent=2)
    
    print(f"✓ Journal written: {journal_file}")

if __name__ == "__main__":
    main()
