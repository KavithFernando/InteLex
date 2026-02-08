"""
Abstract interfaces for services. Enables swapping implementations (e.g. different
vector stores or LLM providers) for scalability and testing.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class IRetrievalService(ABC):
    """Abstract interface for case retrieval (e.g. FAISS, or another vector store)."""

    @abstractmethod
    def search_cases(
        self,
        query_text: str,
        top_cases: int = 10,
        chunk_recall: int | None = None,
        top_chunks_per_case: int = 3,
    ) -> Dict[str, Any]:
        """Return ranked case results for the given query. Keys include 'results' (list of case dicts)."""
        ...
