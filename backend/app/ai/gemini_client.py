"""Gemini Flash client for article analysis — powered by Vertex AI."""

import json
import logging
import re
import time
from collections.abc import Iterator
from dataclasses import dataclass, field

from google import genai
from google.genai import types

from app.ai.prompts import ALLOWED_CONTENT_TYPES, build_gate_prompt, build_prompt
from app.ai.schemas import build_gate_schema
from app.config import settings
from app.models.insight import EMBEDDING_DIM

logger = logging.getLogger(__name__)

MODEL_ID = settings.gemini_model_id

# Chỗ JSON vỡ quan sát được ở char 517 và 1308, nên `text[:200]` không bao giờ
# chạm tới nguyên nhân. Chỉ log dài ở nhánh exception nên không phình log lúc chạy
# bình thường (design D5).
RAW_LOG_CHARS = 2000

# Trần output cho chat. 2048 KHÔNG đủ: Gemini 2.5 tính thinking tokens vào cùng ngân
# sách này, và câu hỏi kiểu "liệt kê tin bảo mật tuần này" sinh ~1150 token nhìn thấy
# được cộng thinking là chạm trần rồi bị cắt giữa từ (đo 22/07/2026).
#
# Nâng 4096 → 8192 (25/07/2026): chỉ bị tính tiền theo token THỰC SINH, nên trần cao hơn
# không đắt hơn cho câu ngắn — nó chỉ ngừng cắt oan câu dài. Đây là tuyến phòng thủ 1;
# tuyến 2 là hỏi lại kèm ràng buộc độ dài (xem `_CONCISE_RETRY_DIRECTIVE`).
CHAT_MAX_OUTPUT_TOKENS = 8192

# Chỉ dẫn dán thêm khi lượt đầu bị cắt. KHÔNG cắt bớt phạm vi câu trả lời — yêu cầu model
# gộp ý để vẫn đủ ý mà vừa ngân sách. Trả về nửa câu kèm lời xin lỗi (cách làm cũ) là không
# chấp nhận được: người dùng nhận một câu trả lời sai lệch vì thiếu vế sau.
_CONCISE_RETRY_DIRECTIVE = (
    "\n\n### RÀNG BUỘC ĐỘ DÀI (bắt buộc)\n"
    "Câu trả lời lần trước đã bị cắt giữa chừng vì quá dài. Lần này hãy trả lời "
    "NGẮN GỌN NHƯNG TRỌN VẸN, phủ ĐỦ Ý đã hỏi:\n"
    "- Tối đa 5 gạch đầu dòng, mỗi gạch 1–2 câu.\n"
    "- Gộp các tin tương tự vào một gạch thay vì liệt kê từng tin.\n"
    "- Bỏ phần dẫn nhập và phần kết luận dài dòng.\n"
    "- BẮT BUỘC kết thúc hoàn chỉnh, tuyệt đối không bỏ dở câu."
)

# --- Bộ phân loại ý định tầng 2 (model nhẹ) ------------------------------------------
# Nhãn MỘT KÝ TỰ để output đúng 1 token — độ trễ ở đây là TTFT, mọi token thêm đều đắt.
INTENT_LABELS: dict[str, str | None] = {
    "S": "salutation",
    "T": "thanks",
    "C": "capability",
    "Q": None,  # câu tra cứu thật
}

# Phần "QUY TẮC" không phải trang trí: đo 25/07/2026, flash-lite gạt nhầm
# "cảm ơn vì tin về mã nguồn mở" → T và "mô hình này có khả năng gì" → C khi thiếu chúng.
# Luật tất định đã chặn phần lớn ca đó trước khi tới đây, nhưng prompt vẫn phải tự đứng
# vững vì tập "lưỡng lự" sẽ đổi khi ta mở rộng luật.
INTENT_CLASSIFIER_PROMPT = """Bạn phân loại câu người dùng gửi cho AI Radar — trợ lý tra cứu tin công nghệ/bảo mật.
Trả về DUY NHẤT một chữ cái in hoa, không giải thích, không dấu câu:

S = câu CHỈ là lời chào, không hỏi gì thêm
T = câu CHỈ là lời cảm ơn, không hỏi gì thêm
C = hỏi về năng lực hoặc danh tính của CHÍNH trợ lý này
Q = mọi câu còn lại — cần tra cứu tin tức

QUY TẮC:
- Chỉ chọn C khi chủ ngữ là chính trợ lý (bạn / bot / trợ lý). Câu hỏi về một sản phẩm,
  công cụ, mô hình hay nhân vật nói trong bài luôn là Q — kể cả khi dùng đúng những chữ
  như "hoạt động thế nào", "hỗ trợ gì", "là ai", "dùng để làm gì".
- Chào hoặc cảm ơn mà KÈM một câu hỏi thật thì là Q, không phải S/T.
- Phân vân thì trả Q."""

# --- Embedding cho retrieval lai (chat-hybrid-retrieval) -----------------------------
# `task_type` KHÔNG phải trang trí: model sinh vector khác nhau cho câu hỏi và cho tài
# liệu, và ghép đúng cặp QUERY↔DOCUMENT là cách dùng chuẩn của họ embedding này. Embed
# cả hai bên bằng cùng một task_type vẫn chạy, chỉ kém — đúng loại lỗi im lặng.
EMBED_TASK_QUERY = "RETRIEVAL_QUERY"
EMBED_TASK_DOCUMENT = "RETRIEVAL_DOCUMENT"

# Trần số chuỗi trong MỘT lượt gọi embed. Vertex giới hạn theo cả số instance lẫn tổng
# token; 32 là mức an toàn cho text cô đọng của insight và vẫn cắt được ~179 tin xuống
# 6 lượt gọi khi backfill.
EMBED_BATCH_SIZE = 32

# Ranh giới câu tiếng Việt cho lưới an toàn cuối cùng.
_SENTENCE_END = ".!?…"


def _trim_to_last_sentence(text: str) -> str:
    """Cắt về câu hoàn chỉnh cuối cùng — lưới an toàn khi hỏi lại vẫn bị cắt.

    Thà mất ý cuối còn hơn hiển thị một câu đứt giữa từ. Nếu không tìm thấy ranh giới
    câu nào (đoạn văn một câu rất dài) thì trả nguyên văn — cắt bừa còn tệ hơn.
    """
    stripped = text.rstrip()
    cut = max(stripped.rfind(c) for c in _SENTENCE_END)
    if cut <= 0:
        return text
    # Giữ cả dòng cuối nếu nó là một gạch đầu dòng đã hoàn chỉnh.
    return stripped[: cut + 1]


def _is_truncated(response) -> bool:
    """Response có bị cắt vì chạm `max_output_tokens` không?

    ⚠️ `types.FinishReason` là enum CHUỖI: `.value` trả `'MAX_TOKENS'`, KHÔNG phải `2`.
    So sánh `== 2` (cách viết cũ ở `analyze()`) không bao giờ đúng, nên cảnh báo cắt
    chưa từng bắn — kể cả trong đợt điều tra runaway generation ngày 20/07/2026.
    """
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return False
    reason = candidates[0].finish_reason
    return getattr(reason, "value", reason) == "MAX_TOKENS"


@dataclass
class ChatStreamState:
    """Sổ ghi của MỘT lượt `chat_stream` — caller đọc sau khi luồng kết thúc *hoặc bị bỏ dở*.

    Vì sao là object truyền vào chứ không phải giá trị trả về: generator bị bỏ dở (client
    ngắt kết nối) không bao giờ chạy tới `return`, mà đó lại đúng lúc ta cần biết **đã tốn
    bao nhiêu tiền**. `calls` được cộng NGAY khi chunk đầu tiên về — thời điểm tiền đã tiêu —
    nên dù caller vứt generator giữa chừng, budget vẫn đọc được (design D5).

    `text` là toàn văn đã ráp; `truncated` để caller quyết có phải hỏi lại không.
    """

    text: str = ""
    calls: int = 0
    truncated: bool = False
    # Bản cuối KHÁC phần đã stream (do hỏi lại hoặc cắt về ranh giới câu) → caller phải
    # thay text đã hiện, không được nối thêm.
    replaced: bool = False


@dataclass
class GateResult:
    """Parsed result from Gemini gate pre-screening."""

    actionability_score: float = 0.0
    content_type: str = "noise"
    gate_reason: str = ""
    pass_gate: bool = False
    error: str | None = None


@dataclass
class AnalysisResult:
    """Parsed result from Gemini deep analysis."""

    topics: list[str] = field(default_factory=list)
    event_type: str | None = None
    nature: str | None = None
    summary_short: str | None = None
    summary_medium: str | None = None
    affected_roles: list[str] = field(default_factory=list)
    confidence: float = 0.0
    raw_response: dict = field(default_factory=dict)
    error: str | None = None
    # v2 actionable fields
    signal: str | None = None
    why_it_matters: str | None = None
    recommendations: dict | None = None
    risks: list[str] | None = None
    # v3 taxonomy overhaul fields
    so_what: str | None = None
    adoption_ring: str | None = None
    practical_indicators: dict | None = None


class GeminiClient:
    """Wrapper around Google Gemini API (Vertex AI) for insight analysis."""

    def __init__(self) -> None:
        self._client = genai.Client(
            vertexai=True,
            project=settings.google_cloud_project,
            location=settings.google_cloud_location,
        )

    def gate_analyze(self, title: str, content: str) -> GateResult:
        """Run lightweight gate pre-screening on an article.

        Returns GateResult. On error, returns result with error field set
        and pass_gate=True (fail-open so we don't lose content due to transient errors).
        """
        prompt = build_gate_prompt(title=title, content=content)
        _retry_delays = [3, 10]

        for attempt, delay in enumerate([0] + _retry_delays):
            if delay:
                logger.info("Retrying gate after %ds (attempt %d/2) for '%s'", delay, attempt, title[:50])
                time.sleep(delay)
            try:
                response = self._client.models.generate_content(
                    model=MODEL_ID,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.0,
                        max_output_tokens=4096,
                        response_mime_type="application/json",
                        response_schema=build_gate_schema(),
                    ),
                )
                raw_text = response.text or ""
                return self._parse_gate_response(raw_text)

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    if attempt < len(_retry_delays):
                        logger.warning("Gate 429 rate-limit for '%s', will retry", title[:50])
                        continue
                logger.error("Gate error for '%s': %s", title[:50], e)
                return GateResult(pass_gate=True, error=err_str)

        return GateResult(pass_gate=True, error="Gate 429 RESOURCE_EXHAUSTED after retries")

    def _parse_gate_response(self, raw_text: str) -> GateResult:
        """Parse Gemini JSON gate response into GateResult."""
        # Extract JSON substring robustly starting from first '{' to last '}'
        start_idx = raw_text.find('{')
        if start_idx != -1:
            text = raw_text[start_idx:]
            end_idx = text.rfind('}')
            if end_idx != -1:
                text = text[:end_idx + 1]
        else:
            text = raw_text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(
                "Failed to parse gate JSON: %s | raw (%d chars): %s",
                e, len(text), text[:RAW_LOG_CHARS],
            )
            return GateResult(pass_gate=True, error=f"Gate JSON parse error: {e}")

        score = float(data.get("actionability_score", 0.0))
        content_type = data.get("content_type", "noise")
        if content_type not in ALLOWED_CONTENT_TYPES:
            content_type = "noise"

        return GateResult(
            actionability_score=score,
            content_type=content_type,
            gate_reason=str(data.get("gate_reason", ""))[:100],
            pass_gate=bool(data.get("pass_gate", False)),
        )

    def analyze(self, title: str, content: str) -> AnalysisResult:
        """Classify and summarize an article using Gemini Flash via Vertex AI.

        Returns an AnalysisResult. On error, returns result with error field set.
        Retries up to 3 times on 429 rate-limit errors with exponential backoff.

        CHƯA bật `response_schema` ở đây (khác với `gate_analyze`). Đo 20/07/2026 trên
        2 batch: bật schema cho lần gọi này làm model sinh `why_it_matters` lan man
        (~6500 ký tự, giới hạn prompt là 300) cho tới khi chạm `max_output_tokens` và
        bị cắt giữa chuỗi → 16/16 doc qua gate đều lỗi `Unterminated string`, 0 insight
        tạo được. Thêm `max_length` vào schema KHÔNG cứu được: Vertex không thực thi
        ràng buộc đó. Gate thì ngược lại — schema chạy sạch (0 lỗi so với nền 3-9/50).
        Đúng thứ tự Migration Plan của change: bật cho gate trước, analyze để sau khi
        tìm được cách chặn runaway generation.
        """
        prompt = build_prompt(title=title, content=content)
        _retry_delays = [5, 15, 45]

        for attempt, delay in enumerate([0] + _retry_delays):
            if delay:
                logger.info("Retrying Gemini after %ds (attempt %d/3) for '%s'", delay, attempt, title[:50])
                time.sleep(delay)
            try:
                response = self._client.models.generate_content(
                    model=MODEL_ID,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=4096,
                        response_mime_type="application/json",
                    ),
                )

                if _is_truncated(response):
                    logger.warning("Gemini response truncated (MAX_TOKENS) for '%s'", title[:50])

                raw_text = response.text or ""
                return self._parse_response(raw_text)

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    if attempt < len(_retry_delays):
                        logger.warning("Gemini 429 rate-limit for '%s', will retry", title[:50])
                        continue
                logger.error("Vertex AI error for '%s': %s", title[:50], e)
                return AnalysisResult(error=err_str)

        return AnalysisResult(error="Gemini 429 RESOURCE_EXHAUSTED after 3 retries")

    def chat(self, system_prompt: str, user_prompt: str) -> tuple[str, int]:
        """Một lượt hỏi đáp cho chat Q&A. Trả `(text, model_calls_used)`.

        KHÁC `analyze()`/`gate_analyze()` ở hai điểm cố ý:

        1. **Không** `response_mime_type`/`response_schema`. Đo 20/07/2026: bật schema cho
           lần gọi có output dài làm model sinh lan man tới chạm `max_output_tokens` rồi bị
           cắt giữa chuỗi → 16/16 doc lỗi `Unterminated string`; `max_length` trong schema
           Vertex KHÔNG được thực thi. Câu trả lời chat đúng hình dạng đó. Trả text thuần
           thì không có JSON để vỡ — citation đi đường riêng qua marker `[n]` (design D4).
        2. Trả kèm số lượt gọi ĐÃ TỐN TIỀN để service tính budget. Retry 429 không có
           response nên không tính; lượt trả về rồi vỡ ở bước sau vẫn tính.

        Hàm này SYNC như phần còn lại của client — caller phải bọc `asyncio.to_thread`
        vì chat nằm trên request path (design D6).

        **Không bao giờ trả về câu trả lời dở dang** (đổi 25/07/2026). Gemini 2.5 tiêu
        thinking tokens trong CÙNG ngân sách output nên câu hỏi kiểu liệt kê vẫn có thể
        chạm trần. Cách cũ — dán "_(Câu trả lời bị cắt…)_" vào cuối đoạn đứt — là hỏng:
        người dùng đọc một câu trả lời THIẾU VẾ SAU, mà phần thiếu thường là phần quan
        trọng nhất (khuyến nghị, rủi ro). Nay: cắt → HỎI LẠI kèm ràng buộc gộp ý cho
        ngắn gọn nhưng đủ ý. Lượt hỏi lại được tính vào `calls` trả về nên budget vẫn khớp.
        """
        text, truncated, calls = self._chat_once(system_prompt, user_prompt)
        if not truncated:
            return text, calls

        logger.warning("Chat response truncated (MAX_TOKENS) — hỏi lại với ràng buộc độ dài")
        retry_text, retry_truncated, retry_calls = self._chat_once(
            system_prompt + _CONCISE_RETRY_DIRECTIVE, user_prompt
        )
        calls += retry_calls

        # Lượt hỏi lại rỗng (hiếm — thinking ăn hết ngân sách) thì bản đầu vẫn hơn không.
        if not retry_text:
            return _trim_to_last_sentence(text), calls

        if retry_truncated:
            # Vẫn cắt sau khi đã ép ngắn: cắt về câu hoàn chỉnh cuối. Không dán lời xin
            # lỗi — câu trả lời phải đọc như một câu trả lời, không phải một lỗi.
            logger.warning("Chat vẫn bị cắt sau khi hỏi lại — cắt về ranh giới câu")
            return _trim_to_last_sentence(retry_text), calls

        return retry_text, calls

    def chat_stream(
        self, system_prompt: str, user_prompt: str, state: ChatStreamState
    ) -> Iterator[str]:
        """Bản **sinh dần** của `chat()` — yield từng chunk text khi model sinh.

        Cùng model, cùng system+user prompt, cùng cấu hình (vẫn KHÔNG structured output —
        bài học `gemini-structured-output` không đổi vì đường truyền đổi). `chat()` một‑phát
        giữ nguyên: route blocking, eval harness và test cũ vẫn đi lối đó.

        Kế toán đi qua `state` chứ không qua giá trị trả về — xem `ChatStreamState`.

        **Chống‑cắt dưới streaming.** `chat()` gặp `MAX_TOKENS` thì hỏi lại cho ngắn gọn mà
        đủ ý; ở đây chữ đã hiện lên màn hình rồi nên không "rút lại" được từng token. Cách
        xử lý: hỏi lại bằng lượt **một‑phát** (không stream — người dùng đã có chữ để đọc,
        stream lần hai chỉ làm nhấp nháy) rồi bật `state.replaced` để caller THAY toàn bộ
        text ở sự kiện chốt. Đây chính là kênh provisional→commit mà fail‑closed đang dùng,
        không phải cơ chế thứ hai. Bất biến "không bao giờ trả câu trả lời dở dang" giữ
        nguyên, và trạng thái chốt vẫn trùng bản blocking.
        """
        yield from self._chat_stream_once(system_prompt, user_prompt, state)
        state.text = state.text.strip()
        if not state.truncated:
            return

        logger.warning("Chat stream bị cắt (MAX_TOKENS) — hỏi lại với ràng buộc độ dài")
        retry_text, retry_truncated, retry_calls = self._chat_once(
            system_prompt + _CONCISE_RETRY_DIRECTIVE, user_prompt
        )
        state.calls += retry_calls
        state.replaced = True

        if not retry_text:
            # Lượt hỏi lại rỗng (thinking ăn hết ngân sách) — bản đầu vẫn hơn không.
            state.text = _trim_to_last_sentence(state.text)
            return
        state.text = _trim_to_last_sentence(retry_text) if retry_truncated else retry_text

    def _chat_stream_once(
        self, system_prompt: str, user_prompt: str, state: ChatStreamState
    ) -> Iterator[str]:
        """Một lượt gọi streaming + retry 429. Cập nhật `state` tại chỗ.

        Chỉ retry khi **chưa** phát chunk nào: một khi chữ đã ra tới người dùng thì gọi lại
        là sinh ra hai câu trả lời chồng nhau trên cùng một bong bóng.
        """
        _retry_delays = [3, 10]

        for attempt, delay in enumerate([0] + _retry_delays):
            if delay:
                logger.info("Retrying chat stream after %ds (attempt %d/2)", delay, attempt)
                time.sleep(delay)

            started = False
            try:
                stream = self._client.models.generate_content_stream(
                    model=MODEL_ID,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.2,
                        max_output_tokens=CHAT_MAX_OUTPUT_TOKENS,
                    ),
                )
                last = None
                for response in stream:
                    if not started:
                        # Tiền đã tiêu ngay từ chunk đầu — cộng ở đây chứ không ở cuối,
                        # vì cuối có thể không bao giờ tới (client ngắt).
                        state.calls += 1
                        started = True
                    last = response
                    piece = response.text or ""
                    if piece:
                        state.text += piece
                        yield piece

                if not started:
                    state.calls += 1  # gọi thành công nhưng model không sinh gì
                state.truncated = _is_truncated(last) if last is not None else False
                return

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    if not started and attempt < len(_retry_delays):
                        logger.warning("Chat stream 429 rate-limit, will retry")
                        continue
                logger.error("Chat stream Vertex AI error: %s", e)
                raise

        raise RuntimeError("Chat stream 429 RESOURCE_EXHAUSTED after retries")

    def embed(
        self, texts: list[str], task_type: str = EMBED_TASK_DOCUMENT
    ) -> list[list[float] | None]:
        """Sinh embedding cho một lô text. Trả list CÙNG ĐỘ DÀI với `texts`.

        Phần tử `None` = lô đó embed lỗi. **Không ném exception**: embedding là phụ trợ
        xếp hạng, không phải đường sống (design D6). Cả `AnalyzerService` lẫn chat đều
        phải chạy tiếp được khi Vertex embedding sự cố — nơi này trả `None`, nơi gọi log
        WARNING rồi đi tiếp bằng đường lexical.

        **KHÔNG đếm vào `model_calls`** — nghĩa là không tiêu `max_daily_chat_calls`.
        Cùng lý do với bộ phân loại ý định tầng 2: bộ đếm đó canh budget của lượt sinh
        văn bản đắt (~19k token trên `gemini-2.5-flash`). Một lượt embed là ~30–200 token
        trên model embedding, rẻ hơn vài bậc; trộn chung là để lượt gọi rẻ bào mòn budget
        đắt (đúng bẫy "đơn vị budget khác nhau" của repo).

        SYNC như phần còn lại của client — caller trên request path phải bọc `to_thread`.
        """
        if not texts:
            return []

        out: list[list[float] | None] = []
        for start in range(0, len(texts), EMBED_BATCH_SIZE):
            batch = texts[start : start + EMBED_BATCH_SIZE]
            out.extend(self._embed_batch(batch, task_type))
        return out

    def embed_one(
        self, text: str, task_type: str = EMBED_TASK_DOCUMENT
    ) -> list[float] | None:
        """`embed()` cho đúng một chuỗi. `None` = lỗi hoặc text rỗng."""
        if not text or not text.strip():
            return None
        return self.embed([text], task_type)[0]

    def _embed_batch(
        self, batch: list[str], task_type: str
    ) -> list[list[float] | None]:
        """Một lượt gọi embed + retry 429. Lỗi → trả `[None] * len(batch)`."""
        _retry_delays = [3, 10]

        for attempt, delay in enumerate([0] + _retry_delays):
            if delay:
                logger.info("Retrying embed after %ds (attempt %d/2)", delay, attempt)
                time.sleep(delay)
            try:
                response = self._client.models.embed_content(
                    model=settings.embedding_model_id,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type=task_type,
                        output_dimensionality=EMBEDDING_DIM,
                        # Text dài hơn trần của model thì CẮT thay vì ném lỗi: một insight
                        # dài bất thường không đáng để mất embedding của cả lô.
                        auto_truncate=True,
                    ),
                )
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < len(
                    _retry_delays
                ):
                    logger.warning("Embed 429 rate-limit, will retry")
                    continue
                logger.warning("Embed lỗi (%d text): %s", len(batch), e)
                return [None] * len(batch)

            embeddings = list(response.embeddings or [])
            if len(embeddings) != len(batch):
                # Ghép sai vị trí còn tệ hơn không có embedding: nó gán vector của tin này
                # cho tin khác và làm hỏng xếp hạng một cách im lặng.
                logger.warning(
                    "Embed trả %d vector cho %d text — bỏ cả lô", len(embeddings), len(batch)
                )
                return [None] * len(batch)
            return [list(e.values) if e.values else None for e in embeddings]

        return [None] * len(batch)

    def classify_intent(self, question: str) -> str | None:
        """Tầng 2 của bộ lọc ý định: model NHẸ phán ca luật lưỡng lự (~3,5% câu hỏi).

        Trả nhóm ý định (`salutation`/`thanks`/`capability`) hoặc `None` = câu tra cứu.

        Ba lựa chọn ép độ trễ xuống sàn, vì hàm này nằm chắn trước câu trả lời:
        - model lite (`intent_classifier_model_id`) — 2.5‑flash không dùng được ở đây,
          thinking ăn hết ngân sách output và trả text rỗng (đo 25/07/2026);
        - nhãn MỘT KÝ TỰ → đúng 1 token output, phần tốn thời gian duy nhất còn lại là
          TTFT (đo: sàn 1.433 ms với prompt rỗng, nên prompt dài thêm gần như miễn phí);
        - `max_output_tokens=4`, `temperature=0` → tất định, không lan man.

        **Fail‑safe về phía pipeline**: mọi lỗi/nhãn lạ đều trả `None`. Câu chào lọt lưới
        chỉ tốn thêm một lượt gọi; gạt nhầm câu hỏi thật thành preset mới là hỏng thật.
        KHÔNG retry — retry ở đây là cộng thẳng vài giây vào thời gian chờ của người dùng
        để cứu một phân loại mà fallback đã xử lý đúng rồi.
        """
        try:
            response = self._client.models.generate_content(
                model=settings.intent_classifier_model_id,
                contents=question,
                config=types.GenerateContentConfig(
                    system_instruction=INTENT_CLASSIFIER_PROMPT,
                    temperature=0.0,
                    max_output_tokens=4,
                ),
            )
        except Exception as e:
            logger.warning("Intent classifier lỗi, rơi về pipeline: %s", e)
            return None

        label = (response.text or "").strip().upper()[:1]
        intent = INTENT_LABELS.get(label)
        if label not in INTENT_LABELS:
            logger.warning("Intent classifier trả nhãn lạ %r → rơi về pipeline", label)
        return intent

    def _chat_once(self, system_prompt: str, user_prompt: str) -> tuple[str, bool, int]:
        """Một lượt gọi chat + retry 429. Trả `(text, bị_cắt, số_lượt_tính_tiền)`."""
        _retry_delays = [3, 10]
        calls = 0

        for attempt, delay in enumerate([0] + _retry_delays):
            if delay:
                logger.info("Retrying chat after %ds (attempt %d/2)", delay, attempt)
                time.sleep(delay)
            try:
                response = self._client.models.generate_content(
                    model=MODEL_ID,
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.2,
                        max_output_tokens=CHAT_MAX_OUTPUT_TOKENS,
                    ),
                )
                calls += 1
                return (response.text or "").strip(), _is_truncated(response), calls

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    if attempt < len(_retry_delays):
                        logger.warning("Chat 429 rate-limit, will retry")
                        continue
                logger.error("Chat Vertex AI error: %s", e)
                raise

        return "", False, calls

        raise RuntimeError("Chat 429 RESOURCE_EXHAUSTED after retries")

    def _parse_response(self, raw_text: str) -> AnalysisResult:
        """Parse Gemini JSON response into AnalysisResult."""
        # Extract JSON substring robustly starting from first '{' to last '}'
        start_idx = raw_text.find('{')
        if start_idx != -1:
            text = raw_text[start_idx:]
            end_idx = text.rfind('}')
            if end_idx != -1:
                text = text[:end_idx + 1]
        else:
            text = raw_text.strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(
                "Failed to parse Gemini JSON response: %s | raw (%d chars): %s",
                e, len(text), text[:RAW_LOG_CHARS],
            )
            return AnalysisResult(error=f"JSON parse error: {e}", raw_response={"raw": raw_text})

        # v2 actionable fields — graceful: missing/wrong type → None
        signal = data.get("signal")
        if not isinstance(signal, str) or not signal.strip():
            signal = None

        why_it_matters = data.get("why_it_matters")
        if not isinstance(why_it_matters, str) or not why_it_matters.strip():
            why_it_matters = None

        recommendations = data.get("recommendations")
        if not isinstance(recommendations, dict):
            recommendations = None

        risks = data.get("risks")
        if not isinstance(risks, list):
            risks = None
        else:
            risks = [r for r in risks if isinstance(r, str) and r.strip()]

        # v3 taxonomy overhaul fields — graceful degradation
        so_what = data.get("so_what")
        if not isinstance(so_what, str) or not so_what.strip():
            so_what = None

        adoption_ring = data.get("adoption_ring")
        if not isinstance(adoption_ring, str) or not adoption_ring.strip():
            adoption_ring = None

        practical_indicators = data.get("practical_indicators")
        if not isinstance(practical_indicators, dict):
            practical_indicators = None
        else:
            valid_keys = {"has_code_example", "has_benchmark", "has_api_change", "has_migration_guide", "has_security_patch"}
            practical_indicators = {
                k: bool(v) for k, v in practical_indicators.items() if k in valid_keys
            } or None

        return AnalysisResult(
            topics=data.get("topics", []),
            event_type=data.get("event_type"),
            nature=data.get("nature"),
            summary_short=data.get("summary_short"),
            summary_medium=data.get("summary_medium"),
            affected_roles=data.get("affected_roles", []),
            confidence=float(data.get("confidence", 0.0)),
            raw_response=data,
            signal=signal,
            why_it_matters=why_it_matters,
            recommendations=recommendations,
            risks=risks,
            so_what=so_what,
            adoption_ring=adoption_ring,
            practical_indicators=practical_indicators,
        )


_chat_client: GeminiClient | None = None


def get_chat_client() -> GeminiClient:
    """Singleton `GeminiClient` cho request path (design D6).

    `AnalyzerService.__init__` tạo client mới mỗi lần khởi tạo service — vô hại với
    script chạy một lần. Nhưng route dùng `Depends(...)` chạy MỖI REQUEST; bắt chước
    pattern đó sẽ dựng `genai.Client` mới cho từng câu hỏi = connection pool mới +
    re-auth Vertex mỗi lần.

    Khởi tạo lười: import module này không được đòi credentials (test/CI không có key).
    """
    global _chat_client
    if _chat_client is None:
        _chat_client = GeminiClient()
    return _chat_client
