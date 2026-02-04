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
)

__all__ = [
    "UserInput",
    "ChatResponse",
    "CaseSummary",
    "ClauseSummary",
    "CaseDetail",
    "ClauseItem",
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
]
