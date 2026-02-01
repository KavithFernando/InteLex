import os
import re
import json
import faiss
import numpy as np
import mysql.connector
from sentence_transformers import SentenceTransformer

import dotenv
dotenv.load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

# Embedding model (starter). Swap later if needed.
EMBED_MODEL = "bhavyagiri/InLegal-Sbert"

# Output files
INDEX_PATH = "index_store/case_chunks.index"
CHUNK_MAP_PATH = "index_store/case_chunks_map.json"

# Chunking parameters (tune these)
CHUNK_TOKENS_APPROX = 400      # target chunk size (approx words)
OVERLAP_TOKENS_APPROX = 80     # overlap between chunks (approx words)
MIN_CHUNK_TOKENS = 100         # drop too-small chunks (noise)

def clean_text(text: str) -> str:
    if not text:
        return ""
    # replace all types of newlines and carriage returns with a single space
    text = text.replace("\n", " ").replace("\r", " ")
    # collapse all whitespace to single space (chunking is word-based)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def chunk_by_words(text: str,
                   chunk_words: int,
                   overlap_words: int,
                   min_words: int):
    """
    Simple, beginner-friendly chunker: splits by words with overlap.
    Also tracks approximate character offsets for later snippet highlighting.
    """
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
            # Approximate char offsets by searching within the original text.
            # For robustness, we store offsets as None if not found.
            # (Offsets are "nice to have", not required for retrieval.)
            start_char = None
            end_char = None
            try:
                # Find first occurrence of chunk_text prefix to locate it
                probe = " ".join(chunk_words_list[: min(30, len(chunk_words_list))])
                idx = text.find(probe)
                if idx != -1:
                    start_char = idx
                    # best-effort end_char
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

def fetch_cases_with_full_text():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor(dictionary=True)

    # Adjust column name if your full text column differs.
    cur.execute("""
        SELECT case_id, case_title, legal_issue, petitioner_claim,
               respondent_argument, outcome, interpretation_summary,
               full_text
        FROM cases
    """)
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows

def build_case_representation(row: dict) -> str:
    """
    For chunk-level indexing, we primarily chunk the full_text.
    But it helps to prepend a short header of structured fields once,
    so chunks carry some context (title/issue/outcome).
    """
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
    rows = fetch_cases_with_full_text()
    if not rows:
        raise RuntimeError("No cases found in DB.")

    model = SentenceTransformer(EMBED_MODEL)

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
            chunk_map.append({
                "case_id": case_id,
                # optional fields for UI/snippets
                "start_word": ch["start_word"],
                "end_word": ch["end_word"],
                "start_char": ch["start_char"],
                "end_char": ch["end_char"],
                "word_count": ch["word_count"],
            })
            all_chunk_texts.append(ch["text"])

    if not all_chunk_texts:
        raise RuntimeError("No chunks were created. Check full_text content or chunk settings.")

    embeddings = model.encode(
        all_chunk_texts,
        normalize_embeddings=True,
        show_progress_bar=True
    )
    embeddings = np.asarray(embeddings, dtype="float32")

    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)   # cosine similarity when normalized
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
    print(f"Total chunks indexed: {len(chunk_map)}")

if __name__ == "__main__":
    main()
