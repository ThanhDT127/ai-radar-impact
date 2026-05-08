"""Connector registry — maps source_type strings to connector classes."""

import logging

from app.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    _connectors: dict[str, type[BaseConnector]] = {}

    @classmethod
    def register(cls, source_type: str, connector_class: type[BaseConnector]) -> None:
        cls._connectors[source_type] = connector_class
        logger.debug("Registered connector '%s' → %s", source_type, connector_class.__name__)

    @classmethod
    def get(cls, source_type: str) -> BaseConnector:
        connector_class = cls._connectors.get(source_type)
        if not connector_class:
            raise ValueError(f"No connector registered for type: {source_type}")
        return connector_class()

    @classmethod
    def list_registered(cls) -> list[str]:
        return list(cls._connectors.keys())
