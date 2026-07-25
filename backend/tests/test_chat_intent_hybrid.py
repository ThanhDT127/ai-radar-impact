"""Bộ lọc ý định HAI TẦNG — luật tất định + `gemini-2.5-flash-lite` (25/07/2026).

Bất biến khoá ở đây là **tầng 2 phải hiếm**. Đo trên 84 ca nhãn tay: sàn round‑trip của
model lite là 1.433–1.685 ms kể cả với prompt rỗng và 1 token output, nên mỗi lần chạm
tầng 2 là cộng thẳng ~1,5s vào thời gian người dùng chờ. Luật quyết 96,4% số câu ở 6µs;
chỉ ca luật TỰ NHẬN lưỡng lự mới được phép gọi model. Test nào nới điều đó ra sẽ âm thầm
biến chat thành chậm hơn 1,5s cho mọi câu.

Đo được với bộ lai: precision 100%, recall 97,7%, 3,6% câu chạm tầng 2.
"""

import uuid

import pytest

from app.ai.gemini_client import INTENT_LABELS, GeminiClient
from app.services.chat_intent import AMBIGUOUS, INTENT_PRESETS, route_intent
from app.services.chat_service import ChatService


# --- Tầng 1: ba trạng thái ------------------------------------------------------

@pytest.mark.parametrize(
    "question,expected",
    [
        # Chắc chắn preset — không được đụng tới model.
        ("xin chào", "salutation"),
        ("cảm ơn nhé", "thanks"),
        ("bạn làm được gì", "capability"),
        ("bạn hoạt động thế nào", "capability"),
        ("khả năng của bạn", "capability"),
        ("trợ lý này làm được gì", "capability"),
        # Chắc chắn câu thật — cũng không được đụng tới model.
        ("tuần này có gì cho Security", None),
        ("OpenSSL là gì", None),
        ("chào, tuần này có gì cho Security", None),
        ("cảm ơn vì tin về mã nguồn mở", None),
        ("API mới của OpenAI dùng để làm gì", None),
        ("giới thiệu về mô hình Qwen", None),
    ],
)
def test_luat_tu_quyet_khong_can_model(question, expected):
    assert route_intent(question) == expected


@pytest.mark.parametrize(
    "question",
    [
        "nó là ai",
        "nó hoạt động thế nào",
        "công cụ này hỗ trợ gì",
        "thư viện này có chức năng gì",
        "mô hình này có khả năng gì",
        "nó giúp được gì cho mình",
        "cái này giúp gì cho team",
    ],
)
def test_dai_tu_hoi_chi_khong_kem_tu_quy_chieu_la_cau_that(question):
    """Luật hồi chỉ — gỡ đúng ca mà cả matching cũ LẪN flash-lite đều sai.

    "nó"/"này" trỏ về bài đang xem, nên dù câu dùng đúng chữ của cụm năng lực
    ("là ai", "hoạt động thế nào") thì nó vẫn đang hỏi về thứ trong bài. Đo 25/07/2026:
    flash-lite trả `capability` cho "nó là ai" NGAY CẢ KHI prompt nêu thẳng ca đó là Q —
    nên chỗ này phải là luật, không được nhường cho model.
    """
    assert route_intent(question) is None


@pytest.mark.parametrize("question", ["giới thiệu đi", "để làm gì", "bot này dùng để làm gì"])
def test_ca_luong_lu_duoc_danh_dau_de_nhuong_model(question):
    """Thiếu chủ ngữ, hoặc tự quy chiếu nhưng còn token lạ → luật không đoán bừa."""
    assert route_intent(question) == AMBIGUOUS


def test_ti_le_luong_lu_phai_hiem():
    """Cổng chặn hồi quy: mỗi ca lưỡng lự tốn ~1,5s. Giữ dưới 10% tập nhãn tay."""
    questions = [
        "xin chào", "chào bạn", "hello", "hi bạn", "cảm ơn", "cảm ơn nhé", "thanks",
        "thank you", "bạn làm được gì", "bạn là ai", "bạn giúp được gì", "khả năng của bạn",
        "bạn có chức năng gì", "bạn hoạt động thế nào", "bạn biết làm gì", "bot có khả năng gì",
        "tuần này có gì cho Security", "OpenSSL là gì", "có tin gì mới về IoT không",
        "tóm tắt các tin bảo mật hôm nay", "rủi ro của nó là gì", "bài này nói gì",
        "so sánh hai tin này", "nó là ai", "công cụ này hỗ trợ gì", "Llama là gì",
        "chức năng mới của Chrome là gì", "thư viện này hoạt động thế nào",
        "cho tôi 3 tin quan trọng nhất", "giới thiệu đi",
    ]
    ambiguous = [q for q in questions if route_intent(q) == AMBIGUOUS]
    ratio = len(ambiguous) / len(questions)
    assert ratio <= 0.10, f"chạm tầng 2 {ratio:.0%} — quá nhiều, xem lại: {ambiguous}"


# --- Tầng 2: gọi model nhẹ ------------------------------------------------------

class _FakeModels:
    def __init__(self, text="Q", raises=None):
        self.text = text
        self.raises = raises
        self.calls = []

    def generate_content(self, model, contents, config):
        self.calls.append((model, contents, config))
        if self.raises:
            raise self.raises
        return type("_R", (), {"text": self.text})()


def _client(text="Q", raises=None) -> tuple[GeminiClient, _FakeModels]:
    client = GeminiClient.__new__(GeminiClient)
    models = _FakeModels(text, raises)
    client._client = type("_C", (), {"models": models})()
    return client, models


@pytest.mark.parametrize("label,expected", list(INTENT_LABELS.items()))
def test_nhan_mot_ky_tu_duoc_anh_xa_dung(label, expected):
    client, _ = _client(text=label)
    assert client.classify_intent("giới thiệu đi") == expected


def test_nhan_la_thi_roi_ve_pipeline():
    client, _ = _client(text="BLAH")
    assert client.classify_intent("giới thiệu đi") is None


def test_model_loi_thi_roi_ve_pipeline_khong_nem_loi():
    """Fail‑safe: phân loại hỏng chỉ được làm câu chào tốn thêm 1 lượt, không làm vỡ chat."""
    client, _ = _client(raises=RuntimeError("Vertex 503"))
    assert client.classify_intent("giới thiệu đi") is None


def test_cau_hinh_goi_toi_uu_cho_do_tre():
    """Nhãn 1 ký tự + trần 4 token + temperature 0 — độ trễ ở đây là TTFT."""
    client, models = _client()
    client.classify_intent("để làm gì")

    model, contents, config = models.calls[0]
    assert "lite" in model, "phải dùng model nhẹ, không dùng model trả lời"
    assert contents == "để làm gì"
    assert config.max_output_tokens <= 4
    assert config.temperature == 0.0


# --- Nối hai tầng trong service -------------------------------------------------

class _SpyGemini:
    """Đếm xem tầng 2 có bị gọi không."""

    def __init__(self, intent=None):
        self.intent = intent
        self.classify_calls: list[str] = []
        self.chat_calls = 0

    def classify_intent(self, question):
        self.classify_calls.append(question)
        return self.intent

    def chat(self, system_prompt, user_prompt):
        self.chat_calls += 1
        return "Trả lời [1].", 1


class _FakeSession:
    def __init__(self, results=()):
        self._results = list(results)
        self.added = []

    async def execute(self, statement, *a, **kw):
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        pass


@pytest.mark.asyncio
@pytest.mark.parametrize("question", ["xin chào", "bạn làm được gì", "nó là ai", "OpenSSL là gì"])
async def test_luat_chac_chan_thi_KHONG_goi_model_nhe(question):
    """Đây là bất biến đắt nhất: gọi thừa tầng 2 = +1,5s cho câu vốn đã miễn phí."""
    gemini = _SpyGemini()
    service = ChatService(_FakeSession(), gemini=gemini)

    await service._route_intent(question)

    assert gemini.classify_calls == [], f"{question!r} phải do luật quyết, không gọi model"


@pytest.mark.asyncio
async def test_ca_luong_lu_thi_goi_model_nhe_va_dung_ket_qua():
    gemini = _SpyGemini(intent="capability")
    service = ChatService(_FakeSession(), gemini=gemini)

    assert await service._route_intent("bot này dùng để làm gì") == "capability"
    assert gemini.classify_calls == ["bot này dùng để làm gì"]


@pytest.mark.asyncio
async def test_model_nhe_bao_cau_that_thi_di_pipeline():
    gemini = _SpyGemini(intent=None)
    service = ChatService(_FakeSession(), gemini=gemini)

    assert await service._route_intent("để làm gì") is None


@pytest.mark.asyncio
async def test_tat_tang_2_thi_luong_lu_roi_ve_pipeline(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "intent_classifier_enabled", False)
    gemini = _SpyGemini(intent="capability")
    service = ChatService(_FakeSession(), gemini=gemini)

    assert await service._route_intent("giới thiệu đi") is None
    assert gemini.classify_calls == []


@pytest.mark.asyncio
async def test_preset_qua_tang_2_van_ghi_model_calls_0():
    """Lượt phân loại KHÔNG tính vào `model_calls` — nó canh budget của lượt trả lời đắt.

    Một lần phân loại là ~259 token vào + 1 token ra trên model rẻ hơn một bậc (≈$0,026
    cho 1000 câu); trộn nó vào bộ đếm `MAX_DAILY_CHAT_CALLS` sẽ để các lượt gọi rẻ bào
    mòn budget đắt — đúng cái bẫy "đơn vị budget khác nhau" đã ghi trong CLAUDE.md.
    """
    gemini = _SpyGemini(intent="capability")
    service = ChatService(_FakeSession(), gemini=gemini)

    result = await service.answer("bot này dùng để làm gì", [], None)

    assert result["mode"] == "meta"
    assert result["answer"] == INTENT_PRESETS["capability"]
    assert result["citations"] == []
    assert gemini.chat_calls == 0, "fast‑path không được gọi model trả lời"
    assert service.session.added[0].model_calls == 0


@pytest.mark.asyncio
async def test_fastpath_qua_tang_2_van_ap_dung_khi_dang_mo_mot_bai():
    gemini = _SpyGemini(intent="capability")
    session = _FakeSession([object()])  # nếu lỡ nạp bài gốc thì hàng đợi này bị rút
    service = ChatService(session, gemini=gemini)

    result = await service.answer("bot này dùng để làm gì", [], uuid.uuid4())

    assert result["mode"] == "meta"
    assert len(session._results) == 1, "không được nạp bài gốc"
