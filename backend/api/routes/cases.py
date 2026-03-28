import os

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from api.auth_deps import get_current_user
from api.deps import get_case_repo
from api.schemas import CaseDetail, FrameDetail
from db.models.user import User
from services.audit import log_audit

router = APIRouter()


@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case_by_id(
    case_id: str,
    current_user: User = Depends(get_current_user),
    case_repo=Depends(get_case_repo),
) -> CaseDetail:
    case = case_repo.fetch_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    log_audit(
        "cases.view",
        user_id=current_user.user_id,
        username=current_user.username,
        resource_type="case",
        resource_id=case_id,
        success=True,
    )
    return CaseDetail(**case)


@router.get("/frames/{frame_id}", response_model=FrameDetail)
def get_frame_by_id(
    frame_id: int,
    current_user: User = Depends(get_current_user),
    case_repo=Depends(get_case_repo),
) -> FrameDetail:
    frame = case_repo.fetch_frame_by_id(frame_id)
    if not frame:
        raise HTTPException(status_code=404, detail="Frame not found.")
    log_audit(
        "cases.view_frame",
        user_id=current_user.user_id,
        username=current_user.username,
        resource_type="interpretation_frame",
        resource_id=str(frame_id),
        success=True,
    )
    return FrameDetail(**frame)


@router.get("/cases/{case_id}/pdf")
def get_case_pdf(
    case_id: str,
    current_user: User = Depends(get_current_user),
    case_repo=Depends(get_case_repo),
) -> FileResponse:
    from config.settings import PDF_ROOT
    if not PDF_ROOT:
        logger.warning("[Cases] PDF requested but PDF_ROOT is not configured")
        raise HTTPException(
            status_code=503,
            detail="PDF storage is not configured on this server. Set PDF_ROOT in the backend .env file.",
        )

    case = case_repo.fetch_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    pdf_rel = case.get("pdf_relative_path")
    if not pdf_rel:
        logger.warning("[Cases] No pdf_relative_path for case {}", case_id)
        raise HTTPException(status_code=404, detail="No PDF is available for this case.")

    full_path = os.path.join(PDF_ROOT, pdf_rel)
    if not os.path.isfile(full_path):
        logger.warning("[Cases] PDF file missing on disk for case {} | path={}", case_id, full_path)
        raise HTTPException(status_code=404, detail="PDF file not found on the server.")

    filename = os.path.basename(full_path)
    return FileResponse(
        full_path,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
