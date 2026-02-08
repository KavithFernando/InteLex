"""
Case chunks table: fetch by faiss_id, truncate, insert. Encapsulated in ChunkRepository.
"""
from typing import Any

from db.connection import get_connection


class ChunkRepository:
    """Repository for case_chunks table access."""

    def fetch_chunks_and_headers_by_faiss_ids(self, faiss_ids: list[int]) -> dict[int, dict[str, Any]]:
        """
        Fetch chunk text and case header fields for the given FAISS row indices.
        Returns dict: faiss_id -> {case_id, chunk_text, case_title, decision_date, legal_issue, outcome}.
        """
        if not faiss_ids:
            return {}

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        placeholders = ",".join(["%s"] * len(faiss_ids))
        cur.execute(
            f"""
            SELECT c.faiss_id, c.case_id, c.chunk_text,
                   ca.case_title, ca.decision_date, ca.legal_issue, ca.outcome
            FROM case_chunks c
            JOIN cases ca ON ca.case_id = c.case_id
            WHERE c.faiss_id IN ({placeholders})
            """,
            list(faiss_ids),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return {r["faiss_id"]: r for r in rows}

    def truncate_case_chunks(self, conn) -> None:
        """Truncate the case_chunks table. Caller must pass an open connection (e.g. for use in a transaction)."""
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE case_chunks")
        conn.commit()
        cur.close()

    def insert_case_chunk(
        self,
        conn,
        case_id: str,
        faiss_id: int,
        chunk_text: str,
        start_word: int,
        end_word: int,
        start_char: Any,
        end_char: Any,
        word_count: int,
    ) -> None:
        """
        Insert one row into case_chunks. Caller must pass an open connection and commit when done.
        """
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO case_chunks
            (case_id, faiss_id, chunk_text, start_word, end_word, start_char, end_char, word_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (case_id, faiss_id, chunk_text, start_word, end_word, start_char, end_char, word_count),
        )
        cur.close()


# Singleton instance for backward compatibility and dependency injection
chunk_repo = ChunkRepository()
