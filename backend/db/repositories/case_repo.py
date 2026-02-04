"""
Case-related database queries.
"""
from typing import Any, Dict, List

from db.connection import get_connection


def fetch_cases_with_full_text() -> List[Dict[str, Any]]:
    """
    Fetch all cases with full_text and fields needed for building case representation.
    Used by index_cases script.
    """
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT case_id, case_title, legal_issue, petitioner_claim,
               respondent_argument, outcome, interpretation_summary,
               full_text
        FROM cases
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def fetch_retrieval_summaries(case_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Fetch case_id, case_title, decision_date, and clauses for the given case_ids.
    Returns list in same order as case_ids; each item has clauses as list of {article, text}.
    Used for API retrieval_result (lightweight list for response body).
    """
    if not case_ids:
        return []

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    placeholders = ",".join(["%s"] * len(case_ids))

    cur.execute(
        f"""
        SELECT case_id, case_title, decision_date
        FROM cases
        WHERE case_id IN ({placeholders})
        """,
        case_ids,
    )
    case_rows = {r["case_id"]: dict(r) for r in cur.fetchall()}

    cur.execute(
        f"""
        SELECT cc.case_id, cl.article, cl.text
        FROM case_clauses cc
        JOIN clauses cl ON cl.clause_id = cc.clause_id
        WHERE cc.case_id IN ({placeholders})
        """,
        case_ids,
    )
    clauses_by_case: Dict[str, List[Dict[str, Any]]] = {cid: [] for cid in case_ids}
    for r in cur.fetchall():
        clauses_by_case.setdefault(r["case_id"], []).append(
            {"article": r["article"], "text": r["text"]}
        )

    cur.close()
    conn.close()

    out = []
    for cid in case_ids:
        row = case_rows.get(cid)
        if not row:
            continue
        d = {
            "case_id": cid,
            "case_title": row.get("case_title"),
            "decision_date": str(row["decision_date"]) if row.get("decision_date") else None,
            "clauses": clauses_by_case.get(cid, []),
        }
        out.append(d)
    return out
