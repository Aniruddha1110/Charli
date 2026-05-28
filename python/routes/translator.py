# routes/translator.py — Translation API endpoints

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from modules.translator import translate, detect_language, LANGUAGES, get_display_name
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/translator", tags=["Translator"])


# ── Models ─────────────────────────────────────────────────────────────────

class TranslateRequest(BaseModel):
    text:        str
    source_lang: str
    target_lang: str
    formal:      Optional[bool] = True


class DetectRequest(BaseModel):
    text: str


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/")
async def translate_text(request: TranslateRequest):
    """Translate text between any two supported languages."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if request.source_lang not in LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown source language: {request.source_lang}"
        )

    if request.target_lang not in LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown target language: {request.target_lang}"
        )

    result = translate(
        text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
        formal=request.formal,
    )

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Translation failed"))

    return result


@router.post("/detect")
async def detect(request: DetectRequest):
    """Detect the language of input text."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    return detect_language(request.text)


@router.get("/languages")
async def get_languages(search: Optional[str] = None):
    """
    Return all supported languages.
    Optional ?search= param filters by name.
    """
    langs = [
        {
            "key":  key,
            "name": name,
            "code": code,
        }
        for key, (name, code) in sorted(LANGUAGES.items(), key=lambda x: x[1][0])
    ]

    if search:
        q = search.lower()
        langs = [l for l in langs if q in l["name"].lower() or q in l["key"]]

    return {"languages": langs, "count": len(langs)}


@router.post("/speak")
async def speak_translation(request: TranslateRequest):
    """Translate text and speak the result aloud."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    result = translate(
        text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang,
        formal=request.formal,
    )

    if result.get("success"):
        from voice.pyttsx3_tts import tts
        tts.speak_async(result["translation"], "en")

    return result