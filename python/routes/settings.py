# routes/settings.py — Settings endpoints
# Reads and writes settings from SQLite settings table.

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from database import get_connection
from utils.logger import get_logger
import subprocess
import sys
import os

logger = get_logger(__name__)
router = APIRouter(prefix="/settings", tags=["Settings"])


# ── Helpers ────────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

def set_setting(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = excluded.updated_at
            """,
            (key, value)
        )

def get_all_settings() -> dict:
    with get_connection() as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
        return {r["key"]: r["value"] for r in rows}


# ── Models ─────────────────────────────────────────────────────────────────

class SettingUpdate(BaseModel):
    key:   str
    value: str

class ProfileUpdate(BaseModel):
    name:   Optional[str] = None
    gender: Optional[str] = None
    photo:  Optional[str] = None   # Base64 encoded image


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("/")
async def get_settings():
    """Get all settings."""
    return get_all_settings()

@router.post("/")
async def update_setting(data: SettingUpdate):
    """Update a single setting."""
    set_setting(data.key, data.value)
    logger.info(f"Setting updated: {data.key} = {data.value}")
    return {"key": data.key, "value": data.value}

@router.post("/profile")
async def update_profile(data: ProfileUpdate):
    """Update user profile — name, gender, photo."""
    if data.name   is not None: set_setting("user_name",   data.name)
    if data.gender is not None: set_setting("user_gender", data.gender)
    if data.photo  is not None: set_setting("user_photo",  data.photo)
    logger.info("Profile updated")
    return {"success": True}

@router.get("/models")
async def get_available_models():
    """Get all locally available Ollama models."""
    try:
        import requests
        resp = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = [m["name"] for m in resp.json().get("models", [])]
        return {"models": models}
    except Exception as e:
        logger.error(f"Could not fetch models: {e}")
        return {"models": ["llama3.2"]}

@router.get("/system")
async def get_system_info():
    """Get system info for the About section."""
    import platform
    import psutil

    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        ram         = psutil.virtual_memory()
        disk        = psutil.disk_usage("C:\\")

        return {
            "app_version":   "0.1.0",
            "platform":      platform.system(),
            "platform_ver":  platform.version()[:50],
            "python_version": sys.version[:10],
            "cpu_usage":     f"{cpu_percent}%",
            "ram_total":     f"{ram.total // (1024**3)} GB",
            "ram_used":      f"{ram.used  // (1024**3)} GB",
            "ram_percent":   f"{ram.percent}%",
            "disk_total":    f"{disk.total // (1024**3)} GB",
            "disk_free":     f"{disk.free  // (1024**3)} GB",
        }
    except Exception as e:
        logger.error(f"System info error: {e}")
        return {"app_version": "0.1.0", "error": str(e)}