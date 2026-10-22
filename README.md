# Resume Chat

Ask questions about a resume. The backend runs the agent and exposes it over the
[AG-UI protocol](https://docs.ag-ui.com); the Streamlit frontend only speaks AG-UI,
so the agent framework can change without touching the frontend.

```
frontend/ (Streamlit)  --AG-UI over SSE-->  backend/ (FastAPI)  -->  agents/<framework>
```

## Run

Backend (terminal 1):
```powershell
cd backend
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-..."
uvicorn main:app --port 8000
```

Frontend (terminal 2):
```powershell
cd frontend
pip install -r requirements.txt
streamlit run app.py
```

Then upload a resume (PDF, DOCX, TXT, MD) in the sidebar and start asking questions.

## Backend endpoints

| Endpoint | Purpose |
|---|---|
| `POST /agent` | AG-UI run: takes `RunAgentInput`, streams AG-UI events (SSE) |
| `POST /resume` | Upload a resume file |
| `GET /resume` | Whether a resume is loaded |

Set `RESUME_PATH` to preload a resume at startup, and `BACKEND_URL` on the frontend
if the backend isn't at `http://localhost:8000`.

## Switching agent frameworks

1. Add `backend/agents/<name>_agent.py` with a class implementing `ResumeAgent.stream()`
   (see `agents/base.py`): take the chat messages + resume text, yield text chunks.
2. Register it in `AGENTS` in `backend/agents/__init__.py`.
3. Start the backend with `AGENT_FRAMEWORK=<name>`.

No changes to `main.py` or the frontend are needed.
