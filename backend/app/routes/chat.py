"""Chat Q&A endpoint — hỏi đáp grounded trên insight repository."""

import logging

from fastapi import APIRouter, Depends, HTTPException
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
        raise HTTPException(
            status_code=429,
            detail=(
                "Đã hết lượt hỏi trong ngày hôm nay. "
                "Bạn quay lại vào ngày mai nhé — hoặc xem trực tiếp trên dashboard."
            ),
        )
    except Exception as e:
        logger.error("Chat request failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail="Trợ lý đang gặp sự cố khi trả lời. Bạn thử lại sau ít phút nhé.",
        )

    return ChatResponse(**result)
