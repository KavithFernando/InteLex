"""
CLI to run case search (FAISS + DB). Run from backend/ or set PYTHONPATH=backend.

  python scripts/search_cases.py "legal query text"
  python scripts/search_cases.py "query" --top 5
"""
import argparse
import sys
import os

# Ensure backend is on path when run from repo root or scripts/
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services.retrieval import search_cases

def main():
    parser = argparse.ArgumentParser(description="Search cases by legal text (FAISS + DB).")
    parser.add_argument("query", help="Legal text or query to search for.")
    parser.add_argument("--top", type=int, default=10, help="Max number of cases to return (default 10).")
    args = parser.parse_args()

    out = search_cases(query_text=args.query.strip(), top_cases=args.top)
    results = out.get("results", [])

    if not results:
        print("No matches.")
        return

    print(f"Found {len(results)} case(s):\n")
    for i, r in enumerate(results, 1):
        print(f"  {i}. [{r.get('case_id')}] {r.get('case_title') or '(no title)'}")
        print(f"     score={r.get('score', 0):.4f}  date={r.get('decision_date') or '—'}")
        if r.get("chunk_text"):
            snippet = (r["chunk_text"] or "")[:200].replace("\n", " ")
            print(f"     snippet: {snippet}...")
        print()


if __name__ == "__main__":
    main()
