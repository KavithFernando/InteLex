"""
Services layer: clause-frame retrieval (FAISS), case_search (for chat tool), chat (Groq + tools), auth.
"""
from services import clause_retrieval, case_search, chat, auth

__all__ = ["clause_retrieval", "case_search", "chat", "auth"]
