# memory.py — Persistent conversation memory using LangChain + SQLite
# Remembers conversation history and key facts across sessions.

import os
import json
from datetime import datetime
from database import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)


# ── Database setup ─────────────────────────────────────────────────────────

def init_memory_tables():
    """Create memory tables if they don't exist."""
    with get_connection() as conn:
        # Conversation history — rolling window of recent messages
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_memory (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                role       TEXT    NOT NULL,   -- user | assistant
                content    TEXT    NOT NULL,
                created_at TEXT    DEFAULT (datetime('now')),
                session_id TEXT    DEFAULT 'default'
            )
        """)

        # Long-term facts — key things Charli learned about you
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_facts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                category   TEXT    NOT NULL,   -- personal | work | preference | project
                fact       TEXT    NOT NULL,
                source     TEXT,               -- what the user said to trigger this
                created_at TEXT    DEFAULT (datetime('now')),
                updated_at TEXT    DEFAULT (datetime('now'))
            )
        """)

    logger.info("Memory tables initialised.")


# ── Conversation memory ────────────────────────────────────────────────────

def save_message(role: str, content: str, session_id: str = "default"):
    """Save a single message to conversation memory."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversation_memory (role, content, session_id)
            VALUES (?, ?, ?)
            """,
            (role, content, session_id)
        )

    # Keep only last 200 messages to avoid bloat
    _trim_conversation(session_id)


def get_recent_messages(limit: int = 20, session_id: str = "default") -> list[dict]:
    """Get the most recent N messages from memory."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM conversation_memory
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (session_id, limit)
        ).fetchall()

    # Reverse so oldest first
    messages = [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    return messages


def get_full_history(session_id: str = "default") -> list[dict]:
    """Get complete conversation history for a session."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM conversation_memory
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,)
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def clear_conversation(session_id: str = "default"):
    """Clear conversation history for a session."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM conversation_memory WHERE session_id = ?",
            (session_id,)
        )
    logger.info(f"Conversation cleared for session: {session_id}")


def _trim_conversation(session_id: str, keep: int = 200):
    """Keep only the most recent N messages."""
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM conversation_memory
            WHERE session_id = ?
            AND id NOT IN (
                SELECT id FROM conversation_memory
                WHERE session_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            )
            """,
            (session_id, session_id, keep)
        )


# ── Long-term facts ────────────────────────────────────────────────────────

def save_fact(category: str, fact: str, source: str = ""):
    """
    Save a long-term fact about the user.

    Args:
        category: personal | work | preference | project
        fact:     The fact to remember
        source:   What the user said that triggered this
    """
    with get_connection() as conn:
        # Check if similar fact exists
        existing = conn.execute(
            "SELECT id FROM memory_facts WHERE fact = ?",
            (fact,)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE memory_facts
                SET updated_at = datetime('now'), source = ?
                WHERE fact = ?
                """,
                (source, fact)
            )
        else:
            conn.execute(
                """
                INSERT INTO memory_facts (category, fact, source)
                VALUES (?, ?, ?)
                """,
                (category, fact, source)
            )

    logger.info(f"Fact saved [{category}]: {fact}")


def get_facts(category: str = None, limit: int = 20) -> list[dict]:
    """Get stored facts, optionally filtered by category."""
    with get_connection() as conn:
        if category:
            rows = conn.execute(
                """
                SELECT category, fact, created_at FROM memory_facts
                WHERE category = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (category, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT category, fact, created_at FROM memory_facts
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()

    return [dict(r) for r in rows]


def delete_fact(fact_id: int) -> bool:
    """Delete a specific fact."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM memory_facts WHERE id = ?", (fact_id,)
        )
        return cursor.rowcount > 0


def clear_all_facts():
    """Clear all long-term facts."""
    with get_connection() as conn:
        conn.execute("DELETE FROM memory_facts")
    logger.info("All facts cleared.")


def get_all_facts_for_prompt() -> list[dict]:
    """Get all facts with IDs for display."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, category, fact, created_at
            FROM memory_facts
            ORDER BY category, updated_at DESC
            """,
        ).fetchall()
    return [dict(r) for r in rows]


# ── Memory summary for system prompt ──────────────────────────────────────

def build_memory_context() -> str:
    """
    Build a memory context string to inject into the system prompt.
    This tells Charli what it remembers about the user.
    """
    facts = get_facts(limit=30)

    if not facts:
        return ""

    # Group by category
    grouped = {}
    for f in facts:
        cat = f["category"]
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(f["fact"])

    lines = ["What I remember about the user:"]
    for cat, items in grouped.items():
        lines.append(f"\n{cat.upper()}:")
        for item in items:
            lines.append(f"  - {item}")

    return "\n".join(lines)


# ── Auto-extract facts from conversation ──────────────────────────────────

def extract_and_save_facts(user_message: str, assistant_reply: str):
    """
    Use Ollama to extract memorable facts from a conversation turn
    and save them to long-term memory.
    Only extracts significant personal/work/preference facts.
    """
    from ai.ollama_client import ollama

    prompt = f"""Extract memorable facts from this conversation.
Only extract facts that are worth remembering long-term about the user.
Ignore small talk and generic questions.

User said: "{user_message}"
Assistant replied: "{assistant_reply}"

Return a JSON array of facts. Each fact has:
- category: "personal" | "work" | "preference" | "project"
- fact: short statement about the user

Return [] if nothing worth remembering.
Return ONLY valid JSON array, nothing else.

Examples of good facts:
- {{"category": "personal", "fact": "User's name is Aniruddha"}}
- {{"category": "project", "fact": "User is building a desktop AI assistant called Charli"}}
- {{"category": "preference", "fact": "User prefers dark mode"}}
- {{"category": "work", "fact": "User is a software developer"}}

JSON:"""

    try:
        response = ollama.prompt(prompt)

        # Extract JSON array
        import re
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if not match:
            return

        facts = json.loads(match.group())
        for f in facts:
            if isinstance(f, dict) and "category" in f and "fact" in f:
                save_fact(
                    category=f["category"],
                    fact=f["fact"],
                    source=user_message[:200]
                )

    except Exception as e:
        logger.debug(f"Fact extraction skipped: {e}")


# ── Module init ────────────────────────────────────────────────────────────
init_memory_tables()