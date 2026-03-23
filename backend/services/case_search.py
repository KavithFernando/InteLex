from typing import Any, Dict, List

from services.interfaces import RetrievalServiceInterface


class CaseSearchService:

    def __init__(self, retrieval_service: RetrievalServiceInterface, case_repository):
        self._retrieval = retrieval_service
        self._case_repo = case_repository

    def run_case_search(self, query_text: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Frame-first retrieval: top_k globally ranked interpretation frames, merged with
        corpus case summaries (clauses list, identifiers) from the DB.
        """
        retrieval = self._retrieval.search_frames(
            query_text=query_text,
            top_k=top_k,
            frame_recall=None,
        )
        results = retrieval.get("results", [])
        if not results:
            return {
                "tool_content": {
                    "message": "Found 0 matching interpretation frame(s) based on the context provided.",
                    "count": 0,
                },
                "retrieval_result": [],
            }

        case_internal_ids = list({int(r["case_internal_id"]) for r in results})
        summaries: List[Dict[str, Any]] = self._case_repo.fetch_corpus_case_summaries(
            case_internal_ids
        )
        summary_by_id = {int(s["case_id"]): s for s in summaries}

        retrieval_result: List[Dict[str, Any]] = []
        for r in results:
            cid = int(r["case_internal_id"])
            s = summary_by_id.get(cid)
            if not s:
                continue
            dd = r.get("decision_date")
            decision_date = str(dd) if dd is not None else s.get("decision_date")
            retrieval_result.append(
                {
                    **s,
                    "score": r.get("score"),
                    "interpretation_frame_id": r.get("interpretation_frame_id"),
                    "frame_identifier": r.get("frame_identifier"),
                    "matched_article": r.get("article"),
                    "matched_subclause": r.get("subclause"),
                    "matched_clause_text": r.get("clause_text"),
                    # Prefer index map title/date when present (same as retrieval row)
                    "case_title": r.get("case_title") or s.get("case_title"),
                    "decision_date": decision_date,
                }
            )

        count = len(retrieval_result)
        tool_content = {
            "message": (
                f"Found {count} matching interpretation frame(s) based on the context provided. "
                "The list is attached in the response body for the user."
            ),
            "count": count,
        }

        return {"tool_content": tool_content, "retrieval_result": retrieval_result}
