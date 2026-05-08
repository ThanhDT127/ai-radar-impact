"""Base connector interface and shared data types."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from app.models.source import Source


@dataclass
class ConnectorEntry:
    """Generic entry returned by any connector."""

    source_url: str
    title: str
    raw_content: str
    author: str | None = None
    published_at: datetime | None = None
    metadata: dict = field(default_factory=dict)


class BaseConnector(ABC):
    @abstractmethod
    def fetch(self, source: Source) -> list[ConnectorEntry]:
        """Fetch entries from the source. Returns list of ConnectorEntry."""
        ...
