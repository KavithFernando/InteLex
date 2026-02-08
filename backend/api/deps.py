"""
Dependency injection for FastAPI routes. Provides repository and service instances.
"""
from typing import Optional

from db.repositories import case_repo, chunk_repo, conversation_repo
from services.retrieval import RetrievalService
from services.case_search import CaseSearchService
from services.chat import ChatService

# Cached service instances (stateless services can be reused)
_retrieval_service: Optional[RetrievalService] = None
_case_search_service: Optional[CaseSearchService] = None
_chat_service: Optional[ChatService] = None


def get_case_repo():
    """Return the CaseRepository singleton."""
    return case_repo


def get_conversation_repo():
    """Return the ConversationRepository singleton."""
    return conversation_repo


def get_retrieval_service() -> RetrievalService:
    """Return a shared RetrievalService instance."""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService(chunk_repo)
    return _retrieval_service


def get_case_search_service() -> CaseSearchService:
    """Return a shared CaseSearchService instance."""
    global _case_search_service
    if _case_search_service is None:
        _case_search_service = CaseSearchService(get_retrieval_service(), case_repo)
    return _case_search_service


def get_chat_service() -> ChatService:
    """Return a shared ChatService instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService(get_case_search_service())
    return _chat_service
