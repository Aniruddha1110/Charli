# main.py — FastAPI application entry point
# Run this to start the Charli Python backend:
#   uvicorn main:app --host 127.0.0.1 --port 8000 --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import API_HOST, API_PORT, APP_NAME, DEBUG_MODE
from database import init_db
from utils.logger import get_logger

# Import route modules
from routes.chat import router as chat_router
# More routers added here as we build them:
from routes.voice     import router as voice_router
from routes.tasks     import router as tasks_router
from routes.notes     import router as notes_router
from routes.files     import router as files_router
from routes.search    import router as search_router
from routes.calendar import router as calendar_router
from routes.settings import router as settings_router
from routes.automation import router as automation_router
from fastapi import APIRouter
from ai.memory import (
    get_all_facts_for_prompt, delete_fact,
    clear_all_facts, get_recent_messages,
    save_fact
)
from routes.reminders import router as reminders_router
from modules.reminders import start_reminder_scheduler
from routes.code import router as code_router
from routes.chats import router as chats_router
from routes.translator import router as translator_router
from routes.wake_word import router as wake_router

# Stores timestamps of wake word triggers for Electron to poll
_wake_triggers = []

logger = get_logger(__name__)

# ── App setup ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=f"{APP_NAME} API",
    description="Local AI backend for Charli Desktop Assistant",
    version="0.1.0",
    docs_url="/docs" if DEBUG_MODE else None,      # Swagger UI in dev only
    redoc_url="/redoc" if DEBUG_MODE else None,
)

# Allow Electron (file:// or localhost) to call this API freely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Fine for localhost-only app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Startup ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    logger.info(f"Starting {APP_NAME} backend...")
    init_db()
    start_reminder_scheduler()

    # Auto-start wake word if enabled in settings
    try:
        from routes.settings import get_setting
        from voice.wake_word import start_wake_word, add_wake_callback

        wake_enabled   = get_setting("wake_word_enabled", "false") == "true"
        wake_threshold = float(get_setting("wake_word_threshold", "0.5"))

        if wake_enabled:
            # Register the IPC callback to notify Electron
            def on_wake():
                logger.info("Wake word triggered — notifying Electron...")
                # We store the trigger in a simple flag
                # Electron polls /wake/status to check for triggers
                import time
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


# ── Register routers ───────────────────────────────────────────────────────

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

# ── Memory management endpoints for facts and conversation history ───────────

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

# In startup event, add after init_db():

@app.on_event("startup")
async def startup():
    logger.info(f"Starting {APP_NAME} backend...")
    init_db()
    start_reminder_scheduler()   # ← add this
    logger.info(f"{APP_NAME} backend ready — http://{API_HOST}:{API_PORT}")
    
@app.get("/wake/triggered")
async def wake_triggered():
    """
    Electron polls this every second.
    Returns True if wake word was detected since last check,
    then clears the trigger.
    """
    if _wake_triggers:
        _wake_triggers.clear()
        return {"triggered": True}
    return {"triggered": False}


# ── Dev runner ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=DEBUG_MODE,
        log_level="debug" if DEBUG_MODE else "info",
    )