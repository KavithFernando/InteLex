from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from config.settings import FRAMES_DIR, MANIFEST_PATH, PDF_RELATIVE_PREFIX
from db.connection import get_connection


def parse_article_ref(raw: str) -> Tuple[str, str]:
    """
    Map frame clause.article strings to constitution_clauses (article, subclause).

    DB / articles.json store subclause like '(1)', '(2)', '(1)(a)' (with parentheses).
    Frame strings are '12(1)', '14(1)(a)', '17', '14A'.
    """
    raw = (raw or "").strip()
    if not raw:
        return "", ""
    # Article prefix: 10, 12, 14, 14A, 15, ...
    m = re.match(r"^([0-9]+[A-Za-z]?)(.*)$", raw)
    if not m:
        return raw, ""
    article = m.group(1)
    rest = (m.group(2) or "").strip()
    if not rest:
        return article, ""
    # Remainder is e.g. '(1)', '(1)(a)', '(16)' — keep as-is for DB lookup
    if rest.startswith("("):
        return article, rest
    # Rare: legacy '12-1' style — normalize to '(1)'-style if possible
    return article, rest


def subclause_lookup_variants(subclause: str) -> List[str]:
    """
    Try DB key as stored, and bare-number legacy form '1' -> '(1)' for lookup.
    """
    s = (subclause or "").strip()
    if not s:
        return [""]
    out = [s]
    if not s.startswith("("):
        out.append(f"({s})")
    # If DB has '(1)' but someone passed '1' only — already handled
    # Strip one layer: '(1)' -> try '1' if first lookup fails (older seeds)
    if s.startswith("(") and s.endswith(")") and len(s) > 2:
        inner = s[1:-1].strip()
        if inner and inner not in out:
            out.append(inner)
    # Dedupe preserving order
    seen: set = set()
    uniq: List[str] = []
    for x in out:
        if x not in seen:
            seen.add(x)
            uniq.append(x)
    return uniq


def normalize_basename(name: str) -> str:
    """Collapse whitespace for fuzzy manifest <-> disk matching."""
    return "".join(name.lower().split())


def build_manifest_lookup(manifest: Dict[str, Any]) -> Dict[str, Tuple[str, Dict[str, Any]]]:
    """
    Map normalized output json basename -> (pdf_filename, manifest_file_entry).
    """
    out: Dict[str, Tuple[str, Dict[str, Any]]] = {}
    for entry in manifest.get("files") or []:
        pdf = entry.get("pdf") or ""
        for rel in entry.get("output_json_files") or []:
            bn = os.path.basename(rel).strip()
            if not bn:
                continue
            out[normalize_basename(bn)] = (pdf, entry)
            out[bn.lower()] = (pdf, entry)
    return out


def resolve_pdf_path(pdf_filename: str) -> str:
    p = (PDF_RELATIVE_PREFIX or "").replace("\\", "/").strip()
    if p and not p.endswith("/"):
        p += "/"
    return p + pdf_filename.replace("\\", "/")


def load_clause_map(cur) -> None:
    """Populate module-level cache: (article, subclause) -> clause_id."""
    global _CLAUSE_BY_ARTICLE_SUB
    cur.execute(
        "SELECT clause_id, article, subclause FROM constitution_clauses"
    )
    _CLAUSE_BY_ARTICLE_SUB = {}
    for row in cur.fetchall():
        cid, art, sub = row[0], str(row[1]).strip(), (row[2] or "").strip()
        _CLAUSE_BY_ARTICLE_SUB[(art, sub)] = cid


_CLAUSE_BY_ARTICLE_SUB: Dict[Tuple[str, str], int] = {}


def resolve_constitution_clause_id(cur, article: str, subclause: str, clause_text: Optional[str]) -> Optional[int]:
    for sub in subclause_lookup_variants(subclause):
        key = (article, sub)
        if key in _CLAUSE_BY_ARTICLE_SUB:
            return _CLAUSE_BY_ARTICLE_SUB[key]

    # Fallback: exact clause_text match (frame often echoes constitution text)
    if clause_text and clause_text.strip():
        cur.execute(
            """
            SELECT clause_id FROM constitution_clauses
            WHERE article = %s AND clause_text = %s
            LIMIT 1
            """,
            (article, clause_text.strip()),
        )
        row = cur.fetchone()
        if row:
            return int(row[0])
    return None


def get_or_create_precedent_id(cur, citation: str) -> int:
    citation = (citation or "").strip()
    if len(citation) > 512:
        citation = citation[:509] + "..."
    cur.execute(
        "SELECT precedent_id FROM precedent_citations WHERE citation = %s",
        (citation,),
    )
    row = cur.fetchone()
    if row:
        return int(row[0])
    cur.execute("INSERT INTO precedent_citations (citation) VALUES (%s)", (citation,))
    return int(cur.lastrowid)


def upsert_case_compat(
    cur,
    case_identifier: str,
    case_title: str,
    court_name: Optional[str],
    decision_date: Optional[str],
    source_citation: Optional[str],
    pdf_relative_path: Optional[str],
    ingest_metadata: Optional[Dict[str, Any]],
) -> int:
    """Same as upsert_case but without INSERT...AS new (older MySQL)."""
    ingest_json = json.dumps(ingest_metadata, ensure_ascii=False) if ingest_metadata else None
    try:
        cur.execute(
            """
            INSERT INTO cases (
                case_identifier, case_title, court_name, decision_date,
                source_citation, pdf_relative_path, ingest_metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                case_title = VALUES(case_title),
                court_name = COALESCE(VALUES(court_name), court_name),
                decision_date = COALESCE(VALUES(decision_date), decision_date),
                source_citation = COALESCE(VALUES(source_citation), source_citation),
                pdf_relative_path = COALESCE(VALUES(pdf_relative_path), pdf_relative_path),
                ingest_metadata = COALESCE(VALUES(ingest_metadata), ingest_metadata)
            """,
            (
                case_identifier,
                case_title,
                court_name,
                decision_date,
                source_citation,
                pdf_relative_path,
                ingest_json,
            ),
        )
    except Exception:
        raise
    cur.execute("SELECT id FROM cases WHERE case_identifier = %s", (case_identifier,))
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"Failed to resolve case id for {case_identifier!r}")
    return int(row[0])


def clear_frame_children(cur, interpretation_frame_pk: int) -> None:
    cur.execute(
        "DELETE FROM frame_precedent_links WHERE interpretation_frame_id = %s",
        (interpretation_frame_pk,),
    )
    cur.execute(
        "DELETE FROM frame_principles WHERE interpretation_frame_id = %s",
        (interpretation_frame_pk,),
    )
    cur.execute(
        "DELETE FROM frame_key_facts WHERE interpretation_frame_id = %s",
        (interpretation_frame_pk,),
    )


def import_one_frame(
    cur,
    payload: Dict[str, Any],
    pdf_relative_path: Optional[str],
    manifest_entry: Optional[Dict[str, Any]],
    dry_run: bool,
) -> Tuple[bool, str]:
    case_obj = payload.get("case") or {}
    case_identifier = (case_obj.get("case_id") or "").strip()
    if not case_identifier:
        return False, "missing case.case_id"

    case_title = (case_obj.get("case_title") or "").strip() or case_identifier
    court_name = case_obj.get("court_name")
    decision_date = case_obj.get("decision_date")
    if decision_date == "":
        decision_date = None
    source_citation = case_obj.get("source_citation")

    src = payload.get("source") or {}
    ingest_meta: Dict[str, Any] = {}
    if manifest_entry:
        ingest_meta["manifest"] = {
            k: manifest_entry[k]
            for k in ("mode", "pages", "frame_count", "discussed_clauses", "dropped_frames")
            if k in manifest_entry
        }
    if src:
        ingest_meta["source"] = src

    clause_obj = payload.get("clause") or {}
    art_raw = (clause_obj.get("article") or "").strip()
    article, subclause = parse_article_ref(art_raw)
    clause_text = clause_obj.get("text")

    cc_id = resolve_constitution_clause_id(cur, article, subclause, clause_text)
    if cc_id is None:
        return (
            False,
            f"no constitution_clauses row for article={article!r} subclause={subclause!r} (raw={art_raw!r})",
        )

    frame_identifier = (payload.get("frame_id") or "").strip()
    if not frame_identifier:
        return False, "missing frame_id (stored as frame_identifier)"

    if dry_run:
        return True, "ok (dry-run)"

    case_pk = upsert_case_compat(
        cur,
        case_identifier=case_identifier,
        case_title=case_title,
        court_name=court_name,
        decision_date=decision_date,
        source_citation=source_citation,
        pdf_relative_path=pdf_relative_path,
        ingest_metadata=ingest_meta or None,
    )

    created_at = payload.get("created_at")
    if created_at == "":
        created_at = None

    ev = payload.get("evidence") or {}
    ev_loc = ev.get("evidence_location") or {}

    ctx = payload.get("case_context") or {}
    reas = payload.get("reasoning") or {}
    out = payload.get("outcome") or {}
    link = payload.get("link_explanation") or {}

    cur.execute(
        """
        INSERT INTO interpretation_frames (
            frame_identifier, case_id, clause_id,
            created_at, annotator_id, source_dataset, source_notes,
            legal_issue, petitioner_claim, respondent_argument,
            interpretation_summary, application_to_facts,
            holding, disposition, remedy_or_orders,
            why_this_clause_matters, relevance_level, match_type,
            evidence_excerpt, evidence_field, evidence_start_char, evidence_end_char
        ) VALUES (
            %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            case_id = VALUES(case_id),
            clause_id = VALUES(clause_id),
            created_at = VALUES(created_at),
            annotator_id = VALUES(annotator_id),
            source_dataset = VALUES(source_dataset),
            source_notes = VALUES(source_notes),
            legal_issue = VALUES(legal_issue),
            petitioner_claim = VALUES(petitioner_claim),
            respondent_argument = VALUES(respondent_argument),
            interpretation_summary = VALUES(interpretation_summary),
            application_to_facts = VALUES(application_to_facts),
            holding = VALUES(holding),
            disposition = VALUES(disposition),
            remedy_or_orders = VALUES(remedy_or_orders),
            why_this_clause_matters = VALUES(why_this_clause_matters),
            relevance_level = VALUES(relevance_level),
            match_type = VALUES(match_type),
            evidence_excerpt = VALUES(evidence_excerpt),
            evidence_field = VALUES(evidence_field),
            evidence_start_char = VALUES(evidence_start_char),
            evidence_end_char = VALUES(evidence_end_char)
        """,
        (
            frame_identifier,
            case_pk,
            cc_id,
            created_at,
            payload.get("annotator_id"),
            src.get("dataset"),
            src.get("notes"),
            ctx.get("legal_issue"),
            ctx.get("petitioner_claim"),
            ctx.get("respondent_argument"),
            reas.get("interpretation_summary"),
            reas.get("application_to_facts"),
            out.get("holding"),
            out.get("disposition"),
            out.get("remedy_or_orders"),
            link.get("why_this_clause_matters"),
            link.get("relevance_level"),
            link.get("match_type"),
            ev.get("evidence_excerpt"),
            ev_loc.get("field"),
            ev_loc.get("start_char"),
            ev_loc.get("end_char"),
        ),
    )

    cur.execute(
        "SELECT id FROM interpretation_frames WHERE frame_identifier = %s",
        (frame_identifier,),
    )
    row = cur.fetchone()
    if not row:
        return False, "failed to resolve interpretation_frames.id after upsert"
    frame_pk = int(row[0])

    clear_frame_children(cur, frame_pk)

    for i, fact in enumerate(ctx.get("key_facts") or []):
        if not (fact or "").strip():
            continue
        cur.execute(
            """
            INSERT INTO frame_key_facts (interpretation_frame_id, sort_order, fact_text)
            VALUES (%s, %s, %s)
            """,
            (frame_pk, i, fact.strip()),
        )

    for i, pr in enumerate(reas.get("principles_established") or []):
        if not (pr or "").strip():
            continue
        cur.execute(
            """
            INSERT INTO frame_principles (interpretation_frame_id, sort_order, principle_text)
            VALUES (%s, %s, %s)
            """,
            (frame_pk, i, pr.strip()),
        )

    raw_cites = [c.strip() for c in (reas.get("precedents_cited") or []) if c and str(c).strip()]
    unique_cites = list(dict.fromkeys(raw_cites))
    for i, cite in enumerate(unique_cites):
        pid = get_or_create_precedent_id(cur, cite)
        cur.execute(
            """
            INSERT INTO frame_precedent_links (interpretation_frame_id, precedent_id, sort_order)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE sort_order = VALUES(sort_order)
            """,
            (frame_pk, pid, i),
        )

    return True, "imported"


def main() -> None:
    parser = argparse.ArgumentParser(description="Import frame JSON corpus into MySQL.")
    parser.add_argument("--frames-dir", default=FRAMES_DIR, help="Directory containing *.json frames")
    parser.add_argument("--manifest", default=MANIFEST_PATH, help="manifest.json path")
    parser.add_argument("--dry-run", action="store_true", help="Parse only; no DB writes")
    parser.add_argument("--limit", type=int, default=0, help="Max number of files (0 = all)")
    args = parser.parse_args()

    frames_dir = os.path.abspath(args.frames_dir)
    if not os.path.isdir(frames_dir):
        print(f"Frames directory not found: {frames_dir}", file=sys.stderr)
        sys.exit(1)

    manifest_path = os.path.abspath(args.manifest)
    manifest: Dict[str, Any] = {}
    if os.path.isfile(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        print(f"Warning: manifest not found at {manifest_path}; PDF paths will be NULL", file=sys.stderr)

    lookup = build_manifest_lookup(manifest)

    json_files = sorted(
        f for f in os.listdir(frames_dir) if f.lower().endswith(".json")
    )
    if args.limit and args.limit > 0:
        json_files = json_files[: args.limit]

    if args.dry_run:
        print(f"Dry-run: would process {len(json_files)} file(s) under {frames_dir}")

    conn = None
    if not args.dry_run:
        conn = get_connection()
        conn.autocommit = False
        cur = conn.cursor()
        load_clause_map(cur)
    else:
        cur = None

    ok_n = skip_n = 0
    errors: List[str] = []

    for fname in json_files:
        path = os.path.join(frames_dir, fname)
        key = normalize_basename(fname)
        pdf_name: Optional[str] = None
        m_entry: Optional[Dict[str, Any]] = None
        if key in lookup:
            pdf_name, m_entry = lookup[key]
        elif fname.lower() in lookup:
            pdf_name, m_entry = lookup[fname.lower()]

        pdf_rel: Optional[str] = None
        if pdf_name:
            pdf_rel = resolve_pdf_path(pdf_name)

        try:
            with open(path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as e:
            errors.append(f"{fname}: JSON error: {e}")
            skip_n += 1
            continue

        if args.dry_run:
            art_raw = ((payload.get("clause") or {}).get("article") or "").strip()
            a, s = parse_article_ref(art_raw)
            print(f"  {fname} -> pdf={pdf_name or '?'} article_parsed=({a!r},{s!r})")
            ok_n += 1
            continue

        assert conn is not None and cur is not None
        try:
            success, msg = import_one_frame(
                cur, payload, pdf_rel, m_entry, dry_run=False
            )
            if success:
                conn.commit()
                ok_n += 1
            else:
                conn.rollback()
                errors.append(f"{fname}: {msg}")
                skip_n += 1
        except Exception as e:
            conn.rollback()
            errors.append(f"{fname}: {e}")
            skip_n += 1

    if conn:
        cur.close()
        conn.close()

    print(f"Done. Imported OK: {ok_n}, skipped/errors: {skip_n}")
    if errors:
        print("Issues (first 30):", file=sys.stderr)
        for line in errors[:30]:
            print(f"  {line}", file=sys.stderr)
        if len(errors) > 30:
            print(f"  ... and {len(errors) - 30} more", file=sys.stderr)


if __name__ == "__main__":
    main()
