from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
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
) -> RedirectResponse:
    case = case_repo.fetch_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")

    pdf_url = case.get("pdf_relative_path")
    if not pdf_url or not pdf_url.startswith("http"):
        logger.warning("[Cases] No R2 URL for case {}", case_id)
        raise HTTPException(status_code=404, detail="No PDF is available for this case.")

    log_audit(
        "cases.view_pdf",
        user_id=current_user.user_id,
        username=current_user.username,
        resource_type="case",
        resource_id=case_id,
        success=True,
    )
    return RedirectResponse(url=pdf_url, status_code=302)
