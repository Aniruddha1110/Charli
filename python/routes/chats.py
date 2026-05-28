# routes/chats.py — Chat session management endpoints

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from modules.chat_history import (
    create_chat, get_chat, get_all_chats,
    get_active_chat, set_active_chat,
    rename_chat, delete_chat,
    add_message, get_messages,
    get_recent_messages_for_context,
    clear_messages, auto_name_chat
)
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chats", tags=["Chats"])


# ── Models ─────────────────────────────────────────────────────────────────

class ChatCreate(BaseModel):
    name: Optional[str] = "New Chat"

class ChatRename(BaseModel):
    name: str


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("/")
async def get_all():
    """Get all chats."""
    return get_all_chats()

@router.post("/")
async def create(data: ChatCreate):
    """Create a new chat."""
    return create_chat(data.name)

@router.get("/active")
async def get_active():
    """Get the currently active chat."""
    return get_active_chat()

@router.post("/{chat_id}/activate")
async def activate(chat_id: int):
    """Set a chat as active."""
    chat = set_active_chat(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@router.patch("/{chat_id}/rename")
async def rename(chat_id: int, data: ChatRename):
    """Rename a chat."""
    chat = rename_chat(chat_id, data.name)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat

@router.delete("/{chat_id}")
async def delete(chat_id: int):
    """Delete a chat."""
    success = delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"deleted": True, "id": chat_id}

@router.get("/{chat_id}/messages")
async def messages(chat_id: int, limit: int = 100):
    """Get messages for a chat."""
    return get_messages(chat_id, limit)

@router.delete("/{chat_id}/messages")
async def clear(chat_id: int):
    """Clear all messages in a chat."""
    clear_messages(chat_id)
    return {"cleared": True, "chat_id": chat_id}