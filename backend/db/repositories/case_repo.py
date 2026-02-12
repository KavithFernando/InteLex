from typing import Any, Dict, List, Optional

from db.connection import get_connection


class CaseRepository:

    def fetch_cases_with_full_text(self) -> List[Dict[str, Any]]:
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

    def fetch_case_summaries(self, case_ids: List[str]) -> List[Dict[str, Any]]:
        if not case_ids:
            return []

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        placeholders = ",".join(["%s"] * len(case_ids))

        # Fetch case headers
        cur.execute(
            f"""
            SELECT case_id, case_title, decision_date
            FROM cases
            WHERE case_id IN ({placeholders})
            """,
            case_ids,
        )
        case_rows = {r["case_id"]: dict(r) for r in cur.fetchall()}

        # Fetch clauses for all cases
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

        # Preserve input order when building results
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

    def fetch_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        cur.execute(
            """
            SELECT c.case_id, c.case_title, c.decision_date, c.legal_issue,
                   c.petitioner_claim, c.respondent_argument, c.interpretation_summary,
                   c.outcome, c.source, c.full_text, co.name AS court_name
            FROM cases c
            JOIN courts co ON co.court_id = c.court_id
            WHERE c.case_id = %s
            """,
            (case_id,),
        )
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return None

        out: Dict[str, Any] = {
            "case_id": row["case_id"],
            "case_title": row.get("case_title"),
            "court_name": row.get("court_name"),
            "decision_date": str(row["decision_date"]) if row.get("decision_date") else None,
            "legal_issue": row.get("legal_issue"),
            "petitioner_claim": row.get("petitioner_claim"),
            "respondent_argument": row.get("respondent_argument"),
            "interpretation_summary": row.get("interpretation_summary"),
            "outcome": row.get("outcome"),
            "source": row.get("source"),
            "full_text": row.get("full_text"),
            "judges": [],
            "clauses": [],
            "keywords": [],
            "precedents_cited": [],
            "principles_established": [],
        }

        cur.execute(
            """
            SELECT j.name
            FROM case_judges cj
            JOIN judges j ON j.judge_id = cj.judge_id
            WHERE cj.case_id = %s
            ORDER BY cj.judge_order ASC, j.name ASC
            """,
            (case_id,),
        )
        out["judges"] = [r["name"] for r in cur.fetchall()]

        cur.execute(
            """
            SELECT cl.article, cl.text
            FROM case_clauses cc
            JOIN clauses cl ON cl.clause_id = cc.clause_id
            WHERE cc.case_id = %s
            """,
            (case_id,),
        )
        out["clauses"] = [{"article": r["article"], "text": r["text"]} for r in cur.fetchall()]

        cur.execute(
            """
            SELECT k.keyword
            FROM case_keywords ck
            JOIN keywords k ON k.keyword_id = ck.keyword_id
            WHERE ck.case_id = %s
            """,
            (case_id,),
        )
        out["keywords"] = [r["keyword"] for r in cur.fetchall()]

        cur.execute(
            """
            SELECT p.citation
            FROM case_precedents cp
            JOIN precedents p ON p.precedent_id = cp.precedent_id
            WHERE cp.case_id = %s
            """,
            (case_id,),
        )
        out["precedents_cited"] = [r["citation"] for r in cur.fetchall()]

        cur.execute(
            """
            SELECT principle_text
            FROM case_principles
            WHERE case_id = %s
            ORDER BY principle_order ASC, principle_id ASC
            """,
            (case_id,),
        )
        out["principles_established"] = [r["principle_text"] for r in cur.fetchall()]

        cur.close()
        conn.close()
        return out


case_repo = CaseRepository()
