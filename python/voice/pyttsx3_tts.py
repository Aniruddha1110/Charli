# pyttsx3_tts.py — Text to Speech with multilingual support
# Uses English voice but handles transliteration for Indian languages.

import pyttsx3
import threading
import re
from config import TTS_RATE, TTS_VOLUME
from utils.logger import get_logger

logger = get_logger(__name__)


def _get_preferred_voice_id():
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.stop()
        del engine
        if not voices:
            return None
        for v in voices:
            if "zira" in v.name.lower():
                return v.id
        return voices[0].id
    except Exception:
        return None

_PREFERRED_VOICE_ID = _get_preferred_voice_id()


class PyttsTTS:
    def __init__(self):
        self._lock = threading.Lock()
        logger.info(f"TTS ready — voice: {_PREFERRED_VOICE_ID}, rate: {TTS_RATE}")

    def speak(self, text: str, language_code: str = "en") -> None:
        """
        Speak text aloud.
        For non-English text, converts to speakable Roman form.
        """
        if not text or not text.strip():
            return

        # Prepare text for English TTS
        speakable = self._prepare_for_tts(text, language_code)
        logger.info(f"Speaking [{language_code}]: '{speakable[:60]}'")

        with self._lock:
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate",   TTS_RATE)
                engine.setProperty("volume", TTS_VOLUME)
                if _PREFERRED_VOICE_ID:
                    engine.setProperty("voice", _PREFERRED_VOICE_ID)
                engine.say(speakable)
                engine.runAndWait()
                engine.stop()
                del engine
            except Exception as e:
                logger.error(f"TTS error: {e}")

    def speak_async(self, text: str, language_code: str = "en") -> None:
        """Speak in background thread."""
        thread = threading.Thread(
            target=self.speak,
            args=(text, language_code),
            daemon=True
        )
        thread.start()

    def _prepare_for_tts(self, text: str, language_code: str) -> str:
        """
        Prepare text for English TTS engine.
        - Remove markdown
        - For non-English scripts, extract any Roman parts
          or use a simplified transliteration
        """
        # Remove markdown
        text = self._clean_markdown(text)

        # If text contains non-Latin scripts and we only have English TTS,
        # we need to make it speakable
        if language_code in ("hi", "bn", "or") and self._has_non_latin(text):
            # Extract Roman/English words that can be spoken
            # Keep numbers, English words, and basic punctuation
            roman_parts = re.findall(
                r'[a-zA-Z0-9\s.,!?\'"-]+', text
            )
            roman_text = " ".join(roman_parts).strip()

            if roman_text:
                return roman_text
            else:
                # Fallback — say language name + truncated original
                lang_names = {
                    "hi": "Hindi text",
                    "bn": "Bengali text",
                    "or": "Odia text",
                    "fr": "French",
                }
                return f"{lang_names.get(language_code, 'text')}: {text[:100]}"

        return text

    def _has_non_latin(self, text: str) -> bool:
        """Check if text contains non-Latin characters."""
        for char in text:
            if ord(char) > 127:
                return True
        return False

    def _clean_markdown(self, text: str) -> str:
        """Strip markdown for natural speech."""
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*",     r"\1", text)
        text = re.sub(r"`(.+?)`",       r"\1", text)
        text = re.sub(r"```[\s\S]*?```", "",   text)
        text = re.sub(r"#+\s",          "",    text)
        text = re.sub(r"\n+",           " ",   text)
        return text.strip()

    def list_voices(self) -> list[dict]:
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            engine.stop()
            del engine
            return [{"id": v.id, "name": v.name} for v in voices]
        except Exception:
            return []


# ── Singleton ──────────────────────────────────────────────────────────────
tts = PyttsTTS()