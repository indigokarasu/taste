#!/usr/bin/env python3
"""
Spotify listening history sync using MCP server.
Pulls recent plays and top tracks via Spotify MCP.
"""
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent.parent
SIGNALS_FILE = DATA_DIR / "signals.jsonl"
ITEMS_FILE = DATA_DIR / "items.jsonl"
CHECKPOINT_FILE = DATA_DIR / "music" / "spotify_sync_checkpoint.json"

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

def call_mcp_tool(tool_name, args=None):
    """Call Spotify MCP tool via hermes mcp."""
    cmd = ["hermes", "mcp", "call", "spotify", tool_name]
    if args:
        for key, value in args.items():
            cmd.extend([f"--{key}", str(value)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            print(f"Error calling MCP tool {tool_name}: {result.stderr}")
            return None
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Timeout calling MCP tool {tool_name}")
        return None
    except Exception as e:
        print(f"Error calling MCP tool {tool_name}: {e}")
        return None

def parse_recently_played(output):
    """Parse recently played output from MCP."""
    tracks = []
    lines = output.strip().split('\n')
    
    for line in lines:
        # Format: "1. Song Name - Artist (played at time)"
        if line.strip() and line[0].isdigit():
            try:
                # Extract track info
                parts = line.split('. ', 1)
                if len(parts) < 2:
                    continue
                
                track_info = parts[1]
                if ' - ' in track_info:
                    name, artist = track_info.split(' - ', 1)
                    tracks.append({
                        "name": name.strip(),
                        "artist": artist.strip(),
                        "played_at": datetime.utcnow().isoformat()  # MCP doesn't return timestamp
                    })
            except Exception as e:
                print(f"Error parsing line: {line} - {e}")
                continue
    
    return tracks

def parse_top_tracks(output):
    """Parse top tracks output from MCP."""
    tracks = []
    lines = output.strip().split('\n')
    
    for line in lines:
        # Format: "1. Song Name - Artist"
        if line.strip() and line[0].isdigit():
            try:
                parts = line.split('. ', 1)
                if len(parts) < 2:
                    continue
                
                track_info = parts[1]
                if ' - ' in track_info:
                    name, artist = track_info.split(' - ', 1)
                    tracks.append({
                        "name": name.strip(),
                        "artist": artist.strip()
                    })
            except Exception as e:
                print(f"Error parsing line: {line} - {e}")
                continue
    
    return tracks

def sync_recently_played(existing_items, existing_signals):
    """Sync recently played tracks via MCP."""
    new_signals = []
    new_items = {}
    
    print("Fetching recently played tracks...")
    output = call_mcp_tool("get_recently_played", {"limit": 50})
    
    if not output:
        print("Failed to fetch recently played tracks")
        return new_signals, new_items
    
    tracks = parse_recently_played(output)
    print(f"Found {len(tracks)} recently played tracks")
    
    now = datetime.utcnow().isoformat()
    
    for track in tracks:
        # Create item ID from name and artist
        item_id = f"spotify-track-{track['name'].lower().replace(' ', '-')}-{track['artist'].lower().replace(' ', '-')}"
        
        # Skip if already have this item
        if item_id in existing_items:
            continue
        
        # Create item
        item_data = {
            "item_id": item_id,
            "name": track['name'],
            "domain": "music",
            "source": "spotify",
            "metadata": {
                "artist": track['artist'],
                "played_at": track['played_at']
            },
            "enriched": True,
            "enriched_at": now,
            "first_seen": track['played_at'],
            "last_seen": track['played_at'],
            "signal_count": 1,
            "visit_dates": [track['played_at']]
        }
        new_items[item_id] = item_data
        
        # Create signal
        signal_id = f"spotify-play-{item_id}-{track['played_at']}"
        signal_data = {
            "signal_id": signal_id,
            "item_id": item_id,
            "domain": "music",
            "source": "play",
            "strength": 0.60,
            "timestamp": track['played_at'],
            "metadata": {
                "played_at": track['played_at'],
                "mcp_source": "spotify"
            }
        }
        new_signals.append(signal_data)
    
    return new_signals, new_items

def sync_top_tracks(existing_items, existing_signals):
    """Sync top tracks via MCP."""
    new_signals = []
    new_items = {}
    
    print("Fetching top tracks...")
    output = call_mcp_tool("get_top_items", {"type": "tracks", "limit": 20, "time_range": "short_term"})
    
    if not output:
        print("Failed to fetch top tracks")
        return new_signals, new_items
    
    tracks = parse_top_tracks(output)
    print(f"Found {len(tracks)} top tracks")
    
    now = datetime.utcnow().isoformat()
    
    for track in tracks:
        # Create item ID from name and artist
        item_id = f"spotify-track-{track['name'].lower().replace(' ', '-')}-{track['artist'].lower().replace(' ', '-')}"
        
        # Skip if already have this item
        if item_id in existing_items:
            continue
        
        # Create item
        item_data = {
            "item_id": item_id,
            "name": track['name'],
            "domain": "music",
            "source": "spotify",
            "metadata": {
                "artist": track['artist'],
                "top_track": True,
                "time_range": "short_term"
            },
            "enriched": True,
            "enriched_at": now,
            "first_seen": now,
            "last_seen": now,
            "signal_count": 1,
            "visit_dates": [now]
        }
        new_items[item_id] = item_data
        
        # Create signal
        signal_id = f"spotify-top-{item_id}-{now}"
        signal_data = {
            "signal_id": signal_id,
            "item_id": item_id,
            "domain": "music",
            "source": "play",
            "strength": 0.60,
            "timestamp": now,
            "metadata": {
                "top_track": True,
                "time_range": "short_term",
                "mcp_source": "spotify"
            }
        }
        new_signals.append(signal_data)
    
    return new_signals, new_items

def check_token_validity():
    """Check if Spotify token is valid before attempting sync.
    
    If the cached token is expired and has no refresh_token, skip the run —
    Spotify's user-data endpoints require interactive browser login to
    re-authorize, which cron cannot do headlessly.
    """
    import time
    if not CHECKPOINT_FILE.parent.exists():
        CHECKPOINT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    cache_path = DATA_DIR / ".cache"
    if not cache_path.exists():
        print("No Spotify token cache found. Run: npx @darrenjaws/spotify-mcp setup")
        return False
    
    try:
        with open(cache_path) as f:
            cache = json.load(f)
        expires_at = cache.get('expires_at', 0)
        has_refresh = bool(cache.get('refresh_token'))
        now = time.time()
        
        if now > expires_at and not has_refresh:
            print(f"Spotify token expired at {datetime.fromtimestamp(expires_at).isoformat()} "
                  f"with no refresh_token. Cannot re-authorize headlessly.")
            print("Run: npx @darrenjaws/spotify-mcp setup (requires interactive browser)")
            return False
        
        if now > expires_at and has_refresh:
            print("Spotify token expired but refresh_token available — spotipy will auto-refresh")
        
        return True
    except Exception as e:
        print(f"Error checking Spotify token: {e}")
        return False


def main():
    """Main sync function."""
    print("Starting Spotify MCP sync...")
    
    # Check token validity first (skill invariant: skip if expired with no refresh)
    if not check_token_validity():
        print("Skipping Spotify sync — token not valid for headless use")
        return
    
    # Check if MCP is configured
    spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
    spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    
    if not spotify_client_id or not spotify_client_secret:
        print("Warning: SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET not set")
        print("MCP calls may fail. Attempting anyway with cached token...")
    
    # Load existing data
    existing_items = load_existing_items()
    existing_signals = load_existing_signals()
    checkpoint = load_checkpoint()
    
    # Sync recently played
    recent_signals, recent_items = sync_recently_played(existing_items, existing_signals)
    
    # Sync top tracks
    top_signals, top_items = sync_top_tracks(existing_items, existing_signals)
    
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