# routes/wake_word.py — Wake word control endpoints

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from voice.wake_word import (
    start_wake_word, stop_wake_word,
    is_running, detector
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/wake", tags=["Wake Word"])


class WakeConfig(BaseModel):
    enabled:   bool
    threshold: Optional[float] = 0.5


@router.post("/")
async def configure_wake(config: WakeConfig):
    """Enable or disable wake word detection."""
    if config.enabled:
        start_wake_word(threshold=config.threshold)
        logger.info(f"Wake word enabled — threshold: {config.threshold}")
        return {"enabled": True, "threshold": config.threshold}
    else:
        stop_wake_word()
        logger.info("Wake word disabled.")
        return {"enabled": False}


@router.get("/status")
async def get_status():
    """Get current wake word detector status."""
    return {
        "running":   is_running(),
        "threshold": detector.threshold,
        "model":     detector.model_name,
    }


@router.post("/threshold")
async def set_threshold(threshold: float):
    """Update detection sensitivity."""
    detector.set_threshold(threshold)
    return {"threshold": detector.threshold}