import os
import sys

# ── Paths ──────────────────────────────────────────────────────────────────

# PyInstaller fix — use exe location, not __file__
if getattr(sys, "frozen", False):
    # Running as compiled exe
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running as normal Python script
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR   = os.path.join(BASE_DIR, "data")
DB_PATH    = os.path.join(DATA_DIR, "charli.db")
MEMORY_DIR = os.path.join(DATA_DIR, "memory")
LOG_DIR    = os.path.join(DATA_DIR, "logs")

# Auto-create data directories on import
for _dir in [DATA_DIR, MEMORY_DIR, LOG_DIR]:
    os.makedirs(_dir, exist_ok=True)

# ── FastAPI Server ─────────────────────────────────────────────────────────
API_HOST = "127.0.0.1"
API_PORT = 8000

# ── Ollama ─────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL  = "http://localhost:11434"
OLLAMA_MODEL     = "llama3.2"
OLLAMA_TIMEOUT   = 60

# ── Whisper ────────────────────────────────────────────────────────────────
WHISPER_MODEL    = "base"

# ── pyttsx3 TTS ────────────────────────────────────────────────────────────
TTS_RATE         = 175
TTS_VOLUME       = 1.0

# ── LangChain Memory ───────────────────────────────────────────────────────
MEMORY_MAX_TOKENS = 2000

# ── App ────────────────────────────────────────────────────────────────────
APP_NAME   = "Charli"
DEBUG_MODE = False      # ← False for production