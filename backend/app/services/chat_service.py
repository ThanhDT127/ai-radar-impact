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
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.gemini_client import ChatStreamState, GeminiClient, get_chat_client
from app.ai.prompts import (
    ALLOWED_ROLES,
    CHAT_SYSTEM_PROMPT,
    OUT_OF_SCOPE_SENTINEL,
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

# --- Sự kiện tiến trình (design D3/D4) ------------------------------------------------
# Phát từ MỐC THẬT của pipeline, không phải chuỗi trang trí chạy theo đồng hồ. Lý do tồn
# tại: Gemini 2.5 tiêu 5–15s đầu cho thinking, giai đoạn đó CHƯA có token nào để stream —
# nếu không lấp bằng status thì streaming vẫn để người dùng nhìn màn hình đứng đúng như
# trước (Nguy hiểm #1). Status nói đúng việc server đang làm, không hứa nhanh hơn thực tế.
STATUS_READING_INSIGHT = "Đang đọc bài đang xem…"
STATUS_SEARCHING = "Đang tìm trong hệ thống…"
STATUS_EXPANDING = "Bài đang xem không đề cập — đang tìm trên toàn hệ thống…"
STATUS_COMPOSING = "Đang soạn câu trả lời…"

# Kênh phát sự kiện. `None` = chế độ blocking: cùng một pipeline, chỉ khác lối ra.
Emitter = Callable[[dict], Awaitable[None]]

# Vật đánh dấu pipeline đã kết thúc, đi qua cùng hàng đợi với sự kiện thật.
_PIPELINE_DONE = object()

# Chờ tối đa ngần này giây cho pipeline tự dừng sau khi client ngắt, để `finally` của nó
# kịp ghi `chat_logs`. Ngắn — nó chỉ còn phải chạy nốt phần thuần CPU + một INSERT.
_ABORT_DRAIN_SECONDS = 10.0


class _SentinelGate:
    """Giữ token đầu luồng mode B lại cho tới khi chắc chắn KHÔNG phải sentinel.

    Đo thật 27/07/2026: câu ngoài phạm vi bài làm model sinh đúng một token
    `[[NGOÀI_PHẠM_VI_BÀI]]`, và nếu phát thẳng thì người dùng **nhìn thấy** chuỗi đó nhấp
    nháy trước khi lượt mở rộng ghi đè. Bản blocking không có lỗi này vì nó chỉ nhìn câu
    hoàn chỉnh — đây đúng là loại lỗi mà streaming sinh ra thêm.

    Cổng rất rẻ vì sentinel ngắn và `is_out_of_scope_answer` chỉ nhận khi nó là TOÀN BỘ câu
    trả lời: chỉ cần giữ chừng nào phần đã nhận còn có thể là *tiền tố* của sentinel. Câu
    trả lời bình thường lệch khỏi tiền tố ngay ở chunk đầu nên gần như không bị trễ.
    """

    def __init__(self, sentinel: str) -> None:
        self._sentinel = sentinel
        self._buffer = ""
        self._open = False

    def feed(self, piece: str) -> str:
        """Trả phần được phép phát ngay (có thể rỗng nếu còn phải giữ)."""
        if self._open:
            return piece
        self._buffer += piece
        # Cùng cách chuẩn hoá với `is_out_of_scope_answer` — hai bên phải nhìn cùng một thứ.
        probe = self._buffer.strip().strip("`").strip()
        if probe and not self._sentinel.startswith(probe):
            self._open = True
            return self._buffer
        return ""


def _next_chunk(iterator):
    """`next()` an toàn để chạy trong thread: `StopIteration` KHÔNG băng qua được ranh giới
    coroutine (nó biến thành `RuntimeError`), nên dịch sang một vật đánh dấu."""
    try:
        return next(iterator)
    except StopIteration:
        return _PIPELINE_DONE


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
    """Vai trò được nhắc tên trong câu hỏi — dùng để chọn trục xếp hạng.

    Khớp theo **BIÊN TỪ**, không phải chuỗi con. Cách cũ (`role.lower() in question.lower()`)
    cho `"tin về device IoT mới"` → `['Dev']` và `"DevOps cần chú ý gì"` → `['Dev']`. Ở công ty
    có trụ cột IoT/Smart Home thì `device` xuất hiện dày đặc, và hậu quả nặng hơn `_relevance`
    sai: `_relevance` lệch điểm MỘT tin, còn nhận nhầm vai trò **đổi cả trục xếp hạng** của toàn
    bộ danh sách sang vai trò đó — lặng lẽ, không log, không dấu hiệu. Nó còn kéo theo
    `empty_roles`, tức là có thể tuyên bố sai "hệ thống không có tin nào cho vai trò X".
    (`DevOps` lại còn thuộc taxonomy `Source.target_roles`, KHÔNG thuộc `ALLOWED_ROLES` — nhận
    ra `Dev` ở đó là sai hai lần.)

    Phải so **dãy token liên tiếp**, không so tập hợp: vai trò là cụm nhiều từ —
    `Data Analyst` (2 token), `Người dùng phổ thông` (4 token) — nên "phổ thông cho người dùng"
    không được tính là khớp. Dùng đúng regex tách token của `_question_terms` để hai bên không
    trôi khỏi nhau.
    """
    tokens = re.findall(r"[0-9a-zA-ZÀ-ỹ]+", question.lower())
    found = []
    for role in ALLOWED_ROLES:
        needle = re.findall(r"[0-9a-zA-ZÀ-ỹ]+", role.lower())
        if not needle:
            continue
        span = len(needle)
        if any(tokens[i:i + span] == needle for i in range(len(tokens) - span + 1)):
            found.append(role)
    return found


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
    """Số từ khoá của câu hỏi xuất hiện trong tin. 0 = không nhắc gì tới câu hỏi.

    So khớp **theo BIÊN TỪ**, không phải chuỗi con. Bản cũ dùng `t in haystack`, nên `"ai"`
    khớp trong *email, domain, training, chain, available, detail, fail, explain* — tầng độ
    liên quan mất sạch khả năng phân biệt đúng ở nhóm từ khoá ASCII ngắn.

    ⚠️ Ngưỡng 2 ký tự của `_question_terms` là ĐÚNG và phải giữ (tiếng Việt đơn âm: `mã`,
    `mở`, `dữ`). Vấn đề chưa bao giờ nằm ở ngưỡng mà ở cách so khớp — nâng ngưỡng lên 3 sẽ
    làm rụng từ tiếng Việt mà vẫn sai với `ML`, `OS`, `Go`.

    Tách haystack bằng CÙNG regex mà `_question_terms` dùng cho câu hỏi: hai bên phải nhìn
    thế giới bằng một luật, không thì lại sinh ra đúng loại lệch vừa phải sửa.
    """
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
    words = set(re.findall(r"[0-9a-zA-ZÀ-ỹ]+", haystack))
    return sum(1 for t in set(terms) if t in words)


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
        # Kênh phát sự kiện của lượt hiện tại. `None` = blocking (không phát gì). Đây là
        # KHÁC BIỆT DUY NHẤT giữa hai lối ra — grounding, xếp hạng, fail‑closed, budget đều
        # dùng chung một đoạn code (design D1).
        self._emit: Emitter | None = None
        # Client đã bỏ đi — token sinh thêm không còn ai đọc, nên dừng sớm. Không phải lỗi.
        self._aborted = False

    async def _status(self, text: str) -> None:
        """Phát một mốc tiến trình. No-op ở chế độ blocking."""
        if self._emit is not None:
            await self._emit({"type": "status", "text": text})

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
        self,
        question: str,
        history: list,
        insight_id: uuid.UUID | None,
        emit: Emitter | None = None,
    ) -> dict:
        """Điểm vào duy nhất. Ghi `chat_logs` trong `finally` để budget không rò rỉ.

        `emit` là lối ra streaming: truyền vào thì pipeline phát thêm `status`/`token` dọc
        đường; bỏ trống thì hàm chạy y hệt bản blocking cũ. KHÔNG có nhánh logic thứ hai —
        `answer_stream()` chỉ là hàm này cộng một hàng đợi (design D1).
        """
        self._emit = emit
        self._aborted = False
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
                    # Người dùng vừa thấy vài token của lượt B (nếu model có sinh gì trước
                    # sentinel) rồi phải chờ thêm 5–20s nữa. Nói thẳng đang làm gì, không
                    # để khoảng lặng thứ hai (design D4).
                    await self._status(STATUS_EXPANDING)
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
        await self._status(STATUS_READING_INSIGHT)
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
        raw_answer = await self._call_model(prompt, hold_sentinel=True)

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
        if focus is None:
            # Ở chế độ mở rộng, `answer()` đã phát STATUS_EXPANDING — nói lại "đang tìm
            # trong hệ thống" chỉ là nhiễu.
            await self._status(STATUS_SEARCHING)
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

        # Trục xếp hạng đang dùng hoàn toàn vô hình từ ngoài — không có cách nào biết
        # production xếp theo trục nào cho một câu cụ thể. Mức DEBUG chứ KHÔNG phải WARNING:
        # đây là quan sát, không phải lỗi. Log này cũng là dữ liệu để quyết có cần bảng đồng
        # nghĩa vai trò không (design D6: `developer` hiện KHÔNG kích hoạt trục `Dev`).
        logger.debug(
            "Trục xếp hạng: %s | %d/%d ứng viên | vai trò rỗng: %s",
            ", ".join(asked_roles) if asked_roles else "(không có vai trò — dùng affected_roles)",
            min(len(matched), settings.chat_index_top_k) if settings.chat_index_top_k > 0 else len(matched),
            len(matched),
            ", ".join(empty_roles) or "không",
        )

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

    async def _call_model(self, prompt: str, hold_sentinel: bool = False) -> str:
        """Gọi Gemini NGOÀI event loop — chat nằm trên request path (design D6).

        Cộng vào `self._calls_used` NGAY khi model trả về, trước khi caller làm bất cứ
        việc gì khác: đó là thời điểm tiền đã tiêu, và mọi lỗi sau đó vẫn phải tính.

        Có `self._emit` thì đi lối streaming — vẫn ĐÚNG MỘT bước, vẫn cùng prompt, vẫn trả
        về toàn văn cho phần grounding phía sau chạy y như cũ.
        """
        await self._status(STATUS_COMPOSING)
        if self._steps_used >= MAX_MODEL_CALLS_PER_QUESTION:
            raise RuntimeError(
                f"Chạm trần {MAX_MODEL_CALLS_PER_QUESTION} bước trả lời cho một câu hỏi"
            )
        self._steps_used += 1

        if self._emit is not None:
            return await self._stream_model(prompt, hold_sentinel=hold_sentinel)

        text, calls = await asyncio.to_thread(self.gemini.chat, CHAT_SYSTEM_PROMPT, prompt)
        # `calls` có thể là 2 nếu lượt đầu bị cắt và client đã hỏi lại — vẫn tốn tiền thật
        # nên vẫn phải cộng vào budget, chỉ là KHÔNG tính như một bước mới.
        self._calls_used += calls
        return text

    async def _stream_model(self, prompt: str, hold_sentinel: bool = False) -> str:
        """Một bước trả lời dạng streaming: phát `token` dọc đường, trả toàn văn ở cuối.

        `gemini.chat_stream` là generator SYNC (như phần còn lại của client), nên mỗi lần
        lấy chunk phải qua `to_thread` — không thì vòng lặp chặn event loop và mọi request
        khác đứng hình đúng lúc ta đang cố làm cho giao diện mượt hơn.

        `state.calls` cộng vào budget trong `finally`: lượt gọi đã tốn tiền phải được tính
        kể cả khi vòng lặp thoát vì client ngắt (design D5).

        `hold_sentinel` bật cổng chặn sentinel cho lượt mode B — xem `_SentinelGate`.
        """
        state = ChatStreamState()
        gate = _SentinelGate(OUT_OF_SCOPE_SENTINEL) if hold_sentinel else None
        iterator = self.gemini.chat_stream(CHAT_SYSTEM_PROMPT, prompt, state)
        try:
            while True:
                piece = await asyncio.to_thread(_next_chunk, iterator)
                if piece is _PIPELINE_DONE:
                    break
                if gate is not None:
                    piece = gate.feed(piece)
                    if not piece:
                        continue
                await self._emit({"type": "token", "text": piece})
                if self._aborted:
                    logger.info("Client đã ngắt — dừng sinh token giữa chừng")
                    break
        finally:
            iterator.close()
            self._calls_used += state.calls
        return state.text

    async def answer_stream(
        self, question: str, history: list, insight_id: uuid.UUID | None
    ) -> AsyncIterator[dict]:
        """Lối ra streaming: yield `status`/`token` dọc đường, kết bằng `commit` hoặc `error`.

        **Sự kiện chốt luôn mang toàn văn câu trả lời**, không chỉ citations. Token đã phát
        là *tạm* theo đúng nghĩa đen: `resolve_citations` dọn marker ngoài phạm vi và
        `enforce_grounding` có thể thay sạch câu trả lời (fail‑closed), mà cả hai chỉ chạy
        được trên câu HOÀN CHỈNH. Cho `commit` mang text cuối là cách duy nhất khiến trạng
        thái chốt trùng bản blocking mà không phải bịa ra một luật hoà giải thứ hai ở
        widget (design D2).

        Pipeline chạy trong task riêng để việc client ngắt (generator này bị đóng) không
        cắt ngang `finally` ghi `chat_logs`. Đó là chỗ rò budget dễ nhất của streaming.
        """
        queue: asyncio.Queue = asyncio.Queue()

        async def emit(event: dict) -> None:
            await queue.put(event)

        async def run() -> None:
            try:
                result = await self.answer(question, history, insight_id, emit=emit)
                await queue.put({"type": "commit", **result})
            except InsightNotFoundError:
                await queue.put({"type": "error", "code": "not_found"})
            except QuotaExceededError:
                await queue.put({"type": "error", "code": "quota"})
            except Exception as e:
                logger.error("Chat stream request failed: %s", e)
                await queue.put({"type": "error", "code": "server"})
            finally:
                await queue.put(_PIPELINE_DONE)

        task = asyncio.create_task(run())
        try:
            while True:
                event = await queue.get()
                if event is _PIPELINE_DONE:
                    break
                yield event
        finally:
            if not task.done():
                # Tới đây nghĩa là người tiêu thụ bỏ đi trước khi pipeline xong.
                self._aborted = True
                logger.info("Luồng chat bị bỏ dở — dừng sinh, vẫn chờ ghi budget")
                # `shield` để lượt huỷ của Starlette không kéo theo cả pipeline: nó còn
                # phải chạy nốt `finally` ghi `chat_logs`. Hết giờ thì thả cho chạy nốt ở
                # nền — thà ghi muộn còn hơn không ghi.
                try:
                    await asyncio.wait_for(
                        asyncio.shield(task), timeout=_ABORT_DRAIN_SECONDS
                    )
                except asyncio.TimeoutError:
                    logger.warning("Pipeline chat chưa kết thúc kịp sau khi client ngắt")
