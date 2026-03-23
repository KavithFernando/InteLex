"""
Legacy: build case_chunks table + case_chunks FAISS index. Superseded by scripts/index_clauses.py.

Run from backend/:  python -m legacy.index_cases
"""
import os
import re
import sys
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from config.settings import (
    CHUNK_MAP_PATH,
    CHUNK_TOKENS_APPROX,
    EMBED_MODEL,
    INDEX_PATH,
    MIN_CHUNK_TOKENS,
    OVERLAP_TOKENS_APPROX,
)
from db.connection import get_connection
from db.repositories.case_repo import case_repo
from legacy.chunk_repo import chunk_repo


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_by_words(text: str, chunk_words: int, overlap_words: int, min_words: int):
    words = text.split()
    if len(words) < min_words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_words, len(words))
        chunk_words_list = words[start:end]
        chunk_text = " ".join(chunk_words_list).strip()

        if len(chunk_words_list) >= min_words:
            start_char = None
            end_char = None
            try:
                probe = " ".join(chunk_words_list[: min(30, len(chunk_words_list))])
                idx = text.find(probe)
                if idx != -1:
                    start_char = idx
                    end_probe = " ".join(chunk_words_list[-min(30, len(chunk_words_list)):])
                    idx2 = text.find(end_probe, idx)
                    if idx2 != -1:
                        end_char = idx2 + len(end_probe)
            except Exception:
                pass

            chunks.append({
                "text": chunk_text,
                "start_word": start,
                "end_word": end,
                "start_char": start_char,
                "end_char": end_char,
                "word_count": len(chunk_words_list)
            })

        if end == len(words):
            break
        start = max(end - overlap_words, start + 1)

    return chunks


def build_case_representation(row: dict) -> str:
    header_parts = []
    if row.get("case_title"):
        header_parts.append(f"Title: {row['case_title']}")
    if row.get("legal_issue"):
        header_parts.append(f"Legal issue: {row['legal_issue']}")
    if row.get("petitioner_claim"):
        header_parts.append(f"Petitioner claim: {row['petitioner_claim']}")
    if row.get("respondent_argument"):
        header_parts.append(f"Respondent argument: {row['respondent_argument']}")
    if row.get("outcome"):
        header_parts.append(f"Outcome: {row['outcome']}")
    if row.get("interpretation_summary"):
        header_parts.append(f"Interpretation summary: {row['interpretation_summary']}")

    header = "\n".join(header_parts).strip()
    body = clean_text(row.get("full_text") or "")

    if header and body:
        return header + "\n\n" + body
    return header or body


def main():
    rows = case_repo.fetch_cases_with_full_text()
    if not rows:
        raise RuntimeError("No cases found in DB.")

    model = SentenceTransformer(EMBED_MODEL)

    conn = get_connection()
    chunk_repo.truncate_case_chunks(conn)

    chunk_map = []
    all_chunk_texts = []

    for row in rows:
        case_id = row["case_id"]
        case_text = build_case_representation(row)
        case_text = clean_text(case_text)
        if not case_text:
            continue

        chunks = chunk_by_words(
            case_text,
            chunk_words=CHUNK_TOKENS_APPROX,
            overlap_words=OVERLAP_TOKENS_APPROX,
            min_words=MIN_CHUNK_TOKENS
        )

        for ch in chunks:
            faiss_id = len(chunk_map)
            chunk_map.append({
                "case_id": case_id,
                "start_word": ch["start_word"],
                "end_word": ch["end_word"],
                "start_char": ch["start_char"],
                "end_char": ch["end_char"],
                "word_count": ch["word_count"],
            })
            all_chunk_texts.append(ch["text"])
            chunk_repo.insert_case_chunk(
                conn,
                case_id,
                faiss_id,
                ch["text"],
                ch["start_word"],
                ch["end_word"],
                ch["start_char"],
                ch["end_char"],
                ch["word_count"],
            )

    conn.commit()
    conn.close()

    if not all_chunk_texts:
        raise RuntimeError("No chunks were created. Check full_text content or chunk settings.")

    embeddings = model.encode(
        all_chunk_texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )
    embeddings = np.asarray(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    with open(CHUNK_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump({
            "embed_model": EMBED_MODEL,
            "chunk_words": CHUNK_TOKENS_APPROX,
            "overlap_words": OVERLAP_TOKENS_APPROX,
            "min_words": MIN_CHUNK_TOKENS,
            "count_chunks": len(chunk_map),
            "chunk_map": chunk_map
        }, f, ensure_ascii=False, indent=2)

    print(f"Saved FAISS index to: {INDEX_PATH}")
    print(f"Saved chunk map to:   {CHUNK_MAP_PATH}")
    print(f"Populated case_chunks table (faiss_id 0..{len(chunk_map) - 1} in same order as FAISS)")
    print(f"Total chunks indexed: {len(chunk_map)}")


if __name__ == "__main__":
    main()
