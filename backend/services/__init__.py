"""
Services layer: retrieval (FAISS + chunks), case_search (for chat tool), chat (Groq + tools), auth.
"""
from services import retrieval, case_search, chat, auth

__all__ = ["retrieval", "case_search", "chat", "auth"]
