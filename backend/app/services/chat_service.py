"""Chat Q&A service — hai chế độ trên cùng một pipeline trả lời.

Chế độ B (per-insight): context = 1 insight + bài gốc, luôn đánh số [1].
Chế độ A (toàn cục):    server lọc → xếp hạng → index nén [1..N] → 1 lượt gọi.

KHÔNG function-calling: đo trên corpus thật (179 insight, 22/07/2026) cả corpus dạng
index nén chỉ ~19.3k token (~$0.007/câu, 1 lượt gọi), rẻ và nhanh hơn hẳn 2-4 lượt tool.
Xem design D3.
"""

import asyncio
import logging
import re
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.gemini_client import GeminiClient, get_chat_client
from app.ai.prompts import (
    ALLOWED_ROLES,
    CHAT_SYSTEM_PROMPT,
    build_chat_expanded_prompt,
    build_chat_global_prompt,
    build_chat_insight_prompt,
)
from app.config import settings
from app.models.insight import Insight
from app.models.raw_document import RawDocument
from app.repositories.chat_log_repo import ChatLogRepository
from app.repositories.insight_repo import InsightRepository
from app.services.chat_grounding import (
    build_index_block,
    build_insight_block,
    enforce_grounding,
    is_out_of_scope_answer,
    resolve_citations,
)
from app.services.chat_intent import AMBIGUOUS, INTENT_PRESETS, route_intent
from app.services.chat_service_terms import STOPWORDS
from app.services.delivery_engine import score_for_role

logger = logging.getLogger(__name__)

# Trần cứng số BƯỚC TRẢ LỜI cho MỘT câu hỏi (design D3). Chế độ B hoặc A là 1 bước;
# mở rộng scope (`chat-scope-routing`) là bước thứ 2. Trần tồn tại để pipeline không
# lặng lẽ trôi thành tool loop.
#
# ⚠️ BƯỚC ≠ LƯỢT GỌI TÍNH TIỀN (sửa 25/07/2026). `GeminiClient.chat()` có thể tiêu 2 lượt
# cho MỘT bước khi câu trả lời bị cắt và phải hỏi lại (`chat-answer-completeness`). Trước
# khi tách hai khái niệm này, đo được hai lỗi thật:
#   (A) mở rộng + lượt 2 bị cắt → 3 lượt, vượt trần mà spec scope-routing tuyên bố;
#   (B) lượt B bị cắt → hỏi lại → bản hỏi lại phát sentinel → mở rộng bị trần chặn →
#       RuntimeError → HTTP 500 cho người dùng.
# Nên: trần áp lên `_steps_used` (bước), còn `_calls_used` (tiền) chỉ dùng để ghi log và
# tính budget. Trần bước 2 × trần 2 lượt/bước ⇒ tối đa 4 lượt tính tiền cho một câu hỏi,
# vẫn có biên, vẫn không thành vòng lặp.
MAX_MODEL_CALLS_PER_QUESTION = 2


@dataclass
class _InsightAttempt:
    """Kết quả một lượt gọi chế độ B — có thể là câu trả lời, hoặc yêu cầu mở rộng.

    `out_of_scope=True` nghĩa là model đã phát sentinel: `answer`/`citations` rỗng và
    caller phải chạy lượt mở rộng. Giữ luôn `insight` + `insight_block` để lượt hai
    không phải nạp lại bài từ DB (design D4 — context mở rộng mang cả bài đang xem).
    """

    answer: str
    citations: list[dict]
    out_of_scope: bool = False
    insight: Insight | None = None
    insight_block: str = ""


class QuotaExceededError(Exception):
    """Hết budget chat trong ngày — route dịch thành HTTP 429."""


class InsightNotFoundError(Exception):
    """`insight_id` không có trong DB — route dịch thành HTTP 404."""


def _history_block(history: list) -> str:
    """Ghép history thành text. `history` là list ChatTurn (đã cap 10 ở schema)."""
    if not history:
        return ""
    lines = []
    for turn in history:
        who = "Người dùng" if turn.role == "user" else "Trợ lý"
        lines.append(f"{who}: {turn.content}")
    return "\n".join(lines)


def _roles_in_question(question: str) -> list[str]:
    """Vai trò được nhắc tên trong câu hỏi — dùng để chọn trục xếp hạng."""
    lowered = question.lower()
    return [role for role in ALLOWED_ROLES if role.lower() in lowered]


# Nguồn sự thật ở `chat_service_terms` (dùng chung với `chat_intent`, tránh import vòng).
_STOPWORDS = STOPWORDS


def _question_terms(question: str) -> list[str]:
    """Từ khoá đủ đặc trưng để đo độ liên quan.

    Ngưỡng độ dài là **2**, không phải 3: tiếng Việt đơn âm nên phần lớn từ mang nghĩa
    chỉ dài 2 ký tự. Lọc ở 3 làm "mã nguồn mở" rụng còn `['nguồn']`, và mất sạch "dữ",
    "mã", "mở", "AI". Việc loại nhiễu giao cho `_STOPWORDS` chứ không giao cho độ dài.
    """
    words = re.findall(r"[0-9a-zA-ZÀ-ỹ]+", question.lower())
    return [w for w in words if len(w) >= 2 and w not in _STOPWORDS]


def _relevance(insight: Insight, terms: list[str]) -> int:
    """Số từ khoá của câu hỏi xuất hiện trong tin. 0 = không nhắc gì tới câu hỏi."""
    if not terms:
        return 0
    haystack = " ".join(
        filter(
            None,
            [
                insight.title,
                insight.signal,
                insight.so_what,
                insight.summary_short,
                " ".join(insight.topics or []),
                " ".join(insight.affected_roles or []),
            ],
        )
    ).lower()
    return sum(1 for t in set(terms) if t in haystack)


class ChatService:
    def __init__(
        self, session: AsyncSession, gemini: GeminiClient | None = None
    ) -> None:
        self.session = session
        # Singleton — KHÔNG tạo GeminiClient mới mỗi request (design D6).
        self.gemini = gemini or get_chat_client()
        self.insight_repo = InsightRepository(session)
        self.chat_log_repo = ChatLogRepository(session)
        # Bộ đếm lượt gọi ĐÃ TỐN TIỀN của request hiện tại. Phải là thuộc tính instance
        # chứ không phải giá trị trả về: nếu đếm bằng return thì một lỗi giữa chừng
        # (sau khi model đã trả lời) làm số đếm biến mất và budget rò rỉ.
        # An toàn vì service là per-request — AsyncSession vốn không dùng chung được.
        self._calls_used = 0
        # Số BƯỚC trả lời đã chạy (mode B / mode A / mở rộng). Tách khỏi `_calls_used` vì
        # một bước có thể tốn 2 lượt khi câu trả lời bị cắt và phải hỏi lại — xem ghi chú
        # ở `MAX_MODEL_CALLS_PER_QUESTION`.
        self._steps_used = 0

    async def _route_intent(self, question: str) -> str | None:
        """Bộ lọc ý định HAI TẦNG (25/07/2026). Trả nhóm preset, hoặc `None` = đi pipeline.

        Tầng 1 là luật tất định (6µs, 0 đồng) và nó quyết ~96,5% câu. Tầng 2 —
        `gemini-2.5-flash-lite` — chỉ chạy khi tầng 1 tự nhận lưỡng lự, vì sàn round‑trip
        của nó là ~1,45s: giao hết cho model là cộng ngần ấy vào mọi câu tra cứu thật,
        đổi lại precision còn TỤT (91,5% so với 97,6% của luật, đo trên 84 ca nhãn tay).

        Lượt gọi tầng 2 KHÔNG tính vào `model_calls`: bộ đếm đó canh budget của lượt trả
        lời đắt tiền (`MAX_DAILY_CHAT_CALLS` = lượt gọi `gemini-2.5-flash` với prompt
        ~19k token). Một lần phân loại là ~259 token vào + 1 token ra trên model rẻ hơn
        một bậc — ≈ $0,026 cho 1000 câu. Trộn hai đơn vị đó vào một bộ đếm sẽ làm budget
        đắt bị bào mòn bởi các lượt gọi rẻ (đúng cái bẫy "đơn vị budget khác nhau").
        """
        intent = route_intent(question)
        if intent != AMBIGUOUS:
            return intent

        if not settings.intent_classifier_enabled:
            return None  # tắt tầng 2 → giữ bias fall‑through

        logger.info("Ý định lưỡng lự, hỏi model nhẹ: %r", question[:60])
        return await asyncio.to_thread(self.gemini.classify_intent, question)

    async def answer(
        self, question: str, history: list, insight_id: uuid.UUID | None
    ) -> dict:
        """Điểm vào duy nhất. Ghi `chat_logs` trong `finally` để budget không rò rỉ."""
        # Định tuyến ý định TRƯỚC cửa quota (design D3): câu chào/meta/cảm ơn 0 lượt gọi
        # model phải trả lời được kể cả khi budget đã cạn, và không tiêu budget. Áp dụng
        # bất kể có `insight_id` hay không — chào trong lúc đang mở một bài vẫn là chào.
        intent = await self._route_intent(question)
        if intent is not None:
            started = time.monotonic()
            # Ghi log `model_calls=0` để đo tần suất fast‑path; bản ghi 0 không đội bộ đếm
            # `SUM(model_calls)` nên không ảnh hưởng budget đã dùng.
            await self.chat_log_repo.create(
                mode="meta",
                model_calls=0,
                citations_count=0,
                latency_ms=int((time.monotonic() - started) * 1000),
            )
            return {"answer": INTENT_PRESETS[intent], "citations": [], "mode": "meta"}

        used = await self.chat_log_repo.sum_model_calls_today()
        if used >= settings.max_daily_chat_calls:
            logger.warning(
                "Chat daily cap reached (%d used / %d)", used, settings.max_daily_chat_calls
            )
            raise QuotaExceededError

        mode = "insight" if insight_id else "global"
        started = time.monotonic()
        self._calls_used = 0
        self._steps_used = 0
        citations: list[dict] = []
        try:
            if insight_id:
                attempt = await self._answer_insight(question, history, insight_id)
                if attempt.out_of_scope:
                    # Auto-fallback (design D2/D4): model đã tự nói "câu này không nằm
                    # trong bài", nên lượt 2 trả lời lại với context rộng hơn. Đây KHÔNG
                    # phải một lượt phân loại — tín hiệu là byproduct của lượt trả lời B.
                    mode = "expanded"
                    answer, citations = await self._answer_global(
                        question, history, focus=attempt
                    )
                else:
                    answer, citations = attempt.answer, attempt.citations
            else:
                answer, citations = await self._answer_global(question, history)
            return {"answer": answer, "citations": citations, "mode": mode}
        finally:
            # Lượt gọi ĐÃ trả về rồi vỡ ở bước sau vẫn tốn tiền → vẫn phải tính.
            # (Retry 429 không có response nên client không đếm.)
            if self._calls_used:
                await self.chat_log_repo.create(
                    mode=mode,
                    model_calls=self._calls_used,
                    citations_count=len(citations),
                    latency_ms=int((time.monotonic() - started) * 1000),
                )

    async def _answer_insight(
        self, question: str, history: list, insight_id: uuid.UUID
    ) -> _InsightAttempt:
        result = await self.session.execute(
            select(Insight)
            .where(Insight.id == insight_id)
            .options(selectinload(Insight.raw_document).selectinload(RawDocument.source))
        )
        insight = result.scalar_one_or_none()
        if insight is None:
            raise InsightNotFoundError

        # Không cắt: trần 8000 ký tự đã áp từ ingest (normalizer.MAX_CONTENT_LENGTH).
        # Rỗng = đã bị tombstone-purge → build_insight_block tự thêm ghi chú.
        raw_doc = insight.raw_document
        content = (raw_doc.normalized_content or "").strip() if raw_doc else ""
        insight_block = build_insight_block(insight, content or None)

        prompt = build_chat_insight_prompt(
            insight_block=insight_block,
            history_block=_history_block(history),
            question=question,
        )
        raw_answer = await self._call_model(prompt)

        # Dò sentinel TRƯỚC grounding: sentinel không mang marker [n] nào, nên để
        # `enforce_grounding` chạy trước thì nó bị thay bằng INSUFFICIENT_GROUNDS_MESSAGE
        # và tín hiệu ngoài‑phạm‑vi mất sạch (design D3).
        if is_out_of_scope_answer(raw_answer):
            logger.info("Câu hỏi ngoài phạm vi bài %s — mở rộng toàn hệ thống", insight_id)
            return _InsightAttempt(
                answer="", citations=[], out_of_scope=True,
                insight=insight, insight_block=insight_block,
            )

        answer, citations = resolve_citations(raw_answer, {1: insight})
        answer, citations = enforce_grounding(answer, citations)
        return _InsightAttempt(answer=answer, citations=citations)

    async def _answer_global(
        self, question: str, history: list, focus: _InsightAttempt | None = None
    ) -> tuple[str, list[dict]]:
        since = None
        if settings.chat_window_days > 0:
            since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
                days=settings.chat_window_days
            )

        matched = await self.insight_repo.list_for_chat(published_since=since)
        asked_roles = _roles_in_question(question)
        # Chế độ mở rộng: bài đang xem đi kèm dạng block đầy đủ ở [1], nên phải loại nó
        # khỏi index toàn cục — không thì cùng một tin xuất hiện hai lần với hai số khác
        # nhau và citation trỏ trùng.
        if focus is not None:
            matched = [i for i in matched if i.id != focus.insight.id]
        matched = self._rank(matched, question)

        # ⚠️ Tính "vai trò không có tin" trên TOÀN BỘ tập khớp, TRƯỚC khi cắt top-K.
        # Nếu tính sau khi cắt, một vai trò có tin nhưng xếp hạng dưới ngưỡng sẽ bị
        # báo nhầm là "chưa có tin nào" — sai nghiêm trọng hơn nhiều so với việc
        # không nhắc tới nó.
        empty_roles = [
            role
            for role in asked_roles
            if not any(role in (i.affected_roles or []) for i in matched)
        ]

        # Cắt sau khi xếp hạng: giữ tin đáng đọc nhất, bỏ phần đuôi mà câu trả lời
        # (trần 5 tin) không bao giờ dùng tới. Xem `settings.chat_index_top_k`.
        total_matched = len(matched)
        candidates = (
            matched[: settings.chat_index_top_k]
            if settings.chat_index_top_k > 0
            else matched
        )

        # Mở rộng: [1] dành cho bài đang xem, tin toàn cục đánh số từ [2] — một dãy số
        # liên tục qua cả hai khối context ⇒ vẫn đúng MỘT bảng ánh xạ.
        index_block, mapping = build_index_block(
            candidates, start=2 if focus is not None else 1
        )
        if focus is not None:
            mapping[1] = focus.insight

        # Model chỉ nhìn thấy phần đã cắt, nên nếu để nó tự đếm "Còn N tin khác" thì con
        # số sẽ thiếu đúng bằng phần bị cắt. Đưa tổng thật vào.
        hidden = total_matched - len(candidates)
        if hidden > 0:
            index_block += (
                f"\n\nLƯU Ý: đây là {len(candidates)} tin đáng chú ý nhất; hệ thống còn "
                f"{hidden} tin nữa xếp hạng thấp hơn. Khi cần nói \"Còn N tin khác\", "
                f"N tính trên tổng {total_matched} tin."
            )

        # Vai trò được hỏi mà KHÔNG tin nào ảnh hưởng tới → nói tất định, đừng trông chờ
        # model tự nhận ra khoảng trống. Đo 22/07/2026: `Data Analyst` và
        # `Người dùng phổ thông` có 0 entry trên toàn corpus, nên đây là ca thật.
        if empty_roles:
            index_block += (
                f"\n\nLƯU Ý: hệ thống hiện KHÔNG có tin nào ảnh hưởng tới vai trò "
                f"{', '.join(empty_roles)}. Hãy nói rõ điều đó."
            )

        history_block = _history_block(history)
        if focus is not None:
            prompt = build_chat_expanded_prompt(
                insight_block=focus.insight_block,
                index_block=index_block,
                history_block=history_block,
                question=question,
            )
        else:
            prompt = build_chat_global_prompt(
                index_block=index_block,
                history_block=history_block,
                question=question,
            )
        raw_answer = await self._call_model(prompt)

        answer, citations = resolve_citations(raw_answer, mapping)
        answer, citations = enforce_grounding(answer, citations)
        return answer, citations

    def _rank(self, insights: list[Insight], question: str) -> list[Insight]:
        """Xếp hạng: ĐỘ LIÊN QUAN tới câu hỏi trước, rồi mới tới độ quan trọng chung.

        Tầng độ-quan-trọng dùng lại `score_for_role` của delivery — KHÔNG tự chế tiêu
        chí mới. Bài học 21/07: xếp hạng, không lọc ngưỡng (Security có 42/64 entry
        `high` còn Data Scientist có 0/49; lọc ngưỡng vừa làm ngập người này vừa bỏ đói
        người kia).

        ⚠️ Vì sao độ liên quan phải đứng TRƯỚC: `score_for_role` đo độ quan trọng chung,
        hoàn toàn mù với nội dung câu hỏi. Đo 22/07/2026 khi cắt top-60 mà chỉ xếp theo
        `score_for_role`: recall tin liên quan chỉ **42%**, riêng câu "mô hình mã nguồn
        mở" còn **2/18 tin (11%)** — tin mã nguồn mở urgency thấp nên nằm hết ở đuôi và
        bị cắt sạch. Tệ hơn nữa là nó IM LẶNG: model vẫn trả lời trôi chảy từ 2 tin sót
        lại. Trộn độ liên quan vào khoá xếp hạng đưa recall lên ~90%.
        """
        if not insights:
            return []

        terms = _question_terms(question)
        roles = _roles_in_question(question)

        def importance(insight: Insight) -> tuple:
            if roles:
                return max(score_for_role(insight, r) for r in roles)
            return max(
                (score_for_role(insight, r) for r in (insight.affected_roles or [])),
                default=score_for_role(insight, "Toàn công ty"),
            )

        return sorted(
            insights,
            key=lambda i: (_relevance(i, terms), importance(i)),
            reverse=True,
        )

    async def _call_model(self, prompt: str) -> str:
        """Gọi Gemini NGOÀI event loop — chat nằm trên request path (design D6).

        Cộng vào `self._calls_used` NGAY khi model trả về, trước khi caller làm bất cứ
        việc gì khác: đó là thời điểm tiền đã tiêu, và mọi lỗi sau đó vẫn phải tính.
        """
        if self._steps_used >= MAX_MODEL_CALLS_PER_QUESTION:
            raise RuntimeError(
                f"Chạm trần {MAX_MODEL_CALLS_PER_QUESTION} bước trả lời cho một câu hỏi"
            )
        self._steps_used += 1
        text, calls = await asyncio.to_thread(self.gemini.chat, CHAT_SYSTEM_PROMPT, prompt)
        # `calls` có thể là 2 nếu lượt đầu bị cắt và client đã hỏi lại — vẫn tốn tiền thật
        # nên vẫn phải cộng vào budget, chỉ là KHÔNG tính như một bước mới.
        self._calls_used += calls
        return text
