from app.channels.base import (
    ChannelAdapter,
    ChannelRegistry,
    DeliveryMessage,
    MessageButton,
    SendResult,
)

# Import để adapter tự đăng ký vào ChannelRegistry (pattern như ConnectorRegistry).
from app.channels.email import EmailAdapter  # noqa: E402,F401

__all__ = [
    "ChannelAdapter",
    "ChannelRegistry",
    "DeliveryMessage",
    "EmailAdapter",
    "MessageButton",
    "SendResult",
]
