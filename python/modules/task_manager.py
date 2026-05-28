# task_manager.py — Tasks CRUD using SQLite

from database import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)


def create_task(title: str, description: str = "", priority: str = "normal", due_date: str = None) -> dict:
    """Create a new task. Returns the created task."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO tasks (title, description, priority, due_date)
            VALUES (?, ?, ?, ?)
            """,
            (title, description, priority, due_date)
        )
        task_id = cursor.lastrowid
        logger.info(f"Task created: [{task_id}] {title}")
        return get_task(task_id)


def get_task(task_id: int) -> dict | None:
    """Get a single task by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_tasks(status: str = None) -> list[dict]:
    """
    Get all tasks, optionally filtered by status.
    status: 'pending' | 'done' | None (all)
    """
    with get_connection() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY created_at DESC",
                (status,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]


def complete_task(task_id: int) -> dict | None:
    """Mark a task as done."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks SET status = 'done', updated_at = datetime('now')
            WHERE id = ?
            """,
            (task_id,)
        )
        logger.info(f"Task completed: [{task_id}]")
        return get_task(task_id)


def delete_task(task_id: int) -> bool:
    """Delete a task by ID. Returns True if deleted."""
    with get_connection() as conn:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Task deleted: [{task_id}]")
        return deleted


def update_task(task_id: int, title: str = None, description: str = None,
                priority: str = None, due_date: str = None) -> dict | None:
    """Update task fields. Only updates provided fields."""
    task = get_task(task_id)
    if not task:
        return None

    new_title       = title       or task["title"]
    new_description = description or task["description"]
    new_priority    = priority    or task["priority"]
    new_due_date    = due_date    or task["due_date"]

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE tasks
            SET title = ?, description = ?, priority = ?, due_date = ?,
                updated_at = datetime('now')
            WHERE id = ?
            """,
            (new_title, new_description, new_priority, new_due_date, task_id)
        )
        logger.info(f"Task updated: [{task_id}]")
        return get_task(task_id)


def search_tasks(query: str) -> list[dict]:
    """Search tasks by title or description."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM tasks
            WHERE title LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
            """,
            (f"%{query}%", f"%{query}%")
        ).fetchall()
        return [dict(r) for r in rows]