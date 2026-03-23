from abc import ABC, abstractmethod
from typing import Any, Dict


class RetrievalServiceInterface(ABC):
    """Semantic search over interpretation-frame vectors (clause-centric FAISS index)."""

    @abstractmethod
    def search_frames(
        self,
        query_text: str,
        top_k: int = 10,
        frame_recall: int | None = None,
    ) -> Dict[str, Any]:
        """
        Return globally ranked interpretation frames.

        Expected shape: {"results": list[dict]} where each dict includes at least
        case_internal_id, score, interpretation_frame_id, and clause/map fields.
        """
        ...
