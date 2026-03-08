from fastapi import APIRouter, Depends, HTTPException, Request

from api.auth_deps import get_current_user
from api.deps import get_case_repo
from api.schemas import CaseDetail
from db.models.user import User
from services.audit import log_audit

router = APIRouter()


@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case_by_id(
    request: Request,
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
        request=request,
    )
    return CaseDetail(**case)
