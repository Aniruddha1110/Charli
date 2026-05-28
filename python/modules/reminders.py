# reminders.py — Time-based reminders with desktop notifications

import threading
import time
import schedule
from datetime import datetime, timedelta
from plyer import notification
from database import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Global scheduler thread ────────────────────────────────────────────────
_scheduler_running = False
_scheduler_thread  = None


# ── CRUD ───────────────────────────────────────────────────────────────────

def create_reminder(title: str, remind_at: str, notes: str = "") -> dict:
    """
    Create a new reminder.

    Args:
        title:     What to remind the user about
        remind_at: ISO datetime string e.g. "2026-05-24T18:00:00"
        notes:     Optional extra details

    Returns:
        Created reminder dict
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO reminders (title, remind_at)
            VALUES (?, ?)
            """,
            (title, remind_at)
        )
        reminder_id = cursor.lastrowid
        logger.info(f"Reminder created: [{reminder_id}] '{title}' at {remind_at}")
        return get_reminder(reminder_id)


def get_reminder(reminder_id: int) -> dict | None:
    """Get a single reminder by ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM reminders WHERE id = ?", (reminder_id,)
        ).fetchone()
        return dict(row) if row else None


def get_all_reminders(include_sent: bool = False) -> list[dict]:
    """Get all reminders, optionally including already-sent ones."""
    with get_connection() as conn:
        if include_sent:
            rows = conn.execute(
                "SELECT * FROM reminders ORDER BY remind_at ASC"
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM reminders
                WHERE is_sent = 0
                ORDER BY remind_at ASC
                """
            ).fetchall()
    return [dict(r) for r in rows]


def get_pending_reminders() -> list[dict]:
    """Get reminders that are due but not yet sent."""
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM reminders
            WHERE is_sent = 0 AND remind_at <= ?
            ORDER BY remind_at ASC
            """,
            (now,)
        ).fetchall()
    return [dict(r) for r in rows]


def mark_sent(reminder_id: int):
    """Mark a reminder as sent."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE reminders SET is_sent = 1 WHERE id = ?",
            (reminder_id,)
        )
    logger.info(f"Reminder marked sent: [{reminder_id}]")


def delete_reminder(reminder_id: int) -> bool:
    """Delete a reminder."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM reminders WHERE id = ?", (reminder_id,)
        )
        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Reminder deleted: [{reminder_id}]")
        return deleted


# ── Natural language time parsing ──────────────────────────────────────────

def parse_reminder_time(text: str) -> dict:
    """
    Use Ollama to extract reminder title and time from natural language.

    Args:
        text: Natural language like "remind me to call mom at 6pm"

    Returns:
        Dict with title and remind_at (ISO string)
    """
    from ai.ollama_client import ollama
    import json
    import re

    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M")

    prompt = f"""Extract reminder details from this text.
Current date and time: {now_str}

User said: "{text}"

Return ONLY valid JSON with these fields:
- title: what to remind about (string)
- remind_at: exact datetime in ISO format YYYY-MM-DDTHH:MM:SS

Time interpretation rules:
- "at 6pm" → today at 18:00:00
- "at 6am" → today at 06:00:00
- "in 30 minutes" → current time + 30 minutes
- "in 2 hours" → current time + 2 hours
- "tomorrow at 9am" → tomorrow at 09:00:00
- "tomorrow morning" → tomorrow at 08:00:00
- "tonight" → today at 20:00:00
- "this evening" → today at 18:00:00

JSON:"""

    try:
        response = ollama.prompt(prompt)
        match    = re.search(r'\{{.*\}}', response, re.DOTALL)
        if match:
            result = json.loads(match.group())
            logger.info(f"Parsed reminder: {result}")
            return result
    except Exception as e:
        logger.error(f"Time parsing failed: {e}")

    # Fallback — remind in 1 hour
    fallback_time = (now + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
    return {
        "title":     text,
        "remind_at": fallback_time,
    }


# ── Desktop notification ───────────────────────────────────────────────────

def fire_reminder(reminder: dict):
    """
    Fire a reminder — show desktop notification and speak it.
    """
    title = reminder["title"]
    logger.info(f"Firing reminder: '{title}'")

    # Desktop notification
    try:
        notification.notify(
            title   = "⏰ Reminder",
            message = title,
            app_name= "Charli",
            timeout = 10,
        )
    except Exception as e:
        logger.warning(f"Desktop notification failed: {e}")

    # Speak it aloud
    try:
        from voice.pyttsx3_tts import tts
        tts.speak_async(f"Reminder: {title}")
    except Exception as e:
        logger.warning(f"TTS reminder failed: {e}")

    # Mark as sent
    mark_sent(reminder["id"])


# ── Background scheduler ───────────────────────────────────────────────────

def check_reminders():
    """Check for due reminders and fire them."""
    pending = get_pending_reminders()
    for reminder in pending:
        fire_reminder(reminder)


def start_reminder_scheduler():
    """
    Start the background thread that checks for due reminders every 30 seconds.
    Call this once at app startup.
    """
    global _scheduler_running, _scheduler_thread

    if _scheduler_running:
        logger.info("Reminder scheduler already running.")
        return

    _scheduler_running = True

    # Check every 30 seconds
    schedule.every(30).seconds.do(check_reminders)

    def run_scheduler():
        logger.info("Reminder scheduler started.")
        while _scheduler_running:
            schedule.run_pending()
            time.sleep(5)
        logger.info("Reminder scheduler stopped.")

    _scheduler_thread = threading.Thread(
        target=run_scheduler,
        daemon=True,
        name="ReminderScheduler"
    )
    _scheduler_thread.start()


def stop_reminder_scheduler():
    """Stop the background scheduler."""
    global _scheduler_running
    _scheduler_running = False
    logger.info("Reminder scheduler stopping...")