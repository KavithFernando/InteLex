"""
Clause / interpretation-frame retrieval using FAISS over index_store/clause_frames.*.

Each index row is one interpretation_frame (constitution clause text + article/subclause).
Results are deduplicated by interpretation_frame_id (best score wins), then ranked globally.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import CLAUSE_INDEX_PATH, CLAUSE_MAP_PATH
from services.interfaces import RetrievalServiceInterface

# How many FAISS hits to pull before deduplicating by frame (recall)
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
        # For pre-filtering by article
        self._article_to_ids: Dict[str, List[int]] = {}
        self._article_base_to_ids: Dict[str, List[int]] = {}

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

        # Build article -> FAISS row index lookup
        if not self._article_to_ids:
            self._article_to_ids = {}
            self._article_base_to_ids = {}
            for i, row in enumerate(self._row_map):
                art = row.get("article", "")
                base = row.get("article_base") or art.split("(")[0].strip()
                self._article_to_ids.setdefault(art, []).append(i)
                self._article_base_to_ids.setdefault(base, []).append(i)

    def search_frames(
        self,
        query_text: str,
        top_k: int = 10,
        frame_recall: int | None = None,
        article_filter: str | None = None, # exact match like "12(2)"
        article_base_filter: str | None = None, # base article like "12"
    ) -> Dict[str, Any]:
        """
        Globally rank interpretation frames: each FAISS row is one frame; keep the best
        score per interpretation_frame_id, then take top_k by score.
        """
        self._load_assets()
        if self._index is None or self._embedder is None or not self._row_map:
            return {"results": []}

        ntotal = int(self._index.ntotal)
        if ntotal == 0:
            return {"results": []}

        if frame_recall is None:
            frame_recall = max(
                FRAME_RECALL_MIN,
                min(FRAME_RECALL_MAX, ntotal // FRAME_RECALL_DIVISOR),
            )

        # Determine eligible FAISS row indices (article pre-filtering, RQ2)
        valid_ids: set | None = None
        if article_filter and article_filter in self._article_to_ids:
            valid_ids = set(self._article_to_ids[article_filter])
        elif article_base_filter and article_base_filter in self._article_base_to_ids:
            valid_ids = set(self._article_base_to_ids[article_base_filter])

        # Compensate: expand recall so filtering doesn't starve top_k
        effective_recall = frame_recall
        if valid_ids is not None:
            filtered_count = len(valid_ids)
            if filtered_count == 0:
                return {"results": []}
            effective_recall = min(FRAME_RECALL_MAX, max(frame_recall, filtered_count * 4))

        effective_recall = min(effective_recall, ntotal)
        top_k = max(1, top_k)

        q = self._embedder.encode([query_text], normalize_embeddings=True).astype("float32")
        scores, idxs = self._index.search(q, effective_recall)

        # frame_id -> (best_score, faiss_idx, row)
        best_by_frame: Dict[int, tuple] = {}
        for score, idx in zip(scores[0], idxs[0]):
            if idx < 0:
                continue
            fi = int(idx)
            if fi >= len(self._row_map):
                continue
            if valid_ids is not None and fi not in valid_ids: # article pre-filter
                continue
            row = self._row_map[fi]
            raw_fid = row.get("interpretation_frame_id")
            if raw_fid is None:
                continue
            fid = int(raw_fid)
            sc = float(score)
            prev = best_by_frame.get(fid)
            if prev is None or sc > prev[0]:
                best_by_frame[fid] = (sc, fi, row)

        ranked = sorted(best_by_frame.values(), key=lambda t: -t[0])[:top_k]

        results: List[Dict[str, Any]] = []
        for sc, fi, row in ranked:
            case_pk = int(row["case_id"])
            results.append(
                {
                    "case_internal_id": case_pk,
                    "score": sc,
                    "interpretation_frame_id": int(row["interpretation_frame_id"]),
                    "frame_identifier": row.get("frame_identifier"),
                    "article": row.get("article"),
                    "subclause": row.get("subclause"),
                    "clause_text": row.get("clause_text"),
                    "case_title": row.get("case_title"),
                    "decision_date": row.get("decision_date"),
                    "best_faiss_id": fi,
                }
            )

        return {"results": results}


def _default_clause_service() -> ClauseFrameRetrievalService:
    return ClauseFrameRetrievalService()


def search_frames(
    query_text: str,
    top_k: int = 10,
    frame_recall: int | None = None,
    article_filter: str | None = None,
    article_base_filter: str | None = None,
) -> Dict[str, Any]:
    return _default_clause_service().search_frames(
        query_text=query_text,
        top_k=top_k,
        frame_recall=frame_recall,
        article_filter=article_filter,
        article_base_filter=article_base_filter,
    )
