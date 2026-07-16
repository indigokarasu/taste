#!/usr/bin/env python3
"""
Script to run historical email and calendar scans with Jared's credentials.
"""

import os
import sys
from pathlib import Path

AGENT_ROOT = Path(os.environ.get("AGENT_ROOT", Path.home() / ".hermes"))

sys.path.insert(0, str(AGENT_ROOT / 'scripts'))

_HELP_ARGS = {"--help", "-h"}
if set(sys.argv[1:]) & _HELP_ARGS:
    print((__doc__ or "").strip() or "Usage: python3 run_historical_scans.py")
    sys.exit(0)

from google_auth import get_gmail_service, get_calendar_service



def run_historical_scans():
    """Run the historical email and calendar scans with Jared's credentials."""
    gmail_service = get_gmail_service(account='jared.zimmerman@gmail.com')
    calendar_service = get_calendar_service(account='jared.zimmerman@gmail.com')

    # Run the historical email scan
    print("Running historical email scan...")
    # TODO: Implement the actual email scan logic

    # Run the historical calendar scan
    print("Running historical calendar scan...")
    calendars = calendar_service.calendarList().list().execute()
    print(f"Found {len(calendars.get('items', []))} calendars.")

    # TODO: Implement the actual calendar scan logic


if __name__ == "__main__":
    run_historical_scans()
