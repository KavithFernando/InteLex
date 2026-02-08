"""
Case routes: get full case by ID (for when user clicks a retrieval result).
"""
from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_case_repo
from api.schemas import CaseDetail

router = APIRouter()


@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case_by_id(
    case_id: str,
    case_repo=Depends(get_case_repo),
) -> CaseDetail:
    """
    Return full case details by ID. Used when the user clicks on a case from the
    retrieval result list. Returns 404 if the case does not exist.
    """
    case = case_repo.fetch_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return CaseDetail(**case)
