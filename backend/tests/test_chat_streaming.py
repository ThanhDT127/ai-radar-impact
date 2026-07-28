"""Lối ra streaming của chat — change `chat-streaming-sse`.

Bất biến khoá:
- **Trạng thái CHỐT của streaming trùng hệt bản blocking** trên cùng đầu vào. Đây là toàn
  bộ lý do `commit` mang text chứ không chỉ mang citations: token đã phát là *tạm*, còn
  `resolve_citations` + `enforce_grounding` chỉ chạy được trên câu hoàn chỉnh.
- Fail‑closed vẫn fail‑closed dưới streaming: text ungrounded đã chảy ra màn hình phải bị
  `commit` thay, không được giữ lại.
- **Budget sống sót khi client ngắt** — chỗ rò dễ nhất của streaming: model đã tốn tiền
  rồi mà `finally` ghi log lại nằm sau vòng lặp mà người tiêu thụ vừa bỏ đi.
- Câu fast‑path (chào/meta) KHÔNG stream token giả và vẫn 0 lượt gọi.
- Status bám mốc THẬT của pipeline, kể cả mốc mở rộng scope.
"""

import asyncio
import json
import uuid
from datetime import datetime

import pytest

from app.ai.prompts import OUT_OF_SCOPE_SENTINEL
from app.routes.chat import _sse, _sse_stream
from app.schemas.chat import ChatRequest
from app.services.chat_grounding import INSUFFICIENT_GROUNDS_MESSAGE
from app.services.chat_service import (
    STATUS_COMPOSING,
    STATUS_EXPANDING,
    STATUS_READING_INSIGHT,
    STATUS_SEARCHING,
    ChatService,
)


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


class _StreamingGemini:
    """Fake client hai lối ra, cùng kịch bản — để so streaming với blocking trên cùng input.

    Mỗi phần tử kịch bản là danh sách chunk; `chat()` nối lại thành một phát, `chat_stream()`
    nhả từng chunk. Kế toán `state.calls` mô phỏng đúng hợp đồng thật: cộng khi chunk đầu về.
    """

    def __init__(self, *scripts):
        self.scripts = [list(s) for s in scripts]
        self.prompts: list[str] = []
        self._cursor = 0

    def _take(self, user_prompt: str) -> list[str]:
        self.prompts.append(user_prompt)
        chunks = self.scripts[self._cursor]
        self._cursor += 1
        return chunks

    def chat(self, system_prompt, user_prompt, state=None):
        return "".join(self._take(user_prompt)).strip(), 1

    def chat_stream(self, system_prompt, user_prompt, state):
        chunks = self._take(user_prompt)
        for idx, chunk in enumerate(chunks):
            if idx == 0:
                state.calls += 1
            state.text += chunk
            yield chunk
        state.text = state.text.strip()

    def classify_intent(self, question):
        return None


def _service(gemini, insight=None, global_pool=()):
    results = [_Result(0)]  # quota
    if insight is not None:
        results.append(_Result(insight))
    session = _FakeSession(results)
    service = ChatService(session, gemini=gemini)

    async def fake_list_for_chat(**kw):
        return list(global_pool)

    service.insight_repo.list_for_chat = fake_list_for_chat
    return service, session


async def _collect(service, question, history=None, insight_id=None):
    return [
        event
        async for event in service.answer_stream(question, history or [], insight_id)
    ]


def _of(events, kind):
    return [e for e in events if e["type"] == kind]


# --- Hình dạng luồng (task 2.1, 3.1) --------------------------------------------


@pytest.mark.asyncio
async def test_luong_phat_status_roi_token_roi_commit():
    tin = _FakeInsight("Tin OpenSSL")
    gemini = _StreamingGemini(["Có ", "lỗ hổng ", "OpenSSL [1]."])
    service, _ = _service(gemini, global_pool=[tin])

    events = await _collect(service, "có tin gì về OpenSSL")

    kinds = [e["type"] for e in events]
    assert kinds[0] == "status", "status phải đến TRƯỚC token — nó lấp khoảng thinking"
    assert kinds[-1] == "commit"
    assert kinds.count("commit") == 1
    statuses = [e["text"] for e in _of(events, "status")]
    # Mốc thứ hai nay mang SỐ LIỆU THẬT của lượt (tên tin đang đọc kỹ, tổng tin khớp) thay
    # cho `STATUS_COMPOSING` chung chung — TTFT 2,6–3,8s không cắt được, nên thứ duy nhất
    # cải thiện được là nói đúng việc đang làm. Vẫn ĐÚNG HAI status: thêm một sự kiện nữa
    # cách nhau vài chục ms chỉ làm dòng chữ nhấp nháy.
    assert len(statuses) == 2
    assert statuses[0] == STATUS_SEARCHING
    assert statuses[1].startswith("Đang đọc kỹ") and "Tin OpenSSL" in statuses[1]
    assert [e["text"] for e in _of(events, "token")] == ["Có ", "lỗ hổng ", "OpenSSL [1]."]


@pytest.mark.asyncio
async def test_mode_B_phat_status_doc_bai():
    tin = _FakeInsight()
    gemini = _StreamingGemini(["Bài này nói lỗ hổng đã có bản vá [1]."])
    service, _ = _service(gemini, insight=tin)

    events = await _collect(service, "bài này nói gì", insight_id=tin.id)

    # Mode B KHÔNG đi qua `build_context` (context là đúng một bài) nên giữ mốc chung chung.
    assert [e["text"] for e in _of(events, "status")] == [
        STATUS_READING_INSIGHT,
        STATUS_COMPOSING,
    ]
    assert _of(events, "commit")[0]["mode"] == "insight"


# --- Trạng thái chốt trùng bản blocking (task 2.2) ------------------------------


@pytest.mark.asyncio
async def test_commit_trung_het_ket_qua_blocking_tren_cung_dau_vao():
    """Bất biến trung tâm của change. Cùng kịch bản model, hai lối ra, một kết quả."""
    script = ["Tin đáng chú ý: ", "OpenSSL vá lỗ hổng [1]."]

    tin_a = _FakeInsight("Tin OpenSSL")
    blocking_service, _ = _service(_StreamingGemini(script), global_pool=[tin_a])
    blocking = await blocking_service.answer("có tin gì về OpenSSL", [], None)

    tin_b = _FakeInsight("Tin OpenSSL")
    tin_b.id = tin_a.id
    stream_service, _ = _service(_StreamingGemini(script), global_pool=[tin_b])
    commit = _of(await _collect(stream_service, "có tin gì về OpenSSL"), "commit")[0]

    assert commit["answer"] == blocking["answer"]
    assert commit["mode"] == blocking["mode"]
    assert [c["insight_id"] for c in commit["citations"]] == [
        c["insight_id"] for c in blocking["citations"]
    ]
    assert commit["citations"][0]["n"] == 1


@pytest.mark.asyncio
async def test_commit_mang_text_da_don_marker_ngoai_pham_vi():
    """Token thô mang `[9]` (ngoài index) — `commit` phải mang bản đã dọn, không phải bản thô."""
    tin = _FakeInsight("Tin OpenSSL")
    gemini = _StreamingGemini(["Có lỗ hổng [1]", " và tin khác [9]."])
    service, _ = _service(gemini, global_pool=[tin])

    events = await _collect(service, "có tin gì về OpenSSL")

    assert "[9]" in "".join(e["text"] for e in _of(events, "token"))
    assert "[9]" not in _of(events, "commit")[0]["answer"]


@pytest.mark.asyncio
async def test_fail_closed_duoi_streaming_hoan_sach_text_ungrounded():
    """Model khẳng định mà không marker: chữ đã chảy ra rồi vẫn phải bị `commit` thay."""
    tin = _FakeInsight("Tin OpenSSL")
    gemini = _StreamingGemini(["Có, ", "Google vừa ra Gemini 4."])
    service, _ = _service(gemini, global_pool=[tin])

    events = await _collect(service, "có tin gì về Gemini")

    streamed = "".join(e["text"] for e in _of(events, "token"))
    assert "Gemini 4" in streamed, "text tạm vẫn được stream — đó là bản chất provisional"
    commit = _of(events, "commit")[0]
    assert commit["answer"] == INSUFFICIENT_GROUNDS_MESSAGE
    assert commit["citations"] == []


# --- Budget khi client ngắt (task 2.3, 3.3) ------------------------------------


@pytest.mark.asyncio
async def test_ngat_giua_luong_van_ghi_budget():
    """Người tiêu thụ bỏ đi sau token đầu — tiền đã tiêu nên `chat_logs` vẫn phải có dòng."""
    tin = _FakeInsight("Tin OpenSSL")
    gemini = _StreamingGemini(["Có ", "lỗ hổng ", "OpenSSL [1]."])
    service, session = _service(gemini, global_pool=[tin])

    agen = service.answer_stream("có tin gì về OpenSSL", [], None)
    seen_token = False
    async for event in agen:
        if event["type"] == "token":
            seen_token = True
            break
    await agen.aclose()

    assert seen_token
    assert len(session.added) == 1, "phải có đúng một bản ghi chat_logs"
    assert session.added[0].model_calls == 1, "lượt đã tốn tiền phải được tính"


@pytest.mark.asyncio
async def test_ngat_giua_luong_dung_sinh_them_token():
    tin = _FakeInsight("Tin OpenSSL")
    gemini = _StreamingGemini([f"chunk {i} [1] " for i in range(20)])
    service, _ = _service(gemini, global_pool=[tin])

    agen = service.answer_stream("có tin gì về OpenSSL", [], None)
    tokens = 0
    async for event in agen:
        if event["type"] == "token":
            tokens += 1
            if tokens == 2:
                break
    await agen.aclose()

    assert tokens == 2, "không được sinh nốt 20 chunk sau khi client đã đi"


@pytest.mark.asyncio
async def test_luong_chay_tron_ven_van_ghi_dung_mot_dong_log():
    tin = _FakeInsight("Tin OpenSSL")
    gemini = _StreamingGemini(["Có lỗ hổng [1]."])
    service, session = _service(gemini, global_pool=[tin])

    await _collect(service, "có tin gì về OpenSSL")

    assert len(session.added) == 1
    assert session.added[0].model_calls == 1
    assert session.added[0].citations_count == 1


# --- Mở rộng scope qua streaming (task 2.4, 4.4) -------------------------------


@pytest.mark.asyncio
async def test_status_mo_rong_phat_truoc_luot_hai():
    other = _FakeInsight("Tin Kubernetes")
    insight = _FakeInsight("Tin OpenSSL")
    gemini = _StreamingGemini(
        [OUT_OF_SCOPE_SENTINEL],
        ["Toàn hệ thống có [2]."],
    )
    service, session = _service(gemini, insight=insight, global_pool=[other])

    events = await _collect(service, "có tin gì về Kubernetes", insight_id=insight.id)

    statuses = [e["text"] for e in _of(events, "status")]
    # Bước 1 là mode B (không qua `build_context`) nên giữ mốc chung; bước 2 đi qua
    # `_answer_global` nên mang số liệu thật của lượt mở rộng.
    assert statuses[:3] == [STATUS_READING_INSIGHT, STATUS_COMPOSING, STATUS_EXPANDING]
    assert len(statuses) == 4
    assert statuses[3].startswith("Đang đọc kỹ") and "Tin OpenSSL" in statuses[3]
    commit = _of(events, "commit")[0]
    assert commit["mode"] == "expanded", "nhãn mở rộng phải đi qua được đường streaming"
    assert [c["insight_id"] for c in commit["citations"]] == [other.id]
    assert session.added[0].model_calls == 2


@pytest.mark.asyncio
async def test_sentinel_khong_bao_gio_lot_ra_ke_ca_duoi_dang_token():
    """Đo thật 27/07: model sinh sentinel thành MỘT token, phát thẳng là người dùng thấy nó.

    Bản blocking miễn nhiễm vì chỉ nhìn câu hoàn chỉnh — lỗi này do streaming đẻ ra, nên
    lưới cũng phải nằm ở đây (`_SentinelGate`).
    """
    other = _FakeInsight("Tin Kubernetes")
    insight = _FakeInsight("Tin OpenSSL")
    gemini = _StreamingGemini([OUT_OF_SCOPE_SENTINEL], ["Toàn hệ thống có [2]."])
    service, _ = _service(gemini, insight=insight, global_pool=[other])

    events = await _collect(service, "có tin gì về Kubernetes", insight_id=insight.id)

    assert OUT_OF_SCOPE_SENTINEL not in _of(events, "commit")[0]["answer"]
    streamed = "".join(e["text"] for e in _of(events, "token"))
    assert OUT_OF_SCOPE_SENTINEL not in streamed, "sentinel không được nhấp nháy trên màn hình"
    assert "[[" not in streamed, "kể cả mảnh vụn của sentinel"


@pytest.mark.asyncio
async def test_sentinel_bi_cat_thanh_nhieu_chunk_van_bi_chan():
    """Chia nhỏ khác đi thì cổng vẫn phải giữ — nó so tiền tố, không so nguyên khối."""
    other = _FakeInsight("Tin Kubernetes")
    insight = _FakeInsight("Tin OpenSSL")
    pieces = [OUT_OF_SCOPE_SENTINEL[:4], OUT_OF_SCOPE_SENTINEL[4:12], OUT_OF_SCOPE_SENTINEL[12:]]
    gemini = _StreamingGemini(pieces, ["Toàn hệ thống có [2]."])
    service, _ = _service(gemini, insight=insight, global_pool=[other])

    events = await _collect(service, "có tin gì về Kubernetes", insight_id=insight.id)

    # Token duy nhất được phát là của LƯỢT MỞ RỘNG — không mảnh vụn nào của lượt B lọt ra.
    assert [e["text"] for e in _of(events, "token")] == ["Toàn hệ thống có [2]."]
    assert _of(events, "commit")[0]["mode"] == "expanded"


@pytest.mark.asyncio
async def test_cong_sentinel_khong_lam_nghen_cau_tra_loi_binh_thuong():
    """Câu bình thường lệch khỏi tiền tố ngay chunk đầu → không mất token nào, không trễ."""
    insight = _FakeInsight("Tin OpenSSL")
    gemini = _StreamingGemini(["Bài này ", "nói lỗ hổng ", "đã có bản vá [1]."])
    service, _ = _service(gemini, insight=insight)

    events = await _collect(service, "bài này nói gì", insight_id=insight.id)

    assert [e["text"] for e in _of(events, "token")] == [
        "Bài này ",
        "nói lỗ hổng ",
        "đã có bản vá [1].",
    ]


# --- Fast-path meta (task 2.5) -------------------------------------------------


@pytest.mark.asyncio
async def test_meta_ra_ngay_mot_commit_khong_token_gia():
    gemini = _StreamingGemini()
    service, session = _service(gemini)

    events = await _collect(service, "xin chào")

    assert [e["type"] for e in events] == ["commit"], "không status, không token giả"
    assert events[0]["mode"] == "meta"
    assert events[0]["citations"] == []
    assert gemini.prompts == [], "0 lượt gọi model"
    assert session.added[0].model_calls == 0


@pytest.mark.asyncio
async def test_meta_van_tra_loi_duoc_khi_het_quota():
    """Cửa quota nằm SAU định tuyến ý định — bất biến của ② không được vỡ vì streaming."""
    from app.config import settings

    gemini = _StreamingGemini()
    session = _FakeSession([_Result(settings.max_daily_chat_calls + 10)])
    service = ChatService(session, gemini=gemini)

    events = await _collect(service, "cảm ơn bạn")

    assert [e["type"] for e in events] == ["commit"]
    assert events[0]["mode"] == "meta"


# --- Quota và lỗi đi bằng sự kiện (task 3.1) -----------------------------------


@pytest.mark.asyncio
async def test_het_quota_phat_su_kien_error():
    from app.config import settings

    tin = _FakeInsight("Tin OpenSSL")
    gemini = _StreamingGemini(["không bao giờ chạy"])
    session = _FakeSession([_Result(settings.max_daily_chat_calls)])
    service = ChatService(session, gemini=gemini)

    async def fake_list_for_chat(**kw):
        return [tin]

    service.insight_repo.list_for_chat = fake_list_for_chat

    events = await _collect(service, "có tin gì về OpenSSL")

    assert [e["type"] for e in events] == ["error"]
    assert events[0]["code"] == "quota"
    assert gemini.prompts == []


# --- Khung SSE (task 3.1) ------------------------------------------------------


def test_khung_sse_khong_vo_khi_token_co_xuong_dong():
    """`\\n` là ký tự kết thúc trường của SSE — token thô sẽ cắt câu trả lời thành rác."""
    frame = _sse("token", {"text": "dòng một\ndòng hai"})

    assert frame.endswith("\n\n")
    body = frame.split("\n")[1]
    assert body.startswith("data: ")
    assert json.loads(body[len("data: "):])["text"] == "dòng một\ndòng hai"
    assert frame.count("\n\n") == 1, "một khung, không phải hai"


@pytest.mark.asyncio
async def test_route_anh_xa_su_kien_sang_khung_sse():
    tin = _FakeInsight("Tin OpenSSL")
    gemini = _StreamingGemini(["Có lỗ hổng [1]."])
    service, _ = _service(gemini, global_pool=[tin])

    frames = [
        chunk
        async for chunk in _sse_stream(
            service, ChatRequest(question="có tin gì về OpenSSL")
        )
    ]

    assert frames[0].startswith("event: status\n")
    assert any(f.startswith("event: token\n") for f in frames)
    assert frames[-1].startswith("event: commit\n")
    commit = json.loads(frames[-1].split("\n")[1][len("data: "):])
    assert commit["mode"] == "global"
    assert uuid.UUID(commit["citations"][0]["insight_id"]) == tin.id
    assert "type" not in commit, "`type` đã thành tên sự kiện, không lặp lại trong data"


@pytest.mark.asyncio
async def test_route_dich_error_sang_thong_bao_nguoi_doc_duoc():
    from app.config import settings

    session = _FakeSession([_Result(settings.max_daily_chat_calls)])
    service = ChatService(session, gemini=_StreamingGemini())

    frames = [
        chunk
        async for chunk in _sse_stream(service, ChatRequest(question="tin gì hôm nay"))
    ]

    assert len(frames) == 1
    assert frames[0].startswith("event: error\n")
    payload = json.loads(frames[0].split("\n")[1][len("data: "):])
    assert payload["code"] == "quota"
    assert "hết lượt hỏi" in payload["message"]


# --- Chống cắt dưới streaming (nối `chat-answer-completeness`) -----------------


@pytest.mark.asyncio
async def test_bi_cat_thi_commit_mang_ban_hoi_lai_chu_khong_phai_doan_do_dang():
    """Chữ đã hiện không rút lại được, nhưng câu CHỐT vẫn phải trọn vẹn."""

    class _TruncatedThenRetry:
        def __init__(self):
            self.prompts: list[str] = []

        def chat_stream(self, system_prompt, user_prompt, state):
            self.prompts.append(user_prompt)
            state.calls += 1
            for chunk in ["Đoạn đầu [1] rồi bị cắt giữa ch"]:
                state.text += chunk
                yield chunk
            state.truncated = True
            # Hợp đồng của `GeminiClient.chat_stream`: hỏi lại một phát rồi THAY text.
            state.calls += 1
            state.text = "Bản gọn: lỗ hổng OpenSSL đã có bản vá [1]."
            state.replaced = True

        def chat(self, system_prompt, user_prompt, state=None):
            raise AssertionError("lối streaming không được rơi về chat() một phát")

        def classify_intent(self, question):
            return None

    tin = _FakeInsight("Tin OpenSSL")
    gemini = _TruncatedThenRetry()
    service, session = _service(gemini, global_pool=[tin])

    events = await _collect(service, "có tin gì về OpenSSL")

    commit = _of(events, "commit")[0]
    assert commit["answer"] == "Bản gọn: lỗ hổng OpenSSL đã có bản vá [1]."
    assert "bị cắt giữa ch" not in commit["answer"]
    assert session.added[0].model_calls == 2, "cả hai lượt đều tốn tiền"


# --- Cùng một nguồn logic (task 2.1) ------------------------------------------


@pytest.mark.asyncio
async def test_blocking_khong_dung_toi_chat_stream():
    """`/chat` phải giữ nguyên đường cũ — nếu không, test cũ và eval harness (④) đổi nghĩa."""

    class _NoStream(_StreamingGemini):
        def chat_stream(self, system_prompt, user_prompt, state):
            raise AssertionError("blocking không được đi lối streaming")
            yield  # pragma: no cover — giữ hàm là generator

    tin = _FakeInsight("Tin OpenSSL")
    service, _ = _service(_NoStream(["Có lỗ hổng [1]."]), global_pool=[tin])

    result = await service.answer("có tin gì về OpenSSL", [], None)

    assert result["mode"] == "global"
    assert len(result["citations"]) == 1


@pytest.mark.asyncio
async def test_tran_buoc_van_ap_dung_o_loi_streaming():
    tin = _FakeInsight("Tin OpenSSL")
    service, _ = _service(_StreamingGemini(["x"]), global_pool=[tin])
    service._emit = lambda event: asyncio.sleep(0)
    service._steps_used = 2

    with pytest.raises(RuntimeError, match="Chạm trần"):
        await service._call_model("prompt bất kỳ")
