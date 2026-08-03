"""Chat KHÔNG BAO GIỜ trả về câu trả lời dở dang (đổi 25/07/2026).

Cách cũ dán "_(Câu trả lời bị cắt vì quá dài — bạn thử hỏi hẹp hơn nhé.)_" vào cuối đoạn
đứt giữa từ. Đó là trả về một câu trả lời THIẾU VẾ SAU — mà phần thiếu thường là khuyến
nghị/rủi ro, tức phần đáng giá nhất. Nay: cắt → hỏi lại kèm ràng buộc gộp ý cho ngắn gọn
nhưng đủ ý; chỉ khi hỏi lại vẫn cắt mới lùi về ranh giới câu hoàn chỉnh.
"""

import pytest

from app.ai.gemini_client import (
    _CONCISE_RETRY_DIRECTIVE,
    ChatStreamState,
    GeminiClient,
    _trim_to_last_sentence,
)

OLD_MARKER = "bị cắt vì quá dài"


class _FakeCandidate:
    def __init__(self, truncated: bool):
        self.finish_reason = "MAX_TOKENS" if truncated else "STOP"


class _FakeResponse:
    """Giống response thật ở đúng hai thứ `chat()` đọc: `.text` và `.candidates`."""

    def __init__(self, text: str, truncated: bool):
        self.text = text
        self.candidates = [_FakeCandidate(truncated)]


class _FakeModels:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls: list[tuple[str, str]] = []  # (system_instruction, user_prompt)

    def generate_content(self, model, contents, config):
        self.calls.append((config.system_instruction, contents))
        return self._responses.pop(0)


def _client(responses) -> tuple[GeminiClient, _FakeModels]:
    client = GeminiClient.__new__(GeminiClient)  # bỏ qua __init__ (không cần credential)
    models = _FakeModels(responses)
    client._client = type("_C", (), {"models": models})()
    return client, models


# --- Đường sung sướng: không cắt thì không đụng gì -------------------------------

def test_khong_cat_thi_tra_nguyen_van_mot_luot():
    client, models = _client([_FakeResponse("Trả lời trọn vẹn [1].", truncated=False)])

    text, calls = client.chat("SYS", "câu hỏi")

    assert text == "Trả lời trọn vẹn [1]."
    assert calls == 1
    assert len(models.calls) == 1, "không được hỏi lại khi chưa bị cắt"


# --- Mốc `retrying` (change `chat-status-milestones`, task 4.3) ------------------
#
# Lượt hỏi lại là khoảng chờ IM LẶNG đắt nhất của chat: người dùng chờ thêm nguyên một lượt
# gọi model mà màn hình không nói gì. Client phải gọi ngược lên trước khi hỏi lại.

def test_bao_moc_hoi_lai_TRUOC_khi_goi_lai():
    client, models = _client([
        _FakeResponse("Tin thứ nhất nói về lỗ hổng ngh", truncated=True),
        _FakeResponse("Gộp lại cho ngắn.", truncated=False),
    ])
    # Ghi lại SỐ LƯỢT GỌI tại thời điểm được báo — đó là cách duy nhất chứng minh mốc tới
    # *trước* lượt hỏi lại chứ không phải sau nó.
    seen: list[int] = []
    state = ChatStreamState(on_retry=lambda: seen.append(len(models.calls)))

    client.chat("SYS", "liệt kê tin bảo mật", state)

    assert seen == [1], "phải báo đúng một lần, khi mới có lượt đầu"


def test_khong_bao_gi_khi_khong_bi_cat():
    client, _ = _client([_FakeResponse("Trọn vẹn.", truncated=False)])
    seen: list[int] = []
    state = ChatStreamState(on_retry=lambda: seen.append(1))

    client.chat("SYS", "câu hỏi", state)

    assert seen == [], "câu không bị cắt thì người dùng không bao giờ thấy mốc này"


def test_kenh_bao_hong_khong_duoc_lam_hong_cau_tra_loi():
    """Mốc tiến trình là thứ trang trí; câu trả lời đã trả tiền để sinh ra thì không."""
    client, _ = _client([
        _FakeResponse("bị cắt giữa ch", truncated=True),
        _FakeResponse("Bản gộp lại.", truncated=False),
    ])

    def no(): raise RuntimeError("event loop đã đóng")

    text, calls = client.chat("SYS", "câu hỏi", ChatStreamState(on_retry=no))

    assert text == "Bản gộp lại."
    assert calls == 2


# --- Cắt lần đầu → hỏi lại ------------------------------------------------------

def test_cat_lan_dau_thi_hoi_lai_va_tra_ban_hoi_lai():
    client, models = _client([
        _FakeResponse("Tin thứ nhất nói về lỗ hổng ngh", truncated=True),
        _FakeResponse("- Tin 1: lỗ hổng nghiêm trọng.\n- Tin 2: bản vá đã ra.", truncated=False),
    ])

    text, calls = client.chat("SYS", "liệt kê tin bảo mật tuần này")

    assert text == "- Tin 1: lỗ hổng nghiêm trọng.\n- Tin 2: bản vá đã ra."
    assert calls == 2, "lượt hỏi lại phải được tính vào budget"
    assert len(models.calls) == 2


def test_luot_hoi_lai_mang_rang_buoc_do_dai_va_giu_nguyen_cau_hoi():
    client, models = _client([
        _FakeResponse("dở dang", truncated=True),
        _FakeResponse("Đủ ý.", truncated=False),
    ])

    client.chat("SYS", "câu hỏi gốc")

    sys_first, user_first = models.calls[0]
    sys_retry, user_retry = models.calls[1]
    assert _CONCISE_RETRY_DIRECTIVE not in sys_first
    assert _CONCISE_RETRY_DIRECTIVE in sys_retry, "hỏi lại phải kèm ràng buộc độ dài"
    assert user_retry == user_first == "câu hỏi gốc", "không được đổi câu hỏi của người dùng"


# --- Không bao giờ lộ marker cũ -------------------------------------------------

@pytest.mark.parametrize(
    "responses",
    [
        [_FakeResponse("a", True), _FakeResponse("Xong.", False)],
        [_FakeResponse("a", True), _FakeResponse("Câu một. Câu hai chưa xo", True)],
        [_FakeResponse("Câu đầy đủ.", False)],
    ],
    ids=["hỏi-lại-thành-công", "hỏi-lại-vẫn-cắt", "không-cắt"],
)
def test_khong_bao_gio_dan_loi_xin_loi_cat_ngan(responses):
    client, _ = _client(responses)

    text, _calls = client.chat("SYS", "q")

    assert OLD_MARKER not in text
    assert "hỏi hẹp hơn" not in text


# --- Lưới an toàn: hỏi lại vẫn cắt ----------------------------------------------

def test_hoi_lai_van_cat_thi_lui_ve_ranh_gioi_cau():
    client, _ = _client([
        _FakeResponse("dở", truncated=True),
        _FakeResponse("Câu một hoàn chỉnh. Câu hai đang viết dở giữa t", truncated=True),
    ])

    text, calls = client.chat("SYS", "q")

    assert text == "Câu một hoàn chỉnh."
    assert calls == 2
    assert not text.endswith("giữa t")


def test_hoi_lai_rong_thi_giu_ban_dau_da_cat_gon():
    client, _ = _client([
        _FakeResponse("Ý thứ nhất xong. Ý thứ hai dở da", truncated=True),
        _FakeResponse("", truncated=False),
    ])

    text, calls = client.chat("SYS", "q")

    assert text == "Ý thứ nhất xong."
    assert calls == 2


# --- Hàm cắt câu ----------------------------------------------------------------

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Một. Hai. Ba chưa xo", "Một. Hai."),
        ("Xong rồi!", "Xong rồi!"),
        ("Hỏi gì? Trả lời dở", "Hỏi gì?"),
        ("Kết thúc bằng ba chấm… phần dư", "Kết thúc bằng ba chấm…"),
        ("- Gạch một.\n- Gạch hai chưa", "- Gạch một."),
    ],
)
def test_trim_to_last_sentence(raw, expected):
    assert _trim_to_last_sentence(raw) == expected


def test_trim_giu_nguyen_khi_khong_co_ranh_gioi_cau():
    """Một đoạn dài không có dấu kết câu: cắt bừa còn tệ hơn giữ nguyên."""
    raw = "một đoạn rất dài không hề có dấu chấm nào cả nên không biết cắt ở đâu"
    assert _trim_to_last_sentence(raw) == raw
