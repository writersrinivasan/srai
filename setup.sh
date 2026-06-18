#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO"

echo "=== SRAI Setup ==="
echo ""

# 1. Python venv
if [ ! -d ".venv" ]; then
  echo "→ Creating virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate

echo "→ Installing dependencies..."
pip install -q -r requirements.txt

# 2. .env
if [ ! -f ".env" ]; then
  echo ""
  echo "→ Creating .env from template..."
  cp .env.example .env
  echo "  ⚠  Edit .env and add your ANTHROPIC_API_KEY and SRAI_PERSONAL_EMAIL."
fi

# 3. Google credentials reminder
if [ ! -f "google_auth/credentials.json" ]; then
  echo ""
  echo "  ⚠  Google credentials not found."
  echo "     1. Go to https://console.cloud.google.com/"
  echo "     2. Create a project → Enable Google Calendar API + Gmail API"
  echo "     3. Create OAuth 2.0 credentials (Desktop app)"
  echo "     4. Download and save as: google_auth/credentials.json"
  echo ""
fi

# 4. Trigger Google OAuth (needs credentials.json + .env)
if [ -f "google_auth/credentials.json" ] && [ -f ".env" ]; then
  echo "→ Testing Google authentication..."
  python -m srai auth && echo "  ✓ Google auth OK"
fi

# 5. Crontab instructions
echo ""
echo "=== Cron Setup ==="
echo "Run 'crontab -e' and add (adjust paths and times to taste):"
echo ""
PYTHON_PATH="$REPO/.venv/bin/python"
echo "# SRAI — morning briefing at 7:00 AM"
echo "0 7 * * *   $PYTHON_PATH $REPO/runs/morning_briefing.py >> $REPO/data/logs/cron.log 2>&1"
echo ""
echo "# SRAI — evening wrap-up at 9:00 PM"
echo "0 21 * * *  $PYTHON_PATH $REPO/runs/evening_wrapup.py >> $REPO/data/logs/cron.log 2>&1"
echo ""
echo "# SRAI — weekly finance sweep at 8:00 AM Sunday"
echo "0 8 * * 0   $PYTHON_PATH $REPO/runs/finance_sweep.py >> $REPO/data/logs/cron.log 2>&1"
echo ""
echo "=== Done ==="
echo "Run 'python -m srai status' to verify the setup."
echo "Run 'python -m srai ask \"What's on my calendar today?\"' to test."
