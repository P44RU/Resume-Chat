"""The contract every agent framework implements.

The AG-UI server (main.py) only talks to this interface, so adding or swapping a
framework never touches the server or the frontend.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal


@dataclass
class ChatMessage:
    role: Literal["user", "assistant"]
    content: str


class ResumeAgent(ABC):
    @abstractmethod
    def stream(self, messages: list[ChatMessage], resume_text: str) -> AsyncIterator[str]:
        """Answer the latest user message, yielding the reply as text chunks."""
