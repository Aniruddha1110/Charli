# routes/reminders.py — Reminder CRUD endpoints

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from modules.reminders import (
    create_reminder, get_reminder, get_all_reminders,
    delete_reminder, parse_reminder_time
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/reminders", tags=["Reminders"])


# ── Models ─────────────────────────────────────────────────────────────────

class ReminderCreate(BaseModel):
    title:     str
    remind_at: str              # ISO datetime: 2026-05-24T18:00:00
    notes:     Optional[str] = ""

class ReminderNatural(BaseModel):
    text: str                   # "remind me to call mom at 6pm"


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("/")
async def get_all(include_sent: bool = False):
    """Get all reminders."""
    return get_all_reminders(include_sent=include_sent)


@router.post("/")
async def create(reminder: ReminderCreate):
    """Create a reminder with explicit datetime."""
    result = create_reminder(
        title=reminder.title,
        remind_at=reminder.remind_at,
        notes=reminder.notes,
    )
    return result


@router.post("/natural")
async def create_natural(request: ReminderNatural):
    """
    Create a reminder from natural language.
    Ollama extracts the title and time automatically.

    Body: { "text": "remind me to call mom at 6pm" }
    """
    logger.info(f"Natural reminder: '{request.text}'")

    parsed = parse_reminder_time(request.text)

    if not parsed.get("title") or not parsed.get("remind_at"):
        raise HTTPException(
            status_code=400,
            detail="Could not extract reminder details from text."
        )

    result = create_reminder(
        title=parsed["title"],
        remind_at=parsed["remind_at"],
    )

    return {
        "reminder": result,
        "parsed":   parsed,
    }


@router.get("/{reminder_id}")
async def get_one(reminder_id: int):
    """Get a single reminder."""
    reminder = get_reminder(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder


@router.delete("/{reminder_id}")
async def delete(reminder_id: int):
    """Delete a reminder."""
    success = delete_reminder(reminder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"deleted": True, "id": reminder_id}