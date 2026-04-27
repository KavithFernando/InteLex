"""
PDF -> Frame JSON -> DB -> incremental FAISS ingest service
"""
from __future__ import annotations

import json
import os
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import boto3
import faiss
import numpy as np
from botocore.exceptions import ClientError
from loguru import logger
from sentence_transformers import SentenceTransformer

from caseframe.pipeline import RunConfig, run_batch
from config.settings import (
    CLAUSE_INDEX_PATH,
    CLAUSE_MAP_PATH,
    CONSTITUTION_PATH,
    EMBED_MODEL,
    FRAMES_DIR,
    INGEST_WORK_DIR,
    PDF_DIR,
    R2_ACCOUNT_ID,
    R2_ACCESS_KEY_ID,
    R2_BUCKET_NAME,
    R2_PUBLIC_URL,
    R2_SECRET_ACCESS_KEY,
)
from scripts.import_frames_corpus import run_import
from scripts.index_clauses import build_embedding_text, fetch_frame_clause_rows
from db.repositories import ingest_job_repo

# ── R2 helpers ───────────────────────────────────────────────────────────────────
R2_CONFIGURED = bool(R2_ACCOUNT_ID and R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_PUBLIC_URL)


def _get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def _upload_pdf_to_r2(pdf_path: Path) -> str:
    """
    Upload a PDF file to R2 and return its public URL.
    Raises RuntimeError if R2 is not configured.
    """
    if not R2_CONFIGURED:
        raise RuntimeError(
            "R2 credentials not configured. Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, "
            "R2_SECRET_ACCESS_KEY, and R2_PUBLIC_URL in the environment."
        )
    s3 = _get_r2_client()
    r2_key = f"pdfs/{pdf_path.name}"
    with open(pdf_path, "rb") as f:
        s3.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=r2_key,
            Body=f.read(),
            ContentType="application/pdf",
        )
    return f"{R2_PUBLIC_URL.rstrip('/')}/{r2_key}"

# ── In-memory cache (fast log appends during execution) ────────────────────────
_JOBS: Dict[str, "IngestJob"] = {}


@dataclass
class IngestJob:
    job_id: str
    status: str                    # "queued" | "running" | "done" | "failed"
    submitted_at: str              # ISO 8601 UTC
    filenames: List[str]
    clauses: Optional[List[str]]   # None → scan all
    log: List[str] = field(default_factory=list)
    frames_created: int = 0
    frames_skipped: int = 0
    errors: int = 0
    error: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "submitted_at": self.submitted_at,
            "filenames": self.filenames,
            "clauses": self.clauses,
            "log": self.log,
            "frames_created": self.frames_created,
            "frames_skipped": self.frames_skipped,
            "errors": self.errors,
            "error": self.error,
        }


def get_job(job_id: str) -> Optional[IngestJob]:
    """Return live in-memory job if running, otherwise load from DB."""
    if job_id in _JOBS:
        return _JOBS[job_id]
    row = ingest_job_repo.get(job_id)
    if row is None:
        return None
    return IngestJob(**row)


def list_jobs() -> List[Dict[str, Any]]:
    """List all jobs from DB (most recent first), overlaying any live running jobs."""
    rows = ingest_job_repo.list_all()
    # Overlay in-memory state for any currently-running jobs so the caller
    # always sees the latest log lines without waiting for a flush.
    live = {job_id: j.as_dict() for job_id, j in _JOBS.items()}
    merged = [live.get(r["job_id"], r) for r in rows]
    # Add any in-memory jobs not yet in DB rows (shouldn't happen, but be safe)
    existing_ids = {r["job_id"] for r in rows}
    for job_id, d in live.items():
        if job_id not in existing_ids:
            merged.insert(0, d)
    return merged


def append_new_frames_to_index(job: IngestJob) -> int:

    if not os.path.exists(CLAUSE_MAP_PATH):
        job.log.append("[FAISS] No existing map found — building from scratch")
        existing_frame_ids: set = set()
        index = None
        meta: Dict[str, Any] = {"embed_model": EMBED_MODEL, "count_rows": 0, "row_map": []}
    else:
        with open(CLAUSE_MAP_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)
        existing_frame_ids = {
            int(r["interpretation_frame_id"]) for r in meta.get("row_map", [])
        }
        index = faiss.read_index(CLAUSE_INDEX_PATH)
        job.log.append(
            f"[FAISS] Loaded existing index: {index.ntotal} vectors, "
            f"{len(existing_frame_ids)} frames already indexed"
        )

    all_rows = fetch_frame_clause_rows()
    new_rows = [
        r for r in all_rows
        if int(r["interpretation_frame_id"]) not in existing_frame_ids
    ]
    job.log.append(
        f"[FAISS] DB has {len(all_rows)} total frame(s); {len(new_rows)} are new"
    )

    if not new_rows:
        job.log.append("[FAISS] Nothing new to embed")
        return 0

    job.log.append(f"[FAISS] Embedding {len(new_rows)} new frame(s) with {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL)
    texts = [build_embedding_text(r) for r in new_rows]
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    embeddings = np.asarray(embeddings, dtype="float32")

    start_faiss_id = index.ntotal if index is not None else 0
    if index is None:
        dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)

    index.add(embeddings)

    row_map: List[Dict[str, Any]] = meta.get("row_map", [])
    for i, r in enumerate(new_rows):
        art = str(r["article"]).strip()
        sub = (r.get("subclause") or "").strip()
        dd = r.get("decision_date")
        row_map.append({
            "faiss_id": start_faiss_id + i,
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

    os.makedirs(os.path.dirname(CLAUSE_INDEX_PATH), exist_ok=True)
    faiss.write_index(index, CLAUSE_INDEX_PATH)
    meta["count_rows"] = len(row_map)
    meta["row_map"] = row_map
    with open(CLAUSE_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    job.log.append(
        f"[FAISS] Appended {len(new_rows)} vector(s). "
        f"Index now has {index.ntotal} total vectors."
    )
    return len(new_rows)



def run_ingest_job(
    job_id: str,
    pdf_bytes_list: List[Tuple[str, bytes]],
    clauses: Optional[List[str]],
    annotator_id: str,
    retrieval_service: Any,
) -> None:

    job = _JOBS[job_id]
    job.status = "running"
    work_dir = Path(INGEST_WORK_DIR) / job_id

    try:
        pdf_work_dir   = work_dir / "pdfs"
        frame_work_dir = work_dir / "frames"
        pdf_work_dir.mkdir(parents=True, exist_ok=True)

        job.log.append(f"[Upload] Writing {len(pdf_bytes_list)} PDF(s) to working dir")
        for fname, data in pdf_bytes_list:
            (pdf_work_dir / fname).write_bytes(data)

        # Stage 1
        clause_desc = "all clauses" if not clauses else str(clauses)
        job.log.append(f"[Stage 1] Starting PDF → frame extraction ({clause_desc})")
        cfg = RunConfig(
            input_dir=pdf_work_dir,
            output_dir=frame_work_dir,
            annotator_id=annotator_id,
            dataset_name="admin_upload",
            notes="Admin PDF ingest",
            clauses=tuple(clauses) if clauses else None,
            constitution_path=Path(CONSTITUTION_PATH),
        )
        run_batch(cfg)

        manifest_path = frame_work_dir / "manifest.json"
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        total_frames = sum(e.get("frame_count", 0) for e in manifest.get("files", []))
        job.log.append(f"[Stage 1] Complete. {total_frames} frame JSON(s) produced.")
        _flush(job)
        # Stage 2
        job.log.append("[Stage 2] Importing frames into database...")
        inserted, skipped, err_count, err_msgs, skip_msgs = run_import(
            frames_dir=str(frame_work_dir / "json"),
            manifest_path=str(manifest_path),
        )
        job.frames_created = inserted
        job.frames_skipped = skipped
        job.errors = err_count
        job.log.append(
            f"[Stage 2] DB import complete: inserted={inserted}, "
            f"skipped={skipped}, errors={err_count}"
        )
        for msg in skip_msgs:
            job.log.append(f"[Stage 2] Skipped (clause not in constitution): {msg}")
        for msg in err_msgs:
            job.log.append(f"[Stage 2] ERROR: {msg}")
        _flush(job)
        # Stage 3
        job.log.append("[Stage 3] Updating vector index (new frames only)...")
        added = append_new_frames_to_index(job)
        job.log.append(f"[Stage 3] Vector index updated: {added} new vector(s).")

        # Stage 4
        job.log.append("[Stage 4] Uploading PDFs to R2 and committing frame JSONs...")
        permanent_frame_dir = Path(FRAMES_DIR)
        permanent_frame_dir.mkdir(parents=True, exist_ok=True)

        for src_pdf in pdf_work_dir.glob("*.pdf"):
            try:
                r2_url = _upload_pdf_to_r2(src_pdf)
                job.log.append(f"[Stage 4] Uploaded {src_pdf.name} → {r2_url}")
            except Exception as upload_exc:
                job.log.append(f"[Stage 4] ERROR uploading {src_pdf.name}: {upload_exc}")
                raise

        json_work_dir = frame_work_dir / "json"
        if json_work_dir.is_dir():
            for src_frame in json_work_dir.glob("*.json"):
                dst = permanent_frame_dir / src_frame.name
                if not dst.exists():
                    shutil.move(str(src_frame), str(dst))

        job.log.append("[Stage 4] PDFs in R2; frame JSONs committed to data/frames/.")

        # Stage 5: hot-reload retrieval service
        job.log.append("[Stage 5] Reloading retrieval service...")
        retrieval_service.reload()
        job.log.append("[Stage 5] Retrieval service reloaded.")

        job.status = "done"
        job.log.append("Ingest complete.")
        logger.info("[Ingest] Job {} done | inserted={} skipped={} errors={}",
                    job_id, inserted, skipped, err_count)

    except Exception as exc:
        job.status = "failed"
        job.error = str(exc)
        job.log.append(f"[ERROR] {exc}")
        logger.exception("[Ingest] Job {} failed", job_id)

    finally:
        _flush(job)
        # Remove from memory — future reads go to DB
        _JOBS.pop(job_id, None)
        # Clean up working dir on success; keep on failure for inspection
        if job.status == "done":
            try:
                shutil.rmtree(work_dir)
            except Exception:
                pass


def create_job(filenames: List[str], clauses: Optional[List[str]]) -> IngestJob:
    job_id = str(uuid.uuid4())
    submitted_at = datetime.now(timezone.utc).isoformat()
    job = IngestJob(
        job_id=job_id,
        status="queued",
        submitted_at=submitted_at,
        filenames=filenames,
        clauses=clauses,
    )
    _JOBS[job_id] = job
    ingest_job_repo.create(
        job_id=job_id,
        filenames=filenames,
        clauses=clauses,
        submitted_at=submitted_at,
    )
    return job


def _flush(job: IngestJob) -> None:
    """Persist current in-memory job state to the DB."""
    ingest_job_repo.update(
        job.job_id,
        status=job.status,
        log=job.log,
        frames_created=job.frames_created,
        frames_skipped=job.frames_skipped,
        errors=job.errors,
        error=job.error,
    )
