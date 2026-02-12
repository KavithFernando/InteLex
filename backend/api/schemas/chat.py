"""
Chat and retrieval request/response schemas.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreateConversationResponse(BaseModel):
    """Response body for POST /conversations/."""
    conversation_id: str = Field(..., description="Use this id for subsequent POST /chat/ requests.")
    created_at: Optional[datetime] = None


class ConversationItem(BaseModel):
    """One item in GET /conversations/ list."""
    conversation_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MessageItem(BaseModel):
    """One message in GET /conversations/{id}/messages."""
    role: str
    content: str
    retrieval_result: Optional[List["CaseSummary"]] = Field(
        default=None,
        description="Case results for this assistant message, if any.",
    )


class UserInput(BaseModel):
    """Request body for POST /chat/."""
    message: str = Field(..., min_length=1, description="User message.")
    conversation_id: str = Field(..., min_length=1, description="Conversation identifier.")


class ClauseSummary(BaseModel):
    """Single clause in a retrieval result (article + text)."""
    article: Optional[str] = None
    text: Optional[str] = None


class CaseSummary(BaseModel):
    """One case in the chat response list: lightweight summary (id, title, date, clauses, score)."""
    case_id: str
    case_title: Optional[str] = None
    decision_date: Optional[str] = None
    clauses: List[ClauseSummary] = Field(default_factory=list)
    score: Optional[float] = None


class ChatResponse(BaseModel):
    """Response body for POST /chat/."""
    response: str
    conversation_id: str
    retrieval_result: List[CaseSummary] = Field(
        default_factory=list,
        description="Top cases: case_id, case_title, decision_date, clauses. Full case via separate API when user clicks.",
    )
