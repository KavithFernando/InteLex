"""
Conversation and message repository (raw SQL). Chat history persistence.
"""
from typing import Any, Dict, List, Optional

from db.connection import get_connection


def get_by_conversation_id(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Return the conversation row by client-facing conversation_id, or None."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT id, conversation_id, user_id, active FROM conversations WHERE conversation_id = %s",
            (conversation_id,),
        )
        row = cur.fetchone()
        cur.close()
        return row
    finally:
        conn.close()


def create(conversation_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Create a new conversation. Returns the created row (id, conversation_id, user_id, active)."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "INSERT INTO conversations (conversation_id, user_id) VALUES (%s, %s)",
            (conversation_id, user_id),
        )
        conn.commit()
        pk = cur.lastrowid
        cur.close()
        return {
            "id": pk,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "active": True,
        }
    finally:
        conn.close()


def get_or_create(conversation_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Get existing conversation by conversation_id or create one. Returns row with id."""
    row = get_by_conversation_id(conversation_id)
    if row:
        return row
    return create(conversation_id, user_id)


def get_messages(conversation_internal_id: int) -> List[Dict[str, Any]]:
    """Return messages for the conversation (by internal id), ordered by created_at. Each item: role, content."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT role, content FROM messages WHERE conversation_id = %s ORDER BY created_at ASC",
            (conversation_internal_id,),
        )
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()


def add_message(conversation_internal_id: int, role: str, content: str) -> None:
    """Append a message (user or assistant) to the conversation."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO messages (conversation_id, role, content) VALUES (%s, %s, %s)",
            (conversation_internal_id, role, content),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def set_active(conversation_internal_id: int, active: bool) -> None:
    """Mark conversation as active or ended."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE conversations SET active = %s WHERE id = %s",
            (1 if active else 0, conversation_internal_id),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()
