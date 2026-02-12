from typing import Optional

from db.repositories import case_repo, chunk_repo, conversation_repo
from services.retrieval import RetrievalService
from services.case_search import CaseSearchService
from services.chat import ChatService

_retrieval_service: Optional[RetrievalService] = None
_case_search_service: Optional[CaseSearchService] = None
_chat_service: Optional[ChatService] = None


def get_case_repo():
    return case_repo


def get_conversation_repo():
    return conversation_repo


def get_retrieval_service() -> RetrievalService:
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService(chunk_repo)
    return _retrieval_service


def get_case_search_service() -> CaseSearchService:
    global _case_search_service
    if _case_search_service is None:
        _case_search_service = CaseSearchService(get_retrieval_service(), case_repo)
    return _case_search_service


def get_chat_service() -> ChatService:
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService(get_case_search_service())
    return _chat_service
