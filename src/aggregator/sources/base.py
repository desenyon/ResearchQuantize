from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ..models.paper import Paper


class BaseSourceClient(ABC):
    """Contract for paper source adapters."""

    source_name: str

    @abstractmethod
    def fetch_papers(self, query: str, limit: int = 10) -> List[Paper]:
        raise NotImplementedError
