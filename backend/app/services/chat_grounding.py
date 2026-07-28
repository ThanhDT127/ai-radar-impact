"""Grounding cho chat: đánh số candidate, dựng index, giải marker [n] thành citation.

Cốt lõi của design D4 — **server cấp phát định danh, model chỉ đánh dấu**:

    server  ──▶  [1] Anthropic ra MCP…      (prompt KHÔNG chứa UUID)
                 [2] EU AI Act giai đoạn 2…
    model   ──▶  "…MCP đang thành chuẩn [1]."   (text thuần)
    server  ──▶  tra bảng n → insight_id  ──▶  citations đầy đủ

Model không bao giờ nhìn thấy UUID nên không có gì để bịa. Đây là lý do chống bịa
citation ở đây là *cấu trúc*, không phải hậu kiểm lọc id lạ.
"""

import logging
import re
import uuid
from dataclasses import dataclass

from app.ai.prompts import OUT_OF_SCOPE_SENTINEL
from app.models.insight import Insight

logger = logging.getLogger(__name__)

# Marker dạng [1], [12] — không khớp [abc] hay [1.5].
_MARKER_RE = re.compile(r"\[(\d+)\]")

# Câu trả lời "không tìm thấy" hợp lệ thì không cần citation (design D4). Nhận diện
# bằng cụm từ vì prompt đã yêu cầu model dùng đúng câu này.
_NOT_FOUND_MARKERS = (
    "không tìm thấy",
    "không có thông tin",
    "chưa có tin nào",
    "không đủ dữ liệu",
)

INSUFFICIENT_GROUNDS_MESSAGE = (
    "Tôi không đủ căn cứ trong hệ thống để trả lời câu hỏi này. "
    "Bạn thử hỏi cụ thể hơn, hoặc xem trực tiếp trên dashboard nhé."
)


def _fmt_date(insight: Insight) -> str:
    when = insight.published_at or insight.created_at
    return when.strftime("%d/%m/%Y") if when else "không rõ ngày"


def build_index_block(
    insights: list[Insight], start: int = 1
) -> tuple[str, dict[int, Insight]]:
    """Dựng index nén đã đánh số + bảng ánh xạ `n → Insight`.

    Một dòng ≈ 108 token (đo trên corpus 22/07/2026: title 60 + signal 144 ký tự).
    KHÔNG đưa UUID vào chuỗi trả về — đó là toàn bộ điểm của D4.

    `start` cho phép chế độ mở rộng (`chat-scope-routing`) dành [1] cho bài đang xem rồi
    đánh số tin toàn cục từ [2]. Một dãy số liên tục qua cả hai khối context ⇒ vẫn đúng
    MỘT bảng ánh xạ, không phải hai không gian số chồng nhau.
    """
    lines: list[str] = []
    mapping: dict[int, Insight] = {}

    for n, insight in enumerate(insights, start=start):
        mapping[n] = insight
        roles = ", ".join(insight.affected_roles or []) or "—"
        topics = ", ".join(insight.topics or []) or "—"
        signal = (insight.signal or insight.summary_short or "").strip()
        lines.append(
            f"[{n}] {insight.title}\n"
            f"    Ý nghĩa: {signal}\n"
            f"    Vai trò: {roles} | Chủ đề: {topics} | Ngày: {_fmt_date(insight)}"
        )

    return "\n".join(lines), mapping


def build_insight_block(insight: Insight, content: str | None, n: int = 1) -> str:
    """Một Ô SÂU: đủ 7 field phân tích + bài gốc, đánh số `[n]`.

    `n` mặc định 1 vì chế độ per-insight cũ chỉ có đúng một nguồn. `build_context`
    (chat-context-depth) truyền 1..k để xếp nhiều ô sâu cạnh nhau — trước đây số `[1]` bị
    chốt cứng trong chuỗi, nên hai ô sâu sẽ mang cùng một số và bảng ánh xạ mất một tin.
    """
    parts = [f"[{n}] {insight.title}"]

    def add(label: str, value) -> None:
        if value:
            parts.append(f"    {label}: {value}")

    add("Ý nghĩa", insight.signal)
    add("Vì sao quan trọng", insight.why_it_matters)
    add("So what", insight.so_what)
    add("Tóm tắt", insight.summary_medium)
    add("Vai trò ảnh hưởng", ", ".join(insight.affected_roles or []))
    add("Chủ đề", ", ".join(insight.topics or []))
    add("Rủi ro", "; ".join(insight.risks or []))

    if insight.recommendations:
        recs = []
        for role, entry in insight.recommendations.items():
            if isinstance(entry, dict):
                note = entry.get("note", "")
                action = entry.get("action_type", "")
                recs.append(f"{role} ({action}): {note}")
        add("Khuyến nghị", " | ".join(recs))

    add("Ngày", _fmt_date(insight))

    if content:
        parts.append(f"\n    NỘI DUNG BÀI GỐC:\n{content}")
    else:
        # Tombstone-purge xoá normalized_content sau retention_months nhưng giữ insight.
        parts.append(
            "\n    (Bài gốc đã hết hạn lưu trữ — chỉ còn phần phân tích ở trên. "
            "Nếu câu hỏi cần chi tiết trong bài gốc, hãy nói rõ là không còn dữ liệu.)"
        )

    return "\n".join(parts)


@dataclass
class ChatContext:
    """Context của một lượt trả lời: vài Ô SÂU + phần index nén, MỘT bảng ánh xạ.

    `deep_block` và `index_block` tách nhau vì prompt phải đặt chúng dưới hai tiêu đề khác
    nhau, nhưng chúng dùng **một dãy số liên tục** và **một `mapping`** — đó là toàn bộ
    điểm của D4: model chỉ thấy số, server giữ bảng.
    """

    deep_block: str
    index_block: str
    mapping: dict[int, Insight]
    deep_count: int
    total_matched: int
    hidden: int
    # Block của TỪNG ô sâu, theo số thứ tự. `deep_block` là các block này ghép lại; giữ
    # riêng vì phần dựng lại context (bộ đo Faithfulness) cần biết mỗi tin được phục vụ ở
    # độ sâu nào. Tách chuỗi `deep_block` ra lại thì không đáng tin — raw content có dòng
    # trống, và một bộ đo chấm sai độ sâu sẽ báo hồi quy giả (đo 28/07: Faith 0,99 → 0,78,
    # toàn bộ là do judge nhìn dòng index nén trong khi model đọc bài gốc).
    deep_blocks: dict[int, str]


def build_context(
    refs: list[Insight],
    ranked: list[Insight],
    k_deep: int,
    index_limit: int,
    include_content: bool = True,
) -> ChatContext:
    """Dựng context: ô sâu lấp TẤT ĐỊNH (refs trước, xếp hạng sau), rồi index nén.

    Đây là **hàm thuần** (design D1) — không DB, không model, không đọc `settings`. Nhờ vậy
    RS harness đo được offline và miễn phí, y như `_rank`.

    Lấp ô sâu **không** hỏi ý định câu hỏi. Mọi heuristic phân loại câu hỏi ở repo này đều
    đã trả giá (`_roles_in_question` khớp chuỗi con, `_CAPABILITY_PHRASES` code chết), nên
    luật ở đây chỉ có một dòng: refs trước, còn chỗ thì lấp bằng đầu danh sách đã xếp hạng.

    Hệ quả có chủ đích: câu toàn cục **không có ref nào** vẫn được 3 bài sâu nhất. Đó chính
    là phần chữa "từ chối sai 4/5 câu hỏi chi tiết" — không cần người dùng bấm gì.

    `index_limit` là TỔNG số tin vào prompt (ô sâu tính trong đó), để ngân sách token không
    phình lên khi thêm ô sâu: 60 tin vẫn là 60 tin, chỉ khác 3 trong số đó được rót sâu.
    """
    # Ô sâu KHÔNG được vượt trần tổng: `index_limit` đếm cả ô sâu, nên `k_deep=3` với
    # `index_limit=1` phải cho đúng 1 tin, không phải 3. Bỏ dòng này thì trần top-K trở
    # thành lời nói suông đúng ở cấu hình chặt nhất — nơi nó quan trọng nhất.
    room_total = k_deep if index_limit <= 0 else min(k_deep, index_limit)

    deep: list[Insight] = []
    seen: set = set()

    def take(insight: Insight) -> None:
        if insight.id in seen or len(deep) >= room_total:
            return
        seen.add(insight.id)
        deep.append(insight)

    for insight in refs:
        take(insight)
    for insight in ranked:
        take(insight)

    # Tin đã vào ô sâu phải BIẾN MẤT khỏi index — không thì cùng một tin mang hai số và
    # citation trỏ trùng (đúng lỗi mà `build_index_block(start=2)` của scope-routing tránh).
    rest = [i for i in ranked if i.id not in seen]
    room = max(index_limit - len(deep), 0) if index_limit > 0 else len(rest)
    candidates = rest[:room]

    deep_blocks = {
        n: build_insight_block(
            insight,
            _deep_content(insight) if include_content else None,
            n=n,
        )
        for n, insight in enumerate(deep, start=1)
    }
    index_block, mapping = build_index_block(candidates, start=len(deep) + 1)
    for n, insight in enumerate(deep, start=1):
        mapping[n] = insight

    # Tin bị cắt = phần đuôi của `ranked` không được rót ở bất kỳ độ sâu nào. Refs đến từ
    # ngoài `ranked` (ví dụ ngoài cửa sổ thời gian) không tính vào đây.
    surfaced = sum(1 for i in ranked if i.id in seen) + len(candidates)
    return ChatContext(
        deep_block="\n\n".join(deep_blocks[n] for n in sorted(deep_blocks)),
        deep_blocks=deep_blocks,
        index_block=index_block,
        mapping=mapping,
        deep_count=len(deep),
        total_matched=len(ranked),
        hidden=max(len(ranked) - surfaced, 0),
    )


def _deep_content(insight: Insight) -> str | None:
    """`normalized_content` của bài gốc, hoặc `None` nếu đã bị tombstone-purge."""
    raw_doc = getattr(insight, "raw_document", None)
    content = (raw_doc.normalized_content or "").strip() if raw_doc else ""
    return content or None


def resolve_citations(
    answer: str, mapping: dict[int, Insight]
) -> tuple[str, list[dict]]:
    """Giải marker [n] → citations; bỏ marker ngoài phạm vi, GIỮ nội dung answer.

    Trả `(answer_đã_dọn, citations)`. Citations giữ thứ tự xuất hiện, không trùng lặp.
    """
    seen: list[int] = []
    for raw in _MARKER_RE.findall(answer):
        n = int(raw)
        if n in mapping and n not in seen:
            seen.append(n)

    cleaned = _MARKER_RE.sub(
        lambda m: m.group(0) if int(m.group(1)) in mapping else "", answer
    )
    # Bỏ marker có thể để lại khoảng trắng thừa trước dấu câu.
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()

    # `n` đi kèm citation, và marker trong answer GIỮ NGUYÊN — không đánh số lại (design D2).
    # Đánh số lại nghe gọn hơn nhưng là *viết lại* nội dung model trả về (hiện chỉ *xoá* marker
    # ngoài phạm vi), và sẽ đá nhau khi câu trả lời tự nhắc "tin số 3 ở trên".
    citations = [
        {
            "n": n,
            "insight_id": mapping[n].id,
            "title": mapping[n].title,
            "source_url": mapping[n].source_url,
        }
        for n in seen
    ]

    # Marker không liền mạch từ 1 nghĩa là model bỏ qua tin ở giữa index — tín hiệu sớm cho
    # việc xếp hạng đặt tin không hợp vào top. Mức DEBUG chứ KHÔNG phải WARNING: sau khi `n`
    # thành dữ liệu thì nhảy cóc không còn gây hỏng, nên đây là quan sát, không phải lỗi.
    if seen and seen != list(range(1, len(seen) + 1)):
        logger.debug("Marker không liền mạch từ 1: %s (index %d tin)", seen, len(mapping))

    return cleaned, citations


def is_out_of_scope_answer(raw_answer: str) -> bool:
    """Lượt gọi chế độ B có phát sentinel ngoài‑phạm‑vi không? (design D3)

    Đọc trên văn bản **thô**, TRƯỚC `resolve_citations`/`enforce_grounding` — sentinel
    không có marker `[n]` nào nên nếu để grounding chạy trước thì nó bị thay bằng
    `INSUFFICIENT_GROUNDS_MESSAGE` và tín hiệu biến mất.

    Nhận diện CHẶT theo đúng bias dè dặt: chỉ khi sentinel là **toàn bộ** câu trả lời.
    Model vừa trả lời vừa kèm sentinel nghĩa là nó trả lời được → không mở rộng, vì mở
    nhầm tốn gấp đôi lượt gọi và độ trễ. Chỉ nới đúng phần rác định dạng model hay thêm
    (dấu nháy ngược, khoảng trắng).
    """
    stripped = raw_answer.strip().strip("`").strip()
    return stripped == OUT_OF_SCOPE_SENTINEL


def is_not_found_answer(answer: str) -> bool:
    """Câu trả lời thuộc dạng 'không tìm thấy' — được phép không có citation."""
    lowered = answer.lower()
    return any(marker in lowered for marker in _NOT_FOUND_MARKERS)


def enforce_grounding(answer: str, citations: list[dict]) -> tuple[str, list[dict]]:
    """Fail-closed: khẳng định mà không có marker nào → thay bằng thông báo.

    Ngược chiều với gate analysis (fail-open): ở đó mất bài còn cứu được ở lần crawl
    sau, còn chat trả lời sai thì người dùng mang đi quyết định.
    """
    if citations:
        return answer, citations
    if is_not_found_answer(answer):
        return answer, []
    return INSUFFICIENT_GROUNDS_MESSAGE, []
