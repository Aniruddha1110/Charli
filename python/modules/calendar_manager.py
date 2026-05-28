# calendar_manager.py — Calendar events CRUD using SQLite

from database import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)


def create_event(
    title: str,
    start_time: str,
    end_time: str = None,
    description: str = "",
    location: str = ""
) -> dict:
    """Create a new calendar event."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO calendar_events
                (title, start_time, end_time, description, location)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, start_time, end_time, description, location)
        )
        event_id = cursor.lastrowid
        logger.info(f"Event created: [{event_id}] {title} at {start_time}")
        return get_event(event_id)


def get_event(event_id: int) -> dict | None:
    """Get a single event by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM calendar_events WHERE id = ?", (event_id,)
        ).fetchone()
        return dict(row) if row else None


def get_events_for_month(year: int, month: int) -> list[dict]:
    """Get all events for a given month."""
    # Format: YYYY-MM
    month_str = f"{year}-{month:02d}"
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM calendar_events
            WHERE start_time LIKE ?
            ORDER BY start_time ASC
            """,
            (f"{month_str}%",)
        ).fetchall()
        return [dict(r) for r in rows]


def get_events_for_day(date: str) -> list[dict]:
    """
    Get all events for a specific day.
    date format: YYYY-MM-DD
    """
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM calendar_events
            WHERE start_time LIKE ?
            ORDER BY start_time ASC
            """,
            (f"{date}%",)
        ).fetchall()
        return [dict(r) for r in rows]


def get_upcoming_events(limit: int = 5) -> list[dict]:
    """Get next N upcoming events from today."""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM calendar_events
            WHERE start_time >= ?
            ORDER BY start_time ASC
            LIMIT ?
            """,
            (today, limit)
        ).fetchall()
        return [dict(r) for r in rows]


def update_event(
    event_id: int,
    title: str = None,
    start_time: str = None,
    end_time: str = None,
    description: str = None,
    location: str = None
) -> dict | None:
    """Update event fields."""
    event = get_event(event_id)
    if not event:
        return None

    new_title       = title       if title       is not None else event["title"]
    new_start       = start_time  if start_time  is not None else event["start_time"]
    new_end         = end_time    if end_time     is not None else event["end_time"]
    new_description = description if description is not None else event["description"]
    new_location    = location    if location    is not None else event["location"]

    with get_connection() as conn:
        conn.execute(
            """
            UPDATE calendar_events
            SET title = ?, start_time = ?, end_time = ?,
                description = ?, location = ?
            WHERE id = ?
            """,
            (new_title, new_start, new_end,
             new_description, new_location, event_id)
        )
        logger.info(f"Event updated: [{event_id}]")
        return get_event(event_id)


def delete_event(event_id: int) -> bool:
    """Delete an event by ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM calendar_events WHERE id = ?", (event_id,)
        )
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Event deleted: [{event_id}]")
        return deleted