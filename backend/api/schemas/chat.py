"""
Chat and retrieval request/response schemas.
"""
from typing import List, Optional

from pydantic import BaseModel, Field


class UserInput(BaseModel):
    """Request body for POST /chat/."""
    message: str = Field(..., min_length=1, description="User message.")
    conversation_id: str = Field(..., min_length=1, description="Conversation identifier.")


class ClauseSummary(BaseModel):
    """Single clause in a retrieval result (article + text)."""
    article: Optional[str] = None
    text: Optional[str] = None


class RetrievalCaseSummary(BaseModel):
    """One case in the retrieval_result list: lightweight summary for response body."""
    case_id: str
    case_title: Optional[str] = None
    decision_date: Optional[str] = None
    clauses: List[ClauseSummary] = Field(default_factory=list)
    score: Optional[float] = None


class ChatResponse(BaseModel):
    """Response body for POST /chat/."""
    response: str
    conversation_id: str
    retrieval_result: List[RetrievalCaseSummary] = Field(
        default_factory=list,
        description="Top cases: case_id, case_title, decision_date, clauses. Full case via separate API when user clicks.",
    )
