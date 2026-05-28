# routes/notes.py — Notes CRUD endpoints

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from modules.notes import (
    create_note, get_all_notes, get_note,
    delete_note, update_note, search_notes
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/notes", tags=["Notes"])


# ── Models ─────────────────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    content: str
    title:   Optional[str] = ""
    tags:    Optional[str] = ""   # comma-separated: "work,ideas,python"

class NoteUpdate(BaseModel):
    title:   Optional[str] = None
    content: Optional[str] = None
    tags:    Optional[str] = None


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/")
async def create(note: NoteCreate):
    """Create a new note."""
    return create_note(
        content=note.content,
        title=note.title,
        tags=note.tags
    )

@router.get("/")
async def get_all():
    """Get all notes."""
    return get_all_notes()

@router.get("/search")
async def search(q: str):
    """Search notes by title, content or tags."""
    return search_notes(q)

@router.get("/{note_id}")
async def get_one(note_id: int):
    """Get a single note by ID."""
    note = get_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.patch("/{note_id}")
async def update(note_id: int, data: NoteUpdate):
    """Update a note."""
    note = update_note(note_id, **data.model_dump(exclude_none=True))
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.delete("/{note_id}")
async def delete(note_id: int):
    """Delete a note."""
    success = delete_note(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"deleted": True, "id": note_id}