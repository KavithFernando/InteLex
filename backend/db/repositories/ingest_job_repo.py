from typing import Any, Dict, List, Optional

from db.engine import SessionLocal
from db.models.ingest_job import IngestJob


def _row_to_dict(r: IngestJob) -> Dict[str, Any]:
    return {
        "job_id": r.job_id,
        "status": r.status,
        "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
        "filenames": r.filenames or [],
        "clauses": r.clauses,
        "log": r.log or [],
        "frames_created": r.frames_created,
        "frames_skipped": r.frames_skipped,
        "errors": r.errors,
        "error": r.error,
    }


def create(
    job_id: str,
    filenames: List[str],
    clauses: Optional[List[str]],
    submitted_at: str,
) -> Dict[str, Any]:
    session = SessionLocal()
    try:
        job = IngestJob(
            job_id=job_id,
            status="queued",
            filenames=filenames,
            clauses=clauses,
            log=[],
            frames_created=0,
            frames_skipped=0,
            errors=0,
            error=None,
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        return _row_to_dict(job)
    finally:
        session.close()


def update(job_id: str, **fields) -> None:
    """Persist updated fields for a job row. Call after mutating the in-memory IngestJob."""
    session = SessionLocal()
    try:
        job = session.query(IngestJob).filter_by(job_id=job_id).first()
        if not job:
            return
        for k, v in fields.items():
            setattr(job, k, v)
        session.commit()
    finally:
        session.close()


def get(job_id: str) -> Optional[Dict[str, Any]]:
    session = SessionLocal()
    try:
        job = session.query(IngestJob).filter_by(job_id=job_id).first()
        return _row_to_dict(job) if job else None
    finally:
        session.close()


def list_all(limit: int = 200) -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        rows = (
            session.query(IngestJob)
            .order_by(IngestJob.submitted_at.desc())
            .limit(limit)
            .all()
        )
        return [_row_to_dict(r) for r in rows]
    finally:
        session.close()
