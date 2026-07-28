"""Cắt `normalized_content` thành đoạn để embed — MỘT chỗ duy nhất (design D3).

Cùng luật với `build_embedding_text`: hằng số ở đây là **một phần của hợp đồng embedding**.
Đổi kích thước cửa sổ hoặc overlap ⇒ vector cũ và vector mới không còn so được với nhau
trong cùng một cột, mà **không có gì báo lỗi** — chỉ là cosine lệch đi một chút và xếp hạng
tệ dần trong im lặng. Đổi thì phải `chunk_documents --redo` toàn bộ.

Đơn vị "token" ở đây là **ước lượng theo ký tự**, không phải tokenizer thật: `text-multilingual-
embedding-002` không lộ tokenizer, và một phép đếm gần đúng ổn định còn hơn một phép đếm chính
xác phụ thuộc thư viện ngoài. Tỉ lệ 4 ký tự/token là ước lượng thô cho văn bản latin; tiếng
Việt có dấu tốn nhiều byte hơn nhưng số **ký tự** thì tương đương, nên trần này vẫn nằm dưới
giới hạn 2048 token của model với biên rất rộng.
"""

import re

# ~400–600 token ⇒ 1.600–2.400 ký tự (design D3). Lấy cận trên làm trần cứng của một đoạn.
CHARS_PER_TOKEN = 4
TARGET_TOKENS = 500
MAX_TOKENS = 600
OVERLAP_RATIO = 0.15

TARGET_CHARS = TARGET_TOKENS * CHARS_PER_TOKEN      # 2000
MAX_CHARS = MAX_TOKENS * CHARS_PER_TOKEN            # 2400
OVERLAP_CHARS = int(TARGET_CHARS * OVERLAP_RATIO)   # 300

# Đoạn quá ngắn không mang đủ ngữ cảnh để embed cho ra vector có nghĩa; nó chỉ thêm một
# hàng vector nhiễu vào bảng và một ứng viên rác vào tầng xếp hạng.
MIN_CHARS = 120

# Ranh giới cắt, ưu tiên giảm dần: hết đoạn văn → hết câu → xuống dòng. KHÔNG cắt giữa câu
# nếu còn lựa chọn nào khác, và không bao giờ cắt giữa từ.
_PARAGRAPH_RE = re.compile(r"\n\s*\n")
_SENTENCE_RE = re.compile(r"(?<=[.!?…])\s")
_NEWLINE_RE = re.compile(r"\n")

# Chỉ nhận ranh giới nằm ở nửa sau cửa sổ: một dấu chấm ở ký tự thứ 40 của cửa sổ 2.000 là
# ranh giới "hợp lệ" nhưng cắt ở đó thì đoạn còn 40 ký tự và ta đã tự phá kích thước mục tiêu.
_MIN_BOUNDARY_RATIO = 0.5


def _cut_at(window: str) -> int:
    """Vị trí cắt tốt nhất trong `window`. Trả `len(window)` nếu không có ranh giới nào."""
    floor = int(len(window) * _MIN_BOUNDARY_RATIO)
    for pattern in (_PARAGRAPH_RE, _SENTENCE_RE, _NEWLINE_RE):
        positions = [m.end() for m in pattern.finditer(window) if m.end() >= floor]
        if positions:
            return positions[-1]
    # Không có ranh giới câu nào (bảng, khối code, văn bản dính liền): lùi về khoảng trắng
    # cuối cùng để ít nhất KHÔNG cắt giữa từ.
    space = window.rfind(" ", floor)
    return space + 1 if space != -1 else len(window)


def _next_start(text: str, start: int, cut: int) -> int:
    """Điểm bắt đầu của đoạn kế: lùi lại `OVERLAP_CHARS` rồi TIẾN tới đầu từ gần nhất.

    Lùi trần trụi `cut - OVERLAP_CHARS` gần như luôn rơi vào giữa một từ, và đoạn kế sẽ mở
    đầu bằng một mảnh vô nghĩa (`huật toán…`). Với embedding thì mảnh cụt ở đầu đoạn không
    làm hỏng vector, nhưng nó lộ ra ngay khi ai đó đọc chunk để gỡ lỗi — và một biểu diễn
    mà người ta không đọc được là một biểu diễn không ai kiểm được.
    """
    back = max(cut - OVERLAP_CHARS, 1)
    space = text.find(" ", start + back)
    nxt = space + 1 if space != -1 and space < start + cut else start + back
    return max(nxt, start + 1)


def split_content(content: str | None) -> list[str]:
    """`normalized_content` → danh sách đoạn, tất định, không trùng lặp thứ tự.

    Cửa sổ trượt có overlap ~15%: một sự thật nằm vắt qua ranh giới hai đoạn vẫn còn nguyên
    vẹn trong ít nhất một đoạn. Đây là lý do duy nhất của overlap — không phải để tăng recall
    chung chung mà để ranh giới cắt không phá mất chính cái chi tiết ta đi tìm.

    Ingest đã chặn `normalized_content` ở 8.000 ký tự nên thực tế ≤ 6 đoạn/bài.
    """
    text = (content or "").strip()
    if len(text) < MIN_CHARS:
        return []

    chunks: list[str] = []
    start = 0
    while True:
        if start + MAX_CHARS >= len(text):
            # Phần đuôi vừa trong một cửa sổ: nuốt trọn rồi DỪNG. Không có `break` ở đây
            # thì bước overlap vẫn đẩy `start` tiến lên và hàm sinh ra vô số bản sao của
            # chính phần đuôi — đúng lỗi bản đầu tiên mắc phải.
            tail = text[start:].strip()
            if len(tail) >= MIN_CHARS:
                chunks.append(tail)
            elif chunks and tail:
                # Mẩu cụt nhập vào đoạn trước thay vì đứng riêng thành một vector nhiễu.
                chunks[-1] = (chunks[-1] + "\n" + tail).strip()
            break

        cut = _cut_at(text[start : start + TARGET_CHARS])
        chunk = text[start : start + cut].strip()
        if len(chunk) >= MIN_CHARS:
            chunks.append(chunk)

        start = _next_start(text, start, cut)

    return chunks
