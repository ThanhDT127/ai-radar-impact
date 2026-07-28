"""Pydantic schemas cho endpoint chat Q&A."""

import uuid

from pydantic import BaseModel, Field, field_validator

# History do client giữ (service stateless). Cap ở đây thay vì tin client tự cắt.
MAX_HISTORY_TURNS = 10

# Trần payload cho working set. KHÁC `settings.chat_deep_slots` (số ô sâu thật, mặc định 3)
# — cái này chỉ chặn payload vô lý ở biên; service mới là chỗ cắt theo cấu hình.
MAX_REFERENCED = 20


class TurnCitation(BaseModel):
    """Marker đã dùng ở một lượt TRƯỚC, kèm nhãn đọc được của nguồn.

    Chỉ mang `n` + `title` — không mang `insight_id`/`source_url`: mục đích duy nhất là để
    server dịch `[n]` trong history thành tên bài, và mọi thứ thừa hơn thế là bề mặt tấn
    công cho client tự khai định danh.
    """

    n: int
    title: str


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
    """

    n: int
    insight_id: uuid.UUID
    title: str
    source_url: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    mode: str  # "insight" | "global" | "meta" | "expanded" | "focused"
