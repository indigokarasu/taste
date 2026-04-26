#!/usr/bin/env python3
"""
Spotify listening history sync for Taste skill.
Pulls recent plays and top tracks, creates ConsumptionSignals.
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
except ImportError:
    print("Error: spotipy not installed. Run: pip install spotipy")
    sys.exit(1)

# Paths
DATA_DIR = Path(__file__).parent.parent
SIGNALS_FILE = DATA_DIR / "signals.jsonl"
ITEMS_FILE = DATA_DIR / "items.jsonl"
CHECKPOINT_FILE = DATA_DIR / "music" / "spotify_sync_checkpoint.json"

# Spotify OAuth configuration
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

def load_checkpoint():
    """Load last sync timestamp."""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {"last_sync": None}

def save_checkpoint(checkpoint):
    """Save sync timestamp."""
    CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)

def load_existing_items():
    """Load existing items to avoid duplicates."""
    items = {}
    if ITEMS_FILE.exists():
        with open(ITEMS_FILE, 'r') as f:
            for line in f:
                item = json.loads(line)
                items[item.get("item_id", "")] = item
    return items

def load_existing_signals():
    """Load existing signals to avoid duplicates."""
    signals = {}
    if SIGNALS_FILE.exists():
        with open(SIGNALS_FILE, 'r') as f:
            for line in f:
                signal = json.loads(line)
                signals[signal.get("signal_id", "")] = signal
    return signals

def create_spotify_client():
    """Create authenticated Spotify client."""
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("Error: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables required")
        print("Set them with:")
        print("  export SPOTIFY_CLIENT_ID='your_client_id'")
        print("  export SPOTIFY_CLIENT_SECRET='your_client_secret'")
        sys.exit(1)

    scope = "user-read-recently-played user-top-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope=scope,
        open_browser=False
    ))
    return sp

def sync_recent_plays(sp, existing_items, existing_signals):
    """Sync recently played tracks (last 24 hours)."""
    new_signals = []
    new_items = {}
    
    try:
        results = sp.current_user_recently_played(limit=50)
    except Exception as e:
        print(f"Error fetching recently played: {e}")
        return new_signals, new_items
    
    for item in results['items']:
        track = item['track']
        played_at = item['played_at']
        track_id = track['id']
        
        # Skip if already have this signal
        signal_id = f"spotify-play-{track_id}-{played_at}"
        if signal_id in existing_signals:
            continue
        
        # Create or update item
        item_id = f"spotify-track-{track_id}"
        if item_id not in existing_items:
            item_data = {
                "item_id": item_id,
                "name": track['name'],
                "domain": "music",
                "source": "spotify",
                "metadata": {
                    "artist": track['artists'][0]['name'] if track['artists'] else None,
                    "album": track['album']['name'] if track['album'] else None,
                    "duration_ms": track['duration_ms'],
                    "spotify_url": track['external_urls'].get('spotify'),
                    "track_id": track_id
                },
                "enriched": True,
                "enriched_at": datetime.utcnow().isoformat(),
                "first_seen": played_at,
                "last_seen": played_at,
                "signal_count": 0,
                "visit_dates": []
            }
            new_items[item_id] = item_data
        else:
            item_data = existing_items[item_id]
            item_data['last_seen'] = played_at
            item_data['signal_count'] += 1
            item_data['visit_dates'].append(played_at)
        
        # Create signal
        signal_data = {
            "signal_id": signal_id,
            "item_id": item_id,
            "domain": "music",
            "source": "play",
            "strength": 0.60,
            "timestamp": played_at,
            "metadata": {
                "played_at": played_at,
                "context": item.get('context', {}).get('type') if item.get('context') else None
            }
        }
        new_signals.append(signal_data)
    
    return new_signals, new_items

def sync_top_tracks(sp, existing_items, existing_signals):
    """Sync top tracks (short term)."""
    new_signals = []
    new_items = {}
    
    try:
        results = sp.current_user_top_tracks(limit=20, time_range='short_term')
    except Exception as e:
        print(f"Error fetching top tracks: {e}")
        return new_signals, new_items
    
    now = datetime.utcnow().isoformat()
    
    for track in results['items']:
        track_id = track['id']
        
        # Create or update item
        item_id = f"spotify-track-{track_id}"
        if item_id not in existing_items:
            item_data = {
                "item_id": item_id,
                "name": track['name'],
                "domain": "music",
                "source": "spotify",
                "metadata": {
                    "artist": track['artists'][0]['name'] if track['artists'] else None,
                    "album": track['album']['name'] if track['album'] else None,
                    "duration_ms": track['duration_ms'],
                    "spotify_url": track['external_urls'].get('spotify'),
                    "track_id": track_id
                },
                "enriched": True,
                "enriched_at": now,
                "first_seen": now,
                "last_seen": now,
                "signal_count": 0,
                "visit_dates": []
            }
            new_items[item_id] = item_data
        else:
            item_data = existing_items[item_id]
            item_data['last_seen'] = now
            item_data['signal_count'] += 1
            item_data['visit_dates'].append(now)
        
        # Create signal
        signal_id = f"spotify-top-{track_id}-{now}"
        signal_data = {
            "signal_id": signal_id,
            "item_id": item_id,
            "domain": "music",
            "source": "play",
            "strength": 0.60,
            "timestamp": now,
            "metadata": {
                "top_track": True,
                "time_range": "short_term"
            }
        }
        new_signals.append(signal_data)
    
    return new_signals, new_items

def main():
    """Main sync function."""
    print("Starting Spotify sync...")
    
    # Load existing data
    existing_items = load_existing_items()
    existing_signals = load_existing_signals()
    checkpoint = load_checkpoint()
    
    # Create Spotify client
    sp = create_spotify_client()
    
    # Sync recent plays
    print("Syncing recent plays...")
    recent_signals, recent_items = sync_recent_plays(sp, existing_items, existing_signals)
    
    # Sync top tracks
    print("Syncing top tracks...")
    top_signals, top_items = sync_top_tracks(sp, existing_items, existing_signals)
    
    # Merge new items
    all_new_items = {**recent_items, **top_items}
    
    # Write new signals
    if recent_signals or top_signals:
        with open(SIGNALS_FILE, 'a') as f:
            for signal in recent_signals + top_signals:
                f.write(json.dumps(signal) + '\n')
        print(f"Created {len(recent_signals + top_signals)} new signals")
    
    # Write updated items
    if all_new_items:
        with open(ITEMS_FILE, 'a') as f:
            for item in all_new_items.values():
                f.write(json.dumps(item) + '\n')
        print(f"Updated {len(all_new_items)} items")
    
    # Save checkpoint
    checkpoint["last_sync"] = datetime.utcnow().isoformat()
    save_checkpoint(checkpoint)
    
    print(f"Sync complete. Last sync: {checkpoint['last_sync']}")

if __name__ == "__main__":
    main()