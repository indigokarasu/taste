#!/usr/bin/env python3
"""
Spotify Recently Played Tracker
Fetches recently played tracks from Spotify API and outputs JSON.
Requires SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, and SPOTIFY_REFRESH_TOKEN environment variables.
"""
import os
import json
import requests
from datetime import datetime, timedelta

def get_access_token():
    """Exchange refresh token for access token."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError("Missing Spotify credentials. Set SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REFRESH_TOKEN")
    
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]

def get_recently_played(access_token, limit=50):
    """Fetch recently played tracks."""
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(
        "https://api.spotify.com/v1/me/player/recently-played",
        headers=headers,
        params={"limit": limit}
    )
    response.raise_for_status()
    return response.json()

def main():
    try:
        # Get access token
        token = get_access_token()
        
        # Fetch recently played tracks
        data = get_recently_played(token)
        
        # Process tracks
        tracks = []
        for item in data.get("items", []):
            track = item.get("track", {})
            played_at = item.get("played_at")
            
            # Convert to ISO format if needed
            if played_at:
                dt = datetime.strptime(played_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                played_at = dt.isoformat() + "Z"
            
            tracks.append({
                "id": track.get("id"),
                "name": track.get("name"),
                "artist": ", ".join(artist.get("name") for artist in track.get("artists", [])),
                "album": track.get("album", {}).get("name"),
                "played_at": played_at,
                "duration_ms": track.get("duration_ms")
            })
        
        # Output JSON
        print(json.dumps(tracks, indent=2))
        
    except Exception as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        exit(1)

if __name__ == "__main__":
    main()