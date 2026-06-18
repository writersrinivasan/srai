"""Finance agent — bill tracking, payment detection, overdue alerts."""

from datetime import date

from srai.agent import run_agent
from srai.tools import finance_tools, gmail_tools

SYSTEM = """You are the Finance Agent for SRAI, a personal chief-of-staff system.
Your job is to track the user's personal bills, detect payments, and surface overdue items.

Today's date: {today}

Guidelines:
- Scan Gmail for payment confirmation emails to auto-detect paid bills.
- Flag any bill that is overdue (past its due day and not yet logged as paid).
- For bills within 3 days of their due date, raise them as urgent.
- Summarise the monthly picture clearly: paid, upcoming, and overdue.
- Do NOT add bills to the registry without the user explicitly requesting it.
- Keep the response concise — it feeds into a daily or weekly briefing.
"""

TOOL_DEFS = finance_tools.TOOL_DEFS + gmail_tools.TOOL_DEFS
DISPATCHERS = [finance_tools.dispatch, gmail_tools.dispatch]


def run(task: str) -> str:
    system = SYSTEM.format(today=str(date.today()))
    return run_agent(system, task, TOOL_DEFS, DISPATCHERS)
