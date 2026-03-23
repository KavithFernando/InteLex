from __future__ import annotations

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
    retrieval_result: Optional[List["FrameSummary"]] = Field(
        default=None,
        description="Ranked interpretation frames for this assistant message, if any.",
    )


class UserInput(BaseModel):
    message: str = Field(..., min_length=1, description="User message.")
    conversation_id: str = Field(..., min_length=1, description="Conversation identifier.")


class ClauseSummary(BaseModel):
    article: Optional[str] = None
    text: Optional[str] = None


class FrameSummary(BaseModel):
    """One retrieval row: a ranked interpretation frame plus case metadata for display."""

    interpretation_frame_id: Optional[int] = Field(
        None,
        description="Primary corpus unit for this hit; omit on legacy stored messages.",
    )
    case_id: str
    case_identifier: Optional[str] = None
    case_title: Optional[str] = None
    decision_date: Optional[str] = None
    clauses: List[ClauseSummary] = Field(default_factory=list)
    score: Optional[float] = None
    frame_identifier: Optional[str] = None
    matched_article: Optional[str] = None
    matched_subclause: Optional[str] = None
    matched_clause_text: Optional[str] = None


CaseSummary = FrameSummary


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    retrieval_result: List[FrameSummary] = Field(
        default_factory=list,
        description="Top interpretation frames: frame id, case id, matched clause, score. Case detail via GET /cases/{id}; frame detail via GET /frames/{id}.",
    )


class InterpretCaseRequest(BaseModel):
    case_id: str = Field(..., min_length=1, description="Case to interpret (internal id or case_identifier).")
    interpretation_frame_id: Optional[int] = Field(
        None,
        description="If set, interpretation uses this frame's narrative fields; must belong to the given case.",
    )
    user_query: str = Field(..., min_length=1, description="The user message that triggered retrieval of this case.")


class InterpretCaseResponse(BaseModel):
    interpretation: str = Field(..., description="Generated interpretation of the case in light of the user's query.")
