from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile

from api.auth_deps import require_admin
from api.schemas.audit import AuditLogResponse
from api.schemas.auth import AdminUserResponse
from api.schemas.ingest import IngestJobResponse
from db.models.user import User
from db.repositories import audit_repo, user_repo
from services.audit import log_audit
from services.ingest import _JOBS, create_job, get_job, list_jobs, run_ingest_job

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[AdminUserResponse])
def list_users(admin: User = Depends(require_admin)) -> list[AdminUserResponse]:
    """Return all registered users. Admin only."""
    users = user_repo.list_all()
    log_audit(
        "admin.list_users",
        user_id=admin.user_id,
        username=admin.username,
        success=True,
    )
    return [
        AdminUserResponse(
            user_id=u.user_id,
            username=u.username,
            role=u.role.name,
            created_at=u.created_at,
            last_login=u.last_login,
        )
        for u in users
    ]


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    admin: User = Depends(require_admin),
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 100,
) -> list[AuditLogResponse]:
    """Return audit logs with optional filters. Admin only."""
    logs = audit_repo.list_logs(user_id=user_id, action=action, since=since, limit=limit)
    return [AuditLogResponse(**r) for r in logs]


# ── Ingest endpoints ───────────────────────────────────────────────────────────

@router.post("/ingest/upload", response_model=IngestJobResponse, status_code=202)
async def upload_pdfs_for_ingest(
    background_tasks: BackgroundTasks,
    request: Request,
    pdfs: List[UploadFile] = File(...),
    clauses: Optional[str] = Form(None),
    annotator_id: str = Form("admin"),
    admin: User = Depends(require_admin),
) -> IngestJobResponse:
    
    if not pdfs:
        raise HTTPException(status_code=400, detail="No PDFs uploaded")

    clause_list: Optional[List[str]] = None
    if clauses and clauses.strip():
        clause_list = [c.strip() for c in clauses.split(",") if c.strip()]

    pdf_bytes_list = [(f.filename, await f.read()) for f in pdfs]
    filenames = [f.filename for f in pdfs]

    job = create_job(filenames=filenames, clauses=clause_list)
    retrieval_svc = request.app.state.retrieval_service

    background_tasks.add_task(
        run_ingest_job,
        job_id=job.job_id,
        pdf_bytes_list=pdf_bytes_list,
        clauses=clause_list,
        annotator_id=annotator_id,
        retrieval_service=retrieval_svc,
    )

    log_audit(
        "admin.ingest.upload",
        user_id=admin.user_id,
        username=admin.username,
        success=True,
        details={"job_id": job.job_id, "files": filenames, "clauses": clause_list},
    )
    return IngestJobResponse(**job.as_dict())


@router.get("/ingest/jobs", response_model=List[IngestJobResponse])
def get_ingest_jobs(admin: User = Depends(require_admin)) -> List[IngestJobResponse]:
    """List all ingest jobs, most recent first. Admin only."""
    return [IngestJobResponse(**j) for j in list_jobs()]


@router.get("/ingest/jobs/{job_id}", response_model=IngestJobResponse)
def get_ingest_job_status(
    job_id: str,
    admin: User = Depends(require_admin),
) -> IngestJobResponse:
    """Poll status and live log for a specific ingest job. Admin only."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return IngestJobResponse(**job.as_dict())
