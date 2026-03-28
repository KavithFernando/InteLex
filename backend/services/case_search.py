from typing import Any, Dict, List

from loguru import logger

from services.interfaces import RetrievalServiceInterface
from services.query_parser import parse_query


def detect_divergence(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detect when retrieved frames contain conflicting case outcomes.

    A divergence exists when the result set contains both petition-granting
    and petition-dismissing dispositions — indicating the clause has been
    interpreted differently across cases.
    """
    GRANTING   = {"upheld", "granted", "allowed", "allowed_in_part"}
    DISMISSING = {"dismissed", "refused"}

    granted   = [r for r in results if (r.get("disposition") or "").lower() in GRANTING]
    dismissed = [r for r in results if (r.get("disposition") or "").lower() in DISMISSING]

    has_divergence = len(granted) > 0 and len(dismissed) > 0

    return {
        "has_divergence": has_divergence,
        "granted_count": len(granted),
        "dismissed_count": len(dismissed),
        "majority_disposition": "granted" if len(granted) >= len(dismissed) else "dismissed",
    }


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
        logger.info("[CaseSearch] Running case search | query_len={} top_k={}", len(query_text), top_k)
        parsed = parse_query(query_text, self._openai_client)
        logger.info(
            "[CaseSearch] Query parsed | type={} article={} article_base={}",
            parsed.query_type,
            parsed.article or "(none)",
            parsed.article_base or "(none)",
        )

        article_filter = None
        article_base_filter = None
        if parsed.query_type == "clause_first":
            if parsed.article:
                article_filter = parsed.article
            if parsed.article_base:
                article_base_filter = parsed.article_base

        logger.info(
            "[CaseSearch] Calling FAISS retrieval | article_filter={} article_base_filter={}",
            article_filter or "(none)",
            article_base_filter or "(none)",
        )
        retrieval = self._retrieval.search_frames(
            query_text=query_text,
            top_k=top_k,
            frame_recall=None,
            article_filter=article_filter,
            article_base_filter=article_base_filter,
        )
        results = retrieval.get("results", [])
        logger.info("[CaseSearch] FAISS returned {} frame(s)", len(results))
        if not results:
            logger.warning("[CaseSearch] No frames matched query — returning empty result")
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
                    "disposition": r.get("disposition"),
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

        divergence = detect_divergence(retrieval_result)
        logger.info(
            "[CaseSearch] Search complete | results={} divergence={} granted={} dismissed={}",
            count,
            divergence["has_divergence"],
            divergence["granted_count"],
            divergence["dismissed_count"],
        )

        return {
            "tool_content": tool_content,
            "retrieval_result": retrieval_result,
            "divergence": divergence,
        }
