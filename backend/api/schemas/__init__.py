"""
Pydantic schemas for API request/response and tool-related DTOs.
"""
from api.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from api.schemas.case import CaseDetail, ClauseItem
from api.schemas.chat import (
    UserInput,
    ChatResponse,
    CaseSummary,
    ClauseSummary,
    ConversationItem,
    CreateConversationResponse,
    InterpretCaseRequest,
    InterpretCaseResponse,
    MessageItem,
)

__all__ = [
    "UserInput",
    "ChatResponse",
    "CaseSummary",
    "ClauseSummary",
    "ConversationItem",
    "CreateConversationResponse",
    "InterpretCaseRequest",
    "InterpretCaseResponse",
    "MessageItem",
    "CaseDetail",
    "ClauseItem",
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
]
