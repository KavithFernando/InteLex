from typing import List, Optional

from pydantic import BaseModel, Field


class ClauseItem(BaseModel):
    article: Optional[str] = None
    text: Optional[str] = None


class CaseDetail(BaseModel):
    case_id: str
    case_identifier: Optional[str] = None
    case_title: Optional[str] = None
    court_name: Optional[str] = None
    decision_date: Optional[str] = None
    legal_issue: Optional[str] = None
    petitioner_claim: Optional[str] = None
    respondent_argument: Optional[str] = None
    interpretation_summary: Optional[str] = None
    outcome: Optional[str] = None
    source: Optional[str] = None
    full_text: Optional[str] = None
    pdf_relative_path: Optional[str] = None
    judges: List[str] = Field(default_factory=list)
    clauses: List[ClauseItem] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    precedents_cited: List[str] = Field(default_factory=list)
    principles_established: List[str] = Field(default_factory=list)
