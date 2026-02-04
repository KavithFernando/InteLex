import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from db.repositories import chunk_repo

INDEX_PATH = "index_store/case_chunks.index"
CHUNK_MAP_PATH = "index_store/case_chunks_map.json"

_embedder = None
_index = None


def _load_assets():
    global _embedder, _index
    if _index is None:
        _index = faiss.read_index(INDEX_PATH)
    if _embedder is None:
        with open(CHUNK_MAP_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        _embedder = SentenceTransformer(meta["embed_model"])

# Diversity guard: scale chunk_recall with corpus size so retrieval doesn't under-recall as DB grows
CHUNK_RECALL_MIN = 80
CHUNK_RECALL_MAX = 500
CHUNK_RECALL_DIVISOR = 4  # recall = ntotal // divisor, clamped

def search_cases(
    query_text: str,
    top_cases: int = 10,
    chunk_recall: int | None = None,
    top_chunks_per_case: int = 3,
):
    """
    chunk_recall: how many top chunks to fetch before aggregating to cases.
      If None, computed from index size: max(CHUNK_RECALL_MIN, min(CHUNK_RECALL_MAX, ntotal // DIVISOR)).
      For ~100 cases 80 is fine; as corpus grows recall increases to improve diversity.
    top_chunks_per_case: number of top chunk snippets to return per case (2-3).
    """
    _load_assets()

    ntotal = _index.ntotal
    if chunk_recall is None:
        chunk_recall = max(
            CHUNK_RECALL_MIN,
            min(CHUNK_RECALL_MAX, ntotal // CHUNK_RECALL_DIVISOR),
        )

    q = _embedder.encode([query_text], normalize_embeddings=True).astype("float32")
    scores, idxs = _index.search(q, chunk_recall)

    # Fetch chunk text + case headers from MySQL for all top chunks (faiss_id = FAISS row index)
    faiss_ids = [int(i) for i in idxs[0] if i >= 0]
    chunk_rows = chunk_repo.fetch_chunks_and_headers_by_faiss_ids(faiss_ids)

    # Per case: keep top top_chunks_per_case chunks by score (for diversity / multiple snippets)
    case_chunks = {}  # case_id -> [(score, faiss_id), ...] sorted desc by score, max top_chunks_per_case
    for score, faiss_id in zip(scores[0], idxs[0]):
        if faiss_id < 0:
            continue
        row = chunk_rows.get(int(faiss_id))
        if not row:
            continue
        cid = row["case_id"]
        score_f = float(score)
        if cid not in case_chunks:
            case_chunks[cid] = []
        lst = case_chunks[cid]
        if len(lst) < top_chunks_per_case or score_f > lst[-1][0]:
            lst.append((score_f, int(faiss_id)))
            lst.sort(key=lambda x: -x[0])
            case_chunks[cid] = lst[:top_chunks_per_case]

    # Rank cases by best chunk score
    ranked = sorted(
        case_chunks.items(),
        key=lambda x: x[1][0][0] if x[1] else 0.0,
        reverse=True,
    )
    ranked = ranked[:top_cases]

    results = []
    for cid, chunk_list in ranked:
        best_score, best_faiss_id = chunk_list[0]
        header_row = chunk_rows.get(best_faiss_id, {})

        top_chunks = []
        for sc, fid in chunk_list:
            r = chunk_rows.get(fid, {})
            top_chunks.append({
                "faiss_id": fid,
                "score": sc,
                "chunk_text": r.get("chunk_text"),
            })

        results.append({
            "case_id": cid,
            "score": best_score,
            "case_title": header_row.get("case_title"),
            "decision_date": str(header_row.get("decision_date")) if header_row.get("decision_date") else None,
            "legal_issue": header_row.get("legal_issue"),
            "outcome": header_row.get("outcome"),
            "best_chunk_ref": best_faiss_id,
            "chunk_text": header_row.get("chunk_text"),
            "top_chunks": top_chunks,
        })

    return {"results": results}
