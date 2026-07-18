"""Channel adapter interface and channel-neutral message types (M7 Delivery)."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class MessageButton:
    """Nút đính kèm message — callback (nội bộ bot) hoặc mở URL."""

    text: str
    callback_data: str | None = None
    url: str | None = None


@dataclass
class DeliveryMessage:
    """Message trung lập kênh — adapter tự render sang định dạng kênh."""

    title: str
    body: str
    url: str | None = None
    buttons: list[MessageButton] = field(default_factory=list)


@dataclass
class SendResult:
    """Kết quả gửi 1 message (có thể bị split thành nhiều phần)."""

    ok: bool
    error: str | None = None
    parts: int = 1


class ChannelAdapter(ABC):
    """Kênh gửi tin — engine chỉ phụ thuộc interface này."""

    channel_type: str

    @abstractmethod
    async def send(self, recipient_ref: str, message: DeliveryMessage) -> SendResult:
        """Gửi message tới recipient (định danh dạng chuỗi, vd. Telegram chat_id)."""
        ...


class ChannelRegistry:
    """Registry kênh gửi — pattern như ConnectorRegistry ở tầng ingest."""

    _adapters: dict[str, ChannelAdapter] = {}

    @classmethod
    def register(cls, adapter: ChannelAdapter) -> None:
        cls._adapters[adapter.channel_type] = adapter

    @classmethod
    def get(cls, channel_type: str) -> ChannelAdapter:
        adapter = cls._adapters.get(channel_type)
        if not adapter:
            raise ValueError(f"No channel adapter registered for type: {channel_type}")
        return adapter

    @classmethod
    def list_registered(cls) -> list[str]:
        return list(cls._adapters.keys())
