from __future__ import annotations

"""Google Calendar tool functions + Anthropic tool definitions."""

from datetime import datetime, timedelta
from typing import Any

import pytz

from srai.config import CALENDAR_ID, TIMEZONE
from srai.google_auth import calendar_service


def _svc():
    return calendar_service()


def _tz() -> pytz.BaseTzInfo:
    return pytz.timezone(TIMEZONE)


def _now_iso() -> str:
    return datetime.now(_tz()).isoformat()


# ── Tool functions ──────────────────────────────────────────────────────────

def list_events(time_min: str | None = None, time_max: str | None = None, max_results: int = 20) -> list[dict]:
    tz = _tz()
    t_min = time_min or datetime.now(tz).isoformat()
    t_max = time_max or (datetime.now(tz) + timedelta(days=7)).isoformat()
    result = _svc().events().list(
        calendarId=CALENDAR_ID,
        timeMin=t_min,
        timeMax=t_max,
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
    ).execute()
    events = []
    for e in result.get("items", []):
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        end = e["end"].get("dateTime", e["end"].get("date", ""))
        events.append({"id": e["id"], "summary": e.get("summary", "(no title)"), "start": start, "end": end, "description": e.get("description", "")})
    return events


def create_event(summary: str, start: str, end: str, description: str = "", location: str = "") -> dict:
    body: dict[str, Any] = {
        "summary": summary,
        "start": {"dateTime": start, "timeZone": TIMEZONE},
        "end": {"dateTime": end, "timeZone": TIMEZONE},
    }
    if description:
        body["description"] = description
    if location:
        body["location"] = location
    created = _svc().events().insert(calendarId=CALENDAR_ID, body=body).execute()
    return {"id": created["id"], "summary": created["summary"], "start": created["start"], "htmlLink": created.get("htmlLink", "")}


def delete_event(event_id: str) -> dict:
    _svc().events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
    return {"deleted": event_id}


def find_free_slots(date_str: str, duration_minutes: int = 60) -> list[dict]:
    """Return free time slots on a given date (YYYY-MM-DD)."""
    tz = _tz()
    day = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)
    t_min = day.replace(hour=8, minute=0, second=0).isoformat()
    t_max = day.replace(hour=21, minute=0, second=0).isoformat()
    events = list_events(t_min, t_max, max_results=50)

    busy: list[tuple[datetime, datetime]] = []
    for e in events:
        try:
            s = datetime.fromisoformat(e["start"]).astimezone(tz)
            en = datetime.fromisoformat(e["end"]).astimezone(tz)
            busy.append((s, en))
        except Exception:
            continue
    busy.sort()

    slots: list[dict] = []
    cursor = day.replace(hour=8, minute=0, second=0)
    end_of_day = day.replace(hour=21, minute=0, second=0)
    delta = timedelta(minutes=duration_minutes)
    for b_start, b_end in busy:
        while cursor + delta <= b_start:
            slots.append({"start": cursor.isoformat(), "end": (cursor + delta).isoformat()})
            cursor += delta
        cursor = max(cursor, b_end)
    while cursor + delta <= end_of_day:
        slots.append({"start": cursor.isoformat(), "end": (cursor + delta).isoformat()})
        cursor += delta
    return slots[:5]


# ── Anthropic tool definitions ──────────────────────────────────────────────

TOOL_DEFS = [
    {
        "name": "calendar_list_events",
        "description": "List personal calendar events within a time window.",
        "input_schema": {
            "type": "object",
            "properties": {
                "time_min": {"type": "string", "description": "ISO 8601 start datetime. Defaults to now."},
                "time_max": {"type": "string", "description": "ISO 8601 end datetime. Defaults to +7 days."},
                "max_results": {"type": "integer", "description": "Max events to return (default 20)."},
            },
        },
    },
    {
        "name": "calendar_create_event",
        "description": "Create a new event on the personal calendar.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Event title."},
                "start": {"type": "string", "description": "ISO 8601 start datetime."},
                "end": {"type": "string", "description": "ISO 8601 end datetime."},
                "description": {"type": "string"},
                "location": {"type": "string"},
            },
            "required": ["summary", "start", "end"],
        },
    },
    {
        "name": "calendar_delete_event",
        "description": "Delete a calendar event by ID.",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": ["event_id"],
        },
    },
    {
        "name": "calendar_find_free_slots",
        "description": "Find free time slots on a given date.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date_str": {"type": "string", "description": "Date as YYYY-MM-DD."},
                "duration_minutes": {"type": "integer", "description": "Slot length in minutes (default 60)."},
            },
            "required": ["date_str"],
        },
    },
]


def dispatch(name: str, args: dict) -> Any:
    if name == "calendar_list_events":
        return list_events(**args)
    if name == "calendar_create_event":
        return create_event(**args)
    if name == "calendar_delete_event":
        return delete_event(**args)
    if name == "calendar_find_free_slots":
        return find_free_slots(**args)
    raise ValueError(f"Unknown calendar tool: {name}")
