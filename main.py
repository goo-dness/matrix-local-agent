from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from agent import run_agent
from memory import init_db, load_history, new_session, save_message


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


MAX_HISTORY = 6  # keep only last 3 exchanges


@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id if request.session_id else new_session()
    history = load_history(session_id)
    history = history[-MAX_HISTORY:]  # trim to last 6 messages
    response = run_agent(request.message, history)
    save_message(session_id, "user", request.message)
    save_message(session_id, "assistant", response)
    return {"response": response, "session_id": session_id}
