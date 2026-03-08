import json
from typing import Any, Dict, List, Optional

from db.connection import get_connection


class ConversationRepository:

    def get_by_conversation_id(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT id, conversation_id, user_id, title, active FROM conversations WHERE conversation_id = %s",
                (conversation_id,),
            )
            row = cur.fetchone()
            cur.close()
            return row
        finally:
            conn.close()

    def create(self, conversation_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "INSERT INTO conversations (conversation_id, user_id) VALUES (%s, %s)",
                (conversation_id, user_id),
            )
            conn.commit()
            pk = cur.lastrowid
            cur.execute("SELECT id, conversation_id, user_id, title, active, created_at FROM conversations WHERE id = %s", (pk,))
            row = cur.fetchone()
            cur.close()
            return row
        finally:
            conn.close()

    def get_or_create(self, conversation_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        row = self.get_by_conversation_id(conversation_id)
        if row:
            return row
        return self.create(conversation_id, user_id)

    def list_all(self) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT conversation_id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
            )
            rows = cur.fetchall()
            cur.close()
            return rows
        finally:
            conn.close()

    def list_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT conversation_id, title, created_at, updated_at FROM conversations "
                "WHERE user_id = %s ORDER BY updated_at DESC",
                (user_id,),
            )
            rows = cur.fetchall()
            cur.close()
            return rows
        finally:
            conn.close()

    def get_messages_by_conversation_id(self, conversation_id: str) -> List[Dict[str, Any]]:
        conv = self.get_by_conversation_id(conversation_id)
        if not conv:
            return []
        return self.get_messages(conv["id"])

    def get_messages(self, conversation_internal_id: int) -> List[Dict[str, Any]]:
        conn = get_connection()
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(
                "SELECT role, content, retrieval_result, created_at FROM messages WHERE conversation_id = %s ORDER BY created_at ASC",
                (conversation_internal_id,),
            )
            rows = cur.fetchall()
            cur.close()
            # Parse retrieval_result JSON if stored as string
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
                    "created_at": r.get("created_at"),
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

    def update_title(self, conversation_internal_id: int, title: str) -> None:
        # Only update if title is currently NULL (prevents overwriting existing titles)
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE conversations SET title = %s WHERE id = %s AND title IS NULL",
                (title, conversation_internal_id),
            )
            conn.commit()
            cur.close()
        finally:
            conn.close()


conversation_repo = ConversationRepository()
