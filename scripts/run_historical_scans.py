#!/usr/bin/env python3
"""
Script to run historical email and calendar scans with the operator's credentials.
"""
import sys
if __name__ == "__main__" and ("--help" in sys.argv or "-h" in sys.argv):
    print('Run historical email/calendar backfill scans for taste signals.')
    print("Usage: run_historical_scans.py [options]")
    print("Run with no arguments for default behavior; see SKILL.md for flags.")
    print("  -h, --help  Show this help message")
    sys.exit(0)

import os
import sys
from pathlib import Path

AGENT_ROOT = Path(os.environ.get("AGENT_ROOT", Path.home() / ".hermes"))

sys.path.insert(0, str(AGENT_ROOT / 'scripts'))

_HELP_ARGS = {"--help", "-h"}
if set(sys.argv[1:]) & _HELP_ARGS:
    print((__doc__ or "").strip() or "Usage: python3 run_historical_scans.py")
    sys.exit(0)

def _auth():
    """Import the shared google_auth helpers lazily (exit 3 if unavailable).

    Module-scope import would break `--help` on machines without the Hermes tree.
    """
    try:
        from google_auth import get_gmail_service, get_calendar_service
    except Exception as e:  # environment dependent
        print("ERROR: google_auth helper unavailable (%s)." % e, file=sys.stderr)
        print("AGENT_ROOT must point at a tree containing scripts/google_auth.py.", file=sys.stderr)
        sys.exit(3)
    return get_gmail_service, get_calendar_service


def run_historical_scans():
    """Run the historical email and calendar scans with the operator's credentials."""
    get_gmail_service, get_calendar_service = _auth()
    gmail_service = get_gmail_service(account=os.environ.get("OCAS_OPERATOR_EMAIL", "operator@example.com"))
    calendar_service = get_calendar_service(account=os.environ.get("OCAS_OPERATOR_EMAIL", "operator@example.com"))

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