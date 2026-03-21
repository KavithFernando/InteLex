from typing import Any, Dict, List, Optional

from db.connection import get_connection


class CaseRepository:
    """Corpus schema: cases.id (BIGINT), case_identifier, interpretation_frames."""

    def fetch_cases_with_full_text(self) -> List[Dict[str, Any]]:
        """Legacy hook for old index pipeline; corpus uses PDFs instead of full_text."""
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """
            SELECT id AS case_id, case_identifier, case_title, decision_date,
                   pdf_relative_path
            FROM cases
            """
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows

    def fetch_corpus_case_summaries(self, case_internal_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Retrieval cards: one row per case internal id, with distinct constitution
        clauses attached to any frame for that case.
        """
        if not case_internal_ids:
            return []

        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        placeholders = ",".join(["%s"] * len(case_internal_ids))
        cur.execute(
            f"""
            SELECT id, case_identifier, case_title, decision_date
            FROM cases
            WHERE id IN ({placeholders})
            """,
            case_internal_ids,
        )
        case_rows = {int(r["id"]): dict(r) for r in cur.fetchall()}

        cur.execute(
            f"""
            SELECT intf.case_id, cc.article, cc.clause_text AS text
            FROM interpretation_frames intf
            JOIN constitution_clauses cc ON cc.clause_id = intf.clause_id
            WHERE intf.case_id IN ({placeholders})
            GROUP BY intf.case_id, cc.clause_id, cc.article, cc.clause_text, cc.subclause
            ORDER BY intf.case_id, cc.article, cc.subclause
            """,
            case_internal_ids,
        )
        clauses_by_case: Dict[int, List[Dict[str, Any]]] = {cid: [] for cid in case_internal_ids}
        seen: Dict[int, set] = {cid: set() for cid in case_internal_ids}
        for r in cur.fetchall():
            cid = int(r["case_id"])
            art = (r.get("article") or "").strip()
            tx = (r.get("text") or "").strip()
            key = (art, tx[:500])
            if key in seen[cid]:
                continue
            seen[cid].add(key)
            clauses_by_case.setdefault(cid, []).append({"article": art, "text": tx})

        cur.close()
        conn.close()

        out: List[Dict[str, Any]] = []
        for cid in case_internal_ids:
            row = case_rows.get(cid)
            if not row:
                continue
            out.append(
                {
                    "case_id": str(cid),
                    "case_identifier": row.get("case_identifier"),
                    "case_title": row.get("case_title"),
                    "decision_date": str(row["decision_date"]) if row.get("decision_date") else None,
                    "clauses": clauses_by_case.get(cid, []),
                }
            )
        return out

    def fetch_case_by_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Lookup by internal numeric id (string) or case_identifier.
        """
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        if case_id.isdigit():
            cur.execute(
                """
                SELECT id, case_identifier, case_title, court_name, decision_date,
                       source_citation, pdf_relative_path, ingest_metadata
                FROM cases
                WHERE id = %s
                """,
                (int(case_id),),
            )
        else:
            cur.execute(
                """
                SELECT id, case_identifier, case_title, court_name, decision_date,
                       source_citation, pdf_relative_path, ingest_metadata
                FROM cases
                WHERE case_identifier = %s
                """,
                (case_id,),
            )
        row = cur.fetchone()
        if not row:
            cur.close()
            conn.close()
            return None

        case_pk = int(row["id"])
        out: Dict[str, Any] = {
            "case_id": str(case_pk),
            "case_identifier": row.get("case_identifier"),
            "case_title": row.get("case_title"),
            "court_name": row.get("court_name"),
            "decision_date": str(row["decision_date"]) if row.get("decision_date") else None,
            "legal_issue": None,
            "petitioner_claim": None,
            "respondent_argument": None,
            "interpretation_summary": None,
            "outcome": None,
            "source": row.get("source_citation"),
            "full_text": None,
            "pdf_relative_path": row.get("pdf_relative_path"),
            "judges": [],
            "clauses": [],
            "keywords": [],
            "precedents_cited": [],
            "principles_established": [],
        }

        cur.execute(
            """
            SELECT DISTINCT cc.article, cc.clause_text AS text
            FROM interpretation_frames intf
            JOIN constitution_clauses cc ON cc.clause_id = intf.clause_id
            WHERE intf.case_id = %s
            ORDER BY cc.article, cc.subclause
            """,
            (case_pk,),
        )
        out["clauses"] = [
            {"article": r["article"], "text": r["text"]} for r in cur.fetchall()
        ]

        cur.execute(
            """
            SELECT legal_issue, petitioner_claim, respondent_argument,
                   interpretation_summary, application_to_facts,
                   holding, disposition, remedy_or_orders
            FROM interpretation_frames
            WHERE case_id = %s
            ORDER BY id
            LIMIT 1
            """,
            (case_pk,),
        )
        fr = cur.fetchone()
        if fr:
            out["legal_issue"] = fr.get("legal_issue")
            out["petitioner_claim"] = fr.get("petitioner_claim")
            out["respondent_argument"] = fr.get("respondent_argument")
            parts = []
            if fr.get("interpretation_summary"):
                parts.append(fr["interpretation_summary"])
            if fr.get("application_to_facts"):
                parts.append(fr["application_to_facts"])
            out["interpretation_summary"] = "\n\n".join(parts) if parts else None
            oh = []
            if fr.get("holding"):
                oh.append(fr["holding"])
            if fr.get("disposition"):
                oh.append(f"Disposition: {fr['disposition']}")
            if fr.get("remedy_or_orders"):
                oh.append(fr["remedy_or_orders"])
            out["outcome"] = "\n".join(oh) if oh else None

        cur.execute(
            """
            SELECT DISTINCT fp.principle_text
            FROM frame_principles fp
            JOIN interpretation_frames intf ON intf.id = fp.interpretation_frame_id
            WHERE intf.case_id = %s
            ORDER BY fp.id
            LIMIT 200
            """,
            (case_pk,),
        )
        out["principles_established"] = [r["principle_text"] for r in cur.fetchall()]

        cur.execute(
            """
            SELECT DISTINCT pc.citation
            FROM frame_precedent_links fpl
            JOIN precedent_citations pc ON pc.precedent_id = fpl.precedent_id
            JOIN interpretation_frames intf ON intf.id = fpl.interpretation_frame_id
            WHERE intf.case_id = %s
            ORDER BY pc.citation
            LIMIT 200
            """,
            (case_pk,),
        )
        out["precedents_cited"] = [r["citation"] for r in cur.fetchall()]

        cur.close()
        conn.close()
        return out


case_repo = CaseRepository()
