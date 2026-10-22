"""Resume Q&A agent built with LangGraph + Claude."""

from collections.abc import AsyncIterator

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessageChunk, SystemMessage
from langgraph.graph import START, END, MessagesState, StateGraph

from .base import ChatMessage, ResumeAgent

SYSTEM_PROMPT = """You answer questions about the candidate whose resume is provided below.

Ground every answer in the resume. If the resume doesn't contain the information, say so
plainly instead of guessing. When useful, quote or point to the relevant section
(e.g. "Experience at Acme, 2021-2023"). Keep answers concise unless asked for detail.

<resume>
{resume}
</resume>"""


class State(MessagesState):
    resume: str


class LangGraphResumeAgent(ResumeAgent):
    def __init__(self):
        llm = ChatAnthropic(model="claude-opus-5-5", max_tokens=16000)

        async def answer(state: State):
            system = SystemMessage(content=SYSTEM_PROMPT.format(resume=state["resume"]))
            response = await llm.ainvoke([system] + state["messages"])
            return {"messages": [response]}

        graph = StateGraph(State)
        graph.add_node("answer", answer)
        graph.add_edge(START, "answer")
        graph.add_edge("answer", END)
        # No checkpointer: AG-UI sends the full conversation on every run.
        self.graph = graph.compile()

    async def stream(self, messages: list[ChatMessage], resume_text: str) -> AsyncIterator[str]:
        inputs = {"messages": [(m.role, m.content) for m in messages], "resume": resume_text}
        async for chunk, _metadata in self.graph.astream(inputs, stream_mode="messages"):
            if isinstance(chunk, AIMessageChunk) and (text := _text(chunk)):
                yield text


def _text(chunk: AIMessageChunk) -> str:
    """Keep only text blocks (Claude may also stream thinking blocks)."""
    if isinstance(chunk.content, str):
        return chunk.content
    return "".join(
        block.get("text", "") for block in chunk.content
        if isinstance(block, dict) and block.get("type") == "text"
    )
