"""Models package — import all models so Alembic can detect them."""

from app.models.source import Source
from app.models.raw_document import RawDocument
from app.models.insight import Insight
from app.models.subscriber import Subscriber
from app.models.delivery_log import DeliveryLog
from app.models.chat_log import ChatLog
from app.models.document_chunk import DocumentChunk

__all__ = ["Source", "RawDocument", "Insight", "Subscriber", "DeliveryLog", "ChatLog", "DocumentChunk"]
