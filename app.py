from __future__ import annotations

import os
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ── helpers ────────────────────────────────────────────────────────────────

def _ok(data):
    return jsonify({"ok": True, "data": data})

def _err(msg, code=400):
    return jsonify({"ok": False, "error": str(msg)}), code

def _has_anthropic() -> bool:
    try:
        from srai.config import ANTHROPIC_API_KEY
        return bool(ANTHROPIC_API_KEY and ANTHROPIC_API_KEY not in ("", "sk-ant-..."))
    except Exception:
        return False

def _try_google() -> bool:
    try:
        from srai.google_auth import get_credentials
        return get_credentials().valid
    except Exception:
        return False


# ── system ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health-check")
def health_check():
    return _ok({
        "anthropic": _has_anthropic(),
        "google": _try_google(),
        "date": date.today().strftime("%A, %B %-d, %Y"),
    })


# ── status ─────────────────────────────────────────────────────────────────

@app.route("/api/status")
def status():
    import srai.memory as mem
    sessions = mem.get_gym_sessions(30)
    habits = mem.get_habits()
    bills = mem.bills_due_this_month()
    month_pfx = date.today().strftime("%Y-%m")
    gym_this_month = [s for s in sessions if s["date"].startswith(month_pfx)]
    return _ok({
        "health": {
            "gym_this_month": len(gym_this_month),
            "last_gym": sessions[-1] if sessions else None,
            "habits": habits,
        },
        "finance": {
            "total": len(bills),
            "paid": sum(1 for b in bills if b["paid"]),
            "overdue": [b for b in bills if b["overdue"]],
            "upcoming": [b for b in bills if not b["paid"] and not b["overdue"]],
        },
    })


# ── calendar ───────────────────────────────────────────────────────────────

@app.route("/api/calendar/events")
def calendar_events():
    try:
        from srai.tools.calendar_tools import list_events
        from datetime import timedelta
        import pytz
        from srai.config import TIMEZONE
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)
        t_max = (now + timedelta(days=7)).isoformat()
        return _ok(list_events(now.isoformat(), t_max, max_results=20))
    except Exception as e:
        return _ok([])


@app.route("/api/calendar/events", methods=["POST"])
def create_calendar_event():
    data = request.get_json() or {}
    for f in ("summary", "start", "end"):
        if f not in data:
            return _err(f"Missing: {f}")
    try:
        from srai.tools.calendar_tools import create_event
        return _ok(create_event(**{k: data[k] for k in ("summary", "start", "end", "description", "location") if k in data}))
    except Exception as e:
        return _err(str(e))


# ── ask ────────────────────────────────────────────────────────────────────

@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.get_json() or {}
    query = data.get("query", "").strip()
    if not query:
        return _err("query is required")
    if not _has_anthropic():
        return _err("ANTHROPIC_API_KEY not configured — add it to .env and restart")
    try:
        from srai.agent import run_agent
        from srai.tools import health_tools, finance_tools, calendar_tools, gmail_tools

        tool_defs = health_tools.TOOL_DEFS + finance_tools.TOOL_DEFS
        dispatchers = [health_tools.dispatch, finance_tools.dispatch]
        if _try_google():
            tool_defs = calendar_tools.TOOL_DEFS + gmail_tools.TOOL_DEFS + tool_defs
            dispatchers = [calendar_tools.dispatch, gmail_tools.dispatch] + dispatchers

        system = (
            f"You are SRAI, a personal chief-of-staff for a founder. "
            f"Answer questions about their personal life using available tools. "
            f"Today: {date.today().strftime('%A, %B %-d, %Y')}. Be concise and direct."
        )
        result = run_agent(system, query, tool_defs, dispatchers)
        return _ok({"response": result})
    except Exception as e:
        return _err(str(e))


# ── briefings ──────────────────────────────────────────────────────────────

@app.route("/api/run/<runner>", methods=["POST"])
def run_briefing(runner: str):
    if runner not in ("morning", "evening", "finance"):
        return _err(f"Unknown runner: {runner}")
    if not _has_anthropic():
        return _err("ANTHROPIC_API_KEY not configured — add it to .env and restart")
    try:
        if runner == "morning":
            import runs.morning_briefing as m; m.main()
        elif runner == "evening":
            import runs.evening_wrapup as e; e.main()
        else:
            import runs.finance_sweep as f; f.main()
        log_file = ROOT / "data" / "logs" / f"{runner}_{date.today().strftime('%Y%m%d')}.txt"
        content = log_file.read_text() if log_file.exists() else "(no output)"
        return _ok({"result": content})
    except Exception as e:
        return _err(str(e))


@app.route("/api/briefings")
def list_briefings():
    logs_dir = ROOT / "data" / "logs"
    files = sorted(logs_dir.glob("*.txt"), reverse=True)[:30]
    items = []
    for f in files:
        items.append({
            "name": f.stem,
            "mtime": f.stat().st_mtime,
            "preview": f.read_text()[:180].strip(),
        })
    return _ok(items)


@app.route("/api/briefings/<name>")
def get_briefing(name: str):
    f = ROOT / "data" / "logs" / f"{name}.txt"
    if not f.exists():
        return _err("not found", 404)
    return _ok({"content": f.read_text()})


# ── finance ────────────────────────────────────────────────────────────────

@app.route("/api/bills")
def get_bills():
    import srai.memory as mem
    return _ok(mem.bills_due_this_month())


@app.route("/api/bills", methods=["POST"])
def add_bill():
    data = request.get_json() or {}
    for f in ("name", "amount", "due_day"):
        if f not in data:
            return _err(f"Missing: {f}")
    import srai.memory as mem
    return _ok(mem.add_bill(
        name=data["name"],
        amount=float(data["amount"]),
        due_day=int(data["due_day"]),
        category=data.get("category", "other"),
        recurring=data.get("recurring", True),
    ))


@app.route("/api/bills/pay", methods=["POST"])
def pay_bill():
    data = request.get_json() or {}
    if "bill_name" not in data or "amount" not in data:
        return _err("bill_name and amount required")
    import srai.memory as mem
    return _ok(mem.log_payment(data["bill_name"], float(data["amount"]), data.get("notes", "")))


# ── health ─────────────────────────────────────────────────────────────────

@app.route("/api/habits")
def get_habits():
    import srai.memory as mem
    return _ok(mem.get_habits())


@app.route("/api/habits/log", methods=["POST"])
def log_habit():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return _err("name required")
    import srai.memory as mem
    return _ok(mem.log_habit(name))


@app.route("/api/gym/log", methods=["POST"])
def log_gym():
    data = request.get_json() or {}
    import srai.memory as mem
    return _ok(mem.log_gym_session(data.get("notes", "")))


@app.route("/api/gym/history")
def gym_history():
    import srai.memory as mem
    return _ok(mem.get_gym_sessions(20))


if __name__ == "__main__":
    app.run(debug=True, port=5055, use_reloader=False)
