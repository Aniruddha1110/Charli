# notes.py — Notes CRUD using SQLite

from database import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)


def create_note(content: str, title: str = "", tags: str = "") -> dict:
    """Create a new note. Returns the created note."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO notes (title, content, tags)
            VALUES (?, ?, ?)
            """,
            (title, content, tags)
        )
        note_id = cursor.lastrowid
        logger.info(f"Note created: [{note_id}] {title or content[:30]}")
        return get_note(note_id)


def get_note(note_id: int) -> dict | None:
    """Get a single note by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM notes WHERE id = ?", (note_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_notes() -> list[dict]:
    """Get all notes ordered by newest first."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM notes ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def delete_note(note_id: int) -> bool:
    """Delete a note by ID."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Note deleted: [{note_id}]")
        return deleted


def update_note(note_id: int, title: str = None,
                content: str = None, tags: str = None) -> dict | None:
    """Update note fields."""
    note = get_note(note_id)
    if not note:
        return None

    new_title   = title   if title   is not None else note["title"]
    new_content = content if content is not None else note["content"]
    new_tags    = tags    if tags    is not None else note["tags"]

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE notes
            SET title = ?, content = ?, tags = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (new_title, new_content, new_tags, note_id)
        )
        logger.info(f"Note updated: [{note_id}]")
        return get_note(note_id)


def search_notes(query: str) -> list[dict]:
    """Search notes by title, content or tags."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM notes
            WHERE title LIKE ? OR content LIKE ? OR tags LIKE ?
            ORDER BY created_at DESC
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%")
        ).fetchall()
        return [dict(r) for r in rows]