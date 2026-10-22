"""Minimal AG-UI client: sends a run request and yields the assistant's text as it streams.

It depends only on the AG-UI wire format, never on the backend's agent framework.
"""

import json
import uuid
from collections.abc import Iterator

import httpx


class AgentError(Exception):
    pass


def run_agent(base_url: str, thread_id: str, messages: list[dict]) -> Iterator[str]:
    """messages: AG-UI messages, each {"id", "role", "content"}."""
    payload = {
        "threadId": thread_id,
        "runId": str(uuid.uuid4()),
        "messages": messages,
        "state": {},
        "tools": [],
        "context": [],
        "forwardedProps": {},
    }
    timeout = httpx.Timeout(10.0, read=300.0)
    headers = {"Accept": "text/event-stream"}
    with httpx.stream("POST", f"{base_url}/agent", json=payload, headers=headers, timeout=timeout) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith("data:"):
                continue
            event = json.loads(line[len("data:"):])
            match event["type"]:
                case "TEXT_MESSAGE_CONTENT":
                    yield event["delta"]
                case "RUN_ERROR":
                    raise AgentError(event.get("message", "Agent run failed"))
                case "RUN_FINISHED":
                    return
