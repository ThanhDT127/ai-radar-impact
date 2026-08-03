"""Pydantic schemas cho endpoint chat Q&A."""

import uuid

from pydantic import BaseModel, Field, field_validator

# Nhập NGƯỢC chiều lớp thông thường (schemas ← services) một cách có chủ đích: tập mốc tiến
# trình là **hợp đồng đường truyền** dùng chung backend↔frontend, nên nó chỉ được có MỘT định
# nghĩa. Chép lại danh sách vào đây để giữ "lớp cho đẹp" là tạo ra hai nguồn sự thật sẽ lệch
# nhau trong im lặng — đúng loại lỗi `chat-citation-integrity` đã trả giá. Không có vòng lặp:
# `chat_service` không nhập gì từ `app.schemas`.
from app.services.chat_service import STATUS_KEYS  # noqa: E402

# History do client giữ (service stateless). Cap ở đây thay vì tin client tự cắt.
MAX_HISTORY_TURNS = 10

# Trần payload cho working set. KHÁC `settings.chat_deep_slots` (số ô sâu thật, mặc định 3)
# — cái này chỉ chặn payload vô lý ở biên; service mới là chỗ cắt theo cấu hình.
MAX_REFERENCED = 20


class TurnCitation(BaseModel):
    """Marker đã dùng ở một lượt TRƯỚC, kèm nhãn đọc được và định danh của nguồn.

    `n` + `title` để server dịch `[n]` trong history thành tên bài (bảng ánh xạ dựng lại mỗi
    lượt nên con số cũ trỏ tin khác). `insight_id` để server GHIM tin đó vào ngữ cảnh lượt
    hiện tại — xem `chat-history-pinning`.

    ⚠️ Bản trước của docstring này nói cố ý KHÔNG mang `insight_id` vì đó là "bề mặt tấn công
    cho client tự khai định danh". Điều đó **đọc sai ranh giới tin cậy thật**:
    `ChatRequest.referenced_insight_ids` đã nhận id thẳng từ client từ `chat-context-depth`,
    nên khả năng "client khiến một insight đi vào ngữ cảnh" đã tồn tại và đã được chấp nhận.
    Thêm trường này KHÔNG mở rộng ranh giới đó — id vẫn phải tra ra một insight `published` +
    `is_primary` có thật, nên client vẫn không đưa được **văn bản tuỳ ý** vào prompt. Đó mới
    là bất biến cần giữ, và nó không đổi.

    Cách còn lại — server tra ngược theo `title` — bị loại: tiêu đề không bảo đảm duy nhất,
    khớp chuỗi là phép mờ, và một lần tra nhầm sẽ ghim SAI tin trong im lặng.
    """

    n: int
    title: str
    # `None` = client cũ không gửi ⇒ không có gì để ghim ⇒ hành vi như trước change. Suy
    # giảm êm, không cần đồng bộ phiên bản FE/BE.
    insight_id: uuid.UUID | None = None


class ChatTurn(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    # Citations của CHÍNH lượt đó. Cần vì bảng ánh xạ `n → insight` được dựng LẠI mỗi lượt:
    # `[3]` của lượt trước và `[3]` của lượt này là hai tin khác nhau (xem `_history_block`).
    citations: list[TurnCitation] = []

    @field_validator("role")
    @classmethod
    def check_role(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError("role phải là 'user' hoặc 'assistant'")
        return v


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = []
    insight_id: uuid.UUID | None = None
    # Working set: insight người dùng đang thao tác (mở trang chi tiết, bấm citation, ghim
    # tay). Tách khỏi `question` một cách CÓ CHỦ ĐÍCH — nhét URL/UUID vào text câu hỏi vừa
    # phá bất biến "prompt không chứa định danh" (D4), vừa làm nhiễu `_question_terms`.
    # Server cắt ở `chat_deep_slots`; cap ở đây chỉ để chặn payload vô lý.
    referenced_insight_ids: list[uuid.UUID] = Field(default=[], max_length=MAX_REFERENCED)

    @field_validator("history")
    @classmethod
    def cap_history(cls, v: list[ChatTurn]) -> list[ChatTurn]:
        """Giữ 10 lượt GẦN NHẤT — cắt đuôi trước, không phải cắt đầu."""
        return v[-MAX_HISTORY_TURNS:]


class Citation(BaseModel):
    """Một nguồn được trích dẫn, kèm CHÍNH con số marker đã xuất hiện trong answer.

    `n` là số thứ tự trong index do server cấp phát (1..N), **không** phải vị trí trong mảng
    này. Hai hệ quy chiếu đó chỉ trùng nhau khi model trích dẫn liền mạch từ [1] — và nó
    thường làm vậy chỉ vì prompt dặn "tin ở đầu danh sách đáng chọn hơn". Client cũ suy `n`
    từ vị trí mảng (`citations[n-1]`) nên trỏ sai ngay khi model bỏ qua một tin ở giữa; tức
    là lỗi bị che bởi chất lượng xếp hạng và sẽ lộ ra đúng lúc xếp hạng kém đi.
    Đưa `n` thành dữ liệu để ranh giới backend↔frontend tự mô tả, không phải cùng đoán đúng.

    `kind` phân biệt LOẠI nguồn, KHÔNG phải một không gian số thứ hai (`chat-web-fallback` D4):
    `insight` = tin đã qua phân tích trong hệ thống; `web` = trang tra cứu ngoài, chỉ sống
    trong đúng lượt hỏi đó. Cả hai dùng CHUNG dãy `n`, nên client vẫn giải marker bằng đúng
    một phép tra theo `n`. Trộn thêm một cách đánh số nữa là dựng lại đúng cái bẫy ở trên,
    ở quy mô lớn hơn.
    """

    n: int
    kind: str = "insight"  # "insight" | "web"
    # `None` KHI VÀ CHỈ KHI `kind == "web"` — nguồn web không phải insight nên không có id.
    insight_id: uuid.UUID | None = None
    title: str
    source_url: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    mode: str  # "insight" | "global" | "meta" | "expanded" | "focused"
    # HTML Search Suggestions do Google trả về, chỉ có ở lượt CÓ tra cứu ngoài.
    # Hiển thị nó là YÊU CẦU TUÂN THỦ điều khoản Grounding with Google Search, không phải
    # hạng mục trang trí có thể cắt khi gấp.
    search_suggestions: str | None = None


class ChatStatusEvent(BaseModel):
    """Một mốc tiến trình trên luồng SSE (`event: status`).

    CHỈ có ở `POST /api/v1/chat/stream`; đường blocking không phát sự kiện nào.

    `key` là định danh **ổn định** của mốc, thuộc tập đóng `STATUS_KEYS`:
    `searching` · `ranked` · `pinned` · `reading` · `expanding` · `retrying` · `composing`.
    `text` là câu tiếng Việt hiển thị, MANG SỐ LIỆU THẬT của lượt đó nên hai lần phát cùng
    một mốc gần như luôn khác chuỗi.

    Client PHẢI phân biệt mốc bằng `key`, không bằng `text` — nếu không, một mốc phát lại với
    số liệu mới sẽ thành một dòng trùng, và việc sửa câu chữ tiếng Việt sẽ âm thầm đổi hành vi
    render. Gặp `key` lạ thì hiện như một mốc mới, KHÔNG bỏ qua: server mới + client cũ không
    được làm mất thông tin của nhau.
    """

    key: str
    text: str

    @field_validator("key")
    @classmethod
    def check_key(cls, v: str) -> str:
        if v not in STATUS_KEYS:
            raise ValueError(f"Mốc tiến trình không hợp lệ: {v!r}")
        return v
