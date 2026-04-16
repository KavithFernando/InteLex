"""
Run:
  python scripts/index_clauses.py
  python scripts/index_clauses.py --dry-run

DB needs to be populated with interpreation frames
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from config.settings import CLAUSE_INDEX_PATH, CLAUSE_MAP_PATH, EMBED_MODEL
from db.connection import get_connection


def build_embedding_text(row: dict) -> str:
    parts = [
        row.get("legal_issue") or "",
        row.get("petitioner_claim") or "",
        row.get("interpretation_summary") or "",
        row.get("application_to_facts") or "",
        row.get("principles_agg") or "",
        row.get("why_this_clause_matters") or "",
        row.get("holding") or "",
        # Clause text last for keeping a grounding
        f"Article {row.get('article', '')} {row.get('subclause', '')}: {row.get('clause_text', '')}",
    ]
    return " ".join(p.strip() for p in parts if p and p.strip())


def fetch_frame_clause_rows():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """
        SELECT
            intf.id             AS interpretation_frame_id,
            intf.frame_identifier,
            intf.legal_issue,
            intf.petitioner_claim,
            intf.interpretation_summary,
            intf.application_to_facts,
            intf.holding,
            intf.disposition,
            intf.why_this_clause_matters,
            intf.relevance_level,
            intf.match_type,
            c.id                AS case_id,
            c.case_identifier,
            c.case_title,
            c.decision_date,
            cc.clause_id,
            cc.article,
            cc.subclause,
            cc.clause_text,
            (
                SELECT GROUP_CONCAT(fp.principle_text ORDER BY fp.id SEPARATOR ' | ')
                FROM frame_principles fp
                WHERE fp.interpretation_frame_id = intf.id
            ) AS principles_agg,
            (
                SELECT GROUP_CONCAT(fkf.fact_text ORDER BY fkf.id SEPARATOR ' | ')
                FROM frame_key_facts fkf
                WHERE fkf.interpretation_frame_id = intf.id
            ) AS key_facts_agg
        FROM interpretation_frames AS intf
        INNER JOIN cases AS c ON c.id = intf.case_id
        INNER JOIN constitution_clauses AS cc ON cc.clause_id = intf.clause_id
        ORDER BY intf.id
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FAISS clause-frame index.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load DB and print counts/sample text only",
    )
    args = parser.parse_args()

    rows = fetch_frame_clause_rows()
    if not rows:
        print("No rows returned. Import interpretation_frames first.", file=sys.stderr)
        sys.exit(1)

    texts = []
    row_map = []
    for r in rows:
        t = build_embedding_text(r)
        texts.append(t)
        dd = r.get("decision_date")
        art = str(r["article"]).strip()
        sub = (r.get("subclause") or "").strip()
        row_map.append({
            "faiss_id": int(len(row_map)),
            "interpretation_frame_id": int(r["interpretation_frame_id"]),
            "frame_identifier": r.get("frame_identifier"),
            "case_id": int(r["case_id"]),
            "case_identifier": r.get("case_identifier"),
            "case_title": r.get("case_title"),
            "decision_date": str(dd) if dd is not None else None,
            "clause_id": int(r["clause_id"]),
            "article": art,
            "article_base": art.split("(")[0].strip(),
            "subclause": sub,
            "clause_text": (r.get("clause_text") or "").strip(),
            "disposition": (r.get("disposition") or "").strip(),
            "relevance_level": (r.get("relevance_level") or "").strip(),
            "match_type": (r.get("match_type") or "").strip(),
        })

    print(f"Loaded {len(rows)} interpretation_frame row(s) for indexing.")

    if args.dry_run:
        print("Sample embedding text (first row):\n---")
        print(texts[0][:1200])
        print("---")
        return

    os.makedirs(os.path.dirname(CLAUSE_INDEX_PATH) or ".", exist_ok=True)

    model = SentenceTransformer(EMBED_MODEL)
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    embeddings = np.asarray(embeddings, dtype="float32")
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    faiss.write_index(index, CLAUSE_INDEX_PATH)
    payload = {
        "embed_model": EMBED_MODEL,
        "count_rows": len(row_map),
        "row_map": row_map,
    }
    with open(CLAUSE_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Wrote FAISS index: {CLAUSE_INDEX_PATH}")
    print(f"Wrote map:         {CLAUSE_MAP_PATH}")
    print(f"Total vectors:     {len(row_map)}")


if __name__ == "__main__":
    main()
