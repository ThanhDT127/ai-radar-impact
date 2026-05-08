from app.connectors.base import BaseConnector, ConnectorEntry
from app.connectors.registry import ConnectorRegistry
from app.connectors.rss_connector import RSSConnector  # triggers auto-registration
from app.connectors.hackernews_connector import HackerNewsConnector  # triggers auto-registration
from app.connectors.reddit_connector import RedditConnector  # triggers auto-registration

__all__ = [
    "BaseConnector",
    "ConnectorEntry",
    "ConnectorRegistry",
    "RSSConnector",
    "HackerNewsConnector",
    "RedditConnector",
]
