# Historical Scan Authentication

## Issue
The historical email and calendar scans (`taste.historical.email` and `taste.historical.calendar`) failed due to incorrect OAuth token usage. The script was authenticating as the agent account (`mx.indigo.karasu@gmail.com`) instead of Jared's account (`jared.zimmerman@gmail.com`). This caused the scans to miss 10 years of Gmail and calendar history.

## Root Cause
- The script was using the agent's credentials (`jared.zimmerman@gmail.com.json`) instead of Jared's credentials (`/root/.hermes/jared.zimmerman@gmail.com.json`).
- The historical scans were not explicitly configured to use Jared's credentials.

## Fix
Always use Jared's credentials (`/root/.hermes/jared.zimmerman@gmail.com.json`) for historical scans. The credentials file must be loaded and used explicitly:

```python
# Load Jared's credentials
with open("/root/.hermes/jared.zimmerman@gmail.com.json", "r") as f:
    jared_credentials = json.load(f)

# Parse the expiry string into a datetime object
try:
    expiry_str = jared_credentials['expiry']
    expiry_str_clean = expiry_str.replace(".295559", "").replace("+00:00", "")
    expiry = datetime.strptime(expiry_str_clean, "%Y-%m-%dT%H:%M:%S")
    jared_credentials['expiry'] = expiry
    
    # Build the Calendar service
    service = build('calendar', 'v3', credentials=Credentials(**jared_credentials))
    
    # List Jared's calendars
    calendars = service.calendarList().list().execute()
    
    # List Jared's Gmail inbox
    gmail_service = build('gmail', 'v1', credentials=Credentials(**jared_credentials))
    jared_email = 'jared.zimmerman@gmail.com'
    jared_results = gmail_service.users().messages().list(userId=jared_email).execute()
    
except Exception as e:
    print(f"Error parsing expiry or building service: {e}")
```

## Verification
After applying the fix, verify the following:
1. The historical scans (`taste.historical.email` and `taste.historical.calendar`) run successfully.
2. The data is stored in `/root/.hermes/commons/data/ocas-taste/`.
3. The signals and items are enriched and ready for recommendation generation.