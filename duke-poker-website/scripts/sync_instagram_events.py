#!/usr/bin/env python3
"""Import newly published, marked Duke Poker event posts into the site data."""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_ROOT = Path(__file__).resolve().parents[1]
EVENTS_FILE = SITE_ROOT / "instagram_events.json"
STATE_FILE = REPO_ROOT / ".github" / "instagram-sync-state.json"
IMAGE_DIR = SITE_ROOT / "static" / "images" / "instagram"
GRAPH_VERSION = os.environ.get("INSTAGRAM_GRAPH_VERSION", "v27.0")
EVENT_MARKER = "#dukepokerevent"
MAX_PAGES = 20
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def api_get(path: str, params: dict[str, str], access_token: str) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"https://graph.instagram.com/{GRAPH_VERSION}/{path}?{query}"
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        detail = ""
        try:
            body = json.loads(error.read().decode("utf-8"))
            detail = body.get("error", {}).get("message", "")
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
        message = f"Instagram API returned HTTP {error.code}"
        if detail:
            message += f": {detail}"
        raise RuntimeError(message) from None
    except (urllib.error.URLError, TimeoutError) as error:
        raise RuntimeError(f"Could not reach the Instagram API: {error.reason if isinstance(error, urllib.error.URLError) else 'request timed out'}") from None

    if not isinstance(payload, dict):
        raise RuntimeError("Instagram API returned an unexpected response.")
    if "error" in payload:
        raise RuntimeError(f"Instagram API error: {payload['error'].get('message', 'unknown error')}")
    return payload


def load_state() -> dict:
    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Sync state is invalid JSON: {error}") from None
    return state if isinstance(state, dict) else {}


def fetch_new_media(user_id: str, access_token: str, state: dict) -> tuple[list[dict], dict]:
    params = {
        "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp",
        "limit": "100",
    }
    last_id = state.get("media_id")
    last_timestamp = state.get("timestamp", "")
    new_media: list[dict] = []
    newest: dict | None = None
    cursor = None

    reached_checkpoint = False
    for _ in range(MAX_PAGES):
        if cursor:
            params["after"] = cursor
        payload = api_get(f"{user_id}/media", params, access_token)
        batch = payload.get("data", [])
        if not isinstance(batch, list):
            raise RuntimeError("Instagram API returned an invalid media list.")
        if batch and newest is None:
            newest = batch[0]

        if not state:
            break

        page_reached_checkpoint = False
        for media in batch:
            if not isinstance(media, dict):
                continue
            if media.get("id") == last_id or (last_timestamp and media.get("timestamp", "") < last_timestamp):
                reached_checkpoint = True
                page_reached_checkpoint = True
                break
            new_media.append(media)

        if page_reached_checkpoint:
            break
        cursors = payload.get("paging", {}).get("cursors", {})
        cursor = cursors.get("after") if isinstance(cursors, dict) else None
        if not cursor or not batch:
            break

    if state and not reached_checkpoint and cursor:
        raise RuntimeError("More than 2,000 posts were found since the last checkpoint; refusing to skip event posts.")
    return new_media, newest or {}


def parse_event(caption: str, media: dict) -> dict | None:
    if EVENT_MARKER not in caption.lower():
        return None

    fields: dict[str, str] = {}
    description_lines: list[str] = []
    for line in caption.splitlines():
        cleaned = line.strip()
        if not cleaned or EVENT_MARKER in cleaned.lower():
            continue
        match = re.match(r"^(title|date|time|location|description|rsvp)\s*:\s*(.*)$", cleaned, re.I)
        if match:
            fields[match.group(1).lower()] = match.group(2).strip()
        else:
            description_lines.append(cleaned)

    title = fields.get("title", "")
    date = fields.get("date", "")
    description = fields.get("description", " ".join(description_lines)).strip()
    if not title or not date:
        raise RuntimeError(
            f"Post {media.get('id', '(unknown)')} has #DukePokerEvent but is missing a Title: or Date: line."
        )

    date_display = date
    if fields.get("time"):
        date_display += f" · {fields['time']}"
    if fields.get("location"):
        date_display += f" · {fields['location']}"
    if not description:
        description = "Event details announced by Duke Poker Club."

    rsvp = fields.get("rsvp", "")
    if rsvp:
        parsed_rsvp = urllib.parse.urlparse(rsvp)
        if parsed_rsvp.scheme not in {"http", "https"} or not parsed_rsvp.netloc:
            rsvp = ""

    return {
        "instagram_id": str(media.get("id", "")),
        "title": html.unescape(title),
        "date": html.unescape(date_display),
        "description": html.unescape(description),
        "image": "",
        "link": rsvp,
        "timestamp": media.get("timestamp", ""),
        "source_url": media.get("permalink", ""),
        "media_type": media.get("media_type", ""),
    }


def download_event_image(media: dict, media_id: str) -> str:
    media_type = media.get("media_type", "")
    image_url = media.get("media_url") if media_type == "IMAGE" else media.get("thumbnail_url")
    if not image_url:
        return ""

    parsed = urllib.parse.urlparse(image_url)
    hostname = (parsed.hostname or "").lower()
    allowed_host = (
        hostname == "cdninstagram.com"
        or hostname.endswith(".cdninstagram.com")
        or hostname == "fbcdn.net"
        or hostname.endswith(".fbcdn.net")
    )
    if parsed.scheme != "https" or not allowed_host:
        print(f"Skipping image for post {media_id}: unexpected media host.")
        return ""

    request = urllib.request.Request(image_url, headers={"User-Agent": "DukePokerEventSync/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content_type = response.headers.get_content_type()
            extensions = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/webp": ".webp",
                "image/gif": ".gif",
            }
            if content_type not in extensions:
                return ""
            content = response.read(MAX_IMAGE_BYTES + 1)
    except (urllib.error.URLError, TimeoutError):
        print(f"Image download failed for post {media_id}; publishing the event without a photo.")
        return ""

    if len(content) > MAX_IMAGE_BYTES:
        print(f"Skipping image for post {media_id}: larger than 8 MB.")
        return ""

    extension = extensions[content_type]
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "", media_id)
    if not safe_id:
        return ""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{safe_id}{extension}"
    (IMAGE_DIR / filename).write_bytes(content)
    return f"images/instagram/{filename}"


def read_events() -> list[dict]:
    try:
        events = json.loads(EVENTS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Event data is invalid JSON: {error}") from None
    if not isinstance(events, list):
        raise RuntimeError("Event data must be a JSON array.")
    return [event for event in events if isinstance(event, dict)]


def write_action_output(state_updated: bool, event_published: bool, latest_title: str = "") -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as output:
        output.write(f"state_updated={'true' if state_updated else 'false'}\n")
        output.write(f"event_published={'true' if event_published else 'false'}\n")
        output.write(f"latest_title={latest_title.replace(chr(10), ' ')}\n")


def main() -> int:
    user_id = os.environ.get("INSTAGRAM_USER_ID", "").strip()
    access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
    if not user_id or not access_token:
        raise RuntimeError("Set the INSTAGRAM_USER_ID and INSTAGRAM_ACCESS_TOKEN repository secrets first.")

    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = load_state()
    media, newest = fetch_new_media(user_id, access_token, state)
    if not state:
        if newest.get("id"):
            state = {"media_id": str(newest["id"]), "timestamp": newest.get("timestamp", "")}
            print("Initial checkpoint saved; existing Instagram posts were not imported.")
        else:
            state = {"initialized": True, "media_id": None, "timestamp": ""}
            print("No Instagram posts found; there is nothing to sync yet.")
        STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        write_action_output(True, False)
        return 0

    events = read_events()
    existing = {str(event.get("instagram_id", "")) for event in events}
    additions: list[dict] = []
    for item in reversed(media):
        caption = item.get("caption", "")
        if not isinstance(caption, str):
            continue
        event = parse_event(caption, item)
        if event is None or event["instagram_id"] in existing:
            continue
        event["image"] = download_event_image(item, event["instagram_id"])
        additions.append(event)
        existing.add(event["instagram_id"])

    merged = list(reversed(additions)) + events
    if additions:
        EVENTS_FILE.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    next_state = {"media_id": str(newest["id"]), "timestamp": newest.get("timestamp", "")} if newest.get("id") else state
    state_updated = next_state != state
    if state_updated:
        STATE_FILE.write_text(json.dumps(next_state, indent=2) + "\n", encoding="utf-8")

    title = additions[-1]["title"] if additions else ""
    if additions:
        print(f"Imported {len(additions)} Instagram event post(s); newest is {title!r}.")
    else:
        print("No new marked event posts found.")
    write_action_output(state_updated, bool(additions), title)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as error:
        print(f"Instagram event sync failed: {error}", file=sys.stderr)
        sys.exit(1)
