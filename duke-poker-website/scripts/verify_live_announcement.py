#!/usr/bin/env python3
"""Wait for a newly synced announcement to appear on the live website."""

from __future__ import annotations

import html
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


SITE_ROOT = Path(__file__).resolve().parents[1]
EVENTS_FILE = SITE_ROOT / "instagram_events.json"
URL = os.environ.get("DUKE_POKER_ANNOUNCEMENTS_URL", "https://dukepoker.org/announcements")
TIMEOUT_SECONDS = int(os.environ.get("DEPLOY_VERIFY_TIMEOUT_SECONDS", "900"))


def main() -> int:
    events = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
    if not events:
        raise RuntimeError("There is no synced Instagram event to verify.")
    expected = str(events[0].get("title", "")).strip()
    if not expected:
        raise RuntimeError("The newest Instagram event has no title.")

    deadline = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(URL, headers={"User-Agent": "DukePokerDeployCheck/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                page = response.read().decode("utf-8", errors="replace")
            if html.unescape(expected) in html.unescape(page):
                print(f"Verified {expected!r} is visible at {URL}.")
                return 0
        except (urllib.error.URLError, TimeoutError) as error:
            print(f"Site not ready yet: {error}")
        time.sleep(20)

    raise RuntimeError(f"Timed out waiting for {expected!r} to appear at {URL}.")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError, json.JSONDecodeError) as error:
        print(f"Live-site verification failed: {error}", file=sys.stderr)
        sys.exit(1)
