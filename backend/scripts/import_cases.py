import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import re
from datetime import datetime

from mysql.connector import Error

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from config import DATA_JSON_PATH
from db.connection import get_connection


# ---------------------------
# Helpers: safe get-or-create
# ---------------------------
# Month names (full) for parsing "17 December 1997" style dates
_MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

def normalize_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str:
        return None
    date_str = str(date_str).strip()
    # Already ISO format YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    # "17 December 1997" style: day month_name year
    m = re.match(r'^(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})$', date_str)
    if m:
        day_str, month_str, year_str = m.groups()
        month_lower = month_str.lower()
        if month_lower in _MONTH_NAMES:
            month_num = _MONTH_NAMES[month_lower]
            day, year = int(day_str), int(year_str)
            try:
                dt = datetime(year, month_num, day)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
    return None


def get_or_create_id(
    cur,
    select_sql: str,
    insert_sql: str,
    select_params: Tuple[Any, ...],
    insert_params: Tuple[Any, ...],
) -> int:
    """
    Returns existing id if found, otherwise inserts and returns new id.
    """
    cur.execute(select_sql, select_params)
    row = cur.fetchone()
    if row:
        return int(row[0])

    cur.execute(insert_sql, insert_params)
    return int(cur.lastrowid)


def normalize_str(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = str(s).strip()
    return s if s else None


def load_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be a list of cases.")
    return data


# ---------------------------
# Insert functions
# ---------------------------
def upsert_case(cur, case_obj: Dict[str, Any], court_id: int) -> str:
    """
    Inserts a case row. If case_id already exists, updates the case text fields.
    Returns case_id.
    """
    case_id = normalize_str(case_obj.get("case_id"))
    if not case_id:
        raise ValueError("Missing case_id in a record.")

    # Basic fields
    case_title = normalize_str(case_obj.get("case_title")) or ""
    decision_date = normalize_date(case_obj.get("date"))  # "YYYY-MM-DD" or None
    legal_issue = normalize_str(case_obj.get("legal_issue"))
    petitioner_claim = normalize_str(case_obj.get("petitioner_claim"))
    respondent_argument = normalize_str(case_obj.get("respondent_argument"))
    interpretation_summary = normalize_str(case_obj.get("interpretation_summary"))
    outcome = normalize_str(case_obj.get("outcome"))
    source = normalize_str(case_obj.get("source"))
    full_text = normalize_str(case_obj.get("full_text"))

    # Try insert; if exists, update
    insert_sql = """
        INSERT INTO cases (
            case_id, case_title, court_id, decision_date,
            legal_issue, petitioner_claim, respondent_argument,
            interpretation_summary, outcome, source, full_text
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    update_sql = """
        UPDATE cases
        SET case_title=%s,
            court_id=%s,
            decision_date=%s,
            legal_issue=%s,
            petitioner_claim=%s,
            respondent_argument=%s,
            interpretation_summary=%s,
            outcome=%s,
            source=%s,
            full_text=%s
        WHERE case_id=%s
    """

    try:
        cur.execute(
            insert_sql,
            (
                case_id,
                case_title,
                court_id,
                decision_date,
                legal_issue,
                petitioner_claim,
                respondent_argument,
                interpretation_summary,
                outcome,
                source,
                full_text,
            ),
        )
    except Error as e:
        # Duplicate primary key: update instead
        if e.errno in (1062,):  # ER_DUP_ENTRY
            cur.execute(
                update_sql,
                (
                    case_title,
                    court_id,
                    decision_date,
                    legal_issue,
                    petitioner_claim,
                    respondent_argument,
                    interpretation_summary,
                    outcome,
                    source,
                    full_text,
                    case_id,
                ),
            )
        else:
            raise

    return case_id


def link_case_judges(cur, case_id: str, judges: List[str]) -> None:
    # Prepare statements
    sel = "SELECT judge_id FROM judges WHERE name=%s"
    ins = "INSERT INTO judges (name) VALUES (%s)"

    link_sql = """
        INSERT INTO case_judges (case_id, judge_id, judge_order)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE judge_order=VALUES(judge_order)
    """

    for idx, jname in enumerate(judges, start=1):
        jname = normalize_str(jname)
        if not jname:
            continue
        judge_id = get_or_create_id(cur, sel, ins, (jname,), (jname,))
        cur.execute(link_sql, (case_id, judge_id, idx))


def link_case_clauses(cur, case_id: str, clauses: List[Dict[str, Any]]) -> None:
    # clauses table uniqueness is (article, text(255)); we will select by article+prefix
    sel = "SELECT clause_id FROM clauses WHERE article=%s AND LEFT(text, 255)=LEFT(%s, 255) LIMIT 1"
    ins = "INSERT INTO clauses (article, text) VALUES (%s, %s)"

    link_sql = """
        INSERT INTO case_clauses (case_id, clause_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE clause_id=clause_id
    """

    for c in clauses:
        article = normalize_str(c.get("article"))
        text = normalize_str(c.get("text"))
        if not article or not text:
            continue
        clause_id = get_or_create_id(cur, sel, ins, (article, text), (article, text))
        cur.execute(link_sql, (case_id, clause_id))


def link_case_keywords(cur, case_id: str, keywords: List[str]) -> None:
    sel = "SELECT keyword_id FROM keywords WHERE keyword=%s"
    ins = "INSERT INTO keywords (keyword) VALUES (%s)"

    link_sql = """
        INSERT INTO case_keywords (case_id, keyword_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE keyword_id=keyword_id
    """

    for kw in keywords:
        kw = normalize_str(kw)
        if not kw:
            continue
        keyword_id = get_or_create_id(cur, sel, ins, (kw,), (kw,))
        cur.execute(link_sql, (case_id, keyword_id))


def link_case_precedents(cur, case_id: str, precedents: List[str]) -> None:
    sel = "SELECT precedent_id FROM precedents WHERE citation=%s"
    ins = "INSERT INTO precedents (citation) VALUES (%s)"

    link_sql = """
        INSERT INTO case_precedents (case_id, precedent_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE precedent_id=precedent_id
    """

    for p in precedents:
        p = normalize_str(p)
        if not p:
            continue
        precedent_id = get_or_create_id(cur, sel, ins, (p,), (p,))
        cur.execute(link_sql, (case_id, precedent_id))


def insert_case_principles(cur, case_id: str, principles: List[str]) -> None:
    """
    For MVP simplicity: delete existing principles for the case and re-insert in order.
    (This keeps the table consistent if you re-run imports.)
    """
    cur.execute("DELETE FROM case_principles WHERE case_id=%s", (case_id,))

    ins = """
        INSERT INTO case_principles (case_id, principle_text, principle_order)
        VALUES (%s, %s, %s)
    """
    for idx, pr in enumerate(principles, start=1):
        pr = normalize_str(pr)
        if not pr:
            continue
        cur.execute(ins, (case_id, pr, idx))


# ---------------------------
# Main import routine
# ---------------------------
def main():
    json_path = DATA_JSON_PATH
    if len(sys.argv) >= 2:
        json_path = sys.argv[1]

    cases = load_json(json_path)
    print(f"Loaded {len(cases)} case records from {json_path}")

    conn = None
    try:
        conn = get_connection()
        conn.autocommit = False  # we control transactions
        cur = conn.cursor()

        # Prepared SQL for court get-or-create
        court_sel = "SELECT court_id FROM courts WHERE name=%s"
        court_ins = "INSERT INTO courts (name) VALUES (%s)"

        inserted = 0

        for i, case_obj in enumerate(cases, start=1):
            court_name = normalize_str(case_obj.get("court")) or "Unknown Court"
            court_id = get_or_create_id(cur, court_sel, court_ins, (court_name,), (court_name,))

            case_id = upsert_case(cur, case_obj, court_id)

            # Link judges
            judges = case_obj.get("judges") or []
            if isinstance(judges, list):
                link_case_judges(cur, case_id, judges)

            # Link clauses
            clauses = case_obj.get("clauses") or []
            if isinstance(clauses, list):
                link_case_clauses(cur, case_id, clauses)

            # Link keywords
            keywords = case_obj.get("keywords") or []
            if isinstance(keywords, list):
                link_case_keywords(cur, case_id, keywords)

            # Link precedents
            precedents = case_obj.get("precedents_cited") or []
            if isinstance(precedents, list):
                link_case_precedents(cur, case_id, precedents)

            # Insert principles
            principles = case_obj.get("principles_established") or []
            if isinstance(principles, list):
                insert_case_principles(cur, case_id, principles)

            inserted += 1

            if i % 25 == 0:
                print(f"Processed {i}/{len(cases)}...")

        conn.commit()
        print(f"Import complete. Processed {inserted} cases.")

    except Exception as e:
        if conn:
            conn.rollback()
        print("Import failed. Rolled back transaction.")
        raise e
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    main()
