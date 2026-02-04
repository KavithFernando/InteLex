"""
Services layer: retrieval (FAISS + chunks), case_search (for chat tool), chat (Groq + tools).
"""
from services import retrieval, case_search, chat

__all__ = ["retrieval", "case_search", "chat"]
