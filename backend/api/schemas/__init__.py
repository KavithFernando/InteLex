"""
Pydantic schemas for API request/response and tool-related DTOs.
"""
from api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from api.schemas.case import CaseDetail, ClauseItem, FrameDetail
from api.schemas.chat import (
    UserInput,
    ChatResponse,
    CaseSummary,
    ClauseSummary,
    ConversationItem,
    CreateConversationResponse,
    FrameSummary,
    InterpretCaseRequest,
    InterpretCaseResponse,
    MessageItem,
)

__all__ = [
    "UserInput",
    "ChatResponse",
    "CaseSummary",
    "FrameSummary",
    "ClauseSummary",
    "ConversationItem",
    "CreateConversationResponse",
    "InterpretCaseRequest",
    "InterpretCaseResponse",
    "MessageItem",
    "CaseDetail",
    "FrameDetail",
    "ClauseItem",
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
]
