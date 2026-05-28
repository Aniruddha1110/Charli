# chat_history.py — Chat session management
# Each conversation is a "chat" with messages, a name, and persistence.

from database import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Chat CRUD ──────────────────────────────────────────────────────────────

def create_chat(name: str = "New Chat") -> dict:
    """Create a new chat session."""
    with get_connection() as conn:
        # Deactivate all other chats
        conn.execute("UPDATE chats SET is_active = 0")
        cursor = conn.execute(
            """
            INSERT INTO chats (name, is_active)
            VALUES (?, 1)
            """,
            (name,)
        )
        chat_id = cursor.lastrowid
        logger.info(f"Chat created: [{chat_id}] {name}")
        return get_chat(chat_id)


def get_chat(chat_id: int) -> dict | None:
    """Get a single chat by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM chats WHERE id = ?", (chat_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_chats() -> list[dict]:
    """Get all chats ordered by most recently updated."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.*,
                   COUNT(m.id) as message_count,
                   MAX(m.created_at) as last_message_at
            FROM chats c
            LEFT JOIN chat_messages m ON m.chat_id = c.id
            GROUP BY c.id
            ORDER BY c.updated_at DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def get_active_chat() -> dict | None:
    """Get the currently active chat, or create one if none exists."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM chats WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        if row:
            return dict(row)

    # No active chat — create one
    return create_chat("New Chat")


def set_active_chat(chat_id: int) -> dict | None:
    """Set a chat as the active one."""
    with get_connection() as conn:
        conn.execute("UPDATE chats SET is_active = 0")
        conn.execute(
            "UPDATE chats SET is_active = 1 WHERE id = ?", (chat_id,)
        )
    logger.info(f"Active chat set: [{chat_id}]")
    return get_chat(chat_id)


def rename_chat(chat_id: int, name: str) -> dict | None:
    """Rename a chat."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE chats
            SET name = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (name, chat_id)
        )
    logger.info(f"Chat renamed: [{chat_id}] → {name}")
    return get_chat(chat_id)


def delete_chat(chat_id: int) -> bool:
    """Delete a chat and all its messages."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM chats WHERE id = ?", (chat_id,)
        )
        deleted = cursor.rowcount > 0

    if deleted:
        logger.info(f"Chat deleted: [{chat_id}]")
        # If we deleted the active chat, activate the most recent one
        with get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM chats ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
            if row:
                set_active_chat(row["id"])

    return deleted


def touch_chat(chat_id: int):
    """Update the chat's updated_at timestamp."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE chats SET updated_at = datetime('now') WHERE id = ?",
            (chat_id,)
        )


# ── Message CRUD ───────────────────────────────────────────────────────────

def add_message(chat_id: int, role: str, content: str) -> dict:
    """Add a message to a chat."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO chat_messages (chat_id, role, content)
            VALUES (?, ?, ?)
            """,
            (chat_id, role, content)
        )
        msg_id = cursor.lastrowid

    touch_chat(chat_id)
    return {"id": msg_id, "chat_id": chat_id, "role": role, "content": content}


def get_messages(chat_id: int, limit: int = 100) -> list[dict]:
    """Get all messages for a chat."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM chat_messages
            WHERE chat_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (chat_id, limit)
        ).fetchall()
    return [dict(r) for r in rows]


def get_recent_messages_for_context(chat_id: int, limit: int = 20) -> list[dict]:
    """Get recent messages formatted for Ollama context."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM chat_messages
            WHERE chat_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (chat_id, limit)
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def clear_messages(chat_id: int):
    """Clear all messages in a chat."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM chat_messages WHERE chat_id = ?", (chat_id,)
        )
    touch_chat(chat_id)


# ── Auto-naming ────────────────────────────────────────────────────────────

def auto_name_chat(chat_id: int, first_message: str):
    """
    Use Ollama to generate a short name for the chat
    based on the first user message.
    Runs in background thread so it doesn't block the response.
    """
    import threading

    def _name():
        try:
            from ai.ollama_client import ollama
            prompt = f"""Generate a very short chat title (3-5 words max) for a conversation that starts with:
"{first_message}"

Rules:
- 3 to 5 words maximum
- No punctuation at the end
- Title case
- Be specific and descriptive
- Return ONLY the title, nothing else

Title:"""
            name = ollama.prompt(prompt).strip().strip('"').strip("'")
            # Truncate if too long
            if len(name) > 40:
                name = name[:40]
            if name:
                rename_chat(chat_id, name)
                logger.info(f"Auto-named chat [{chat_id}]: {name}")
        except Exception as e:
            logger.error(f"Auto-naming failed: {e}")

    threading.Thread(target=_name, daemon=True).start()