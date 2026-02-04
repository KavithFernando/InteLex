"""
Case routes: get full case by ID (for when user clicks a retrieval result).
"""
from fastapi import APIRouter, HTTPException

from api.schemas import CaseDetail
from db.repositories import case_repo

router = APIRouter()


@router.get("/cases/{case_id}", response_model=CaseDetail)
def get_case_by_id(case_id: str) -> CaseDetail:
    """
    Return full case details by ID. Used when the user clicks on a case from the
    retrieval result list. Returns 404 if the case does not exist.
    """
    case = case_repo.fetch_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found.")
    return CaseDetail(**case)
