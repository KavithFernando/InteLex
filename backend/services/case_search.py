"""
High-level case search: runs retrieval (FAISS + chunk/headers) and enriches
with case summaries (title, date, clauses) for the chat tool and API response.
"""
from typing import Any, Dict, List

from db.repositories import case_repo
from services.retrieval import search_cases as run_retrieval


def run_case_search(query_text: str, top_k: int = 10) -> Dict[str, Any]:
    """
    Run retrieval (FAISS + DB chunk/headers), then fetch case summaries (title, date, clauses).
    Returns tool_content (short message for the LLM) and retrieval_result (for API response body).
    """
    retrieval = run_retrieval(
        query_text=query_text,
        top_cases=top_k,
        chunk_recall=None,
        top_chunks_per_case=3,
    )
    results = retrieval.get("results", [])

    case_ids = [r["case_id"] for r in results]
    summaries: List[Dict[str, Any]] = case_repo.fetch_case_summaries(case_ids)

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
