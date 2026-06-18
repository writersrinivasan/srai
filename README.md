# SRAI — Personal Chief of Staff

An agentic AI system that handles your personal life so you can focus on building your company.

SRAI runs three domain agents (Calendar, Health, Finance) orchestrated by Claude, with a web dashboard and scheduled cron runners that deliver morning briefings, evening wrap-ups, and weekly finance sweeps — all delivered to your inbox.

---

## What it does

| Domain | Capabilities |
|---|---|
| **Calendar** | Reviews upcoming events, protects deep-work blocks, finds free slots, creates events |
| **Health** | Tracks gym sessions, manages habit streaks, monitors weekly fitness goals |
| **Finance** | Tracks recurring bills, detects payments via Gmail, flags overdue items |

Scheduled runs:
- **7 AM daily** — Morning briefing: calendar highlights, health check, urgent finance alerts
- **9 PM daily** — Evening wrap-up: what happened today, tomorrow's top events
- **8 AM Sunday** — Finance sweep: Gmail payment scan, overdue bills, month-to-date summary

---

## Architecture

```
srai/
├── agent.py          # Core Claude agentic loop (tool_use → dispatch → iterate)
├── orchestrator.py   # Runs multiple domain agents, synthesises into one briefing
├── config.py         # Settings loaded from .env
├── memory.py         # JSON state store — bills, payments, habits, gym logs
├── google_auth.py    # Google OAuth 2.0 helper
└── tools/
    ├── calendar_tools.py   # Google Calendar read/write + tool definitions
    ├── gmail_tools.py      # Gmail search, send, draft + tool definitions
    ├── health_tools.py     # Gym log, habit streaks + tool definitions
    └── finance_tools.py    # Bill registry, payment detection + tool definitions

agents/
├── calendar_agent.py   # Schedule protection, conflict detection
├── health_agent.py     # Gym frequency, habit tracking
└── finance_agent.py    # Bill status, Gmail payment scanning

runs/
├── morning_briefing.py   # Cron: 7 AM daily
├── evening_wrapup.py     # Cron: 9 PM daily
└── finance_sweep.py      # Cron: 8 AM Sunday

app.py                # Flask web dashboard (API + frontend)
templates/index.html  # Single-page dashboard UI
```

**How the agentic loop works:**
1. A runner (or the web UI) sends a task to the orchestrator
2. The orchestrator dispatches to one or more domain agents
3. Each agent runs a Claude `tool_use` loop — Claude calls tools, gets results, calls more tools, until it produces a final answer
4. The orchestrator sends all agent outputs to Claude for a final synthesis into a single briefing

---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/writersrinivasan/srai.git
cd srai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
SRAI_PERSONAL_EMAIL=you@gmail.com
SRAI_TIMEZONE=America/Los_Angeles   # your local timezone
SRAI_CALENDAR_ID=primary            # or a specific calendar ID
```

### 3. Google API credentials

SRAI uses Google Calendar and Gmail. You need an OAuth 2.0 credential:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → **Enable APIs**: Google Calendar API, Gmail API
3. Go to **Credentials** → Create → **OAuth 2.0 Client ID** → Desktop app
4. Download the JSON file and save it as:

```
google_auth/credentials.json
```

5. Run the auth flow (opens a browser window once):

```bash
python -m srai auth
```

The OAuth token is saved to `google_auth/token.json` and refreshes automatically.

### 4. Register your bills

```bash
python -m srai bill add "Rent"      3200  1  housing
python -m srai bill add "PG&E"       120  15 utilities
python -m srai bill add "Internet"    80  20 utilities
python -m srai bill add "Netflix"     18  12 subscriptions
```

Arguments: `bill add <name> <amount> <due_day_of_month> <category>`

---

## Web Dashboard

Start the server:

```bash
source .venv/bin/activate
python app.py
```

Open **http://localhost:5055** in your browser.

| Page | What you can do |
|---|---|
| Dashboard | Overview: today's events, gym count, bill status, habit streaks |
| Ask SRAI | Natural-language questions answered using your live data |
| Calendar | View next 7 days, create events |
| Health | Log gym sessions, track habit streaks |
| Finance | Add bills, mark payments, view monthly status |
| Briefings | Trigger and read morning / evening / finance reports |

The sidebar shows live connection status for Claude and Google. Both dots turn green once credentials are configured.

---

## CLI

```bash
# Ask a question
python -m srai ask "Did I go to the gym this week?"
python -m srai ask "Any bills overdue?"
python -m srai ask "What's on my calendar tomorrow?"

# Manual briefing runs
python -m srai run morning
python -m srai run evening
python -m srai run finance

# Status snapshot (no API calls)
python -m srai status

# Bill management
python -m srai bill list
python -m srai bill add "Rent" 3200 1 housing
python -m srai bill paid "Rent" 3200

# Health tracking
python -m srai gym log "45 min strength · chest + back"
python -m srai habit log meditation
python -m srai habit status

# Re-run Google OAuth
python -m srai auth
```

---

## Cron scheduling

Run `bash setup.sh` to get the exact cron lines for your machine, or add these manually via `crontab -e` (adjust the path):

```cron
# SRAI — morning briefing at 7:00 AM
0 7 * * *   /path/to/srai/.venv/bin/python /path/to/srai/runs/morning_briefing.py >> /path/to/srai/data/logs/cron.log 2>&1

# SRAI — evening wrap-up at 9:00 PM
0 21 * * *  /path/to/srai/.venv/bin/python /path/to/srai/runs/evening_wrapup.py >> /path/to/srai/data/logs/cron.log 2>&1

# SRAI — weekly finance sweep at 8:00 AM Sunday
0 8 * * 0   /path/to/srai/.venv/bin/python /path/to/srai/runs/finance_sweep.py >> /path/to/srai/data/logs/cron.log 2>&1
```

Each run saves a log to `data/logs/` and emails you the briefing if `SRAI_PERSONAL_EMAIL` is set.

---

## Extending SRAI

### Add a new domain agent

1. **Add tool functions** in `srai/tools/my_tools.py` — plain Python functions that do the work
2. **Add `TOOL_DEFS`** — list of Anthropic tool definition dicts describing each function
3. **Add `dispatch(name, args)`** — routes tool calls by name to your functions
4. **Create `agents/my_agent.py`** — set a `SYSTEM` prompt and call `run_agent()`
5. **Register in a runner** — import your agent and add it to the `tasks` dict in the relevant `runs/` file

The `health_tools.py` + `agents/health_agent.py` pair is the simplest example to follow.

### Add a new tool to an existing agent

Add a new entry to `TOOL_DEFS` and a matching branch in `dispatch()`. The agentic loop will automatically make it available to Claude.

---

## Data & privacy

- All personal state (bills, habits, gym logs) is stored locally in `data/state.json`
- Google OAuth tokens are stored locally in `google_auth/token.json`
- Neither file is ever committed to git (both are in `.gitignore`)
- Briefing logs are saved to `data/logs/` — also gitignored
- The only data leaving your machine is what Claude needs to answer each query (calendar events, email snippets, bill status)

---

## Requirements

- Python 3.9+
- [Anthropic API key](https://console.anthropic.com/)
- Google Cloud project with Calendar API + Gmail API enabled
- macOS / Linux (cron-based scheduling)
