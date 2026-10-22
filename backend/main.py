"""FastAPI server exposing the resume agent over the AG-UI protocol.

The frontend only speaks AG-UI, so swapping the agent framework (AGENT_FRAMEWORK,
see agents/__init__.py) never requires a frontend change.

Run:  uvicorn main:app --port 8000
"""

import os
import uuid
from pathlib import Path

from ag_ui.core import (
    EventType,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
)
from ag_ui.encoder import EventEncoder
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from agents import ChatMessage, get_agent
from resume_loader import extract_text, load_resume

app = FastAPI(title="Resume Agent (AG-UI)")
agent = get_agent()

# Single-user local app: the current resume lives in memory.
resume = {"filename": None, "text": None}
if path := os.getenv("RESUME_PATH"):
    resume.update(filename=Path(path).name, text=load_resume(path))


def to_chat_messages(messages) -> list[ChatMessage]:
    """Convert AG-UI messages to the framework-neutral ChatMessage list."""
    result = []
    for message in messages:
        if message.role not in ("user", "assistant"):
            continue
        content = message.content
        if isinstance(content, list):  # multimodal user input: keep the text parts
            content = "".join(getattr(part, "text", "") for part in content)
        if content:
            result.append(ChatMessage(role=message.role, content=content))
    return result


@app.post("/agent")
async def run_agent(input_data: RunAgentInput, request: Request):
    encoder = EventEncoder(accept=request.headers.get("accept"))
    ids = {"thread_id": input_data.thread_id, "run_id": input_data.run_id}

    async def events():
        yield encoder.encode(RunStartedEvent(type=EventType.RUN_STARTED, **ids))
        try:
            if not resume["text"]:
                raise ValueError("No resume uploaded yet. Upload one first.")

            message_id = str(uuid.uuid4())
            yield encoder.encode(TextMessageStartEvent(
                type=EventType.TEXT_MESSAGE_START, message_id=message_id, role="assistant"))
            async for delta in agent.stream(to_chat_messages(input_data.messages), resume["text"]):
                yield encoder.encode(TextMessageContentEvent(
                    type=EventType.TEXT_MESSAGE_CONTENT, message_id=message_id, delta=delta))
            yield encoder.encode(TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=message_id))

            yield encoder.encode(RunFinishedEvent(type=EventType.RUN_FINISHED, **ids))
        except Exception as exc:
            yield encoder.encode(RunErrorEvent(type=EventType.RUN_ERROR, message=str(exc)))

    return StreamingResponse(events(), media_type=encoder.get_content_type())


@app.post("/resume")
async def upload_resume(file: UploadFile = File(...)):
    try:
        text = extract_text(await file.read(), Path(file.filename or "").suffix)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    resume.update(filename=file.filename, text=text)
    return {"filename": file.filename, "characters": len(text)}


@app.get("/resume")
def resume_status():
    return {"loaded": resume["text"] is not None, "filename": resume["filename"]}
