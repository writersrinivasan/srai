"""Calendar agent — schedule protection, event management, free-slot finding."""

from datetime import date

from srai.agent import run_agent
from srai.tools import calendar_tools, gmail_tools

SYSTEM = """You are the Calendar Agent for SRAI, a personal chief-of-staff system.
Your job is to manage the user's personal calendar: review upcoming events, protect
deep-work blocks, find free time, and create or clean up events as requested.

Today's date: {today}

Guidelines:
- Deep-work blocks should be at least 2 hours and ideally before noon.
- Protect at least one evening (finish by 6pm) per week for personal time.
- When creating events, confirm the details clearly in your final response.
- Be concise — the response will be part of a daily briefing.
"""

TOOL_DEFS = calendar_tools.TOOL_DEFS + gmail_tools.TOOL_DEFS
DISPATCHERS = [calendar_tools.dispatch, gmail_tools.dispatch]


def run(task: str) -> str:
    system = SYSTEM.format(today=str(date.today()))
    return run_agent(system, task, TOOL_DEFS, DISPATCHERS)
