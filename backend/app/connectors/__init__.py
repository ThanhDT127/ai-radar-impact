from app.connectors.base import BaseConnector, ConnectorEntry
from app.connectors.registry import ConnectorRegistry
from app.connectors.rss_connector import RSSConnector  # triggers auto-registration
from app.connectors.hackernews_connector import HackerNewsConnector  # triggers auto-registration
from app.connectors.reddit_connector import RedditConnector  # triggers auto-registration
from app.connectors.github_trending_connector import GitHubTrendingConnector  # triggers auto-registration
from app.connectors.huggingface_connector import HuggingFaceConnector  # triggers auto-registration
from app.connectors.web_index_connector import WebIndexConnector  # triggers auto-registration
from app.connectors.playwright_connector import PlaywrightConnector  # triggers auto-registration

__all__ = [
    "BaseConnector",
    "ConnectorEntry",
    "ConnectorRegistry",
    "RSSConnector",
    "HackerNewsConnector",
    "RedditConnector",
    "GitHubTrendingConnector",
    "HuggingFaceConnector",
    "WebIndexConnector",
    "PlaywrightConnector",
]
