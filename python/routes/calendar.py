# routes/calendar.py — Calendar CRUD endpoints

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from modules.calendar_manager import (
    create_event, get_event, get_events_for_month,
    get_events_for_day, get_upcoming_events,
    update_event, delete_event
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/calendar", tags=["Calendar"])


# ── Models ─────────────────────────────────────────────────────────────────

class EventCreate(BaseModel):
    title:       str
    start_time:  str            # ISO format: 2026-05-24T14:00
    end_time:    Optional[str] = None
    description: Optional[str] = ""
    location:    Optional[str] = ""

class EventUpdate(BaseModel):
    title:       Optional[str] = None
    start_time:  Optional[str] = None
    end_time:    Optional[str] = None
    description: Optional[str] = None
    location:    Optional[str] = None


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/")
async def create(event: EventCreate):
    """Create a new calendar event."""
    return create_event(
        title=event.title,
        start_time=event.start_time,
        end_time=event.end_time,
        description=event.description,
        location=event.location,
    )

@router.get("/month")
async def get_month(year: int, month: int):
    """
    Get all events for a month.
    GET /calendar/month?year=2026&month=5
    """
    return get_events_for_month(year, month)

@router.get("/day")
async def get_day(date: str):
    """
    Get all events for a specific day.
    GET /calendar/day?date=2026-05-24
    """
    return get_events_for_day(date)

@router.get("/upcoming")
async def upcoming(limit: int = 5):
    """Get next N upcoming events."""
    return get_upcoming_events(limit)

@router.get("/{event_id}")
async def get_one(event_id: int):
    """Get a single event."""
    event = get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.patch("/{event_id}")
async def update(event_id: int, data: EventUpdate):
    """Update an event."""
    event = update_event(event_id, **data.model_dump(exclude_none=True))
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.delete("/{event_id}")
async def delete(event_id: int):
    """Delete an event."""
    success = delete_event(event_id)
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"deleted": True, "id": event_id}