#!/usr/bin/env python3
"""
SRAI CLI — ad-hoc queries and manual runner.

Usage:
  python -m srai ask "Did I go to the gym this week?"
  python -m srai run morning
  python -m srai run evening
  python -m srai run finance
  python -m srai status
  python -m srai bill add "Rent" 3200 1 housing
  python -m srai bill list
  python -m srai bill paid "Rent" 3200
  python -m srai habit log meditation
  python -m srai habit status
  python -m srai gym log "45 min cardio + weights"
  python -m srai auth          # trigger Google OAuth flow
"""

import json
import sys
from datetime import date


def cmd_ask(query: str) -> None:
    from srai.agent import run_agent
    from srai.tools import calendar_tools, finance_tools, gmail_tools, health_tools

    system = f"""You are SRAI, a personal chief-of-staff for a founder.
Answer questions about their personal life using the available tools.
Today: {date.today().strftime('%A, %B %-d, %Y')}
Be concise and direct."""

    tool_defs = (
        calendar_tools.TOOL_DEFS
        + gmail_tools.TOOL_DEFS
        + health_tools.TOOL_DEFS
        + finance_tools.TOOL_DEFS
    )
    dispatchers = [
        calendar_tools.dispatch,
        gmail_tools.dispatch,
        health_tools.dispatch,
        finance_tools.dispatch,
    ]
    result = run_agent(system, query, tool_defs, dispatchers)
    print(result)


def cmd_run(runner: str) -> None:
    if runner == "morning":
        import runs.morning_briefing as m; m.main()
    elif runner == "evening":
        import runs.evening_wrapup as e; e.main()
    elif runner == "finance":
        import runs.finance_sweep as f; f.main()
    else:
        print(f"Unknown runner: {runner}. Choose: morning, evening, finance")
        sys.exit(1)


def cmd_status() -> None:
    import srai.memory as mem
    summary = {
        "health": mem.health_summary() if hasattr(mem, "health_summary") else {},
        "finance": mem.bills_due_this_month(),
        "notes": mem.get_notes(limit=3),
    }

    # inline health summary
    sessions = mem.get_gym_sessions(10)
    habits = mem.get_habits()
    print(f"\n{'='*50}")
    print(f"SRAI STATUS — {date.today().strftime('%A, %B %-d, %Y')}")
    print(f"{'='*50}")
    print(f"\nGYM  — {len(sessions)} sessions logged (last 10 shown)")
    if sessions:
        print(f"       Last session: {sessions[-1]['date']}")
    print(f"\nHABITS")
    if habits:
        for name, h in habits.items():
            print(f"  {name}: streak={h['streak']} last={h['last_logged']}")
    else:
        print("  (none tracked yet)")
    bills = mem.bills_due_this_month()
    print(f"\nBILLS THIS MONTH ({date.today().strftime('%B')})")
    for b in bills:
        status = "PAID" if b["paid"] else ("OVERDUE" if b["overdue"] else f"due day {b['due_day']}")
        print(f"  {b['name']:20s}  ${b['amount']:>8.2f}  {status}")
    if not bills:
        print("  (no bills registered — use `srai bill add` to set up)")
    print()


def cmd_bill(args: list[str]) -> None:
    import srai.memory as mem
    if not args:
        print("Usage: srai bill add|list|paid")
        return
    sub = args[0]
    if sub == "list":
        bills = mem.get_bills()
        if not bills:
            print("No bills registered.")
            return
        for b in bills:
            print(f"{b['name']:20s}  ${b['amount']:>8.2f}  due day {b['due_day']:2d}  [{b['category']}]")
    elif sub == "add":
        if len(args) < 4:
            print("Usage: srai bill add <name> <amount> <due_day> [category]")
            return
        name, amount, due_day = args[1], float(args[2]), int(args[3])
        cat = args[4] if len(args) > 4 else "other"
        b = mem.add_bill(name, amount, due_day, cat)
        print(f"Added: {json.dumps(b)}")
    elif sub == "paid":
        if len(args) < 3:
            print("Usage: srai bill paid <name> <amount> [notes]")
            return
        name, amount = args[1], float(args[2])
        notes = args[3] if len(args) > 3 else ""
        p = mem.log_payment(name, amount, notes)
        print(f"Logged payment: {json.dumps(p)}")
    else:
        print(f"Unknown bill sub-command: {sub}")


def cmd_habit(args: list[str]) -> None:
    import srai.memory as mem
    if not args:
        print("Usage: srai habit log|status")
        return
    sub = args[0]
    if sub == "log":
        if len(args) < 2:
            print("Usage: srai habit log <habit_name>")
            return
        result = mem.log_habit(args[1])
        if result["already_logged"]:
            print(f"'{args[1]}' already logged today. Streak: {result['streak']}")
        else:
            print(f"Logged '{args[1]}'. Streak: {result['streak']} day(s)")
    elif sub == "status":
        habits = mem.get_habits()
        if not habits:
            print("No habits tracked yet.")
            return
        for name, h in habits.items():
            print(f"{name:20s}  streak={h['streak']:3d}  last={h['last_logged']}")
    else:
        print(f"Unknown habit sub-command: {sub}")


def cmd_gym(args: list[str]) -> None:
    import srai.memory as mem
    if not args:
        print("Usage: srai gym log [notes]")
        return
    if args[0] == "log":
        notes = " ".join(args[1:])
        result = mem.log_gym_session(notes)
        print(f"Gym session logged: {json.dumps(result)}")
    else:
        print(f"Unknown gym sub-command: {args[0]}")


def cmd_auth() -> None:
    from srai.google_auth import get_credentials
    creds = get_credentials()
    print(f"Google auth OK. Token valid: {creds.valid}")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0]
    rest = args[1:]

    if cmd == "ask":
        cmd_ask(" ".join(rest))
    elif cmd == "run":
        cmd_run(rest[0] if rest else "")
    elif cmd == "status":
        cmd_status()
    elif cmd == "bill":
        cmd_bill(rest)
    elif cmd == "habit":
        cmd_habit(rest)
    elif cmd == "gym":
        cmd_gym(rest)
    elif cmd == "auth":
        cmd_auth()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
