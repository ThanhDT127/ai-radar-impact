"""Auto-fallback từ scope bài sang scope mở rộng — change `chat-scope-routing`.

Bất biến khoá:
- Chế độ B bí (model phát sentinel) SHALL mở rộng sang toàn hệ thống, KHÔNG trả lời cụt
  và KHÔNG bao giờ để sentinel lọt ra cho người dùng.
- Mở rộng dùng ĐÚNG 2 BƯỚC trả lời; câu trong phạm vi bài dùng đúng 1. (Một bước có thể
  tốn 2 lượt tính tiền khi câu trả lời bị cắt và phải hỏi lại — xem nhóm test cuối file.)
- Tín hiệu ngoài-phạm-vi là byproduct của lượt trả lời B — KHÔNG có lượt gọi phân loại riêng.
- Sentinel phát DÈ DẶT: model vừa trả lời vừa kèm sentinel = trả lời được → không mở rộng
  (mở nhầm tốn gấp đôi lượt gọi và độ trễ; thiếu mở rộng thì người dùng còn badge tay).
"""

import uuid
from datetime import datetime

import pytest

from app.ai.prompts import OUT_OF_SCOPE_SENTINEL, build_chat_insight_prompt
from app.services.chat_grounding import (
    INSUFFICIENT_GROUNDS_MESSAGE,
    is_out_of_scope_answer,
)
from app.services.chat_service import MAX_MODEL_CALLS_PER_QUESTION, ChatService


class _FakeSource:
    name = "Test Source"


class _FakeRawDoc:
    normalized_content = "Nội dung bài gốc nói về lỗ hổng OpenSSL."
    source = _FakeSource()


class _FakeInsight:
    def __init__(self, title="Tin đang xem"):
        self.id = uuid.uuid4()
        self.title = title
        self.signal = f"Ý nghĩa của {title}"
        self.so_what = "Nên vá ngay"
        self.why_it_matters = "Ảnh hưởng hệ thống nội bộ"
        self.summary_short = "ngắn"
        self.summary_medium = "vừa"
        self.affected_roles = ["Security"]
        self.topics = ["Security & Compliance"]
        self.risks = []
        self.recommendations = {
            "Security": {"action_type": "read", "note": "n", "urgency": "high"}
        }
        self.source_url = f"https://example.com/{title}"
        self.published_at = datetime(2026, 7, 20, 10, 0)
        self.created_at = datetime(2026, 7, 21, 10, 0)
        self.impact_label = "Cao"
        self.actionability_score = 0.5
        self.intelligence_tier = "Tactical"
        self.trust_score = 0.8
        self.practical_indicators = None
        self.raw_document = _FakeRawDoc()


class _Result:
    def __init__(self, value):
        self._value = value

    def scalar_one(self):
        return self._value

    def scalar_one_or_none(self):
        return self._value


class _FakeSession:
    def __init__(self, results):
        self._results = list(results)
        self.added = []

    async def execute(self, statement, *a, **kw):
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass


class _ScriptedGemini:
    """Trả lần lượt các câu đã kịch bản hoá; đếm số lượt gọi thật."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.prompts: list[str] = []

    def chat(self, system_prompt, user_prompt, state=None):
        self.prompts.append(user_prompt)
        return self.answers.pop(0), 1

    def classify_intent(self, question):  # tầng 2 của intent router — không dùng ở đây
        return None


def _service(insight, global_pool, gemini):
    session = _FakeSession([_Result(0), _Result(insight)])  # quota, nạp bài
    service = ChatService(session, gemini=gemini)

    async def fake_list_for_chat(**kw):
        return list(global_pool)

    service.insight_repo.list_for_chat = fake_list_for_chat
    return service, session


# --- Bộ dò sentinel (task 1.2) --------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        (OUT_OF_SCOPE_SENTINEL, True),
        (f"  {OUT_OF_SCOPE_SENTINEL}  ", True),
        (f"`{OUT_OF_SCOPE_SENTINEL}`", True),
        ("Bài này nói về OpenSSL [1].", False),
        ("", False),
        # DÈ DẶT: trả lời được rồi mới kèm sentinel → coi như trả lời được.
        (f"Bài này có nói qua [1]. {OUT_OF_SCOPE_SENTINEL}", False),
    ],
)
def test_nhan_dien_sentinel(raw, expected):
    assert is_out_of_scope_answer(raw) is expected


def test_luat_pham_vi_nam_trong_prompt_mode_B():
    prompt = build_chat_insight_prompt("[1] Bài", "", "câu hỏi")
    assert OUT_OF_SCOPE_SENTINEL in prompt
    assert "DÙ CHỈ MỘT PHẦN" in prompt, "phải nêu rõ điều kiện KHÔNG phát sentinel"


# --- Câu trong phạm vi bài: không mở rộng (task 2.3, 4.1) -----------------------

@pytest.mark.asyncio
async def test_cau_trong_pham_vi_dung_dung_1_luot():
    gemini = _ScriptedGemini("Bài này nói lỗ hổng đã có bản vá [1].")
    insight = _FakeInsight()
    service, session = _service(insight, [], gemini)

    result = await service.answer("bài này nói gì", [], insight.id)

    assert result["mode"] == "insight"
    assert len(gemini.prompts) == 1, "câu in-scope KHÔNG được sinh lượt gọi thứ hai"
    assert session.added[0].model_calls == 1
    assert len(result["citations"]) == 1


# --- Câu ngoài phạm vi: mở rộng (task 2.1, 2.2, 2.3) ---------------------------

@pytest.mark.asyncio
async def test_sentinel_kich_hoat_mo_rong_va_tra_loi_tu_tin_khac():
    other = _FakeInsight("Tin Kubernetes")
    gemini = _ScriptedGemini(
        OUT_OF_SCOPE_SENTINEL,
        "Bài bạn đang xem không nhắc tới điều này; tìm toàn hệ thống thấy [2].",
    )
    insight = _FakeInsight()
    service, session = _service(insight, [other], gemini)

    result = await service.answer("có tin gì về Kubernetes", [], insight.id)

    assert result["mode"] == "expanded"
    assert len(gemini.prompts) == 2, "mở rộng dùng đúng 2 lượt"
    assert session.added[0].model_calls == 2
    assert OUT_OF_SCOPE_SENTINEL not in result["answer"], "sentinel không được lộ ra ngoài"
    assert [c["insight_id"] for c in result["citations"]] == [other.id]


@pytest.mark.asyncio
async def test_context_mo_rong_mang_ca_bai_dang_xem_lan_index_toan_cuc():
    """Design D4 — lượt 2 phải so sánh chéo được, nên giữ cả bài B."""
    other = _FakeInsight("Tin Kubernetes")
    gemini = _ScriptedGemini(OUT_OF_SCOPE_SENTINEL, "Thấy [2].")
    insight = _FakeInsight("Tin OpenSSL")
    service, _ = _service(insight, [other], gemini)

    await service.answer("có tin gì về Kubernetes", [], insight.id)

    expanded = gemini.prompts[1]
    assert "Tin OpenSSL" in expanded, "bài đang xem phải có mặt ở lượt mở rộng"
    assert "Tin Kubernetes" in expanded
    assert "[1] Tin OpenSSL" in expanded, "bài đang xem giữ số [1]"
    assert "[2] Tin Kubernetes" in expanded, "tin toàn cục đánh số từ [2]"


@pytest.mark.asyncio
async def test_bai_dang_xem_khong_bi_lap_lai_trong_index_toan_cuc():
    """Bài B nằm trong cả hai khối sẽ có hai số khác nhau → citation trỏ trùng."""
    insight = _FakeInsight("Tin OpenSSL")
    gemini = _ScriptedGemini(OUT_OF_SCOPE_SENTINEL, "Thấy [1].")
    # Bài đang xem CŨNG nằm trong kho toàn cục — đúng như thực tế.
    service, _ = _service(insight, [insight], gemini)

    await service.answer("hỏi gì đó", [], insight.id)

    expanded = gemini.prompts[1]
    # Khẳng định trên SỐ THỨ TỰ, không đếm chuỗi: title còn nằm trong `signal` của bài
    # nên đếm số lần xuất hiện sẽ bắt nhầm chính nó.
    assert "[1] Tin OpenSSL" in expanded, "bài đang xem giữ [1]"
    assert "[2]" not in expanded, "kho toàn cục chỉ có bài đang xem → index phải rỗng"
    assert "không có tin nào khác" in expanded


@pytest.mark.asyncio
async def test_khong_co_luot_goi_phan_loai_rieng():
    """Tín hiệu ngoài-phạm-vi là byproduct của lượt trả lời B, không phải call thứ ba."""
    other = _FakeInsight("Tin khác")
    gemini = _ScriptedGemini(OUT_OF_SCOPE_SENTINEL, "Thấy [2].")
    insight = _FakeInsight()
    service, _ = _service(insight, [other], gemini)

    await service.answer("câu ngoài phạm vi", [], insight.id)

    assert len(gemini.prompts) == 2, "đúng 2 lượt: trả lời B + trả lời mở rộng"


# --- Mở rộng nhưng toàn hệ thống cũng không có (task 2.4) ----------------------

@pytest.mark.asyncio
async def test_mo_rong_ma_toan_he_thong_cung_khong_co():
    gemini = _ScriptedGemini(
        OUT_OF_SCOPE_SENTINEL,
        "Không tìm thấy thông tin này trong hệ thống.",
    )
    insight = _FakeInsight()
    service, _ = _service(insight, [], gemini)

    result = await service.answer("có tin gì về blockchain", [], insight.id)

    assert result["mode"] == "expanded"
    assert result["citations"] == []
    assert result["answer"].startswith("Không tìm thấy")


@pytest.mark.asyncio
async def test_mo_rong_ma_model_bia_thi_van_fail_closed():
    """Fail-closed giữ nguyên ở lượt 2 — mở rộng không phải cửa hậu để bịa."""
    gemini = _ScriptedGemini(OUT_OF_SCOPE_SENTINEL, "Có, Google vừa ra Gemini 4.")
    insight = _FakeInsight()
    service, _ = _service(insight, [], gemini)

    result = await service.answer("có gì mới", [], insight.id)

    assert result["answer"] == INSUFFICIENT_GROUNDS_MESSAGE
    assert result["citations"] == []


# --- Tương tác với `chat-answer-completeness` (đo 25/07/2026) -------------------
#
# `GeminiClient.chat()` có thể tiêu 2 lượt cho MỘT bước khi câu trả lời bị cắt và phải
# hỏi lại. Trước khi tách "bước" khỏi "lượt tính tiền", hai ca dưới đây hỏng thật:
#   (A) mở rộng + lượt 2 bị cắt → 3 lượt, vượt trần mà spec tuyên bố;
#   (B) lượt B bị cắt → hỏi lại → bản hỏi lại phát sentinel → mở rộng bị trần chặn →
#       RuntimeError thoát ra thành HTTP 500.
# Trần nay áp lên SỐ BƯỚC; budget vẫn đếm lượt thật.


class _CostedGemini:
    """Trả `(text, calls)` theo kịch bản — `calls=2` mô phỏng một bước đã phải hỏi lại."""

    def __init__(self, *pairs):
        self.pairs = list(pairs)
        self.prompts: list[str] = []

    def chat(self, system_prompt, user_prompt, state=None):
        self.prompts.append(user_prompt)
        return self.pairs.pop(0)

    def classify_intent(self, question):
        return None


@pytest.mark.asyncio
async def test_mo_rong_van_chay_khi_luot_hai_bi_cat_va_hoi_lai():
    """Ca (A): 2 bước, bước thứ hai tốn 2 lượt → budget ghi 3, KHÔNG vỡ trần bước."""
    other = _FakeInsight("Tin khác")
    insight = _FakeInsight()
    gemini = _CostedGemini((OUT_OF_SCOPE_SENTINEL, 1), ("Thấy [2].", 2))
    service, session = _service(insight, [other], gemini)

    result = await service.answer("câu ngoài phạm vi", [], insight.id)

    assert result["mode"] == "expanded"
    assert service._steps_used == 2, "đúng 2 BƯỚC trả lời"
    assert session.added[0].model_calls == 3, "budget phải ghi đủ 3 lượt đã tốn tiền"


@pytest.mark.asyncio
async def test_luot_B_bi_cat_roi_phat_sentinel_van_mo_rong_duoc():
    """Ca (B): trần cũ chặn nhầm ở đây và ném RuntimeError ra thành HTTP 500."""
    other = _FakeInsight("Tin khác")
    insight = _FakeInsight()
    gemini = _CostedGemini((OUT_OF_SCOPE_SENTINEL, 2), ("Thấy [2].", 1))
    service, session = _service(insight, [other], gemini)

    result = await service.answer("câu ngoài phạm vi", [], insight.id)

    assert result["mode"] == "expanded", "không được chết vì trần"
    assert [c["insight_id"] for c in result["citations"]] == [other.id]
    assert session.added[0].model_calls == 3


@pytest.mark.asyncio
async def test_tran_buoc_van_chan_buoc_thu_ba():
    """Trần vẫn phải là trần: bước vượt trần bị chặn dù mới tốn ít lượt.

    Đọc trần từ hằng số chứ KHÔNG chép số: nó đã đổi 2 → 3 cho đường tra cứu ngoài
    (`chat-web-fallback`), và một test chép cứng số sẽ đỏ mỗi lần trần đổi mà không nói được
    điều gì về *cơ chế* — thứ nó thật sự canh.
    """
    insight = _FakeInsight()
    service, _ = _service(insight, [], _CostedGemini())
    service._steps_used = MAX_MODEL_CALLS_PER_QUESTION

    with pytest.raises(RuntimeError, match="Chạm trần"):
        await service._call_model("prompt bất kỳ")
