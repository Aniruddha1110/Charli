# config.py — Central configuration for Charli
# All constants live here. Change once, works everywhere.

import os

# ── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
DB_PATH     = os.path.join(DATA_DIR, "charli.db")
MEMORY_DIR  = os.path.join(DATA_DIR, "memory")
LOG_DIR     = os.path.join(DATA_DIR, "logs")

# Auto-create data directories on import
for _dir in [DATA_DIR, MEMORY_DIR, LOG_DIR]:
    os.makedirs(_dir, exist_ok=True)

# ── FastAPI Server ─────────────────────────────────────────────────────────
API_HOST = "127.0.0.1"
API_PORT = 8000

# ── Ollama ─────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL  = "http://localhost:11434"
OLLAMA_MODEL     = "llama3.2"       # Change to "mistral" etc. as needed
OLLAMA_TIMEOUT   = 60               # Seconds before request times out

# ── Whisper ────────────────────────────────────────────────────────────────
WHISPER_MODEL    = "base"           # tiny | base | small | medium | large

# ── pyttsx3 TTS ────────────────────────────────────────────────────────────
TTS_RATE         = 175              # Words per minute
TTS_VOLUME       = 1.0              # 0.0 – 1.0

# ── LangChain Memory ───────────────────────────────────────────────────────
MEMORY_MAX_TOKENS = 2000            # Max tokens kept in rolling memory

# ── App ────────────────────────────────────────────────────────────────────
APP_NAME         = "Charli"
DEBUG_MODE       = True             # Set False for production