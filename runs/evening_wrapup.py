#!/usr/bin/env python3
"""
Evening wrap-up — runs at ~9 PM via cron.
Summarises what happened today and surfaces tomorrow's top items.
"""

import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from srai.config import LOGS_DIR, PERSONAL_EMAIL, TIMEZONE
from srai.orchestrator import run_briefing

import agents.calendar_agent as cal
import agents.health_agent as health

import pytz

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("evening_wrapup")


def _windows() -> tuple[str, str, str, str]:
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    day_start = now.replace(hour=0, minute=0, second=0)
    day_end = now.replace(hour=23, minute=59, second=59)
    tomorrow_start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0)
    tomorrow_end = (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
    return day_start.isoformat(), day_end.isoformat(), tomorrow_start.isoformat(), tomorrow_end.isoformat()


def main() -> None:
    today = date.today()
    d_start, d_end, t_start, t_end = _windows()

    tasks = {
        "calendar": (
            cal.run,
            f"List what was on my calendar today ({d_start} to {d_end}). "
            f"Then list tomorrow's events ({t_start} to {t_end}). "
            "Flag anything I might need to prep for tonight.",
        ),
        "health": (
            health.run,
            "Did I log a gym session today? Check habit completion for today. "
            "Give me a brief end-of-day health check — am I on track for the week?",
        ),
    }

    wrap = run_briefing(tasks, briefing_style="evening")

    log_file = LOGS_DIR / f"evening_{today.strftime('%Y%m%d')}.txt"
    log_file.write_text(wrap)
    log.info("Wrap-up saved to %s", log_file)

    print("\n" + "=" * 60)
    print(f"SRAI EVENING WRAP-UP — {today.strftime('%A, %B %-d, %Y')}")
    print("=" * 60)
    print(wrap)
    print("=" * 60 + "\n")

    if PERSONAL_EMAIL:
        try:
            from srai.tools.gmail_tools import send_email
            send_email(
                to=PERSONAL_EMAIL,
                subject=f"SRAI Evening Wrap-Up — {today.strftime('%a %b %-d')}",
                body=wrap,
            )
            log.info("Wrap-up emailed to %s", PERSONAL_EMAIL)
        except Exception as e:
            log.warning("Could not email wrap-up: %s", e)


if __name__ == "__main__":
    main()
