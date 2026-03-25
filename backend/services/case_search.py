from typing import Any, Dict, List

from services.interfaces import RetrievalServiceInterface
from services.query_parser import parse_query


class CaseSearchService:

    def __init__(
        self,
        retrieval_service: RetrievalServiceInterface,
        case_repository,
        openai_client=None, # enables query parsing
    ):
        self._retrieval = retrieval_service
        self._case_repo = case_repository
        self._openai_client = openai_client

    def run_case_search(self, query_text: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Frame-first retrieval: top_k globally ranked interpretation frames, merged with
        corpus case summaries (clauses list, identifiers) from the DB.
        """
        # Parse the query to detect article references before hitting FAISS
        parsed = parse_query(query_text, self._openai_client)

        article_filter = None
        article_base_filter = None
        if parsed.query_type == "clause_first":
            if parsed.article:
                article_filter = parsed.article
            if parsed.article_base:
                article_base_filter = parsed.article_base

        retrieval = self._retrieval.search_frames(
            query_text=query_text,
            top_k=top_k,
            frame_recall=None,
            article_filter=article_filter,
            article_base_filter=article_base_filter,
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
