"""Agent registry. Set AGENT_FRAMEWORK to pick which implementation the server runs.

To add a framework: write a ResumeAgent subclass in this package and register it below.
"""

import importlib
import os

from .base import ChatMessage, ResumeAgent

AGENTS = {
    "langgraph": "agents.langgraph_agent:LangGraphResumeAgent",
}


def get_agent() -> ResumeAgent:
    name = os.getenv("AGENT_FRAMEWORK", "langgraph")
    if name not in AGENTS:
        raise ValueError(f"Unknown AGENT_FRAMEWORK '{name}'. Available: {', '.join(AGENTS)}")
    module_name, class_name = AGENTS[name].split(":")
    return getattr(importlib.import_module(module_name), class_name)()


__all__ = ["ChatMessage", "ResumeAgent", "get_agent"]
