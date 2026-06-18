from __future__ import annotations

"""
Persistent JSON state store for SRAI.

Schema:
  health:
    habits: { name -> { streak, last_logged } }
    gym_sessions: [ { date, notes } ]
  finance:
    bills: [ { name, amount, due_day, category, recurring } ]
    payments: [ { bill, date, amount, notes } ]
  notes: [ { date, text } ]
"""

import json
from datetime import date, datetime
from typing import Any

from srai.config import STATE_FILE

_DEFAULTS: dict[str, Any] = {
    "health": {
        "habits": {},
        "gym_sessions": [],
    },
    "finance": {
        "bills": [],
        "payments": [],
    },
    "notes": [],
}


def _load() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            data = json.load(f)
        # merge missing top-level keys from defaults
        for k, v in _DEFAULTS.items():
            if k not in data:
                data[k] = v
        return data
    return json.loads(json.dumps(_DEFAULTS))


def _save(data: dict) -> None:
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


# ── Health ─────────────────────────────────────────────────────────────────

def log_gym_session(notes: str = "") -> dict:
    data = _load()
    entry = {"date": str(date.today()), "notes": notes}
    data["health"]["gym_sessions"].append(entry)
    _save(data)
    return entry


def get_gym_sessions(limit: int = 10) -> list[dict]:
    return _load()["health"]["gym_sessions"][-limit:]


def log_habit(name: str) -> dict:
    data = _load()
    today = str(date.today())
    habits = data["health"]["habits"]
    if name not in habits:
        habits[name] = {"streak": 0, "last_logged": None}
    h = habits[name]
    if h["last_logged"] == today:
        return {"name": name, "streak": h["streak"], "already_logged": True}
    yesterday = str(date.fromordinal(date.today().toordinal() - 1))
    h["streak"] = (h["streak"] + 1) if h["last_logged"] == yesterday else 1
    h["last_logged"] = today
    _save(data)
    return {"name": name, "streak": h["streak"], "already_logged": False}


def get_habits() -> dict:
    return _load()["health"]["habits"]


# ── Finance ────────────────────────────────────────────────────────────────

def add_bill(name: str, amount: float, due_day: int, category: str = "other", recurring: bool = True) -> dict:
    data = _load()
    bill = {"name": name, "amount": amount, "due_day": due_day, "category": category, "recurring": recurring}
    data["finance"]["bills"].append(bill)
    _save(data)
    return bill


def get_bills() -> list[dict]:
    return _load()["finance"]["bills"]


def log_payment(bill_name: str, amount: float, notes: str = "") -> dict:
    data = _load()
    entry = {"bill": bill_name, "date": str(date.today()), "amount": amount, "notes": notes}
    data["finance"]["payments"].append(entry)
    _save(data)
    return entry


def get_payments(month: str | None = None) -> list[dict]:
    payments = _load()["finance"]["payments"]
    if month:
        payments = [p for p in payments if p["date"].startswith(month)]
    return payments


def bills_due_this_month() -> list[dict]:
    """Return bills with their payment status for the current month."""
    today = date.today()
    month_str = today.strftime("%Y-%m")
    paid_names = {p["bill"] for p in get_payments(month=month_str)}
    result = []
    for b in get_bills():
        result.append({
            **b,
            "paid": b["name"] in paid_names,
            "overdue": b["due_day"] < today.day and b["name"] not in paid_names,
        })
    return result


# ── Notes ──────────────────────────────────────────────────────────────────

def add_note(text: str) -> dict:
    data = _load()
    entry = {"date": datetime.now().isoformat(timespec="seconds"), "text": text}
    data["notes"].append(entry)
    _save(data)
    return entry


def get_notes(limit: int = 10) -> list[dict]:
    return _load()["notes"][-limit:]
