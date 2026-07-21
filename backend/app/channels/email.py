"""EmailAdapter — gửi bản tin qua SMTP (Gmail App Password).

Một email cho một người nhận (`To:` đúng một địa chỉ, KHÔNG BCC): nội dung đã cá nhân
hoá theo vai trò, và gửi hàng loạt bằng BCC làm tăng khả năng bị xếp spam.
"""

import logging
from email.message import EmailMessage
from email.utils import formataddr

import aiosmtplib

from app.channels.base import ChannelAdapter, ChannelRegistry, DeliveryMessage, SendResult
from app.config import settings

logger = logging.getLogger(__name__)


def mask_email(email: str) -> str:
    """`an.nguyen@rangdong.vn` → `an***@rangdong.vn` — tránh log PII trần."""
    local, _, domain = email.partition("@")
    if not domain:
        return "***"
    keep = local[:2] if len(local) > 2 else local[:1]
    return f"{keep}***@{domain}"


class EmailAdapter(ChannelAdapter):
    """Gửi qua SMTP với kết nối dùng chung cho cả một lượt gửi."""

    channel_type = "email"

    def __init__(self) -> None:
        self._client: aiosmtplib.SMTP | None = None

    async def open(self) -> None:
        """Mở và xác thực một kết nối SMTP cho cả run."""
        if self._client is not None:
            return
        client = aiosmtplib.SMTP(
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            start_tls=settings.smtp_port == 587,
            use_tls=settings.smtp_port == 465,
        )
        await client.connect()
        if settings.smtp_user:
            await client.login(settings.smtp_user, settings.smtp_password)
        self._client = client
        logger.info("SMTP đã kết nối %s:%d", settings.smtp_host, settings.smtp_port)

    async def close(self) -> None:
        if self._client is None:
            return
        try:
            await self._client.quit()
        except Exception as e:  # noqa: BLE001 — đóng lỗi không được che lỗi gửi
            logger.warning("Đóng SMTP lỗi: %s", e)
        finally:
            self._client = None

    def _build(self, recipient: str, message: DeliveryMessage) -> EmailMessage:
        msg = EmailMessage()
        msg["Subject"] = message.title
        msg["From"] = formataddr((settings.email_from_name, settings.email_from or settings.smtp_user))
        msg["To"] = recipient
        if settings.email_reply_to:
            msg["Reply-To"] = settings.email_reply_to
        for key, value in message.headers.items():
            msg[key] = value

        msg.set_content(message.body)
        if message.html_body:
            msg.add_alternative(message.html_body, subtype="html")
        return msg

    async def send(self, recipient_ref: str, message: DeliveryMessage) -> SendResult:
        """Gửi một email. Lỗi SMTP trả `ok=False` chứ KHÔNG raise.

        Engine dựa vào đó để không ghi delivery_log → kỳ sau tự gửi lại.
        """
        try:
            opened_here = self._client is None
            if opened_here:
                await self.open()
            assert self._client is not None
            await self._client.send_message(self._build(recipient_ref, message))
            if opened_here:
                await self.close()
            return SendResult(ok=True)
        except Exception as e:  # noqa: BLE001
            logger.error("Gửi email tới %s lỗi: %s", mask_email(recipient_ref), e)
            # Kết nối có thể đã hỏng — bỏ để lần sau mở lại từ đầu
            self._client = None
            return SendResult(ok=False, error=str(e))


ChannelRegistry.register(EmailAdapter())
