"""Chat Q&A endpoint — hỏi đáp grounded trên insight repository.

Hai endpoint, MỘT pipeline:
- `POST /api/v1/chat`        — blocking, trả JSON một phát. Client cũ, test, eval harness.
- `POST /api/v1/chat/stream` — SSE, phát `status`/`token` dọc đường rồi `commit` ở cuối.
"""

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import (
    ChatService,
    InsightNotFoundError,
    QuotaExceededError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

QUOTA_MESSAGE = (
    "Đã hết lượt hỏi trong ngày hôm nay. "
    "Bạn quay lại vào ngày mai nhé — hoặc xem trực tiếp trên dashboard."
)
NOT_FOUND_MESSAGE = "Không tìm thấy insight này"
SERVER_MESSAGE = "Trợ lý đang gặp sự cố khi trả lời. Bạn thử lại sau ít phút nhé."

_ERROR_MESSAGES = {
    "quota": QUOTA_MESSAGE,
    "not_found": NOT_FOUND_MESSAGE,
    "server": SERVER_MESSAGE,
}


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """Hỏi đáp 2 chế độ: có `insight_id` → per-insight, không có → toàn cục.

    `ChatService` khởi tạo mỗi request (rẻ — chỉ giữ session + repo), nhưng
    `GeminiClient` bên trong là singleton (design D6).
    """
    service = ChatService(session)
    try:
        result = await service.answer(
            question=payload.question,
            history=payload.history,
            insight_id=payload.insight_id,
        )
    except InsightNotFoundError:
        raise HTTPException(status_code=404, detail="Không tìm thấy insight này")
    except QuotaExceededError:
        raise HTTPException(status_code=429, detail=QUOTA_MESSAGE)
    except Exception as e:
        logger.error("Chat request failed: %s", e)
        raise HTTPException(status_code=502, detail=SERVER_MESSAGE)

    return ChatResponse(**result)


def _sse(event: str, payload: dict) -> str:
    """Một khung SSE. `data` LUÔN là JSON một dòng.

    Không phải trang trí: token của model chứa xuống dòng thoải mái, mà `\\n` là ký tự kết
    thúc trường của giao thức SSE — dán text thô vào `data:` sẽ cắt câu trả lời thành các
    sự kiện rác ngay lần đầu model xuống dòng.
    """
    body = json.dumps(payload, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {body}\n\n"


async def _sse_stream(service: ChatService, payload: ChatRequest) -> AsyncIterator[str]:
    """Ánh xạ sự kiện của `answer_stream` sang khung SSE.

    Lỗi đi bằng **sự kiện `error`**, không phải mã HTTP — kể cả 429 hết quota. Lý do: cửa
    quota nằm SAU bộ định tuyến ý định (câu chào phải trả lời được khi budget đã cạn, xem
    `chat-intent-router`), nên muốn trả 429 thật thì phải chạy lại phần định tuyến ở route
    = nhân đôi logic. Widget đọc `code` và hiện đúng thông báo.
    """
    async for event in service.answer_stream(
        question=payload.question,
        history=payload.history,
        insight_id=payload.insight_id,
    ):
        kind = event.pop("type")
        if kind == "error":
            code = event.get("code", "server")
            yield _sse("error", {"code": code, "message": _ERROR_MESSAGES[code]})
            return
        yield _sse(kind, event)


@router.post("/stream")
async def chat_stream(
    payload: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Bản streaming của `/chat` — cùng payload, cùng pipeline, khác cách trả về."""
    service = ChatService(session)
    return StreamingResponse(
        _sse_stream(service, payload),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # nginx đệm response theo mặc định → SSE về thành một cục ở cuối, tức là mất
            # sạch streaming mà không có lỗi nào bắn ra. Header này tắt đệm cho riêng
            # route này; xem ghi chú deploy trong CLAUDE.md.
            "X-Accel-Buffering": "no",
        },
    )
