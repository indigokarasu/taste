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

```python
from pathlib import Path
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

token_paths = [
    Path.home() / ".hermes" / "google_token.json",           # Primary (user)
    Path.home() / ".hermes-indigo" / "google_token.json",    # Agent (calendar fallback only)
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

## Spotify OAuth (Spotipy)

`hermes mcp call` does not exist — the Hermes MCP CLI only supports `add`,
`remove`, `list`, `serve`, `test`, and `configure`. For programmatic Spotify
access from cron scripts, use Spotipy directly with a cached OAuth token:

```python
import spotipy
from spotipy.oauth2 import SpotifyOAuth

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
