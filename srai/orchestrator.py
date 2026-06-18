"""
Top-level orchestrator. Runs a set of domain agents and synthesises
their outputs into a single briefing via a final Claude call.
"""

import logging
from datetime import date
from typing import Callable

import anthropic

from srai.config import ANTHROPIC_API_KEY, MODEL

log = logging.getLogger(__name__)


def run_briefing(
    tasks: dict[str, tuple[Callable[[str], str], str]],
    briefing_style: str = "morning",
) -> str:
    """
    Args:
        tasks: { domain_label -> (agent_run_fn, task_prompt) }
        briefing_style: 'morning', 'evening', or 'finance'

    Returns:
        A synthesised briefing string.
    """
    results: dict[str, str] = {}
    for label, (agent_fn, prompt) in tasks.items():
        log.info("Running agent: %s", label)
        try:
            results[label] = agent_fn(prompt)
        except Exception as e:
            log.exception("Agent %s failed", label)
            results[label] = f"[error: {e}]"

    return _synthesise(results, briefing_style)


def _synthesise(agent_outputs: dict[str, str], style: str) -> str:
    sections = "\n\n".join(
        f"=== {label.upper()} ===\n{output}"
        for label, output in agent_outputs.items()
    )

    style_instructions = {
        "morning": (
            "This is a MORNING briefing. Lead with the day's calendar highlights, "
            "then health status, then any urgent finance items. "
            "End with a single action the user should prioritise today."
        ),
        "evening": (
            "This is an EVENING wrap-up. Summarise what was handled today, "
            "flag anything unresolved, and surface tomorrow's top calendar events. "
            "Keep it under 200 words."
        ),
        "finance": (
            "This is a WEEKLY FINANCE SWEEP. Lead with overdue bills (urgent), "
            "then what's coming due this week, then the month-to-date paid summary. "
            "Be precise about amounts and dates."
        ),
    }.get(style, "Summarise the agent outputs into a concise personal briefing.")

    prompt = f"""You are SRAI, a personal chief-of-staff. Below are outputs from your domain agents.
Synthesise them into a clean, structured briefing for the founder.

{style_instructions}

Format: plain text with short section headers. No bullet overload — prose where it flows better.
Today: {date.today().strftime('%A, %B %-d, %Y')}

--- AGENT OUTPUTS ---
{sections}
"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
