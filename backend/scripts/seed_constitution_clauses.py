"""
Load constitution_clauses from backend/data/articles.json (Chapter III FR excerpt).

Run from backend/:
  python scripts/seed_constitution_clauses.py

Requires DB_* env vars and existing schema (constitution_clauses table).
"""
import json
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

ARTICLES_PATH = os.path.join(_backend_dir, "data", "articles.json")

from db.connection import get_connection


def main() -> None:
    with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    articles = data.get("articles") or []
    if not articles:
        raise SystemExit("No articles[] in articles.json")

    conn = get_connection()
    cur = conn.cursor()
    sql = """
        INSERT INTO constitution_clauses (article, subclause, clause_text)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE clause_text = VALUES(clause_text)
    """

    n = 0
    for art in articles:
        article = str(art.get("article", "")).strip()
        if not article:
            continue
        for row in art.get("clauses") or []:
            sub = row.get("clause")
            subclause = "" if sub is None else str(sub).strip()
            text = (row.get("text") or "").strip()
            if not text:
                continue
            cur.execute(sql, (article, subclause, text))
            n += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Upserted {n} constitution clause row(s) from {ARTICLES_PATH}")


if __name__ == "__main__":
    main()
