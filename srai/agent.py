from __future__ import annotations

"""
Core agentic loop: sends messages to Claude, executes tool calls,
and iterates until stop_reason == 'end_turn'.
"""

import json
import logging
from typing import Any

import anthropic

from srai.config import ANTHROPIC_API_KEY, MODEL

log = logging.getLogger(__name__)
_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def run_agent(
    system: str,
    user_message: str,
    tool_defs: list[dict],
    dispatchers: list,
    max_iterations: int = 12,
) -> str:
    """
    Run an agentic loop with Claude.

    Args:
        system: System prompt for the agent.
        user_message: Initial user message / task.
        tool_defs: List of Anthropic tool definition dicts.
        dispatchers: List of dispatch(name, args) callables — one per tool module.
        max_iterations: Safety cap on tool-call rounds.

    Returns:
        Final text response from Claude.
    """
    client = _get_client()
    messages: list[dict] = [{"role": "user", "content": user_message}]

    for iteration in range(max_iterations):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            messages=messages,
            tools=tool_defs,
        )
        log.debug("iteration=%d stop_reason=%s", iteration, response.stop_reason)

        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        if response.stop_reason == "tool_use":
            tool_results: list[dict] = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                name, args = block.name, block.input
                log.info("tool_call name=%s args=%s", name, args)
                result = _execute_tool(name, args, dispatchers)
                log.debug("tool_result name=%s result=%s", name, str(result)[:200])
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, default=str),
                })
            messages.append({"role": "user", "content": tool_results})
            continue

        # unexpected stop reason
        break

    return "[agent: max iterations reached]"


def _execute_tool(name: str, args: dict, dispatchers: list) -> Any:
    for dispatcher in dispatchers:
        try:
            return dispatcher(name, args)
        except ValueError:
            continue
    return {"error": f"No dispatcher handled tool '{name}'"}
