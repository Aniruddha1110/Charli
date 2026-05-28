# routes/voice.py — Voice endpoints with intent routing

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from voice.whisper_stt import stt
from voice.pyttsx3_tts import tts
from ai.ollama_client import ollama
from ai.intent_router import classify_intent, execute_intent
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/voice", tags=["Voice"])


# ── Models ─────────────────────────────────────────────────────────────────

class SpeakRequest(BaseModel):
    text: str

class ListenResponse(BaseModel):
    text:    str
    success: bool

class VoiceChatRequest(BaseModel):
    history:       Optional[list[dict]] = []
    system_prompt: Optional[str]        = None
    use_intent:    Optional[bool]       = True   # Route through intent classifier

class VoiceChatResponse(BaseModel):
    heard:      str
    reply:      str
    intent:     Optional[str] = None
    data:       Optional[dict] = {}
    model_used: str


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/speak")
async def speak(request: SpeakRequest):
    """Make Charli speak a given text aloud."""
    tts.speak_async(request.text)
    return {"status": "speaking", "text": request.text}


@router.post("/listen", response_model=ListenResponse)
async def listen():
    """Listen to mic with auto silence detection."""
    text = stt.listen()
    return ListenResponse(text=text, success=bool(text))


@router.post("/chat", response_model=VoiceChatResponse)
async def voice_chat(request: VoiceChatRequest):
    """
    Full voice round-trip with multilingual support.
    Auto-detects spoken language via Whisper.
    """
    logger.info("Voice chat — listening (multilingual)...")

    # Step 1 — Listen + detect language
    result = stt.listen()
    heard  = result["text"]
    lang   = result["language_code"]

    logger.info(f"Detected language: {result['language']} ({lang})")

    if not heard:
        msg = "Sorry, I didn't catch that. Please try again."
        tts.speak_async(msg, "en")
        return VoiceChatResponse(
            heard="", reply=msg, intent="none",
            data={}, model_used=ollama.model
        )

    # Step 2 — Route intent
    if request.use_intent:
        intent_result = classify_intent(heard)
        intent        = intent_result.get("intent", "chat")
        params        = intent_result.get("params", {})
        if intent == "chat" and not params.get("message"):
            params["message"] = heard
        execution = execute_intent(intent, params, history=request.history)
        reply     = execution.get("response", "Done.")
        data      = execution.get("data", {})
    else:
        intent = "chat"
        from routes.chat import get_bot_name, build_system_prompt
        from ai.memory  import build_memory_context
        bot_name       = get_bot_name()
        memory_context = build_memory_context()
        system         = build_system_prompt(bot_name, memory_context)
        messages = [{"role": "system", "content": system}]
        if request.history:
            messages.extend(request.history)
        messages.append({"role": "user", "content": heard})
        reply  = ollama.chat(messages)
        data   = {}

    # Step 3 — Speak reply (pass detected language)
    tts.speak_async(reply, lang)

    return VoiceChatResponse(
        heard=heard,
        reply=reply,
        intent=intent,
        data=data,
        model_used=ollama.model
    )


@router.get("/voices")
async def list_voices():
    """Return all available TTS voices."""
    return {"voices": tts.list_voices()}