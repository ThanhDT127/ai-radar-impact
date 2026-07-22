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
    """Message trung lập kênh — adapter tự render sang định dạng kênh.

    `body` luôn là bản plain-text đọc được độc lập; `html_body` là bản giàu định dạng
    tuỳ chọn (email gửi cả hai dạng multipart/alternative).
    """

    title: str
    body: str
    url: str | None = None
    buttons: list[MessageButton] = field(default_factory=list)
    html_body: str | None = None
    headers: dict[str, str] = field(default_factory=dict)


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
        """Gửi message tới recipient (định danh dạng chuỗi, vd. địa chỉ email)."""
        ...

    async def open(self) -> None:
        """Mở tài nguyên dùng chung cho cả một lượt gửi (mặc định no-op).

        SMTP mở 1 kết nối cho cả run thay vì mỗi email một kết nối — vừa nhanh hơn
        vừa tránh bị nhà cung cấp throttle.
        """
        return None

    async def close(self) -> None:
        """Đóng tài nguyên đã mở ở `open()` (mặc định no-op)."""
        return None


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
