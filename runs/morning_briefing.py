#!/usr/bin/env python3
"""
Morning briefing — runs at ~7 AM via cron.
Checks calendar (today + tomorrow), health status, and urgent finance items.
Saves output to data/logs/ and optionally emails it to you.
"""

import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# allow running from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from srai.config import LOGS_DIR, PERSONAL_EMAIL, TIMEZONE
from srai.orchestrator import run_briefing

import agents.calendar_agent as cal
import agents.health_agent as health
import agents.finance_agent as finance

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("morning_briefing")

import pytz


def _window() -> tuple[str, str]:
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    end = (now + timedelta(days=2)).replace(hour=23, minute=59)
    return now.isoformat(), end.isoformat()


def main() -> None:
    today = date.today()
    t_min, t_max = _window()

    tasks = {
        "calendar": (
            cal.run,
            f"Review my calendar from now until {t_max}. "
            "Highlight today's commitments, flag any conflicts, and check if I have a deep-work block today. "
            "If not, find a free 2-hour slot and note it.",
        ),
        "health": (
            health.run,
            "Check my gym history and habit streaks. "
            "Tell me if I'm on track this week (goal: 4 sessions). "
            "Check the calendar for any gym sessions scheduled today.",
        ),
        "finance": (
            finance.run,
            "Scan Gmail for recent payment confirmations. "
            "Check if any bills are overdue or due within the next 3 days. "
            "Give me a quick status.",
        ),
    }

    briefing = run_briefing(tasks, briefing_style="morning")

    # Save to log file
    log_file = LOGS_DIR / f"morning_{today.strftime('%Y%m%d')}.txt"
    log_file.write_text(briefing)
    log.info("Briefing saved to %s", log_file)

    # Print to stdout (captured by cron or terminal)
    print("\n" + "=" * 60)
    print(f"SRAI MORNING BRIEFING — {today.strftime('%A, %B %-d, %Y')}")
    print("=" * 60)
    print(briefing)
    print("=" * 60 + "\n")

    # Email the briefing if PERSONAL_EMAIL is set
    if PERSONAL_EMAIL:
        try:
            from srai.tools.gmail_tools import send_email
            send_email(
                to=PERSONAL_EMAIL,
                subject=f"SRAI Morning Briefing — {today.strftime('%a %b %-d')}",
                body=briefing,
            )
            log.info("Briefing emailed to %s", PERSONAL_EMAIL)
        except Exception as e:
            log.warning("Could not email briefing: %s", e)


if __name__ == "__main__":
    main()
