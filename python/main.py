# main.py — FastAPI application entry point

import sys

# Fix for PyInstaller: uvicorn crashes if stdout/stderr is None
if sys.stdout is None:
    sys.stdout = open("nul", "w")
if sys.stderr is None:
    sys.stderr = open("nul", "w")

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import API_HOST, API_PORT, APP_NAME, DEBUG_MODE
from database import init_db
from utils.logger import get_logger

from routes.chat       import router as chat_router
from routes.voice      import router as voice_router
from routes.tasks      import router as tasks_router
from routes.notes      import router as notes_router
from routes.files      import router as files_router
from routes.search     import router as search_router
from routes.calendar   import router as calendar_router
from routes.settings   import router as settings_router
from routes.automation import router as automation_router
from routes.reminders  import router as reminders_router
from routes.code       import router as code_router
from routes.chats      import router as chats_router
from routes.translator import router as translator_router
from routes.wake_word  import router as wake_router

from ai.memory import (
    get_all_facts_for_prompt, delete_fact,
    clear_all_facts, get_recent_messages,
    save_fact
)
from modules.reminders import start_reminder_scheduler

_wake_triggers = []

logger = get_logger(__name__)

# ── App setup ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=f"{APP_NAME} API",
    description="Local AI backend for Charli Desktop Assistant",
    version="0.1.0",
    docs_url="/docs" if DEBUG_MODE else None,
    redoc_url="/redoc" if DEBUG_MODE else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup (ONE definition only) ──────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info(f"Starting {APP_NAME} backend...")
    init_db()
    start_reminder_scheduler()

    try:
        from routes.settings import get_setting
        from voice.wake_word import start_wake_word, add_wake_callback

        wake_enabled   = get_setting("wake_word_enabled", "false") == "true"
        wake_threshold = float(get_setting("wake_word_threshold", "0.5"))

        if wake_enabled:
            def on_wake():
                import time
                logger.info("Wake word triggered — notifying Electron...")
                _wake_triggers.append(time.time())

            add_wake_callback(on_wake)
            start_wake_word(threshold=wake_threshold)
            logger.info("Wake word auto-started from settings.")

    except Exception as e:
        logger.warning(f"Wake word auto-start skipped: {e}")

    logger.info(f"{APP_NAME} backend ready — http://{API_HOST}:{API_PORT}")
    logger.info(f"Swagger docs — http://{API_HOST}:{API_PORT}/docs")

# ── Root ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"app": APP_NAME, "status": "running", "version": "0.1.0"}

# ── Routers ────────────────────────────────────────────────────────────────

app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(tasks_router)
app.include_router(notes_router)
app.include_router(files_router)
app.include_router(search_router)
app.include_router(calendar_router)
app.include_router(settings_router)
app.include_router(automation_router)
app.include_router(reminders_router)
app.include_router(code_router)
app.include_router(chats_router)
app.include_router(translator_router)
app.include_router(wake_router)

# ── Memory router ──────────────────────────────────────────────────────────

memory_router = APIRouter(prefix="/memory", tags=["Memory"])

@memory_router.get("/facts")
async def get_facts():
    return {"facts": get_all_facts_for_prompt()}

@memory_router.delete("/facts/{fact_id}")
async def remove_fact(fact_id: int):
    success = delete_fact(fact_id)
    return {"deleted": success, "id": fact_id}

@memory_router.delete("/facts")
async def clear_facts():
    clear_all_facts()
    return {"cleared": True}

@memory_router.get("/history")
async def get_history(session_id: str = "default", limit: int = 50):
    messages = get_recent_messages(limit=limit, session_id=session_id)
    return {"messages": messages, "count": len(messages)}

app.include_router(memory_router)

# ── Wake word poll endpoint ────────────────────────────────────────────────

@app.get("/wake/triggered")
async def wake_triggered():
    if _wake_triggers:
        _wake_triggers.clear()
        return {"triggered": True}
    return {"triggered": False}

# ── Dev runner ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="debug" if DEBUG_MODE else "info",
    )