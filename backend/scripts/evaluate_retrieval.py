"""
RQ3 — Retrieval evaluation: Recall@K, MRR, and article-match rate.

Run from backend/:
    python scripts/evaluate_retrieval.py

Outputs: per-query pass/fail, then aggregate Recall@1/3/5/10, MRR,
article-match rate.
"""
from __future__ import annotations

import glob
import json
import os
import sys

from rank_bm25 import BM25Okapi

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from dotenv import load_dotenv
load_dotenv()

from services.clause_retrieval import ClauseFrameRetrievalService
from services.query_parser import parse_query


class BM25Retriever:
    """Sparse BM25 baseline over the same text corpus as FAISS.

    Reads clause_frames_map.json (same source as ClauseFrameRetrievalService)
    so both retrievers operate over an identical corpus.
    """

    def __init__(self) -> None:
        map_path = os.path.join(_backend_dir, "index_store", "clause_frames_map.json")
        with open(map_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self._row_map = meta.get("row_map") or []
        tokenised = [row["clause_text"].lower().split() for row in self._row_map]
        self._bm25 = BM25Okapi(tokenised)

    def search(self, query: str, top_k: int = 10) -> list[str]:
        """Return top_k frame_identifier strings ranked by BM25 score.

        Deduplicates by frame_identifier keeping highest-ranked occurrence,
        matching the same dedup logic as ClauseFrameRetrievalService.
        """
        tokens = query.lower().split()
        scores = self._bm25.get_scores(tokens)
        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        seen: set[str] = set()
        result: list[str] = []
        for idx in ranked_indices:
            fid = self._row_map[idx].get("frame_identifier", "")
            if fid and fid not in seen:
                seen.add(fid)
                result.append(fid)
            if len(result) >= top_k:
                break
        return result


# ---------------------------------------------------------------------------
# Ground truth
#
# Each entry has:
#   query            : the natural-language question
#   expected_article : the constitutional article the retriever should focus on
#                      - exact clause  e.g. "12(2)"  → ground truth = all frames for that clause
#                      - base article  e.g. "13"     → ground truth = all sub-clauses combined
#                      - None                        → no Recall/MRR measured (always ART✓)
#
# expected_frame_ids is NOT used here; ground truth is derived automatically
# at eval-time from data/frames/*.json by _get_effective_expected_ids().
# This ensures exhaustive coverage: every annotated frame for the right article
# counts as a valid hit, not just a hand-picked subset.
# ---------------------------------------------------------------------------
GROUND_TRUTH = [
    # ===================================================================
    # SECTION A — Clause-first queries (explicit article in query text)
    # Parser extracts the article via regex; pre-filtering is applied.
    # Tests both query parsing accuracy AND within-article frame ranking.
    # ===================================================================
    {
        "query": "Has Article 12(2) been used to challenge employment discrimination by the government?",
        "expected_article": "12(2)",   # 49 frames
    },
    {
        "query": "How has the court interpreted the right against torture under Article 11?",
        "expected_article": "11",       # 62 frames
    },
    {
        "query": "What does Article 13(2) say about detention without trial?",
        "expected_article": "13(2)",   # 60 frames
    },
    {
        "query": "Has the freedom of speech under Article 14(1)(a) been restricted by the state?",
        "expected_article": "14(1)(a)", # 34 frames
    },
    {
        "query": "Has the Supreme Court interpreted Article 17 to allow direct petitions?",
        "expected_article": "17",       # 28 frames
    },
    {
        "query": "Was the petitioner's arrest lawful under Article 13(1) — was the reason for arrest communicated?",
        "expected_article": "13(1)",   # 72 frames
    },
    {
        "query": "How has Article 13(3) protected the right to a fair trial and legal representation?",
        "expected_article": "13(3)",   # 10 frames
    },
    {
        "query": "Has Article 13(4) been applied to challenge preventive detention as unlawful punishment?",
        "expected_article": "13(4)",   # 12 frames
    },
    {
        "query": "Has Article 14(1)(b) been used to protect the right to hold public meetings or protests?",
        "expected_article": "14(1)(b)", # 10 frames
    },
    {
        "query": "How has Article 14(1)(g) been applied to protect freedom to carry on a lawful occupation?",
        "expected_article": "14(1)(g)", # 21 frames
    },
    {
        "query": "Can emergency regulations justify restricting fundamental rights under Article 15(7)?",
        "expected_article": "15(7)",   # 12 frames
    },
    {
        "query": "Has freedom of thought, conscience and religion under Article 10 been violated?",
        "expected_article": "10",       # 7 frames
    },
    {
        "query": "How has Article 12(1) equal protection been applied to public service appointments and transfers?",
        "expected_article": "12(1)",   # 196 frames
    },
    {
        "query": "Has Article 14(1)(c) been used to challenge restrictions on forming civic organisations?",
        "expected_article": "14(1)(c)", # 11 frames — previously uncovered article
    },
    # ===================================================================
    # SECTION B — Fact-pattern / broad queries (no explicit article ref)
    # Parser returns fact_pattern; no FAISS pre-filtering applied.
    # Tests purely semantic retrieval quality.
    # ===================================================================
    {
        "query": "Cases where government employment policies violated the equal protection clause",
        "expected_article": "12(1)",   # 196 frames — semantic match test
    },
    {
        "query": "Can a citizen challenge a police arrest under the constitution?",
        "expected_article": "13",       # all Art 13 sub-clauses ~158 frames
    },
    {
        "query": "Article 12 discrimination based on race or religion",
        "expected_article": "12(2)",   # 49 frames — parser will base-filter Art 12
    },
    {
        "query": "Freedom of movement or right to travel — has the court ever restricted it?",
        "expected_article": "14(1)(h)", # 11 frames — pure semantic test
    },
    {
        "query": "A government official rejected a job application solely because of the applicant's religion",
        "expected_article": "12(2)",   # 49 frames — discrimination fact-pattern, no article named
    },
    {
        "query": "A person was held in police custody for three days without being produced before a court",
        "expected_article": "13(2)",   # 60 frames — custodial detention fact-pattern
    },
    {
        "query": "A journalist was arrested following the publication of reports critical of the government",
        "expected_article": "14(1)(a)", # 34 frames — press freedom fact-pattern
    },
    {
        "query": "Employees were prevented from forming a group to collectively represent their workplace interests",
        "expected_article": "14(1)(c)", # 11 frames — freedom of association fact-pattern
    },
    # ===================================================================
    # SECTION D — Ambiguous / edge-case queries
    # No explicit article; semantically challenging or low-frequency.
    # Tests robustness on harder semantic cases and sparse articles.
    # ===================================================================
    {
        "query": "Can the government revoke a person's licence to practise their profession without justification?",
        "expected_article": "14(1)(g)", # 21 frames — ambiguous phrasing; primary right is occupation
    },
    {
        "query": "Is a person constitutionally entitled to be presumed innocent before their guilt is established?",
        "expected_article": "13(5)",    # 2 frames — low-frequency article; edge case for sparse coverage
    },
    # ===================================================================
    # SECTION C — Open-ended (no article expectation)
    # Contributes to Article-Match Rate only (always True when None).
    # Verifies the system doesn't crash on vague queries.
    # ===================================================================
    {
        "query": "What remedy did courts grant when fundamental rights were violated?",
        "expected_article": None,
    },
]

K_VALUES = [1, 3, 5, 10]

# ---------------------------------------------------------------------------
# Exhaustive ground truth loader
# ---------------------------------------------------------------------------
_FRAMES_DIR = os.path.join(_backend_dir, "data", "frames")


def _load_frames_by_article() -> dict[str, list[str]]:
    """Read every data/frames/*.json and return article → [frame_id, ...] mapping.

    This makes ground truth exhaustive: for an article-specific query, ALL
    frames annotated to that clause count as valid expected answers — not just
    a hand-picked subset.  Called once at the start of run_evaluation().
    """
    by_article: dict[str, list[str]] = {}
    for fpath in glob.glob(os.path.join(_FRAMES_DIR, "*.json")):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            article = data.get("clause", {}).get("article", "")
            frame_id = data.get("frame_id", "")
            if article and frame_id:
                by_article.setdefault(article, []).append(frame_id)
        except Exception:
            continue
    return by_article


def _get_effective_expected_ids(
    expected_art: str | None,
    frames_by_article: dict[str, list[str]],
) -> list[str]:
    """Build the full expected frame ID set for a query.

    - Exact clause ("12(2)")  → all frames for that specific clause.
    - Base article ("12")     → frames for all sub-clauses combined.
    - None                    → empty list (query skipped for Recall/MRR).
    """
    if expected_art is None:
        return []
    if expected_art in frames_by_article:
        return list(frames_by_article[expected_art])
    # Base article — no parentheses in expected_art
    if "(" not in expected_art:
        base = expected_art.strip()
        combined: list[str] = []
        for art, ids in frames_by_article.items():
            if art.split("(")[0].strip() == base:
                combined.extend(ids)
        return combined
    return []


def recall_at_k(retrieved_ids: list, expected_ids: list, k: int):
    """1.0 if any expected frame appears in the top-k results, else 0.0.
    Returns None when expected_ids is empty (no ground truth = skip)."""
    if not expected_ids:
        return None
    return 1.0 if any(eid in retrieved_ids[:k] for eid in expected_ids) else 0.0


def reciprocal_rank(retrieved_ids: list, expected_ids: list):
    """1/rank of the first relevant frame found; 0.0 if none found.
    Returns None when expected_ids is empty."""
    if not expected_ids:
        return None
    for i, rid in enumerate(retrieved_ids, start=1):
        if rid in expected_ids:
            return 1.0 / i
    return 0.0


def article_match(parsed_article: str | None, expected_article: str | None) -> bool:
    """True if the parsed article is at least a base-level match to the expected one."""
    if expected_article is None:
        return True  # No article expectation — always a match
    if parsed_article is None:
        return False
    base_parsed = parsed_article.split("(")[0].strip()
    base_expected = expected_article.split("(")[0].strip()
    return parsed_article == expected_article or base_parsed == base_expected


def run_evaluation() -> None:
    service = ClauseFrameRetrievalService()
    bm25 = BM25Retriever()

    try:
        from openai import OpenAI
        from config.settings import OPENAI_API_KEY
        client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    except Exception:
        client = None
        print("Warning: OpenAI client unavailable — running without LLM query parsing.")

    frames_by_article = _load_frames_by_article()
    total_frames = sum(len(v) for v in frames_by_article.values())
    print(
        f"\nGround truth source: {total_frames} frames across "
        f"{len(frames_by_article)} articles loaded from data/frames/"
    )

    conditions = ["bm25", "dense_nofilter", "dense_filtered"]
    recalls = {cond: {k: [] for k in K_VALUES} for cond in conditions}
    rr_scores: dict[str, list[float]] = {cond: [] for cond in conditions}
    article_matches: list[bool] = []

    print(f"\nRunning evaluation over {len(GROUND_TRUTH)} queries...\n")
    print("-" * 70)

    for i, test in enumerate(GROUND_TRUTH, start=1):
        query = test["query"]
        expected_art = test.get("expected_article")
        expected_ids = _get_effective_expected_ids(expected_art, frames_by_article)

        parsed = parse_query(query, client)
        if parsed.query_type == "clause_first":
            article_filter = parsed.article
            article_base_filter = parsed.article_base
        else:
            article_filter = None
            article_base_filter = None

        art_ok = article_match(parsed.article or parsed.article_base, expected_art)
        article_matches.append(art_ok)

        # Condition 1: BM25, no filtering
        bm25_ids = bm25.search(query, top_k=10)

        # Condition 2: Dense, no filtering
        result_nofilter = service.search_frames(query_text=query, top_k=10)
        dense_nofilter_ids = [
            r.get("frame_identifier") or "" for r in result_nofilter.get("results", [])
        ]

        # Condition 3: Dense + article filter (full system)
        result_filtered = service.search_frames(
            query_text=query,
            top_k=10,
            article_filter=article_filter,
            article_base_filter=article_base_filter,
        )
        dense_filtered_ids = [
            r.get("frame_identifier") or "" for r in result_filtered.get("results", [])
        ]

        retrieved_by_cond = {
            "bm25": bm25_ids,
            "dense_nofilter": dense_nofilter_ids,
            "dense_filtered": dense_filtered_ids,
        }

        for cond in conditions:
            ids = retrieved_by_cond[cond]
            for k in K_VALUES:
                v = recall_at_k(ids, expected_ids, k)
                if v is not None:
                    recalls[cond][k].append(v)
            rr = reciprocal_rank(ids, expected_ids)
            if rr is not None:
                rr_scores[cond].append(rr)

        art_flag = "ART✓" if art_ok else "ART✗"
        gt_label = f"GT={len(expected_ids)}" if expected_ids else "GT=skip"
        r5_bm25 = recall_at_k(bm25_ids, expected_ids, 5)
        r5_dnf = recall_at_k(dense_nofilter_ids, expected_ids, 5)
        r5_dft = recall_at_k(dense_filtered_ids, expected_ids, 5)
        r5_str = (
            (f"BM25={r5_bm25:.0f}" if r5_bm25 is not None else "BM25=N/A") + "  "
            + (f"DNF={r5_dnf:.0f}" if r5_dnf is not None else "DNF=N/A") + "  "
            + (f"DFT={r5_dft:.0f}" if r5_dft is not None else "DFT=N/A")
        )
        print(f"[{i:02d}] {art_flag} {gt_label} R@5: {r5_str} | {query[:40]}...")

    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print(f"{'Metric':<14} {'BM25':>12} {'Dense(no filt)':>15} {'Dense+Filter':>13}")
    print("-" * 56)
    for k in K_VALUES:
        row = f"  Recall@{k:<3}  "
        for cond in conditions:
            if recalls[cond][k]:
                avg = sum(recalls[cond][k]) / len(recalls[cond][k])
                n = len(recalls[cond][k])
                row += f"  {avg:.3f}(n={n})"
            else:
                row += f"  {'N/A':>12}"
        print(row)
    row = "  MRR        "
    for cond in conditions:
        if rr_scores[cond]:
            mrr = sum(rr_scores[cond]) / len(rr_scores[cond])
            n = len(rr_scores[cond])
            row += f"  {mrr:.3f}(n={n})"
        else:
            row += f"  {'N/A':>12}"
    print(row)
    art_rate = sum(article_matches) / len(article_matches) if article_matches else 0.0
    print(f"\n  Article-Match Rate = {art_rate:.3f}  (over {len(article_matches)} queries)")
    print("  (Article-Match is parser accuracy only; identical across all 3 conditions)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_evaluation()
