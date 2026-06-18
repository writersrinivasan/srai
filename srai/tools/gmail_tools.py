"""Gmail tool functions + Anthropic tool definitions."""

import base64
import email as email_lib
from email.mime.text import MIMEText
from typing import Any

from srai.config import PERSONAL_EMAIL
from srai.google_auth import gmail_service


def _svc():
    return gmail_service()


def _decode_body(msg_payload) -> str:
    parts = msg_payload.get("parts", [])
    if parts:
        for p in parts:
            if p.get("mimeType") == "text/plain":
                data = p["body"].get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    data = msg_payload.get("body", {}).get("data", "")
    if data:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    return ""


# ── Tool functions ──────────────────────────────────────────────────────────

def search_emails(query: str, max_results: int = 10) -> list[dict]:
    """Search Gmail with a query string (same syntax as Gmail search bar)."""
    result = _svc().users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    messages = result.get("messages", [])
    emails = []
    for m in messages:
        msg = _svc().users().messages().get(userId="me", id=m["id"], format="full").execute()
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        snippet = msg.get("snippet", "")
        body = _decode_body(msg["payload"])[:500]
        emails.append({
            "id": m["id"],
            "subject": headers.get("Subject", "(no subject)"),
            "from": headers.get("From", ""),
            "date": headers.get("Date", ""),
            "snippet": snippet,
            "body_preview": body,
        })
    return emails


def send_email(to: str, subject: str, body: str) -> dict:
    mime = MIMEText(body)
    mime["to"] = to
    mime["from"] = PERSONAL_EMAIL
    mime["subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    sent = _svc().users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"id": sent["id"], "to": to, "subject": subject}


def draft_email(to: str, subject: str, body: str) -> dict:
    mime = MIMEText(body)
    mime["to"] = to
    mime["from"] = PERSONAL_EMAIL
    mime["subject"] = subject
    raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
    draft = _svc().users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    return {"draft_id": draft["id"], "to": to, "subject": subject}


def list_unread(max_results: int = 15) -> list[dict]:
    return search_emails("is:unread in:inbox", max_results=max_results)


# ── Anthropic tool definitions ──────────────────────────────────────────────

TOOL_DEFS = [
    {
        "name": "gmail_search",
        "description": "Search Gmail using standard Gmail query syntax (e.g. 'from:bank subject:statement is:unread').",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Gmail search query."},
                "max_results": {"type": "integer", "description": "Max emails to return (default 10)."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "gmail_list_unread",
        "description": "List unread inbox emails.",
        "input_schema": {
            "type": "object",
            "properties": {
                "max_results": {"type": "integer", "description": "Max emails to return (default 15)."},
            },
        },
    },
    {
        "name": "gmail_draft",
        "description": "Create a Gmail draft (does not send).",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
    {
        "name": "gmail_send",
        "description": "Send an email immediately.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
]


def dispatch(name: str, args: dict) -> Any:
    if name == "gmail_search":
        return search_emails(**args)
    if name == "gmail_list_unread":
        return list_unread(**args)
    if name == "gmail_draft":
        return draft_email(**args)
    if name == "gmail_send":
        return send_email(**args)
    raise ValueError(f"Unknown gmail tool: {name}")
