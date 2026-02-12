"""
Conversation and message repository (raw SQL). Chat history persistence. Encapsulated in ConversationRepository.
"""
import json
from typing import Any, Dict, List, Optional

from db.connection import get_connection


class ConversationRepository:
    """Repository for conversations and messages."""

    def get_by_conversation_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
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

    def create(self, conversation_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a new conversation. Returns the created row (id, conversation_id, user_id, active, created_at)."""
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "INSERT INTO conversations (conversation_id, user_id) VALUES (%s, %s)",
                (conversation_id, user_id),
            )
            conn.commit()
            pk = cur.lastrowid
            cur.execute("SELECT id, conversation_id, user_id, active, created_at FROM conversations WHERE id = %s", (pk,))
            row = cur.fetchone()
            cur.close()
            return row
        finally:
            conn.close()

    def get_or_create(self, conversation_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get existing conversation by conversation_id or create one. Returns row with id."""
        row = self.get_by_conversation_id(conversation_id)
        if row:
            return row
        return self.create(conversation_id, user_id)

    def list_all(self) -> List[Dict[str, Any]]:
        """Return all conversations, newest first. Each row: conversation_id, created_at, updated_at."""
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT conversation_id, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
            )
            rows = cur.fetchall()
            cur.close()
            return rows
        finally:
            conn.close()

    def get_messages_by_conversation_id(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Return messages for the conversation (by client-facing id), ordered by created_at. Each item: role, content, retrieval_result."""
        conv = self.get_by_conversation_id(conversation_id)
        if not conv:
            return []
        return self.get_messages(conv["id"])

    def get_messages(self, conversation_internal_id: int) -> List[Dict[str, Any]]:
        """Return messages for the conversation (by internal id), ordered by created_at. Each item: role, content, retrieval_result (list or None)."""
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT role, content, retrieval_result FROM messages WHERE conversation_id = %s ORDER BY created_at ASC",
                (conversation_internal_id,),
            )
            rows = cur.fetchall()
            cur.close()
            out = []
            for r in rows:
                retrieval = r.get("retrieval_result")
                if retrieval is not None:
                    if isinstance(retrieval, str):
                        try:
                            retrieval = json.loads(retrieval) if retrieval else []
                        except (json.JSONDecodeError, TypeError):
                            retrieval = []
                    elif not isinstance(retrieval, list):
                        retrieval = []
                else:
                    retrieval = None
                out.append({
                    "role": r["role"],
                    "content": r["content"],
                    "retrieval_result": retrieval,
                })
            return out
        finally:
            conn.close()

    def add_message(
        self,
        conversation_internal_id: int,
        role: str,
        content: str,
        retrieval_result: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Append a message (user or assistant) to the conversation. retrieval_result is for assistant messages with case results."""
        conn = get_connection()
        try:
            cur = conn.cursor()
            json_val = json.dumps(retrieval_result) if retrieval_result else None
            cur.execute(
                "INSERT INTO messages (conversation_id, role, content, retrieval_result) VALUES (%s, %s, %s, %s)",
                (conversation_internal_id, role, content, json_val),
            )
            conn.commit()
            cur.close()
        finally:
            conn.close()

    def set_active(self, conversation_internal_id: int, active: bool) -> None:
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


# Singleton instance for backward compatibility and dependency injection
conversation_repo = ConversationRepository()
