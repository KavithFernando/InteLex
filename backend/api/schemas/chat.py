from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class CreateConversationResponse(BaseModel):
    conversation_id: str = Field(..., description="Use this id for subsequent POST /chat/ requests.")
    created_at: Optional[datetime] = None


class ConversationItem(BaseModel):
    conversation_id: str
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MessageItem(BaseModel):
    role: str
    content: str
    created_at: Optional[datetime] = None
    retrieval_result: Optional[List["CaseSummary"]] = Field(
        default=None,
        description="Case results for this assistant message, if any.",
    )


class UserInput(BaseModel):
    message: str = Field(..., min_length=1, description="User message.")
    conversation_id: str = Field(..., min_length=1, description="Conversation identifier.")


class ClauseSummary(BaseModel):
    article: Optional[str] = None
    text: Optional[str] = None


class CaseSummary(BaseModel):
    case_id: str
    case_title: Optional[str] = None
    decision_date: Optional[str] = None
    clauses: List[ClauseSummary] = Field(default_factory=list)
    score: Optional[float] = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    retrieval_result: List[CaseSummary] = Field(
        default_factory=list,
        description="Top cases: case_id, case_title, decision_date, clauses. Full case via separate API when user clicks.",
    )
