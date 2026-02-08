"""
High-level case search: runs retrieval (FAISS + chunk/headers) and enriches
with case summaries (title, date, clauses) for the chat tool and API response.
Implemented as CaseSearchService for OOP.
"""
from typing import Any, Dict, List

from services.interfaces import IRetrievalService


class CaseSearchService:
    """Orchestrates retrieval and case summaries for chat and API."""

    def __init__(self, retrieval_service: IRetrievalService, case_repository):
        """
        :param retrieval_service: Implementation of IRetrievalService (e.g. RetrievalService).
        :param case_repository: CaseRepository for fetching case summaries.
        """
        self._retrieval = retrieval_service
        self._case_repo = case_repository

    def run_case_search(self, query_text: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Run retrieval (FAISS + DB chunk/headers), then fetch case summaries (title, date, clauses).
        Returns tool_content (short message for the LLM) and retrieval_result (for API response body).
        """
        retrieval = self._retrieval.search_cases(
            query_text=query_text,
            top_cases=top_k,
            chunk_recall=None,
            top_chunks_per_case=3,
        )
        results = retrieval.get("results", [])

        case_ids = [r["case_id"] for r in results]
        summaries: List[Dict[str, Any]] = self._case_repo.fetch_case_summaries(case_ids)

        score_by_id = {r["case_id"]: r["score"] for r in results}
        retrieval_result = [
            {**s, "score": score_by_id.get(s["case_id"])}
            for s in summaries
        ]

        count = len(retrieval_result)
        tool_content = {
            "message": f"Found {count} matching case(s) based on the context provided. The list is attached in the response body for the user.",
            "count": count,
        }

        return {"tool_content": tool_content, "retrieval_result": retrieval_result}
