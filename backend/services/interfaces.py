from abc import ABC, abstractmethod
from typing import Any, Dict, List


class RetrievalServiceInterface(ABC):

    @abstractmethod
    def search_cases(
        self,
        query_text: str,
        top_cases: int = 10,
        chunk_recall: int | None = None,
        top_chunks_per_case: int = 3,
    ) -> Dict[str, Any]:
        ...
