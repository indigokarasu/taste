# API authentication patterns

<!-- TODO: migrate OAuth to ocas-auth skill -->

This document holds service-specific OAuth and API-auth code that taste needs
for Gmail, Google Calendar, and Spotify access. These patterns materially
affect correctness, which is why they live here as Python rather than prose.
Long-term this content belongs in the shared `ocas-auth` skill; taste holds it
until that skill lands.

## Gmail API credential loading (multi-profile)

`himalaya` is not installed in the target environment and cannot be installed
(no cargo/Rust toolchain, PEP 668 blocks pip). Email scanning must use the
Gmail API directly via `google.oauth2.credentials.Credentials`.

Key detail: the token file uses key `token`, not `access_token`, for the
OAuth access token. Pass `token=token_data.get('token')` when building
`Credentials`. The `gmail.readonly` scope is sufficient for scanning.

Tokens can live under either the user profile or the agent profile. Never
use the agent profile for email scanning — it has no consumption emails.
Always try the user token first and fall back to the agent token only for
calendar if the primary is missing.

### Token file locations

This system has multiple Google OAuth token files from different profiles.
Check ALL of them before concluding auth is unavailable — they may have
different client IDs and refresh states:

```python
token_paths = [
    Path.home() / ".hermes" / "jared_google_credentials.json",   # Jared Zimmerman (user)

    Path.home() / ".hermes" / "indigo_google_credentials.json",  # Indigo Karasu (agent)

]
```

The credentials file at `~/.hermes/*_google_credentials.json` may lack an `expiry`
field (so `creds.expired` returns `False` even when the token is actually
dead). In this case the refresh only fails when an actual API call is made.
Always test with a real API call (`gmail.users().getProfile().execute()`)
or a direct HTTP refresh to confirm the token works.

### Revocation detection

When a refresh fails with `invalid_grant: Token has been expired or revoked.`,
the token is definitively dead — no retry will help. Causes include:
- Password change on the Google account
- Manual revocation in myaccount.google.com → Security → Third-party apps
- 6+ months of inactivity with no token refresh

To confirm: try a raw HTTP POST to confirm the library isn't mangling the request:
```python
import requests
resp = requests.post("https://oauth2.googleapis.com/token", data={
    "client_id": token_data["client_id"],
    "client_secret": token_data["client_secret"],
    "refresh_token": token_data["refresh_token"],
    "grant_type": "refresh_token",
})
# Both library and HTTP will return 400 {"error": "invalid_grant"}
```

### Recovery flow

When all tokens are revoked, the user must re-authorize. Generate the OAuth
URL using the google-workspace setup script (NOT by manually constructing
the URL — the script handles PKCE code verifier and state correctly):

```bash
cd /root/.hermes/hermes-agent
python skills/productivity/google-workspace/scripts/setup.py --auth-url
```

The user signs in with **jared.zimmerman@gmail.com** (the account with 248K
consumption emails), authorizes the scopes, copies the code from the
redirect URL, and sends it back. Exchange with:

```bash
python skills/productivity/google-workspace/scripts/setup.py --auth-code CODE
```

The token is saved to `~/.hermes/google_token.json`. Verify with:

```bash
python skills/productivity/google-workspace/scripts/setup.py --check
```

```python
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

token_paths = [
    Path.home() / ".hermes" / "indigo_google_credentials.json",  # Indigo (agent)
    Path.home() / ".hermes" / "jared_google_credentials.json",   # Jared (user)
]

creds = None
for tp in token_paths:
    if not tp.exists():
        continue
    candidate = Credentials.from_authorized_user_file(str(tp))
    if candidate.valid or (candidate.expired and candidate.refresh_token):
        try:
            candidate.refresh(Request())
            creds = candidate
            break
        except Exception:
            continue
```

If refresh raises `invalid_grant: Bad Request`, the token has been revoked
and the user must re-authorize.

### Known pitfall: Calendar API scope not in token

If `build('calendar', 'v1', credentials=creds)` raises
`googleapiclient.errors.UnknownApiNameOrVersion: name: calendar version: v1`,
the OAuth token lacks the `calendar.readonly` or `calendar.events.readonly`
scope. The `google_credentials.json` on this system currently only has
`gmail.readonly` scope. The calendar scan must be skipped gracefully:

```python
try:
    calendar = build('calendar', 'v1', credentials=creds)
except Exception:
    # Calendar scope not available — skip calendar scan
    calendar = None
```

To fix: re-authorize with `calendar.readonly` scope added to the OAuth
client's authorized scopes, then the token will include calendar access on
next interactive login.

## Spotify OAuth (Spotipy)

Spotify app credentials are loaded from environment, not hardcoded in
scripts. Set `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` in
`~/.hermes/.env`:

```
SPOTIFY_CLIENT_ID=<client_id_from_developer_dashboard>
SPOTIFY_CLIENT_SECRET=<client_secret_from_developer_dashboard>
```

`hermes mcp call` does not exist — the Hermes MCP CLI only supports `add`,
`remove`, `list`, `serve`, `test`, and `configure`. For programmatic Spotify
access from cron scripts, use Spotipy directly with a cached OAuth token:

```python
import os, spotipy
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID = os.environ["SPOTIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SPOTIFY_CLIENT_SECRET"]

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=str(CACHE_FILE),
)
token_info = sp_oauth.get_cached_token()
sp = spotipy.Spotify(auth=token_info['access_token'])

results = sp.current_user_recently_played(limit=50)
top_tracks = sp.current_user_top_tracks(limit=20, time_range='short_term')
```

### Known pitfall: Spotify token has no refresh_token

The `.cache` file at `{agent_root}/commons/data/ocas-taste/.cache` may contain
an expired `access_token` with no `refresh_token`. All four auth approaches
(Spotipy cached token, MCP JSON-RPC, Client Credentials, browser automation)
fail headlessly because Spotify's user-data endpoints require the OAuth
Authorization Code flow with interactive browser login.

Resolution: the user runs `npx @darrenjaws/spotify-mcp setup` in a
browser-accessible environment, which writes tokens to
`~/.spotify-mcp/tokens.json`. Gate the cron job on a valid-token check to
avoid repeated failed runs.
