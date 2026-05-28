# routes/chat.py — Chat endpoint with session management + memory

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from ai.ollama_client import ollama
from ai.memory import build_memory_context, extract_and_save_facts
from modules.chat_history import (
    get_active_chat, create_chat,
    add_message, get_recent_messages_for_context,
    auto_name_chat, get_messages
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


# ── Models ─────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:       str
    chat_id:       Optional[int]        = None
    history:       Optional[list[dict]] = []
    system_prompt: Optional[str]        = None
    model:         Optional[str]        = None
    use_memory:    Optional[bool]       = True


class ChatResponse(BaseModel):
    reply:      str
    model_used: str
    chat_id:    int


# ── Helper ─────────────────────────────────────────────────────────────────

def get_bot_name() -> str:
    try:
        from database import get_connection
        with get_connection() as conn:
            row = conn.execute(
                "SELECT value FROM settings WHERE key = 'bot_name'"
            ).fetchone()
            return row["value"] if row and row["value"] else "Charli"
    except Exception:
        return "Charli"
    
# Note: The system prompt is critical for multilingual behavior. It must be clear and explicit.
    
def build_system_prompt(bot_name: str, memory_context: str = "") -> str:
    """Build multilingual-aware system prompt."""
    return (
        f"You are {bot_name}, a smart, friendly, and efficient personal AI assistant "
        f"running entirely on the user's laptop. Your name is {bot_name}.\n\n"

        f"LANGUAGE RULES — CRITICAL:\n"
        f"- Always detect the language of the user's message\n"
        f"- Reply in the SAME language the user used\n"
        f"- Supported: English, Hindi, Bengali, Odia, French\n"
        f"- If the user writes in Roman script casually (Hinglish like 'kya hal hai'), "
        f"reply in Roman script too (e.g. 'Main theek hoon, aap batao!')\n"
        f"- If the user writes formally in native script (Devanagari, Bengali, Odia), "
        f"reply in the same native script\n"
        f"- If the user speaks in mixed languages, match their style\n"
        f"- NEVER reply in English if the user wrote in another language\n\n"

        f"CAPABILITIES:\n"
        f"You help with coding, tasks, notes, file management, "
        f"web search, translation, and general questions.\n"
        f"Be concise, clear, and proactive.\n\n"

        + (f"MEMORY:\n{memory_context}\n\n" if memory_context else "")
    )


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint with session management.
    Uses active chat session for persistent history.
    """
    logger.info(f"Chat — '{request.message[:60]}'")

    bot_name = get_bot_name()

    # ── Get or create active chat ──────────────────────────────────────
    if request.chat_id:
        from modules.chat_history import get_chat, set_active_chat
        chat_session = get_chat(request.chat_id)
        if not chat_session:
            chat_session = get_active_chat()
    else:
        chat_session = get_active_chat()

    chat_id = chat_session["id"]

    # ── Check if this is the first message (for auto-naming) ───────────
    existing = get_messages(chat_id, limit=1)
    is_first = len(existing) == 0

    # ── Build memory context ───────────────────────────────────────────
    memory_context = ""
    if request.use_memory:
        memory_context = build_memory_context()

    # ── Build system prompt ────────────────────────────────────────────
    system = request.system_prompt or build_system_prompt(bot_name, memory_context)

    # ── Build message list ─────────────────────────────────────────────
    messages = [{"role": "system", "content": system}]

    # Load history from this chat session
    recent = get_recent_messages_for_context(chat_id, limit=20)
    messages.extend(recent)
    messages.append({"role": "user", "content": request.message})

    # ── Call Ollama ────────────────────────────────────────────────────
    reply = ollama.chat(messages, model=request.model)

    # ── Save messages to chat session ──────────────────────────────────
    add_message(chat_id, "user",      request.message)
    add_message(chat_id, "assistant", reply)

    # ── Auto-name on first message ─────────────────────────────────────
    if is_first:
        auto_name_chat(chat_id, request.message)

    # ── Extract long-term facts in background ──────────────────────────
    if request.use_memory:
        import threading
        threading.Thread(
            target=extract_and_save_facts,
            args=(request.message, reply),
            daemon=True
        ).start()

    return ChatResponse(
        reply=reply,
        model_used=request.model or ollama.model,
        chat_id=chat_id,
    )


@router.get("/health")
async def health_check():
    is_up  = ollama.is_running()
    models = ollama.list_models() if is_up else []
    return {
        "ollama_running":   is_up,
        "current_model":    ollama.model,
        "available_models": models,
    }