#!/usr/bin/env python3
"""
Weekly finance sweep — runs every Sunday at ~8 AM via cron.
Scans Gmail for payment confirmations, checks bill status, flags overdue items.
"""

import logging
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from srai.config import LOGS_DIR, PERSONAL_EMAIL
from srai.orchestrator import run_briefing

import agents.finance_agent as finance

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("finance_sweep")


def main() -> None:
    today = date.today()

    tasks = {
        "finance": (
            finance.run,
            "Perform the weekly finance sweep: "
            "1. Scan Gmail for payment confirmation emails from the past 7 days and note any bills that appear paid. "
            "2. Check the bill registry for overdue items (past due date, not logged as paid). "
            "3. List bills due in the next 7 days with amounts. "
            "4. Summarise the month-to-date payment picture. "
            "Be specific about amounts and dates.",
        ),
    }

    sweep = run_briefing(tasks, briefing_style="finance")

    log_file = LOGS_DIR / f"finance_{today.strftime('%Y%m%d')}.txt"
    log_file.write_text(sweep)
    log.info("Finance sweep saved to %s", log_file)

    print("\n" + "=" * 60)
    print(f"SRAI WEEKLY FINANCE SWEEP — {today.strftime('%A, %B %-d, %Y')}")
    print("=" * 60)
    print(sweep)
    print("=" * 60 + "\n")

    if PERSONAL_EMAIL:
        try:
            from srai.tools.gmail_tools import send_email
            send_email(
                to=PERSONAL_EMAIL,
                subject=f"SRAI Finance Sweep — Week of {today.strftime('%b %-d')}",
                body=sweep,
            )
            log.info("Finance sweep emailed to %s", PERSONAL_EMAIL)
        except Exception as e:
            log.warning("Could not email sweep: %s", e)


if __name__ == "__main__":
    main()
