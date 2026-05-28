# database.py — SQLite initialisation and connection management
# Run this once at startup; safe to run repeatedly (CREATE IF NOT EXISTS).

import sqlite3
from contextlib import contextmanager
from config import DB_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


def init_db() -> None:
    """
    Create all Charli tables if they don't exist.
    Safe to call on every startup — idempotent.
    """
    logger.info(f"Initialising database at: {DB_PATH}")
    with get_connection() as conn:
        cursor = conn.cursor()

        # ── Tasks ──────────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT,
                status      TEXT    DEFAULT 'pending',   -- pending | done
                priority    TEXT    DEFAULT 'normal',    -- low | normal | high
                due_date    TEXT,                        -- ISO 8601 string
                created_at  TEXT    DEFAULT (datetime('now')),
                updated_at  TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── Notes ──────────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT,
                content     TEXT    NOT NULL,
                tags        TEXT,                        -- comma-separated
                created_at  TEXT    DEFAULT (datetime('now')),
                updated_at  TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── Reminders ──────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                remind_at   TEXT    NOT NULL,            -- ISO 8601 datetime
                is_sent     INTEGER DEFAULT 0,           -- 0 = pending, 1 = fired
                created_at  TEXT    DEFAULT (datetime('now'))
            )
        """)

        # ── Calendar Events ────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT    NOT NULL,
                description TEXT,
                start_time  TEXT    NOT NULL,            -- ISO 8601
                end_time    TEXT,
                location    TEXT,
                created_at  TEXT    DEFAULT (datetime('now'))
            )
        """)
        
        # ── Chats ──────────────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    DEFAULT 'New Chat',
                created_at TEXT    DEFAULT (datetime('now')),
                updated_at TEXT    DEFAULT (datetime('now')),
                is_active  INTEGER DEFAULT 0
            )
        """)

        # ── Chat Messages ──────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id    INTEGER NOT NULL,
                role       TEXT    NOT NULL,
                content    TEXT    NOT NULL,
                created_at TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
        """)

        # ── Settings ───────────────────────────────────────────────────────
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key         TEXT    PRIMARY KEY,
                value       TEXT    NOT NULL,
                updated_at  TEXT    DEFAULT (datetime('now'))
            )
        """)

        # Seed default settings if they don't exist
        defaults = [
            ("bot_name", "Charli"),
            ("theme",        "dark"),
            ("llm_model",    "llama3.2"),
            ("tts_rate",     "175"),
            ("tts_volume",   "1.0"),
            ("wake_word",    "hey charli"),
            ("wake_word_enabled", "false"),
            ("startup",      "false"),
            ("user_name",    ""),
            ("user_gender",  ""),
            ("user_photo",   ""),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            defaults
        )

        conn.commit()
        logger.info("Database initialised successfully.")


@contextmanager
def get_connection():
    """
    Context manager for SQLite connections.
    Automatically commits on success, rolls back on exception.

    Usage:
        with get_connection() as conn:
            conn.execute("SELECT ...")
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # Rows accessible as dicts
    conn.execute("PRAGMA journal_mode=WAL")   # Better concurrency
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"DB transaction rolled back: {e}")
        raise
    finally:
        conn.close()