# whisper_stt.py — Mic → Text with automatic language detection
# Whisper auto-detects Hindi, Bengali, Odia, French, English etc.

import whisper
import sounddevice as sd
import numpy as np
import tempfile
import os
import scipy.io.wavfile as wav
from config import WHISPER_MODEL
from utils.logger import get_logger

logger = get_logger(__name__)

# Supported languages — Whisper language codes
SUPPORTED_LANGUAGES = {
    "english":  "en",
    "hindi":    "hi",
    "bengali":  "bn",
    "odia":     "or",
    "french":   "fr",
}


class WhisperSTT:
    def __init__(self, model_name: str = WHISPER_MODEL):
        logger.info(f"Loading Whisper model: {model_name}...")
        self.model       = whisper.load_model(model_name)
        self.sample_rate = 16000
        logger.info("Whisper ready — multilingual mode enabled.")

    def listen(
        self,
        silence_threshold: float = 0.05,
        silence_duration:  float = 2.0,
        max_duration:      float = 30.0,
        min_duration:      float = 1.0,
        language:          str   = None,   # None = auto-detect
    ) -> dict:
        """
        Record from mic until silence, then transcribe.
        Auto-detects language unless specified.

        Returns:
            Dict with 'text', 'language', 'language_code'
        """
        logger.info("Listening... (multilingual, auto-detect)")

        chunk_size           = int(self.sample_rate * 0.1)
        max_chunks           = int(max_duration / 0.1)
        min_chunks           = int(min_duration / 0.1)
        silent_chunks_needed = int(silence_duration / 0.1)

        recorded         = []
        silent_count     = 0
        total_chunks     = 0
        speaking_started = False

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=chunk_size,
            device=1,
        ) as stream:
            while total_chunks < max_chunks:
                chunk, _ = stream.read(chunk_size)
                recorded.append(chunk.copy())
                total_chunks += 1

                rms = float(np.sqrt(np.mean(chunk ** 2)))

                if rms > silence_threshold:
                    speaking_started = True
                    silent_count     = 0
                else:
                    if speaking_started and total_chunks > min_chunks:
                        silent_count += 1
                        if silent_count >= silent_chunks_needed:
                            logger.info("Silence detected — stopping.")
                            break

        if not recorded:
            return {"text": "", "language": "english", "language_code": "en"}

        audio = np.concatenate(recorded, axis=0)
        return self._transcribe(audio, language)

    def _transcribe(self, audio: np.ndarray, language: str = None) -> dict:
        """Transcribe audio, auto-detecting language if not specified."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            audio_int16 = (audio * 32767).astype(np.int16)
            wav.write(tmp_path, self.sample_rate, audio_int16)

            logger.debug("Transcribing (auto-detect language)...")

            # Transcribe with language detection
            result = self.model.transcribe(
                tmp_path,
                language=language,   # None = auto-detect
                fp16=False,
                task="transcribe",   # keep original language
            )

            text          = result["text"].strip()
            detected_lang = result.get("language", "en")

            # Map Whisper code to friendly name
            lang_names = {v: k for k, v in SUPPORTED_LANGUAGES.items()}
            lang_name  = lang_names.get(detected_lang, detected_lang)

            logger.info(f"Heard [{detected_lang}]: '{text}'")
            return {
                "text":          text,
                "language":      lang_name,
                "language_code": detected_lang,
            }

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {"text": "", "language": "english", "language_code": "en"}

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def transcribe_file(self, file_path: str, language: str = None) -> dict:
        """Transcribe an audio file directly."""
        try:
            result = self.model.transcribe(
                file_path,
                language=language,
                fp16=False,
            )
            return {
                "text":          result["text"].strip(),
                "language":      result.get("language", "en"),
                "language_code": result.get("language", "en"),
            }
        except Exception as e:
            logger.error(f"File transcription failed: {e}")
            return {"text": "", "language": "en", "language_code": "en"}


# ── Singleton ──────────────────────────────────────────────────────────────
stt = WhisperSTT()