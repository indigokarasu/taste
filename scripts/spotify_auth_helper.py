#!/usr/bin/env python3
"""
Interactive Spotify OAuth authorization helper for Taste sync.
Run this script in an environment with browser access to complete
the Spotify OAuth authorization flow and save the access token.

Usage:
  python3 spotify_auth_helper.py

The script will:
1. Start a local callback server on port 8888
2. Open the Spotify authorization URL in your default browser
3. Capture the authorization code from the callback
4. Exchange the code for access and refresh tokens
5. Save the tokens to the Taste data directory
6. Optionally run the full sync immediately after authorization
"""
import json
import os
import sys
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Config
DATA_DIR = Path("/root/.hermes/commons/data/ocas-taste")
MUSIC_DIR = DATA_DIR / "music"
TOKEN_FILE = MUSIC_DIR / "spotify_token.json"
CACHE_FILE = Path.home() / ".cache-spotify-taste"

CLIENT_ID = "794b8aeff8344464a68d8430646f236a"
CLIENT_SECRET = "bc088493f2c348cca7281d75adab3129"
REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "user-read-recently-played user-top-read user-library-read"

def generate_auth_url():
    """Generate Spotify authorization URL."""
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'show_dialog': 'false'
    }
    return f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code):
    """Exchange authorization code for access token."""
    import requests
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Token exchange failed: {response.status_code}")
        print(response.text)
        return None

def refresh_access_token(refresh_token):
    """Refresh an expired access token."""
    import requests
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Token refresh failed: {response.status_code}")
        print(response.text)
        return None

def save_token(token_data):
    """Save token data to file."""
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    save_data = {
        'access_token': token_data['access_token'],
        'refresh_token': token_data.get('refresh_token', ''),
        'expires_at': time.time() + token_data.get('expires_in', 3600),
        'scope': token_data.get('scope', SCOPE)
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(save_data, f, indent=2)
    print(f"Token saved to {TOKEN_FILE}")
    return save_data

def interactive_auth():
    """Run interactive OAuth flow with browser callback."""
    auth_url = generate_auth_url()
    
    auth_code = [None]
    
    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            if 'code' in params:
                auth_code[0] = params['code'][0]
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"""
                <html><body>
                <h1>Authorization Successful!</h1>
                <p>Spotify has been authorized for Taste sync. You can close this tab.</p>
                </body></html>
                """)
            elif 'error' in params:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(f"Authorization failed: {params['error'][0]}".encode())
            else:
                self.send_response(404)
                self.end_headers()
        
        def log_message(self, format, *args):
            pass
    
    print("=" * 60)
    print("Spotify OAuth Authorization for Taste Sync")
    print("=" * 60)
    print(f"\nOpening browser for Spotify authorization...")
    print(f"\nAuth URL: {auth_url}")
    
    # Try to open browser
    import webbrowser
    webbrowser.open(auth_url)
    
    print("\nWaiting for authorization callback on port 8888...")
    print("(Press Ctrl+C to cancel)")
    
    server = HTTPServer(('localhost', 8888), CallbackHandler)
    server.timeout = 120  # 2 minute timeout
    
    try:
        server.handle_request()
    except KeyboardInterrupt:
        print("\nAuthorization cancelled.")
        return None
    
    if auth_code[0]:
        print("\nGot authorization code! Exchanging for token...")
        token_data = exchange_code_for_token(auth_code[0])
        if token_data:
            save_data = save_token(token_data)
            # Also save to spotipy cache
            cache_data = {
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token', ''),
                'expires_at': time.time() + token_data.get('expires_in', 3600),
                'scope': token_data.get('scope', SCOPE),
                'token_type': 'Bearer'
            }
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache_data, f, indent=2)
            print(f"Spotipy cache saved to {CACHE_FILE}")
            return save_data
        else:
            print("Failed to exchange code for token.")
            return None
    else:
        print("No authorization code received within timeout.")
        return None

def run_sync(access_token):
    """Run the full Spotify sync after authentication."""
    sys.path.insert(0, str(DATA_DIR / "scripts"))
    
    # Use spotipy directly with the access token
    import spotipy
    
    sp = spotipy.Spotify(auth=access_token)
    
    # Fetch recently played
    print("\nFetching recently played tracks...")
    try:
        results = sp.current_user_recently_played(limit=50)
        recent_tracks = results.get('items', [])
        print(f"Found {len(recent_tracks)} recently played tracks")
    except Exception as e:
        print(f"Error fetching recently played: {e}")
        recent_tracks = []
    
    # Fetch top tracks
    print("Fetching top tracks...")
    try:
        top_short = sp.current_user_top_tracks(limit=20, time_range='short_term')
        top_medium = sp.current_user_top_tracks(limit=20, time_range='medium_term')
        print(f"Found {len(top_short.get('items', []))} top tracks (short term)")
        print(f"Found {len(top_medium.get('items', []))} top tracks (medium term)")
    except Exception as e:
        print(f"Error fetching top tracks: {e}")
        top_short = {'items': []}
        top_medium = {'items': []}
    
    # Process and save
    now = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
    new_signals = []
    new_items = {}
    
    # Load existing data for dedup
    existing_signal_ids = set()
    existing_item_ids = set()
    
    if SIGNALS_FILE.exists():
        with open(SIGNALS_FILE) as f:
            for line in f:
                if line.strip():
                    try:
                        s = json.loads(line)
                        existing_signal_ids.add(s.get('signal_id', ''))
                    except:
                        pass
    
    if ITEMS_FILE.exists():
        with open(ITEMS_FILE) as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)
                        existing_item_ids.add(item.get('item_id', ''))
                    except:
                        pass
    
    # Process recently played
    for item in recent_tracks:
        track = item.get('track', {})
        played_at = item.get('played_at', now)
        track_id = track.get('id', '')
        artists = ', '.join([a.get('name', 'Unknown') for a in track.get('artists', [])])
        
        item_id = f"spotify-track-{track_id}" if track_id else f"spotify-track-{track.get('name', 'unknown').lower().replace(' ', '-')}"
        signal_id = f"spotify-play-{track_id}-{played_at}" if track_id else f"spotify-play-{track.get('name', 'unknown')}-{played_at}"
        
        # Create signal
        if signal_id not in existing_signal_ids:
            signal = {
                "signal_id": signal_id,
                "item_id": item_id,
                "domain": "music",
                "source": "play",
                "strength": 0.60,
                "timestamp": played_at,
                "metadata": {
                    "track_name": track.get('name', 'Unknown'),
                    "artist": artists,
                    "album": track.get('album', {}).get('name', 'Unknown'),
                    "spotify_id": track_id,
                    "played_at": played_at,
                    "mcp_source": "spotify"
                }
            }
            new_signals.append(signal)
            existing_signal_ids.add(signal_id)
        
        # Create item
        if item_id not in existing_item_ids:
            item_data = {
                "item_id": item_id,
                "name": f"{track.get('name', 'Unknown')} - {artists}",
                "domain": "music",
                "source": "spotify",
                "metadata": {
                    "track_name": track.get('name', 'Unknown'),
                    "artist": artists,
                    "album": track.get('album', {}).get('name', 'Unknown'),
                    "spotify_id": track_id,
                    "spotify_uri": track.get('uri', ''),
                    "duration_ms": track.get('duration_ms', 0),
                    "popularity": track.get('popularity', 0)
                },
                "enriched": True,
                "enriched_at": now,
                "first_seen": played_at,
                "last_seen": played_at,
                "signal_count": 1,
                "visit_dates": [played_at]
            }
            new_items[item_id] = item_data
            existing_item_ids.add(item_id)
    
    # Process top tracks
    for time_range, tracks_data in [('short_term', top_short), ('medium_term', top_medium)]:
        for track in tracks_data.get('items', []):
            track_id = track.get('id', '')
            artists = ', '.join([a.get('name', 'Unknown') for a in track.get('artists', [])])
            
            item_id = f"spotify-track-{track_id}" if track_id else f"spotify-track-{track.get('name', 'unknown').lower().replace(' ', '-')}"
            signal_id = f"spotify-top-{track_id}-{time_range}" if track_id else f"spotify-top-{track.get('name', 'unknown')}-{time_range}"
            
            if signal_id not in existing_signal_ids:
                signal = {
                    "signal_id": signal_id,
                    "item_id": item_id,
                    "domain": "music",
                    "source": "top",
                    "strength": 0.65,
                    "timestamp": now,
                    "metadata": {
                        "track_name": track.get('name', 'Unknown'),
                        "artist": artists,
                        "album": track.get('album', {}).get('name', 'Unknown'),
                        "spotify_id": track_id,
                        "top_track": True,
                        "time_range": time_range,
                        "mcp_source": "spotify"
                    }
                }
                new_signals.append(signal)
                existing_signal_ids.add(signal_id)
            
            if item_id not in existing_item_ids:
                item_data = {
                    "item_id": item_id,
                    "name": f"{track.get('name', 'Unknown')} - {artists}",
                    "domain": "music",
                    "source": "spotify",
                    "metadata": {
                        "track_name": track.get('name', 'Unknown'),
                        "artist": artists,
                        "album": track.get('album', {}).get('name', 'Unknown'),
                        "spotify_id": track_id,
                        "spotify_uri": track.get('uri', ''),
                        "duration_ms": track.get('duration_ms', 0),
                        "popularity": track.get('popularity', 0),
                        "top_track": True,
                        "time_range": time_range
                    },
                    "enriched": True,
                    "enriched_at": now,
                    "first_seen": now,
                    "last_seen": now,
                    "signal_count": 1,
                    "visit_dates": [now]
                }
                new_items[item_id] = item_data
                existing_item_ids.add(item_id)
    
    # Write signals
    if new_signals:
        with open(SIGNALS_FILE, 'a') as f:
            for signal in new_signals:
                f.write(json.dumps(signal) + '\n')
        print(f"\nWrote {len(new_signals)} new music signals")
    
    # Write items
    if new_items:
        with open(ITEMS_FILE, 'a') as f:
            for item in new_items.values():
                f.write(json.dumps(item) + '\n')
        print(f"Wrote {len(new_items)} new music items")
    
    # Update checkpoint
    checkpoint = {"last_sync": now}
    with open(MUSIC_DIR / "spotify_sync_checkpoint.json", 'w') as f:
        json.dump(checkpoint, f, indent=2)
    print(f"\nCheckpoint updated: {now}")
    
    print(f"\nSync complete! {len(new_signals)} signals, {len(new_items)} items")

def main():
    # Check for existing valid token first
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE) as f:
            tokens = json.load(f)
        if tokens.get('expires_at', 0) > time.time():
            print(f"Valid token found (expires in {int((tokens['expires_at'] - time.time()) / 60)} minutes)")
            print("Running sync with existing token...")
            run_sync(tokens['access_token'])
            return
        elif tokens.get('refresh_token'):
            print("Token expired, attempting refresh...")
            new_tokens = refresh_access_token(tokens['refresh_token'])
            if new_tokens:
                save_data = save_token(new_tokens)
                run_sync(save_data['access_token'])
                return
    
    # No valid token - run interactive auth
    result = interactive_auth()
    if result:
        print("\nAuthorization successful! Running sync...")
        run_sync(result['access_token'])
    else:
        print("\nAuthorization failed or was cancelled.")
        print("To complete authorization manually:")
        print(f"1. Visit: {generate_auth_url()}")
        print("2. After authorizing, copy the 'code' from the redirect URL")
        print(f"3. Run: python3 {__file__} --code <authorization_code>")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--code' and len(sys.argv) > 2:
        # Manual code entry mode
        code = sys.argv[2]
        print("Exchanging authorization code for token...")
        token_data = exchange_code_for_token(code)
        if token_data:
            save_data = save_token(token_data)
            print("Token saved! Running sync...")
            run_sync(save_data['access_token'])
        else:
            print("Failed to exchange code for token.")
    else:
        main()