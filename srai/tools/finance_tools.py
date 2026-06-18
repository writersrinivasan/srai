from __future__ import annotations

"""Finance tool functions + Anthropic tool definitions.

Bill detection: scans Gmail for payment confirmation emails.
Manual bill registry: managed via state.json.
"""

from typing import Any

import srai.memory as mem
from srai.tools.gmail_tools import search_emails


# ── Tool functions ──────────────────────────────────────────────────────────

def get_bills() -> list[dict]:
    return mem.get_bills()


def add_bill(name: str, amount: float, due_day: int, category: str = "other", recurring: bool = True) -> dict:
    return mem.add_bill(name, amount, due_day, category, recurring)


def log_payment(bill_name: str, amount: float, notes: str = "") -> dict:
    return mem.log_payment(bill_name, amount, notes)


def bills_status() -> list[dict]:
    """Return all bills with paid/overdue status for the current month."""
    return mem.bills_due_this_month()


def payment_history(month: str | None = None) -> list[dict]:
    """Get payment history. month format: YYYY-MM (defaults to current month)."""
    from datetime import date
    m = month or date.today().strftime("%Y-%m")
    return mem.get_payments(month=m)


def scan_gmail_for_payments(keywords: str = "payment confirmation receipt paid") -> list[dict]:
    """Search Gmail for recent payment confirmations."""
    query = f"({keywords}) newer_than:30d"
    return search_emails(query, max_results=15)


def finance_summary() -> dict:
    bills = bills_status()
    paid = [b for b in bills if b["paid"]]
    overdue = [b for b in bills if b["overdue"]]
    upcoming = [b for b in bills if not b["paid"] and not b["overdue"]]
    return {
        "total_bills": len(bills),
        "paid": [b["name"] for b in paid],
        "overdue": [{"name": b["name"], "amount": b["amount"], "due_day": b["due_day"]} for b in overdue],
        "upcoming": [{"name": b["name"], "amount": b["amount"], "due_day": b["due_day"]} for b in upcoming],
    }


# ── Anthropic tool definitions ──────────────────────────────────────────────

TOOL_DEFS = [
    {
        "name": "finance_get_bills",
        "description": "Get the list of tracked recurring bills.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "finance_add_bill",
        "description": "Add a new recurring bill to track.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Bill name (e.g. 'Rent', 'PG&E', 'Internet')."},
                "amount": {"type": "number", "description": "Amount in USD."},
                "due_day": {"type": "integer", "description": "Day of month the bill is due (1-31)."},
                "category": {"type": "string", "description": "Category: housing, utilities, subscriptions, insurance, other."},
                "recurring": {"type": "boolean", "description": "Whether this repeats monthly (default true)."},
            },
            "required": ["name", "amount", "due_day"],
        },
    },
    {
        "name": "finance_log_payment",
        "description": "Record that a bill has been paid.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bill_name": {"type": "string", "description": "Name of the bill (must match registry)."},
                "amount": {"type": "number", "description": "Amount paid."},
                "notes": {"type": "string"},
            },
            "required": ["bill_name", "amount"],
        },
    },
    {
        "name": "finance_bills_status",
        "description": "Get current month's bill status — which are paid, overdue, or upcoming.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "finance_payment_history",
        "description": "Get payment history for a given month.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "Month as YYYY-MM. Defaults to current month."},
            },
        },
    },
    {
        "name": "finance_scan_gmail",
        "description": "Scan Gmail for recent payment confirmation emails to detect bills paid.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keywords": {"type": "string", "description": "Search keywords (default: 'payment confirmation receipt paid')."},
            },
        },
    },
    {
        "name": "finance_summary",
        "description": "High-level finance summary: paid, overdue, and upcoming bills for the month.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def dispatch(name: str, args: dict) -> Any:
    if name == "finance_get_bills":
        return get_bills()
    if name == "finance_add_bill":
        return add_bill(**args)
    if name == "finance_log_payment":
        return log_payment(**args)
    if name == "finance_bills_status":
        return bills_status()
    if name == "finance_payment_history":
        return payment_history(**args)
    if name == "finance_scan_gmail":
        return scan_gmail_for_payments(**args)
    if name == "finance_summary":
        return finance_summary()
    raise ValueError(f"Unknown finance tool: {name}")
