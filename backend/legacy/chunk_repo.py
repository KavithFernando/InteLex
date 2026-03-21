from typing import Any

from db.connection import get_connection


class ChunkRepository:

    def fetch_chunks_and_headers_by_faiss_ids(self, faiss_ids: list[int]) -> dict[int, dict[str, Any]]:
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


chunk_repo = ChunkRepository()
