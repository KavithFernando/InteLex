"""
CLI: clause-frame search (FAISS + corpus DB). Run from backend/:

  python scripts/search_cases.py "legal query text"
  python scripts/search_cases.py "query" --top 5
"""
import argparse
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services.case_search import CaseSearchService
from services.clause_retrieval import ClauseFrameRetrievalService
from db.repositories.case_repo import case_repo


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search corpus by legal text (clause-frame FAISS + DB).",
    )
    parser.add_argument("query", help="Legal text or query to search for.")
    parser.add_argument("--top", type=int, default=10, help="Max cases (default 10).")
    args = parser.parse_args()

    svc = CaseSearchService(ClauseFrameRetrievalService(), case_repo)
    out = svc.run_case_search(query_text=args.query.strip(), top_k=args.top)
    results = out.get("retrieval_result", [])

    if not results:
        print("No matches.")
        return

    print(f"Found {len(results)} case(s):\n")
    for i, r in enumerate(results, 1):
        print(f"  {i}. [case id={r.get('case_id')}] {r.get('case_title') or '(no title)'}")
        if r.get("case_identifier"):
            print(f"     identifier: {r['case_identifier'][:80]}...")
        print(f"     score={r.get('score', 0):.4f}  date={r.get('decision_date') or '—'}")
        if r.get("matched_article"):
            print(f"     matched article: {r['matched_article']}")
        if r.get("matched_clause_text"):
            sn = (r["matched_clause_text"] or "")[:180].replace("\n", " ")
            print(f"     clause: {sn}...")
        print()


if __name__ == "__main__":
    main()
