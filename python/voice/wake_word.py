# wake_word.py — Always-on wake word detection
# Listens in background, activates Charli when wake phrase is detected.
# Uses OpenWakeWord — fully local, no API key needed.

import threading
import time
import numpy as np
import sounddevice as sd
from utils.logger import get_logger

logger = get_logger(__name__)

# ── State ──────────────────────────────────────────────────────────────────
_listening         = False
_listener_thread   = None
_on_wake_callbacks = []   # Functions to call when wake word detected


def add_wake_callback(fn):
    """Register a function to call when wake word is detected."""
    _on_wake_callbacks.append(fn)


def remove_wake_callback(fn):
    """Remove a registered callback."""
    if fn in _on_wake_callbacks:
        _on_wake_callbacks.remove(fn)


def _fire_callbacks():
    """Call all registered wake word callbacks."""
    for fn in _on_wake_callbacks:
        try:
            fn()
        except Exception as e:
            logger.error(f"Wake callback error: {e}")


# ── Wake word detector ─────────────────────────────────────────────────────

class WakeWordDetector:
    """
    Lightweight always-on wake word detector.
    Uses OpenWakeWord with hey_jarvis model (closest to 'Hey Charli').
    Runs in a background thread — very low CPU usage.
    """

    def __init__(
        self,
        model_name:  str   = "hey_jarvis",
        threshold:   float = 0.5,
        sample_rate: int   = 16000,
        chunk_size:  int   = 1280,
        device:      int   = 1,
    ):
        self.model_name  = model_name
        self.threshold   = threshold
        self.sample_rate = sample_rate
        self.chunk_size  = chunk_size
        self.device      = device
        self.model       = None
        self._running    = False
        self._thread     = None
        self._cooldown   = False   # Prevents rapid re-triggering

    def load(self) -> bool:
        """Load the OpenWakeWord model. Returns True if successful."""
        try:
            from openwakeword.model import Model
            self.model = Model(
                wakeword_models=[self.model_name],
                inference_framework="onnx",
            )
            logger.info(f"Wake word model loaded: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to load wake word model: {e}")
            return False

    def start(self):
        """Start listening in background thread."""
        if self._running:
            logger.info("Wake word detector already running.")
            return

        if not self.model:
            if not self.load():
                logger.error("Cannot start — model not loaded.")
                return

        self._running = True
        self._thread  = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="WakeWordDetector",
        )
        self._thread.start()
        logger.info("Wake word detector started — listening for wake phrase.")

    def stop(self):
        """Stop the background listener."""
        self._running = False
        logger.info("Wake word detector stopped.")

    def set_threshold(self, threshold: float):
        """Adjust detection sensitivity (0.0 - 1.0). Lower = more sensitive."""
        self.threshold = max(0.1, min(0.99, threshold))
        logger.info(f"Wake word threshold set to {self.threshold}")

    def _listen_loop(self):
        """Main listening loop — runs in background thread."""
        logger.info(f"Listening for wake word on device {self.device}...")

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=self.chunk_size,
                device=self.device,
            ) as stream:
                while self._running:
                    try:
                        chunk, _ = stream.read(self.chunk_size)
                        audio    = chunk.flatten()

                        # Run wake word prediction
                        prediction = self.model.predict(audio)

                        # Check all models in prediction
                        for model_key, score in prediction.items():
                            if score >= self.threshold and not self._cooldown:
                                logger.info(
                                    f"Wake word detected! "
                                    f"Model: {model_key}, Score: {score:.3f}"
                                )
                                self._trigger()
                                break

                    except Exception as e:
                        if self._running:
                            logger.debug(f"Listen loop error: {e}")
                        time.sleep(0.1)

        except Exception as e:
            logger.error(f"Wake word stream error: {e}")
            self._running = False

    def _trigger(self):
        """Handle a wake word detection event."""
        # Set cooldown to prevent double-triggering
        self._cooldown = True

        # Fire all registered callbacks
        _fire_callbacks()

        # Release cooldown after 3 seconds
        def release_cooldown():
            time.sleep(3)
            self._cooldown = False

        threading.Thread(target=release_cooldown, daemon=True).start()


# ── Module-level singleton ─────────────────────────────────────────────────
detector = WakeWordDetector()


# ── Convenience functions ──────────────────────────────────────────────────

def start_wake_word(threshold: float = 0.5):
    """Start the wake word detector with given threshold."""
    detector.set_threshold(threshold)
    detector.start()


def stop_wake_word():
    """Stop the wake word detector."""
    detector.stop()


def is_running() -> bool:
    """Check if wake word detector is running."""
    return detector._running