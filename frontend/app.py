"""Streamlit chat UI for the resume agent. Talks to the backend over AG-UI.

Run:  streamlit run app.py
"""

import os
import uuid

import httpx
import streamlit as st

from agui_client import AgentError, run_agent

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Resume Chat", page_icon="📄")
st.title("📄 Resume Chat")


def reset_chat():
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []


if "thread_id" not in st.session_state:
    reset_chat()

with st.sidebar:
    st.header("Resume")
    uploaded = st.file_uploader("Upload a resume", type=["pdf", "docx", "txt", "md"])
    if uploaded and uploaded.file_id != st.session_state.get("uploaded_id"):
        try:
            response = httpx.post(
                f"{BACKEND_URL}/resume",
                files={"file": (uploaded.name, uploaded.getvalue())},
                timeout=60,
            )
            if response.status_code == 200:
                st.session_state.uploaded_id = uploaded.file_id
                reset_chat()  # new resume, fresh conversation
            else:
                st.error(response.json().get("detail", "Upload failed"))
        except httpx.HTTPError as exc:
            st.error(f"Upload failed: {exc}")

    try:
        status = httpx.get(f"{BACKEND_URL}/resume", timeout=5).json()
    except httpx.HTTPError:
        st.error(f"Can't reach the backend at {BACKEND_URL}. Is it running?")
        st.stop()

    if status["loaded"]:
        st.success(f"Loaded: {status['filename']}")
    else:
        st.info("Upload a resume to start chatting.")

    st.button("Clear chat", on_click=reset_chat)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question := st.chat_input("Ask about the resume...", disabled=not status["loaded"]):
    st.session_state.messages.append({"id": str(uuid.uuid4()), "role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(
                run_agent(BACKEND_URL, st.session_state.thread_id, st.session_state.messages)
            )
            st.session_state.messages.append({"id": str(uuid.uuid4()), "role": "assistant", "content": answer})
        except (AgentError, httpx.HTTPError) as exc:
            st.session_state.messages.pop()  # drop the unanswered question
            st.error(f"Agent error: {exc}")
