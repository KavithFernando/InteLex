from typing import Any, Dict, List

from services.interfaces import RetrievalServiceInterface


class CaseSearchService:

    def __init__(self, retrieval_service: RetrievalServiceInterface, case_repository):
        self._retrieval = retrieval_service
        self._case_repo = case_repository

    def run_case_search(self, query_text: str, top_k: int = 10) -> Dict[str, Any]:
        retrieval = self._retrieval.search_cases(
            query_text=query_text,
            top_cases=top_k,
            chunk_recall=None,
            top_chunks_per_case=3,
        )
        results = retrieval.get("results", [])
        
        # Fetch case summaries and merge with retrieval scores
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
