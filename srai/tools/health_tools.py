"""Health & fitness tool functions + Anthropic tool definitions."""

from typing import Any

import srai.memory as mem


# ── Tool functions ──────────────────────────────────────────────────────────

def log_gym(notes: str = "") -> dict:
    return mem.log_gym_session(notes)


def get_gym_history(limit: int = 10) -> list[dict]:
    return mem.get_gym_sessions(limit)


def log_habit(name: str) -> dict:
    return mem.log_habit(name)


def get_habits() -> dict:
    return mem.get_habits()


def health_summary() -> dict:
    sessions = mem.get_gym_sessions(limit=30)
    habits = mem.get_habits()
    return {
        "gym_sessions_last_30": len(sessions),
        "last_gym": sessions[-1]["date"] if sessions else None,
        "habits": habits,
    }


# ── Anthropic tool definitions ──────────────────────────────────────────────

TOOL_DEFS = [
    {
        "name": "health_log_gym",
        "description": "Log a gym session for today.",
        "input_schema": {
            "type": "object",
            "properties": {
                "notes": {"type": "string", "description": "Optional workout notes."},
            },
        },
    },
    {
        "name": "health_gym_history",
        "description": "Get recent gym session history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of recent sessions (default 10)."},
            },
        },
    },
    {
        "name": "health_log_habit",
        "description": "Mark a habit as done for today and update the streak.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Habit name (e.g. 'meditation', 'reading')."},
            },
            "required": ["name"],
        },
    },
    {
        "name": "health_get_habits",
        "description": "Get all tracked habits with current streak information.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "health_summary",
        "description": "Get a high-level health summary: gym frequency, habit streaks.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def dispatch(name: str, args: dict) -> Any:
    if name == "health_log_gym":
        return log_gym(**args)
    if name == "health_gym_history":
        return get_gym_history(**args)
    if name == "health_log_habit":
        return log_habit(**args)
    if name == "health_get_habits":
        return get_habits()
    if name == "health_summary":
        return health_summary()
    raise ValueError(f"Unknown health tool: {name}")
