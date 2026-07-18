"""Long-polling worker (getUpdates) — chạy như asyncio task trong backend.

Không cần webhook/domain public. Tự phục hồi với exponential backoff khi lỗi
mạng; heartbeat log định kỳ để kiểm tra sống. Lỗi xử lý một update không làm
chết vòng poll.
"""

import asyncio
import logging
import time

from app.bot.router import UpdateRouter
from app.channels.telegram import TelegramAPI

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL_SECONDS = 600
MAX_BACKOFF_SECONDS = 60


class TelegramPollingWorker:
    def __init__(self, api: TelegramAPI, router: UpdateRouter) -> None:
        self._api = api
        self._router = router
        self._offset: int | None = None

    async def run(self) -> None:
        logger.info("[bot] Long-polling worker started")
        backoff = 1
        last_heartbeat = time.monotonic()
        while True:
            try:
                updates = await self._api.get_updates(self._offset)
                backoff = 1
                for update in updates:
                    self._offset = update["update_id"] + 1
                    try:
                        await self._router.route(update)
                    except Exception:
                        logger.exception(
                            "[bot] Error handling update %s", update.get("update_id")
                        )
            except asyncio.CancelledError:
                logger.info("[bot] Worker cancelled — shutting down")
                raise
            except Exception as exc:
                logger.warning("[bot] Polling error: %s — retry in %ds", exc, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF_SECONDS)

            if time.monotonic() - last_heartbeat >= HEARTBEAT_INTERVAL_SECONDS:
                logger.info("[bot] heartbeat — alive, offset=%s", self._offset)
                last_heartbeat = time.monotonic()
