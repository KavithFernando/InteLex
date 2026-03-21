"""
Clause / interpretation-frame retrieval using FAISS over index_store/clause_frames.*.

Each index row is one interpretation_frame (constitution clause text + article/subclause).
Results are grouped by case (internal id), ranked by best frame score per case.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from config import CLAUSE_INDEX_PATH, CLAUSE_MAP_PATH
from services.interfaces import RetrievalServiceInterface

# How many FAISS hits to pull before grouping by case (diversity)
FRAME_RECALL_MIN = 80
FRAME_RECALL_MAX = 500
FRAME_RECALL_DIVISOR = 4


class ClauseFrameRetrievalService(RetrievalServiceInterface):
    """FAISS search over clause-frame vectors; implements RetrievalServiceInterface."""

    def __init__(self) -> None:
        self._index = None
        self._embedder = None
        self._row_map: List[Dict[str, Any]] = []
        self._embed_model: Optional[str] = None

    def _load_assets(self) -> None:
        if self._index is None:
            self._index = faiss.read_index(CLAUSE_INDEX_PATH)
        if not self._row_map:
            with open(CLAUSE_MAP_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self._embed_model = meta.get("embed_model")
            self._row_map = meta.get("row_map") or []
        if self._embedder is None and self._embed_model:
            self._embedder = SentenceTransformer(self._embed_model)

    def search_cases(
        self,
        query_text: str,
        top_cases: int = 10,
        chunk_recall: int | None = None,
        top_chunks_per_case: int = 3,
    ) -> Dict[str, Any]:
        """
        chunk_recall -> frame_recall (candidate FAISS hits).
        top_chunks_per_case -> max frames kept per case before ranking cases.
        """
        self._load_assets()
        if self._index is None or self._embedder is None or not self._row_map:
            return {"results": []}

        ntotal = int(self._index.ntotal)
        if ntotal == 0:
            return {"results": []}

        if chunk_recall is None:
            frame_recall = max(
                FRAME_RECALL_MIN,
                min(FRAME_RECALL_MAX, ntotal // FRAME_RECALL_DIVISOR),
            )
        else:
            frame_recall = chunk_recall

        frame_recall = min(frame_recall, ntotal)
        top_frames_per_case = max(1, top_chunks_per_case)

        q = self._embedder.encode([query_text], normalize_embeddings=True).astype("float32")
        scores, idxs = self._index.search(q, frame_recall)

        # Group by case_internal_id (case_id in map), keep top N frames per case by score
        case_frames: Dict[int, List[tuple]] = {}
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0:
                continue
            fi = int(idx)
            if fi >= len(self._row_map):
                continue
            row = self._row_map[fi]
            case_pk = int(row["case_id"])
            sc = float(score)
            if case_pk not in case_frames:
                case_frames[case_pk] = []
            lst = case_frames[case_pk]
            lst.append((sc, fi, row))
            lst.sort(key=lambda x: -x[0])
            case_frames[case_pk] = lst[:top_frames_per_case]

        ranked_cases = sorted(
            case_frames.items(),
            key=lambda x: x[1][0][0] if x[1] else 0.0,
            reverse=True,
        )[:top_cases]

        results: List[Dict[str, Any]] = []
        for case_pk, frame_list in ranked_cases:
            best_score, best_faiss_id, best_row = frame_list[0]
            top_frames: List[Dict[str, Any]] = []
            for sc, fid, r in frame_list:
                top_frames.append(
                    {
                        "faiss_id": fid,
                        "score": sc,
                        "interpretation_frame_id": r.get("interpretation_frame_id"),
                        "frame_identifier": r.get("frame_identifier"),
                        "article": r.get("article"),
                        "subclause": r.get("subclause"),
                        "clause_text": r.get("clause_text"),
                    }
                )

            results.append(
                {
                    "case_internal_id": case_pk,
                    "score": best_score,
                    "case_title": best_row.get("case_title"),
                    "decision_date": best_row.get("decision_date"),
                    "interpretation_frame_id": best_row.get("interpretation_frame_id"),
                    "frame_identifier": best_row.get("frame_identifier"),
                    "article": best_row.get("article"),
                    "subclause": best_row.get("subclause"),
                    "clause_text": best_row.get("clause_text"),
                    "best_faiss_id": best_faiss_id,
                    "top_frames": top_frames,
                }
            )

        return {"results": results}


def _default_clause_service() -> ClauseFrameRetrievalService:
    return ClauseFrameRetrievalService()


def search_cases(
    query_text: str,
    top_cases: int = 10,
    chunk_recall: int | None = None,
    top_chunks_per_case: int = 3,
) -> Dict[str, Any]:
    return _default_clause_service().search_cases(
        query_text=query_text,
        top_cases=top_cases,
        chunk_recall=chunk_recall,
        top_chunks_per_case=top_chunks_per_case,
    )
