"""
RQ3 — Retrieval evaluation: Recall@K, MRR, and article-match rate.

Run from backend/:
    python scripts/evaluate_retrieval.py

Outputs: per-query pass/fail, then aggregate Recall@1/3/5/10, MRR,
article-match rate.
"""
from __future__ import annotations

import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from dotenv import load_dotenv
load_dotenv()

from services.clause_retrieval import ClauseFrameRetrievalService
from services.query_parser import parse_query

# ---------------------------------------------------------------------------
# Ground truth
#
# Each entry has:
#   query              : the natural-language question
#   expected_article   : the article the retriever should focus on
#                        (None = no article expectation, counts as a match)
#   expected_frame_ids : list of frame_identifier values that are known-good
#                        answers.  At least one must appear in top-10 for
#                        the query to count as a "hit".
#                        Populated from actual data/frames/*.json files.
# ---------------------------------------------------------------------------
GROUND_TRUTH = [
    # -----------------------------------------------------------------------
    # Q1 — Article 12(2): government employment discrimination
    # -----------------------------------------------------------------------
    {
        "query": "Has Article 12(2) been used to challenge employment discrimination by the government?",
        "expected_article": "12(2)",
        "expected_frame_ids": [
            "RQ1_016-SLLR-SLLR-1987-1-LAXAMANA-AND-OTHERS_081_C01__12(2)",
            "RQ1_017-SLLR-SLLR-1988-V-1-THE-PUBLIC-SERVIC_088_C02__12(2)",
            "RQ1_029-SLLR-1988-V2-DAYAWATHIE-AND-PEIRIS-V_142_C01__12(2)",
            "RQ1_049-SLLR-SLLR-1996-V-2-CHANDRASENA-V.-KU_197_C02__12(2)",
            "RQ1_058-SLLR-SLLR-1996-V-2-ATHUKORALA-V.-JAY_209_C01__12(2)",
        ],
    },
    # -----------------------------------------------------------------------
    # Q2 — Article 11: right against torture
    # -----------------------------------------------------------------------
    {
        "query": "How has the court interpreted the right against torture under Article 11?",
        "expected_article": "11",
        "expected_frame_ids": [
            "RQ1_001-SLLR-SLLR-1989-V-1-SAMAN-V.-LEELADAS_002_C01__11",
            "RQ1_003-SLLR-SLLR-1999-V-2-SUMITH-JAYANTHA-D_004_C01__11",
            "RQ1_003-SLLR-SLLR-2003-1-SRIYANI-SILVA-WIFE-_005_C01__11",
            "RQ1_004-SLLR-SLLR-1999-V-2-SUBASINGHE-V.-POL_006_C01__11",
            "RQ1_004-SLLR-SLLR-2008-V-2-ROMESH-COORAY-V.-_007_C01__11",
        ],
    },
    # -----------------------------------------------------------------------
    # Q3 — Article 13(2): detention without trial / judicial oversight
    # -----------------------------------------------------------------------
    {
        "query": "What does Article 13(2) say about detention without trial?",
        "expected_article": "13(2)",
        "expected_frame_ids": [
            "RQ1_001-SLLR-SLLR_1994_V1-CHANNA_PIERIS__AND_001_C02__13(2)",
            "RQ1_009-SLLR-SLLR-1993-1-CHANDRASIRI-V.-GEN._019_C01__13(2)",
            "RQ1_016-SLLR-SLLR-1993-1-PALITHA-V.-O.-I.-C-_039_C01__13(2)",
            "RQ1_032-SLLR-SLLR_1992_V__1_-_SUBBASH_CHANDR_075_C02__13(2)",
            "RQ1_003-SLLR-SLLR-1999-V-2-SUMITH-JAYANTHA-D_005_C02__13(2)",
        ],
    },
    # -----------------------------------------------------------------------
    # Q4 — Article 14(1)(a): freedom of speech restricted by state
    # -----------------------------------------------------------------------
    {
        "query": "Has the freedom of speech under Article 14(1)(a) been restricted by the state?",
        "expected_article": "14(1)(a)",
        "expected_frame_ids": [
            "RQ1_001-SLLR-SLLR_1994_V1-CHANNA_PIERIS__AND_001_C01__14(1)(a)",
            "RQ1_012-SLLR-SLLR-1983-1-RATNASARA-THERO-V.-_021_C01__14(1)(a)",
            "RQ1_018-SLLR-SLLR-1996-1-ATUKORALE-AND-OTHER_030_C01__14(1)(a)",
            "RQ1_018-SLLR-SLLR-1999-V-2-SARANAPALA-V.-SOL_031_C01__14(1)(a)",
            "RQ1_034-SLLR-SLLR-1995-V-1-DESHAPRIYA-AND-AN_059_C01__14(1)(a)",
        ],
    },
    # -----------------------------------------------------------------------
    # Q5 — Article 12(1): equal protection / government employment policies
    # -----------------------------------------------------------------------
    {
        "query": "Cases where government employment policies violated the equal protection clause",
        "expected_article": "12",
        "expected_frame_ids": [
            "RQ1_001-SLLR-SLLR-2001-V-1-KAMALAWATHIE-AND-_004_C01__12(1)",
            "RQ1_002-SLLR-SLLR-1991-V-1-RAMUPPILLAI-V.-FE_007_C01__12(1)",
            "RQ1_002-SLLR-SLLR-1994-V1-PERERA-AND-NINE-OT_008_C01__12(1)",
        ],
    },
    # -----------------------------------------------------------------------
    # Q6 — No specific article: remedy for fundamental rights violations
    #        (expected_article=None → article-match always true)
    # -----------------------------------------------------------------------
    {
        "query": "What remedy did courts grant when fundamental rights were violated?",
        "expected_article": None,
        "expected_frame_ids": [
            "RQ1_001-SLLR-SLLR-1989-V-1-SAMAN-V.-LEELADAS_002_C01__11",
            "RQ1_003-SLLR-SLLR-1999-V-2-SUMITH-JAYANTHA-D_005_C02__13(2)",
            "RQ1_001-SLLR-SLLR_1994_V1-CHANNA_PIERIS__AND_001_C02__13(2)",
        ],
    },
    # -----------------------------------------------------------------------
    # Q7 — Article 13: police arrest constitutional challenge
    # -----------------------------------------------------------------------
    {
        "query": "Can a citizen challenge a police arrest under the constitution?",
        "expected_article": "13",
        "expected_frame_ids": [
            "RQ1_001-SLLR-SLLR_1994_V1-CHANNA_PIERIS__AND_001_C01__13(1)",
            "RQ1_003-SLLR-SLLR_1983-1-GUNAWARDENA_V._PERE_004_C01__13(1)",
            "RQ1_010-SLLR-SLLR-1991-V2-SIRISENA-AND-OTHER_021_C01__13(1)",
            "RQ1_007-SLLR-SLLR-2007-V-2-SARJUN-V.-KAMALDE_015_C01__13(1)",
        ],
    },
    # -----------------------------------------------------------------------
    # Q8 — Article 17: direct petitions to Supreme Court
    # -----------------------------------------------------------------------
    {
        "query": "Has the Supreme Court interpreted Article 17 to allow direct petitions?",
        "expected_article": "17",
        "expected_frame_ids": [
            "RQ1_001-SLLR-SLLR_1994_V1-CHANNA_PIERIS__AND_001_C02__17",
            "RQ1_003-SLLR-SLLR-2003-1-SRIYANI-SILVA-WIFE-_003_C01__17",
            "RQ1_008-SLLR-SLLR-2003-V-2-SRIYANI-SILVA-V.-_004_C01__17",
            "RQ1_012-SLLR-SLLR-1983-2-JANATHA-FINANCE-AND_008_C02__17",
            "RQ1_012-SLLR-SLLR-2007-V-2-RODRIGO-V.-IMALKA_009_C02__17",
        ],
    },
    # -----------------------------------------------------------------------
    # Q9 — Article 12: discrimination based on race or religion
    # -----------------------------------------------------------------------
    {
        "query": "Article 12 discrimination based on race or religion",
        "expected_article": "12",
        "expected_frame_ids": [
            "RQ1_012-SLLR-SLLR-2000-V-1-MANEL-FERNANDO-AN_063_C02__12(2)",
            "RQ1_050-SLLR-SLLR-2006-V-1-WEERAWANSHA-AND-O_200_C02__12(2)",
            "RQ1_036-SLLR-SLLR-2004-V-3-KONESHALINGAM-V.-_177_C02__12(2)",
        ],
    },
    # -----------------------------------------------------------------------
    # Q10 — Article 14(1)(h): freedom of movement / right to travel
    # -----------------------------------------------------------------------
    {
        "query": "Freedom of movement or right to travel — has the court ever restricted it?",
        "expected_article": "14",
        "expected_frame_ids": [
            "RQ1_007-SLLR-SLLR-2007-V-2-SARJUN-V.-KAMALDE_013_C01__14(1)(h)",
            "RQ1_011-SLLR-SLLR-2003-1-THAVANEETHAN-V.-DAY_020_C02__14(1)(h)",
            "RQ1_012-SLLR-SLLR-2007-V-2-RODRIGO-V.-IMALKA_022_C01__14(1)(h)",
            "RQ1_013-SLLR-SLLR-2002-3-SOLOMAN-DIAS-V.-SEC_023_C01__14(1)(h)",
            "RQ1_015-SLLR-SLLR-2002-3-VADIVELU-V.-OFFICER_028_C01__14(1)(h)",
        ],
    },
]

K_VALUES = [1, 3, 5, 10]


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

    try:
        from openai import OpenAI
        from config.settings import OPENAI_API_KEY
        client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
    except Exception:
        client = None
        print("Warning: OpenAI client unavailable — running without LLM query parsing.")

    recalls: dict[int, list[float]] = {k: [] for k in K_VALUES}
    rr_scores: list[float] = []
    article_matches: list[bool] = []

    print(f"\nRunning evaluation over {len(GROUND_TRUTH)} queries...\n")
    print("-" * 70)

    for i, test in enumerate(GROUND_TRUTH, start=1):
        query = test["query"]
        expected_ids = test.get("expected_frame_ids") or []
        expected_art = test.get("expected_article")

        parsed = parse_query(query, client)

        # Only apply pre-filtering when the parser identified a specific clause
        if parsed.query_type == "clause_first":
            article_filter = parsed.article
            article_base_filter = parsed.article_base
        else:
            article_filter = None
            article_base_filter = None

        result = service.search_frames(
            query_text=query,
            top_k=10,
            article_filter=article_filter,
            article_base_filter=article_base_filter,
        )
        retrieved = result.get("results", [])
        retrieved_ids = [r.get("frame_identifier") or "" for r in retrieved]

        art_ok = article_match(parsed.article or parsed.article_base, expected_art)
        article_matches.append(art_ok)

        for k in K_VALUES:
            v = recall_at_k(retrieved_ids, expected_ids, k)
            if v is not None:
                recalls[k].append(v)

        rr = reciprocal_rank(retrieved_ids, expected_ids)
        if rr is not None:
            rr_scores.append(rr)

        art_flag = "ART✓" if art_ok else "ART✗"
        rr_flag = f"RR={rr:.2f}" if rr is not None else "RR=N/A"
        r5 = recall_at_k(retrieved_ids, expected_ids, 5)
        r5_flag = f"R@5={r5:.0f}" if r5 is not None else "R@5=N/A"
        print(f"[{i:02d}] {art_flag} {rr_flag} {r5_flag} | {query[:52]}...")
        if retrieved_ids:
            print(f"       Top-3 returned: {retrieved_ids[:3]}")

    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    for k in K_VALUES:
        if recalls[k]:
            avg = sum(recalls[k]) / len(recalls[k])
            print(f"  Recall@{k:<3} = {avg:.3f}  (over {len(recalls[k])} queries with ground truth)")
        else:
            print(f"  Recall@{k:<3} = N/A   (no ground truth populated)")
    if rr_scores:
        mrr = sum(rr_scores) / len(rr_scores)
        print(f"  MRR          = {mrr:.3f}")
    else:
        print("  MRR          = N/A   (no ground truth populated)")
    art_rate = sum(article_matches) / len(article_matches) if article_matches else 0.0
    print(f"  Article-Match Rate = {art_rate:.3f}  (over {len(article_matches)} queries)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_evaluation()
