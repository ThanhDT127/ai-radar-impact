"""Định tuyến ý định deterministic cho chat — fast‑path chào hỏi / meta / cảm ơn.

Mục tiêu: câu KHÔNG cần tra cứu ("xin chào", "bạn làm được gì?", "cảm ơn") trả lời tức
thì bằng preset tĩnh, **0 lượt gọi model**, không tiêu quota (design D1/D3 của change
`chat-intent-router`). Phân loại bằng LUẬT, không bằng LLM: một lượt gọi LLM để phân loại
sẽ tái lập đúng chi phí/độ trễ đang cắt.

Bias **fall‑through** (design D2): chỉ fast‑path khi câu **chỉ** là chào/meta; còn nội dung
thực chất → trả `None` để đi pipeline. False‑positive (gạt nhầm câu hỏi thật) tệ hơn nhiều
false‑negative (tốn 1 lượt gọi cho câu chào lọt lưới).
"""

import re

from app.services.chat_service_terms import STOPWORDS

# --- Tập token khởi đầu: NHỎ và CHẮC CHẮN. Mở rộng theo log fast‑path thật, ĐỪNG đoán
# trước (design "Ngưỡng tập chào"). Nhận diện theo TOKEN (ranh giới từ), không theo chuỗi
# con — bài học biên‑từ của `_roles_in_question`: "hi" chỉ khớp từ "hi", không khớp trong
# một từ dài hơn.

_SALUTATION_TOKENS = {
    "chào", "chao", "hi", "hello", "helo", "hey", "xin", "alo",
}

_THANKS_TOKENS = {
    "cảm", "cám", "ơn", "thanks", "thank", "tks", "thankyou", "thanx",
}

# Từ xưng hô / tiểu từ tình thái: bỏ được khi phân loại (không mang nội dung tra cứu), để
# "cảm ơn nhé" hay "chào bạn" rút về rỗng. KHÔNG dùng để quyết định nhóm.
_FILLER_TOKENS = {
    "bạn", "bot", "trợ", "lý", "ơi", "nhé", "nha", "nhá", "nhỉ",
    "vậy", "đấy", "nè", "hen", "ha",
}

# Câu hỏi năng lực thường chỉ gồm xưng hô + stopword ("bạn làm được gì", "bạn là ai"), nên
# phải nhận bằng CỤM chứ không token đơn. Khớp trên chuỗi token đã nối bằng space → vẫn tôn
# trọng ranh giới từ. Giữ cụm ĐẶC TRƯNG, tránh cụm quá rộng như "là gì"/"làm gì" (chúng xuất
# hiện trong câu hỏi thật "OpenSSL là gì"); cổng "phần còn lại rỗng" đã chặn phần lớn ca đó.
_CAPABILITY_PHRASES = (
    "làm được gì", "làm được những gì", "giúp được gì", "giúp được những gì",
    "giúp gì", "là ai", "chức năng", "khả năng", "công dụng", "hỗ trợ gì",
    "hỗ trợ được gì", "dùng để làm gì", "để làm gì", "biết làm gì",
    "hoạt động thế nào", "hoạt động như thế nào", "giới thiệu",
)

_INTENT_TOKENS = _SALUTATION_TOKENS | _THANKS_TOKENS | _FILLER_TOKENS

# Preset tĩnh tiếng Việt, `citations=[]`. Preset `capability` phải ĐIỀU HƯỚNG: nêu ví dụ truy
# vấn tốt (design D4) — câu chào không cần "thông minh", cần rẻ + tức thì + dạy hỏi tốt hơn.
INTENT_PRESETS: dict[str, str] = {
    "salutation": (
        "Chào bạn 👋 Mình là trợ lý AI Radar. Bạn muốn hỏi gì về các tin công nghệ / "
        "bảo mật đang có trong hệ thống? Ví dụ: \"tuần này có gì cho Security?\""
    ),
    "capability": (
        "Mình giúp bạn tra cứu và tổng hợp các insight trong AI Radar — theo chủ đề, "
        "theo vai trò, hoặc theo mức độ ảnh hưởng. Thử hỏi: \"tuần này có gì đáng chú ý "
        "cho Dev?\", \"có rủi ro bảo mật nào mới không?\", hoặc mở một tin cụ thể rồi hỏi "
        "chi tiết ngay trong bài đó."
    ),
    "thanks": (
        "Rất vui được giúp bạn! 🙌 Cần tra cứu thêm tin gì thì cứ hỏi mình nhé."
    ),
}


def _tokens(question: str) -> list[str]:
    return re.findall(r"[0-9a-zA-ZÀ-ỹ]+", question.lower())


def classify_intent(question: str) -> str | None:
    """Trả về nhóm ý định fast‑path, hoặc `None` (câu thật → đi pipeline).

    Cách làm (design D2): bỏ token chào/meta/filler + `STOPWORDS` khỏi câu; nếu phần còn
    lại **rỗng** thì đây chỉ là câu chào/meta → chọn nhóm theo dấu hiệu có mặt; còn nội
    dung thực chất → `None`.
    """
    tokens = _tokens(question)
    if not tokens:
        return None

    remaining = [t for t in tokens if t not in _INTENT_TOKENS and t not in STOPWORDS]
    if remaining:
        return None  # còn nội dung thực chất → không fast‑path

    # Phần còn lại rỗng → chỉ là chào/meta. Ưu tiên: capability (cụm) > thanks > salutation.
    joined = " ".join(tokens)
    if any(phrase in joined for phrase in _CAPABILITY_PHRASES):
        return "capability"

    present = set(tokens)
    if present & _THANKS_TOKENS:
        return "thanks"
    if present & _SALUTATION_TOKENS:
        return "salutation"
    return None
