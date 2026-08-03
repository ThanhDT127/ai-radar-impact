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

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.gemini_client import (
    EMBED_TASK_QUERY,
    ChatStreamState,
    GeminiClient,
    get_chat_client,
)
from app.ai.prompts import (
    ALLOWED_ROLES,
    CHAT_SYSTEM_PROMPT,
    OUT_OF_SCOPE_SENTINEL,
    build_chat_expanded_prompt,
    build_chat_focused_prompt,
    build_chat_global_prompt,
    build_chat_insight_prompt,
)
from app.config import settings
from app.models.insight import Insight
from app.models.raw_document import RawDocument
from app.repositories.chat_log_repo import ChatLogRepository
from app.repositories.document_chunk_repo import DocumentChunkRepository
from app.repositories.insight_repo import InsightRepository
from app.services.chat_grounding import (
    build_context,
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

# Hằng số làm phẳng của Reciprocal Rank Fusion: `1/(RRF_K + rank)`. 60 là giá trị chuẩn
# trong tài liệu gốc và điều nó mua là **chống nhiễu ở đỉnh** — chênh lệch giữa hạng 1 và
# hạng 2 chỉ 1/61 − 1/62, nên một tín hiệu xếp sai một bậc không lật được kết quả.
#
# ⚠️ Trùng số 60 với `settings.chat_index_top_k` là NGẪU NHIÊN, hai thứ không liên quan:
# đây là hằng số làm phẳng, kia là số tin đưa vào prompt. Đổi K không được đổi số này.
RRF_K = 60

# --- Sự kiện tiến trình (design D3/D4) ------------------------------------------------
# Phát từ MỐC THẬT của pipeline, không phải chuỗi trang trí chạy theo đồng hồ. Lý do tồn
# tại: Gemini 2.5 tiêu 5–15s đầu cho thinking, giai đoạn đó CHƯA có token nào để stream —
# nếu không lấp bằng status thì streaming vẫn để người dùng nhìn màn hình đứng đúng như
# trước (Nguy hiểm #1). Status nói đúng việc server đang làm, không hứa nhanh hơn thực tế.
STATUS_READING_INSIGHT = "Đang đọc bài đang xem…"
STATUS_SEARCHING = "Đang tìm trong hệ thống…"
STATUS_EXPANDING = "Bài đang xem không đề cập — đang tìm trên toàn hệ thống…"
STATUS_COMPOSING = "Đang soạn câu trả lời…"

# Số tin nêu tên trong status. Hai là đủ để người dùng nhận ra hệ thống đang đọc ĐÚNG bài
# mình quan tâm; nhiều hơn thì dòng status dài quá và bị cắt trên panel hẹp.
_STATUS_TITLES = 2
_STATUS_TITLE_LEN = 38


def _reading_status(ctx) -> str:
    """Mốc "đang đọc kỹ" mang SỐ LIỆU THẬT của lượt này.

    Vì sao đáng làm: đo 28/07/2026 trên đường SSE (client singleton, kết nối ấm) — TTFT
    2,6–3,8s, và **85% của nó là lượt gọi model**, không cắt được bằng cách nhỏ prompt hay
    ngắn câu trả lời (đã đo cả hai: bỏ raw content khỏi ô sâu đổi TTFT 3,3 → 3,2s trong khi
    câu hỏi chi tiết quay lại từ chối). Bài học `chat-streaming-sse` giữ nguyên: TTFT thật
    không cắt được, **status mới là thứ chữa** — nên cải thiện nằm ở chỗ nói ĐÚNG việc đang
    làm, không ở chỗ chạy nhanh hơn.

    Số liệu lấy từ `ctx`, không phải chuỗi trang trí chạy theo đồng hồ: nói sai việc còn tệ
    hơn nói chung chung.
    """
    if not ctx.deep_count:
        return STATUS_COMPOSING

    def short(title: str) -> str:
        title = (title or "").strip()
        return title if len(title) <= _STATUS_TITLE_LEN else title[: _STATUS_TITLE_LEN - 1] + "…"

    titles = [f"«{short(ctx.mapping[n].title)}»" for n in range(1, ctx.deep_count + 1)]
    named = ", ".join(titles[:_STATUS_TITLES])
    if len(titles) > _STATUS_TITLES:
        named += f" và {len(titles) - _STATUS_TITLES} tin nữa"
    scope = f" trong {ctx.total_matched} tin khớp" if ctx.total_matched else ""
    return f"Đang đọc kỹ {ctx.deep_count} tin: {named}{scope}…"

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


_HISTORY_MARKER_RE = re.compile(r"\[(\d+)\]")


def _history_block(history: list) -> str:
    """Ghép history thành text, **giải marker `[n]` thành tên bài** (design D4).

    Bảng ánh xạ `n → insight` được dựng LẠI mỗi lượt (theo kết quả `_rank` của lượt đó),
    nên một con số trong history gần như chắc chắn trỏ tin khác ở lượt hiện tại: lượt trước
    `[3]` là tin Kubernetes, lượt này `[3]` là tin EU AI Act, và model đọc được hai nghĩa
    của cùng một số. Đây là lỗi **đã tồn tại** trước change này, chỉ chưa lộ vì mỗi lượt
    model chủ yếu nhìn khối DỮ LIỆU mới.

    Không đánh số lại và không xoá trắng: đánh lại đòi một sổ đánh số sống qua nhiều lượt
    mà server thì stateless; xoá trắng thì mất luôn khả năng hiểu "so sánh [1] với [2] ở
    trên". Thay bằng nhãn đọc được giữ nguyên ngữ nghĩa tham chiếu mà không tạo hệ quy
    chiếu số thứ hai.

    Lượt không kèm citations (client cũ) → marker bị **bỏ**, vì một con số vô nghĩa còn tệ
    hơn không có gì.
    """
    if not history:
        return ""
    lines = []
    for turn in history:
        who = "Người dùng" if turn.role == "user" else "Trợ lý"
        titles = {c.n: c.title for c in getattr(turn, "citations", None) or []}
        content = _HISTORY_MARKER_RE.sub(
            lambda m: f"[«{titles[int(m.group(1))]}»]" if int(m.group(1)) in titles else "",
            turn.content,
        )
        lines.append(f"{who}: {content.strip()}")
    return "\n".join(lines)


def _history_pin_ids(history: list, limit: int) -> list[uuid.UUID]:
    """Định danh insight cần GHIM, lấy từ citations của các lượt trước.

    Quét theo **LỚP**, không phải cạn từng lượt: vòng đầu lấy nguồn thứ nhất của mỗi lượt
    (lượt mới trước lượt cũ), vòng sau lấy nguồn thứ hai của mỗi lượt, cứ thế tới `limit`.
    Hàm THUẦN, tất định — cùng history cho cùng kết quả, KHÔNG phụ thuộc câu hỏi hiện tại.

    ⚠️ **Vì sao theo lớp — bản "cạn từng lượt" đã ĐO ĐƯỢC là hỏng** (29/07/2026). Một lượt
    trả lời toàn cục trích tới **5 nguồn**, mà chỉ có 3 chỗ ghim. Duyệt cạn lượt gần nhất
    trước ⇒ **đúng một lượt chen giữa là đủ để đẩy sạch mọi thứ trước nó ra ngoài**. Đo thật:
    bàn tin X ở lượt 1, hỏi một câu khác chủ đề ở lượt 2 (trích 5 nguồn), thì tới lượt 3 tập
    ghim là 3 nguồn của **riêng lượt 2** — X đứng thứ **6** trong danh sách, văng khỏi trần.
    Nghĩa là cơ chế chỉ phủ được đúng lượt liền trước, không phải "3 tin gần nhất của cuộc
    hội thoại" như spec tuyên bố.

    Quét theo lớp sửa đúng chỗ đó mà **không** đổi hành vi ca phổ biến nhất: history chỉ có
    một lượt có nguồn thì vòng 1/2/3 lần lượt lấy nguồn 1, 2, 3 của chính lượt đó ⇒ kết quả
    trùng khít bản cũ. Chỉ khi có nhiều lượt thì nó mới trải ra — và đó đúng là lúc bản cũ sai.

    Cái cần nhớ là **3 CHỦ ĐỀ gần nhất**, không phải 3 dòng trích gần nhất.

    Vì sao "gần nhất" chứ không phải "liên quan nhất": chấm điểm liên quan ở đây là một
    heuristic đoán ý định, đúng loại lỗi repo này đã trả giá nhiều lần (`_roles_in_question`
    khớp chuỗi con, `_CAPABILITY_PHRASES` code chết). Luật một dòng thì kiểm chứng được.

    ⚠️ Đây là bất biến **đã thu hẹp** so với câu chữ của `chat-context-depth` ("MỌI tin được
    nhắc trong history đều còn mặt trong ngữ cảnh"). Bản nguyên văn không thực thi được:
    history đầy có thể nhắc tới ~25 tin, mà RS harness cho thấy ghim quá 6 chỗ là recall@K
    tụt khỏi baseline (0,968 → 0,954 ở 7 chỗ). Giữ recall, thu hẹp lời hứa — và nói rõ ra.
    """
    if limit <= 0:
        return []
    # Nguồn của từng lượt, lượt MỚI trước. Lượt không có nguồn nào (câu người dùng, hoặc
    # client cũ không gửi định danh) biến mất khỏi đây luôn — nó không chiếm một lớp.
    theo_luot: list[list[uuid.UUID]] = []
    for turn in reversed(history):
        ids = [
            c.insight_id
            for c in (getattr(turn, "citations", None) or [])
            if getattr(c, "insight_id", None) is not None
        ]
        if ids:
            theo_luot.append(ids)

    out: list[uuid.UUID] = []
    seen: set[uuid.UUID] = set()
    lop = 0
    while len(out) < limit:
        con_nguon = False
        for ids in theo_luot:
            if lop >= len(ids):
                continue
            con_nguon = True
            insight_id = ids[lop]
            if insight_id in seen:
                continue
            seen.add(insight_id)
            out.append(insight_id)
            if len(out) >= limit:
                return out
        if not con_nguon:  # mọi lượt đã cạn nguồn
            break
        lop += 1
    return out


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


def _best_chunk_match(chunk_ranks: dict[uuid.UUID, int] | None) -> uuid.UUID | None:
    """Tin giữ đoạn khớp NHẤT toàn corpus (hạng đoạn 1), hoặc `None`.

    Chỉ nhận hạng **1** chứ không phải "hạng tốt nhất trong số đã trả về": hạng 1 nghĩa là
    trên toàn bảng `document_chunks` không đoạn nào gần câu hỏi hơn đoạn này. Nới ra hạng 2–3
    là bắt đầu đoán, và ô sâu chỉ có 3 suất — mỗi suất chen vào là một tin xếp hạng cao bị
    đẩy ra.

    Hoà nhau (nhiều tin cùng hạng 1) thì trả `None`: không có căn cứ chọn tin nào, mà chọn
    bừa theo thứ tự dict là đưa một yếu tố tuỳ tiện vào context.
    """
    if not chunk_ranks:
        return None
    firsts = [i for i, rank in chunk_ranks.items() if rank == 1]
    return firsts[0] if len(firsts) == 1 else None


def _cosine(a, b) -> float:
    """Cosine similarity giữa hai vector. Trả 0.0 nếu một bên là vector không.

    Nhận cả `list[float]` (fixture, JSON) lẫn `numpy.ndarray` (pgvector trả về) — hai đường
    này gặp nhau ở đây nên phép quy đổi phải nằm đúng một chỗ.
    """
    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    norm = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if norm == 0.0:
        return 0.0
    return float(np.dot(va, vb) / norm)


def _competition_ranks(scores: list[float]) -> list[int]:
    """Thứ hạng 1..N theo điểm giảm dần, **điểm bằng nhau thì hạng bằng nhau**.

    Bắt buộc phải là competition ranking chứ không phải `enumerate` trên danh sách đã sort:
    tầng lexical cho rất nhiều tin cùng điểm 0 (câu hỏi không nhắc từ khoá nào của chúng), và
    nếu phá hoà bằng thứ tự tình cờ trong list thì RRF nhận một tín hiệu NGẪU NHIÊN — tin nào
    tình cờ đứng trước trong kết quả SQL được cộng điểm. Hạng bằng nhau thì đóng góp RRF bằng
    nhau, và việc phân định nhường lại cho tầng vector và khoá phụ `score_for_role`.
    """
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    ranks = [0] * len(scores)
    prev_score = None
    prev_rank = 0
    for position, idx in enumerate(order, start=1):
        if prev_score is not None and scores[idx] == prev_score:
            ranks[idx] = prev_rank
        else:
            ranks[idx] = position
            prev_rank = position
            prev_score = scores[idx]
    return ranks


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
        # Tầng đoạn chạm DB ở ĐÂY và chỉ ở đây (design D4, phương án B) — `_rank` nhận
        # `chunk_ranks` làm tham số và vẫn là hàm thuần, nhờ vậy RS harness đo được offline.
        self.chunk_repo = DocumentChunkRepository(session)
        # Bộ đếm lượt gọi ĐÃ TỐN TIỀN của request hiện tại. Phải là thuộc tính instance
        # chứ không phải giá trị trả về: nếu đếm bằng return thì một lỗi giữa chừng
        # (sau khi model đã trả lời) làm số đếm biến mất và budget rò rỉ.
        # An toàn vì service là per-request — AsyncSession vốn không dùng chung được.
        self._calls_used = 0
        # Số BƯỚC trả lời đã chạy (mode B / mode A / mở rộng). Tách khỏi `_calls_used` vì
        # một bước có thể tốn 2 lượt khi câu trả lời bị cắt và phải hỏi lại — xem ghi chú
        # ở `MAX_MODEL_CALLS_PER_QUESTION`.
        self._steps_used = 0
        # Token SUY LUẬN cộng dồn của lượt hiện tại. `None` = chưa đo được lần nào (nhà cung
        # cấp không báo cáo) — KHÁC `0` = đã ghìm về 0 và model tuân thủ. Cộng dồn qua mọi
        # bước, kể cả lượt mở rộng và lượt hỏi lại chống-cắt, vì tất cả đều tốn tiền thật.
        self._thinking_tokens: int | None = None
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
        referenced_insight_ids: list[uuid.UUID] | None = None,
    ) -> dict:
        """Điểm vào duy nhất. Ghi `chat_logs` trong `finally` để budget không rò rỉ.

        `emit` là lối ra streaming: truyền vào thì pipeline phát thêm `status`/`token` dọc
        đường; bỏ trống thì hàm chạy y hệt bản blocking cũ. KHÔNG có nhánh logic thứ hai —
        `answer_stream()` chỉ là hàm này cộng một hàng đợi (design D1).

        `referenced_insight_ids` là working set người dùng chọn (chat-context-depth). Có
        refs ⇒ `mode="focused"`, **một** lượt gọi, không sentinel: context đã mang cả ô sâu
        lẫn index toàn hệ thống nên không còn gì để mở rộng sang (design D5).
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

        # Refs nạp TRƯỚC khi chốt mode: ref chết bị bỏ lặng lẽ (design D7), nên "có refs
        # trong payload" chưa chắc là "có ô sâu do người dùng chọn".
        refs = await self._load_refs(referenced_insight_ids)
        if refs:
            mode = "focused"
        elif insight_id:
            mode = "insight"
        else:
            mode = "global"
        started = time.monotonic()
        self._calls_used = 0
        self._steps_used = 0
        self._thinking_tokens = None
        citations: list[dict] = []
        try:
            if refs:
                # Đường working set: bỏ qua hoàn toàn mode B + sentinel. `insight_id` (bài
                # đang mở) đã nằm trong refs do widget tự thêm, nên không mất ngữ cảnh.
                answer, citations = await self._answer_global(question, history, refs=refs)
            elif insight_id:
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
                    thinking_tokens=self._thinking_tokens,
                )

    async def _load_refs(
        self, ids: list[uuid.UUID] | None, limit: int | None = None
    ) -> list[Insight]:
        """Nạp insight theo danh sách id, GIỮ thứ tự client gửi.

        Suy giảm êm (design D7) — ref chết bị bỏ **lặng lẽ**, không 404: người dùng có thể
        ghim một tin rồi tin đó bị unpublish giữa chừng, và làm hỏng cả câu hỏi vì một chip
        cũ là đổi sai. Thứ tự client gửi quyết định thứ tự ô sâu, nên phải sắp lại sau khi
        SQL trả về (`IN` không bảo toàn thứ tự).

        Cắt ở `limit` (mặc định `chat_deep_slots`): gửi thừa thì lấy phần đầu, không báo lỗi.

        Dùng chung cho **hai** nguồn id: working set (`referenced_insight_ids`) và tin ghim vì
        lịch sử (`chat-history-pinning`). Cố ý một đường nạp duy nhất — hai đường với hai bộ
        lọc hơi khác nhau là cách chắc chắn để một hôm nào đó ghim được thứ mà working set
        không nạp nổi, hoặc ngược lại, mà không có gì báo lỗi.
        """
        if not ids:
            return []
        wanted = ids[: settings.chat_deep_slots if limit is None else limit]
        result = await self.session.execute(
            select(Insight)
            .where(Insight.id.in_(wanted))
            .where(Insight.status == "published")
            # Ô sâu cần `normalized_content`; nạp kèm ngay để không thành N+1 khi dựng block.
            .options(selectinload(Insight.raw_document).selectinload(RawDocument.source))
        )
        by_id = {i.id: i for i in result.scalars().all()}
        refs = [by_id[i] for i in wanted if i in by_id]
        if len(refs) < len(wanted):
            logger.info(
                "Bỏ %d tham chiếu không còn khả dụng (còn %d)", len(wanted) - len(refs), len(refs)
            )
        return refs

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
        self,
        question: str,
        history: list,
        focus: _InsightAttempt | None = None,
        refs: list[Insight] | None = None,
    ) -> tuple[str, list[dict]]:
        """Một đường trả lời cho ba ca: toàn cục · working set · mở rộng.

        Chúng chỉ khác nhau ở **ai chọn tin để rót sâu** — và đó đúng là tham số `refs` của
        `build_context`. Tách thành hai method là để hai lối ra trôi khỏi nhau trong im lặng
        (bài học `chat-streaming-sse`: grounding/xếp hạng/fail-closed phải dùng chung code).
        """
        refs = refs or []
        if focus is None and not refs:
            # Ở chế độ mở rộng, `answer()` đã phát STATUS_EXPANDING — nói lại "đang tìm
            # trong hệ thống" chỉ là nhiễu.
            await self._status(STATUS_SEARCHING)
        elif refs:
            await self._status(STATUS_READING_INSIGHT)
        since = None
        if settings.chat_window_days > 0:
            since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(
                days=settings.chat_window_days
            )

        asked_roles = _roles_in_question(question)
        # Hai việc độc lập hoàn toàn: embed câu hỏi (~1,4s, chờ mạng Vertex) và nạp ứng viên
        # (~0,2s, chờ Postgres). Chạy nối tiếp là cộng thẳng hai khoảng chờ vào độ trễ; ở ngân
        # sách 5s thì 0,2s tiết kiệm được là 4% (design D4).
        #
        # Chế độ mở rộng của `chat-scope-routing` đi qua đúng hàm này, nên nó hưởng luôn
        # recall ngữ nghĩa mà không cần một đường truy hồi riêng.
        # Tín hiệu đoạn PHỤ THUỘC vector câu hỏi, nên nó không thể song song với
        # `_embed_question` — nhưng chuỗi (embed → truy vấn đoạn) thì song song được với
        # `list_for_chat`. Gộp thành một nhánh để phần chờ Postgres (~0,2s) che luôn truy vấn
        # HNSW (~13ms), thay vì cộng nối tiếp vào sau.
        async def _vector_then_chunks():
            vector = await self._embed_question(question)
            return vector, await self._chunk_ranks(vector)

        matched, (query_vector, chunk_ranks) = await asyncio.gather(
            self.insight_repo.list_for_chat(published_since=since),
            _vector_then_chunks(),
        )
        matched = self._rank(matched, question, query_vector, chunk_ranks)

        # Tin ghim vì lịch sử nạp NỐI TIẾP, cố ý KHÔNG nhét vào cụm `gather` trên.
        # `AsyncSession` không an toàn khi hai truy vấn chạy đồng thời; cụm trên chỉ sống
        # được vì nhánh vector phải chờ `_embed_question` (~0,37s) xong mới chạm DB, tức là
        # `list_for_chat` gần như luôn xong trước. Thêm một truy vấn khởi động NGAY vào đó là
        # đua thẳng với `list_for_chat` — hỏng ngẫu nhiên dưới tải, đúng loại lỗi không tái
        # hiện được. Giá phải trả là một truy vấn theo khoá chính (~vài ms), so với 85% TTFT
        # nằm ở lượt gọi model thì không đáng để đánh đổi.
        pinned = await self._load_refs(
            _history_pin_ids(history, settings.chat_history_pin_slots),
            limit=settings.chat_history_pin_slots,
        )

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
        # Ô sâu lấp tất định rồi mới tới index nén — cắt vẫn ở `chat_index_top_k`, chỉ khác
        # là vài tin đầu được rót đầy đủ thay vì một dòng 115 token.
        #
        # Mở rộng (`focus`) đi qua đúng hàm này với **một** ô sâu là bài đang xem, tức là
        # trùng khít hành vi cũ ([1] = bài đang xem, index từ [2], bài đó bị loại khỏi
        # index) — design D5 giữ đường cũ nguyên xi.
        ctx = build_context(
            refs=[focus.insight] if focus is not None else refs,
            ranked=matched,
            k_deep=1 if focus is not None else settings.chat_deep_slots,
            index_limit=settings.chat_index_top_k,
            include_content=True if focus is not None else settings.chat_deep_include_content,
            # Chỉ áp cho chế độ toàn cục/working set. Chế độ mở rộng có đúng MỘT ô sâu là bài
            # đang xem (design D5 giữ đường cũ nguyên xi), chen tin khác vào đó sẽ đẩy chính
            # bài người dùng đang đọc ra ngoài.
            best_chunk_match=None if focus is not None else _best_chunk_match(chunk_ranks),
            # Áp cho CẢ ba ca (toàn cục · working set · mở rộng) — một đường code, không rẽ
            # nhánh theo mode. Lịch sử hội thoại là một luồng duy nhất từ `chat-context-depth`,
            # nên tin đã bàn cần có mặt bất kể lượt này đang ở phạm vi nào.
            pinned=pinned,
        )
        index_block, mapping = ctx.index_block, ctx.mapping

        logger.debug(
            "Trục xếp hạng: %s | truy hồi: %s | %d ô sâu (%d do người dùng chọn) + %d index / %d ứng viên"
            " | vai trò rỗng: %s",
            ", ".join(asked_roles) if asked_roles else "(không có vai trò — dùng affected_roles)",
            # Phân biệt lượt chạy lai với lượt đã rơi về lexical: suy giảm êm mà không để
            # lại dấu vết nào thì một sự cố embedding kéo dài trông y hệt "chat hơi kém".
            "lai (vector+lexical)" if query_vector is not None else "CHỈ LEXICAL (embed vắng)",
            ctx.deep_count,
            len(refs),
            len(ctx.mapping) - ctx.deep_count,
            ctx.total_matched,
            ", ".join(empty_roles) or "không",
        )

        # Model chỉ nhìn thấy phần đã cắt, nên nếu để nó tự đếm "Còn N tin khác" thì con
        # số sẽ thiếu đúng bằng phần bị cắt. Đưa tổng thật vào.
        if ctx.hidden > 0:
            shown = ctx.total_matched - ctx.hidden
            index_block += (
                f"\n\nLƯU Ý: đây là {shown} tin đáng chú ý nhất; hệ thống còn "
                f"{ctx.hidden} tin nữa xếp hạng thấp hơn. Khi cần nói \"Còn N tin khác\", "
                f"N tính trên tổng {ctx.total_matched} tin."
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
        # Cho phép hình dạng đối chiếu khi có ≥2 ô sâu — dưới đó thì "so sánh" vô nghĩa.
        allow_comparison = ctx.deep_count >= 2
        if focus is not None:
            prompt = build_chat_expanded_prompt(
                insight_block=ctx.deep_block,
                index_block=index_block,
                history_block=history_block,
                question=question,
            )
        elif refs:
            prompt = build_chat_focused_prompt(
                deep_block=ctx.deep_block,
                index_block=index_block,
                history_block=history_block,
                question=question,
                allow_comparison=allow_comparison,
            )
        else:
            prompt = build_chat_global_prompt(
                index_block=index_block,
                history_block=history_block,
                question=question,
                deep_block=ctx.deep_block,
                allow_comparison=allow_comparison,
            )
        # Thay STATUS_COMPOSING chung chung bằng mốc mang số liệu thật — KHÔNG phát thêm
        # một sự kiện nữa: hai status cách nhau vài chục ms chỉ làm dòng chữ nhấp nháy.
        raw_answer = await self._call_model(prompt, status=_reading_status(ctx))

        answer, citations = resolve_citations(raw_answer, mapping)
        answer, citations = enforce_grounding(answer, citations)
        return answer, citations

    def _rank(
        self,
        insights: list[Insight],
        question: str,
        query_vector: list[float] | None = None,
        chunk_ranks: dict[uuid.UUID, int] | None = None,
    ) -> list[Insight]:
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

        **Tầng độ-liên-quan nay là LAI (chat-hybrid-retrieval, 27/07/2026)**: trộn thứ
        hạng lexical (`_relevance`, khớp biên từ) với thứ hạng vector (cosine embedding)
        bằng Reciprocal Rank Fusion `1/(60 + rank)`. Lý do là chế độ hỏng còn lại của bản
        thuần keyword: hỏi "cắt giảm nhân sự" trong khi tin ghi *layoff* thì `_relevance`
        trả 0 và tin đúng nằm ở đuôi — mù đồng nghĩa, và im lặng y hệt ca 42% ở trên.

        Vì sao **RRF chứ không cộng điểm thô**: cosine và số-từ-khoá-khớp không cùng thang
        đo, chuẩn hoá chúng về một thang là bịa ra một hằng số không ai kiểm được. RRF chỉ
        đọc THỨ HẠNG nên miễn nhiễm với chuyện đó.

        Vì sao **giữ cả lexical** thay vì thay hẳn bằng vector: vector kém ở khớp CHÍNH XÁC
        (tên model, mã CVE, số phiên bản) — đúng loại câu hỏi hay gặp ở đây. RRF giữ được
        cả hai điểm mạnh; đó là lý do dùng *hybrid* chứ không *vector-only*.

        **KHÔNG ngưỡng similarity** (design D3): vector chỉ để xếp hạng TỐT HƠN, không để
        lọc. Vẫn cắt top-K nên tập ứng viên không bao giờ rỗng vì "không tin nào đủ giống" —
        ngưỡng cứng sẽ tái sinh đúng cái chế độ hỏng change này đang chữa.

        `query_vector=None` (embed lỗi, hoặc tắt bằng `chat_embedding_enabled`) → tầng
        vector biến mất và thứ tự **trùng khít bản lexical cũ**: RRF trên một tín hiệu là
        hàm đơn điệu của chính thứ hạng đó. Suy giảm êm theo đúng nghĩa đen, không phải một
        đường xếp hạng thứ hai chạy song song (design D6).

        **Số hạng THỨ BA: tương đồng ở mức ĐOẠN THÂN BÀI** (`chat-chunk-retrieval`,
        28/07/2026). Hai tín hiệu trên đều đọc *bản phân tích do Gemini viết*, không đọc bài
        viết: `_relevance` soi 5 field phân tích, `build_embedding_text` embed đúng 5 field
        đó. Đo 28/07 trên 179 bài, biểu diễn truy hồi phủ **4%** từ vựng thân bài — thứ mất
        đi là phần đặc trưng nhất (`CVE-2026-9770`, `SquashFS`, `SPDX`, `Annex III`). Hệ quả
        là **khám phá bằng chi tiết** hỏng: hỏi bằng một định danh chỉ có trong thân bài thì
        không tín hiệu nào biết bài đó tồn tại. `chunk_ranks` mang thứ hạng của **đoạn khớp
        tốt nhất** thuộc mỗi tin (design D1 — trung bình sẽ phạt bài dài có nhiều đoạn lạc đề).

        `chunk_ranks=None` hoặc tin vắng mặt trong đó → mượn `rank_vector` của chính nó, đúng
        luật mà tin thiếu embedding đang dùng (design D2). Đây là điều kiện làm cửa sổ backfill
        không thành một thiên lệch hệ thống.
        """
        if not insights:
            return []

        terms = _question_terms(question)
        roles = _roles_in_question(question)

        # Câu hỏi KHÔNG mang từ nội dung nào ("Có gì mới không?", "Có tin AI nào không?" —
        # `ai` là stopword vì trùng đại từ tiếng Việt) thì embedding của nó là **nhiễu**:
        # không có chủ đề để mà giống. Xếp hạng ở đây phải rơi về độ quan trọng, đúng như
        # thiết kế cũ — `_relevance` trả 0 cho tất cả cũng chính là để nhường cho
        # `score_for_role`.
        #
        # Đo 27/07/2026: bỏ cổng này thì `rank-generic` ("Có gì mới không?") tụt recall@5
        # từ 1,00 xuống 0,00 — tin CISA ra lệnh vá khẩn rơi xuống hạng 23 để nhường chỗ cho
        # những tin có embedding tình cờ gần một câu hỏi rỗng nghĩa. Tức là tầng vector
        # **đè** tầng độ quan trọng bằng nhiễu.
        #
        # ⚠️ Điều kiện là "câu hỏi rỗng từ khoá", KHÔNG phải "không tin nào khớp từ khoá".
        # Câu tiếng Việt hỏi về corpus tiếng Anh cho `_relevance` = 0 ở mọi tin nhưng vẫn có
        # nội dung ngữ nghĩa thật — đó đúng là ca tầng vector sinh ra để cứu.
        if not terms:
            query_vector = None
            # ⚠️ Tầng ĐOẠN phải tắt cùng lúc, không chỉ tầng vector mức insight. Lý do y hệt
            # và hậu quả còn nặng hơn: câu không có chủ đề thì đoạn nào cũng "hơi giống", mà
            # đoạn là văn bản thô nên nhiễu còn mạnh hơn bản phân tích cô đọng.
            #
            # Đo 28/07/2026, bỏ sót đúng dòng này: `rank-generic` ("Có gì mới không?") tụt
            # recall@60 1,00 → 0,00 — tin CISA ra lệnh vá khẩn rơi xuống **hạng 109/179**,
            # tức là văng khỏi cả index chứ không chỉ khỏi top-5. Lượt mô phỏng trước đó
            # KHÔNG thấy lỗi này vì script mô phỏng tự áp cổng ở ngoài; chỉ khi tầng đoạn
            # chạy qua đúng `_rank` của production thì nó mới lộ ra.
            chunk_ranks = None

        def importance(insight: Insight) -> tuple:
            if roles:
                return max(score_for_role(insight, r) for r in roles)
            return max(
                (score_for_role(insight, r) for r in (insight.affected_roles or [])),
                default=score_for_role(insight, "Toàn công ty"),
            )

        lexical_ranks = _competition_ranks([_relevance(i, terms) for i in insights])
        vector_ranks = self._vector_ranks(insights, query_vector)

        def rrf(index: int) -> float:
            rank_lexical = lexical_ranks[index]
            # Tin không có tầng vector (chưa backfill, embed lỗi, hoặc cả lượt này không có
            # vector câu hỏi) mượn CHÍNH thứ hạng lexical của nó cho số hạng thứ hai —
            # "thiếu thông tin thì giả định tín hiệu vắng mặt đồng ý với tín hiệu đang có".
            #
            # ⚠️ Bỏ hẳn số hạng đó đi (cách viết đầu tiên) là một hình phạt NGẦM và rất nặng:
            # tin thiếu vector chỉ được cộng một nửa số điểm, nên nó thua cả khi khớp từ khoá
            # chính xác. Test `test_insight_without_embedding_is_not_dropped` bắt đúng ca đó:
            # tin khớp `kubernetes` nhưng chưa embed thua một tin lạc đề đã embed. Trong cửa
            # sổ backfill (nhiều tin NULL) điều đó thành một thiên lệch hệ thống, im lặng.
            #
            # Cho cosine = 0 cũng sai theo hướng khác: 0 là một thứ hạng THẬT ở cuối bảng,
            # tức là biến "chưa biết" thành "chắc chắn không liên quan".
            rank_vector = vector_ranks[index]
            if rank_vector is None:
                rank_vector = rank_lexical
            score = 1.0 / (RRF_K + rank_lexical) + 1.0 / (RRF_K + rank_vector)

            if not chunk_ranks:
                # ⚠️ Cả lượt không có tín hiệu đoạn (truy vấn chunk lỗi, chưa backfill, câu
                # rỗng từ khoá) thì BỎ HẲN số hạng thứ ba — không phải cho nó mượn
                # `rank_vector`. Mượn ở đây sẽ nhân đôi trọng số tầng vector và cho ra một
                # thứ tự KHÁC bản hai tín hiệu, tức là một đường xếp hạng thứ ba xuất hiện
                # đúng vào lúc hệ thống đang hỏng. Suy giảm êm nghĩa là **trùng khít**.
                return score
            # Trong lượt CÓ tín hiệu đoạn, tin chưa được chunk mượn `rank_vector` của chính
            # nó (design D2) — cùng luật với tin thiếu embedding ở trên, và cùng lý do: bỏ
            # số hạng đi là phạt ngầm một phần ba, cho cosine 0 là biến "chưa biết" thành
            # "chắc chắn không liên quan". Đó là điều kiện để cửa sổ backfill không thành
            # một thiên lệch hệ thống.
            rank_chunk = chunk_ranks.get(insights[index].id, rank_vector)
            return score + 1.0 / (RRF_K + rank_chunk)

        order = sorted(
            range(len(insights)),
            key=lambda idx: (rrf(idx), importance(insights[idx])),
            reverse=True,
        )
        return [insights[idx] for idx in order]

    @staticmethod
    def _vector_ranks(
        insights: list[Insight], query_vector: list[float] | None
    ) -> list[int | None]:
        """Thứ hạng theo cosine với câu hỏi. `None` = tin này không có tầng vector.

        Tin `embedding IS NULL` (chưa backfill, hoặc embed lỗi lúc publish) nhận `None` chứ
        KHÔNG bị loại: nó vẫn cạnh tranh đầy đủ ở tầng lexical và vẫn có thể lọt top-K
        (design D6). Cho nó cosine 0 thay vì `None` sẽ tệ hơn — 0 là một thứ hạng THẬT ở
        cuối bảng, tức là biến "chưa biết" thành "chắc chắn không liên quan".

        Xếp hạng tính trong Python trên tập ứng viên đã nạp sẵn, không phải bằng `ORDER BY
        embedding <=> :q` trong SQL. Cố ý: `_rank` phải là hàm THUẦN để RS harness đo được
        offline, miễn phí, tất định. Ở quy mô vài nghìn tin thì 179×768 phép nhân là vài
        mili‑giây — đắt hơn nhiều là lượt gọi model 5–22s ngay sau đó.

        Cái giá đã biết: mỗi câu hỏi toàn cục kéo thêm ~550KB vector từ Postgres (179 tin ×
        768 × 4 byte). Chấp nhận được ở quy mô này và vẫn nhỏ so với 5–22s chờ model; khi
        corpus tới hàng chục nghìn tin thì đây mới là lúc đẩy phần lọc thô xuống index HNSW
        đã dựng sẵn ở migration 012, và khi đó phải nghĩ lại cách RS harness đo.
        """
        if query_vector is None:
            return [None] * len(insights)

        indexed = [(idx, i) for idx, i in enumerate(insights) if i.embedding is not None]
        if not indexed:
            return [None] * len(insights)

        similarities = [_cosine(query_vector, i.embedding) for _, i in indexed]
        ranks = _competition_ranks(similarities)
        out: list[int | None] = [None] * len(insights)
        for (idx, _), rank in zip(indexed, ranks):
            out[idx] = rank
        return out

    async def _chunk_ranks(self, query_vector: list[float] | None) -> dict[uuid.UUID, int]:
        """Thứ hạng đoạn khớp tốt nhất mỗi insight. `{}` = không có tín hiệu đoạn lượt này.

        **Suy giảm êm là bất biến, không phải nỗ lực** (cùng luật với tầng vector): truy vấn
        lỗi → `{}` → `_rank` bỏ hẳn số hạng thứ ba → thứ tự **trùng khít** bản hai tín hiệu.
        Chat không bao giờ 500 vì bảng đoạn.

        """
        if query_vector is None or not settings.chat_embedding_enabled:
            return {}
        try:
            ranks = await self.chunk_repo.retrieve_chunk_ranks(query_vector)
            if not ranks:
                # Bảng đoạn RỖNG trong khi mọi điều kiện đều bật = chưa backfill, hoặc vừa
                # `alembic downgrade` (DROP TABLE xoá sạch dữ liệu rồi upgrade dựng lại bảng
                # trống). Không có dòng này thì hệ thống chỉ **âm thầm** tụt về hai tín hiệu:
                # chat vẫn trả lời trôi chảy, không lỗi nào bắn ra, và người vận hành không
                # có cách nào biết mình đang chạy một pipeline kém hơn.
                logger.warning(
                    "Không có thứ hạng đoạn nào — bảng `document_chunks` rỗng? "
                    "Chạy `python -m app.scripts.chunk_documents`. Xếp hạng đang chạy bằng "
                    "2 tín hiệu thay vì 3."
                )
            return ranks
        except Exception as e:
            # WARNING chứ không ERROR: pipeline vẫn trả lời đúng, chỉ kém một tín hiệu. Nhưng
            # phải để lại dấu vết — một sự cố kéo dài ở đây trông y hệt "chat hơi kém".
            logger.warning("Truy hồi mức đoạn lỗi — xếp hạng bằng 2 tín hiệu: %s", e)
            return {}

    async def _embed_question(self, question: str) -> list[float] | None:
        """Embedding của câu hỏi cho tầng vector. `None` = xếp hạng bằng lexical thôi.

        Không bao giờ ném lỗi ra ngoài: embedding là phụ trợ xếp hạng, không phải đường
        sống của chat (design D6). Vertex embedding sự cố thì câu trả lời chỉ kém ngữ
        nghĩa hơn tạm thời — đổi lấy một HTTP 500 là đổi sai.

        Lượt gọi này KHÔNG cộng vào `self._calls_used`: bộ đếm đó canh budget lượt sinh văn
        bản đắt (`max_daily_chat_calls`). Xem `GeminiClient.embed`.
        """
        if not settings.chat_embedding_enabled:
            return None
        # Câu rỗng từ khoá sẽ bị `_rank` bỏ tầng vector (xem cổng ở đó). Gọi embed rồi vứt kết
        # quả là tiêu ~1,4s chờ mạng cho một thứ chắc chắn không dùng tới — bỏ HẲN lượt gọi.
        #
        # ⚠️ Cổng này CỐ Ý có ở cả hai nơi. Ở đây nó tiết kiệm thời gian; ở `_rank` nó là phần
        # của phép xếp hạng và phải giữ, vì RS harness gọi thẳng `_rank` với vector đông lạnh
        # sẵn cho MỌI kịch bản — bỏ cổng bên đó là để nhiễu quay lại đúng ca `rank-generic`.
        if not _question_terms(question):
            logger.debug("Câu rỗng từ khoá — bỏ lượt embed, xếp hạng theo độ quan trọng")
            return None
        try:
            return await asyncio.to_thread(
                self.gemini.embed_one, question, EMBED_TASK_QUERY
            )
        except Exception as e:
            # `GeminiClient.embed` đã tự nuốt lỗi Vertex, nên tới đây là những thứ nó không
            # lường: client không có hàm `embed_one` (fake trong test cũ), lỗi lập trình,
            # timeout ở tầng thread. Vẫn không được để nổ ra ngoài — lý do y hệt.
            logger.warning("Embed câu hỏi lỗi, xếp hạng bằng lexical: %s", e)
            return None

    async def _call_model(
        self, prompt: str, hold_sentinel: bool = False, status: str | None = None
    ) -> str:
        """Gọi Gemini NGOÀI event loop — chat nằm trên request path (design D6).

        Cộng vào `self._calls_used` NGAY khi model trả về, trước khi caller làm bất cứ
        việc gì khác: đó là thời điểm tiền đã tiêu, và mọi lỗi sau đó vẫn phải tính.

        Có `self._emit` thì đi lối streaming — vẫn ĐÚNG MỘT bước, vẫn cùng prompt, vẫn trả
        về toàn văn cho phần grounding phía sau chạy y như cũ.
        """
        await self._status(status or STATUS_COMPOSING)
        if self._steps_used >= MAX_MODEL_CALLS_PER_QUESTION:
            raise RuntimeError(
                f"Chạm trần {MAX_MODEL_CALLS_PER_QUESTION} bước trả lời cho một câu hỏi"
            )
        self._steps_used += 1

        if self._emit is not None:
            return await self._stream_model(prompt, hold_sentinel=hold_sentinel)

        # `state` là sổ ghi dùng chung với lối streaming — nhờ nó số token suy luận đọc được
        # ở CẢ hai lối ra, không phải chỉ ở lối stream.
        state = ChatStreamState()
        text, calls = await asyncio.to_thread(
            self.gemini.chat, CHAT_SYSTEM_PROMPT, prompt, state
        )
        # `calls` có thể là 2 nếu lượt đầu bị cắt và client đã hỏi lại — vẫn tốn tiền thật
        # nên vẫn phải cộng vào budget, chỉ là KHÔNG tính như một bước mới.
        self._calls_used += calls
        self._add_thinking(state.thinking_tokens)
        return text

    def _add_thinking(self, tokens: int | None) -> None:
        """Cộng dồn token suy luận qua các bước. Giữ `None` nếu chưa từng đo được số nào."""
        if tokens is None:
            return
        self._thinking_tokens = (self._thinking_tokens or 0) + tokens

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
            self._add_thinking(state.thinking_tokens)
        return state.text

    async def answer_stream(
        self,
        question: str,
        history: list,
        insight_id: uuid.UUID | None,
        referenced_insight_ids: list[uuid.UUID] | None = None,
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
                result = await self.answer(
                    question, history, insight_id, emit=emit,
                    referenced_insight_ids=referenced_insight_ids,
                )
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
