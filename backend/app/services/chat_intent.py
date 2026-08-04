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
    # Thêm 25/07/2026 theo đo 70 ca: "thank you" và "cảm ơn nhiều" trượt fast‑path chỉ vì
    # hai token này. An toàn vì chúng không tự quyết định nhóm — câu rút về rỗng mà không
    # có token chào/cảm‑ơn nào vẫn rơi xuống `return None`.
    "you", "nhiều",
}

# Token TỰ QUY CHIẾU về bot. Đây là thứ phân biệt "hỏi về năng lực của bot" với "hỏi về sản
# phẩm nói trong bài" — và chính là tín hiệu bị mất khi "bạn"/"bot" nằm trong filler rồi bị
# xoá. Giữ HẸP: "trợ lý" phải khớp theo CỤM, vì token "trợ" đơn lẻ còn nằm trong "hỗ trợ"
# (nếu coi "trợ" là tự quy chiếu thì "hỗ trợ gì" hỏi về một công cụ sẽ bị gạt nhầm).
_SELF_TOKENS = {"bạn", "bot", "chatbot", "mày", "cậu"}
_SELF_PHRASES = ("trợ lý",)

# Đại từ hồi chỉ: trỏ ngược về BÀI ĐANG XEM / thứ vừa nhắc. Có nó mà KHÔNG có tự quy chiếu
# thì câu đang hỏi về sản phẩm trong bài, không phải về trợ lý — "nó là ai", "công cụ này
# hỗ trợ gì". Luật này gỡ đúng ca mà cả matching cũ LẪN gemini-2.5-flash-lite đều sai (đo
# 25/07/2026: flash-lite trả `capability` cho "nó là ai" dù prompt nêu thẳng ca đó là Q).
_ANAPHORA_TOKENS = {"nó", "này", "kia", "đó", "ấy", "cái", "bài", "tin", "chúng"}

# Luật lưỡng lự → nhường cho model nhẹ phán. Không phải một nhóm ý định.
AMBIGUOUS = "__ambiguous__"

# Câu hỏi năng lực thường chỉ gồm xưng hô + stopword ("bạn làm được gì", "bạn là ai"), nên
# phải nhận bằng CỤM chứ không token đơn. Khớp trên chuỗi token đã nối bằng space → vẫn tôn
# trọng ranh giới từ. Giữ cụm ĐẶC TRƯNG, tránh cụm quá rộng như "là gì"/"làm gì" (chúng xuất
# hiện trong câu hỏi thật "OpenSSL là gì"); cổng "phần còn lại rỗng" đã chặn phần lớn ca đó.
#
# Bỏ "dùng để làm gì" (25/07/2026): nó là hậu tố của "để làm gì" nên không bao giờ khớp thêm
# được câu nào — cụm ngắn hơn luôn khớp trước.
_CAPABILITY_PHRASES = (
    "làm được gì", "làm được những gì", "giúp được gì", "giúp được những gì",
    "giúp gì", "là ai", "chức năng", "khả năng", "công dụng", "hỗ trợ gì",
    "hỗ trợ được gì", "để làm gì", "biết làm gì",
    "hoạt động thế nào", "hoạt động như thế nào", "giới thiệu",
)


def _tokens(question: str) -> list[str]:
    return re.findall(r"[0-9a-zA-ZÀ-ỹ]+", question.lower())


# Token mang nội dung của chính các cụm năng lực ("giúp", "chức", "năng", "hoạt", "động"…).
# SUY RA TỪ `_CAPABILITY_PHRASES`, không viết tay: đo 25/07/2026 cho thấy 14/17 cụm là code
# chết vì cổng "phần còn lại rỗng" chạy TRƯỚC và những token này không nằm trong
# STOPWORDS/filler nên không cụm nào chạm tới. Suy ra tự động ⇒ thêm cụm mới sau này không
# thể tái sinh lỗi đó.
_CAPABILITY_CONTENT_TOKENS = {
    t for phrase in _CAPABILITY_PHRASES for t in _tokens(phrase)
} - STOPWORDS - _SALUTATION_TOKENS - _THANKS_TOKENS - _FILLER_TOKENS

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


def _is_self_referential(tokens: list[str], joined: str) -> bool:
    """Câu có nói về CHÍNH bot không ("bạn…", "bot này…", "trợ lý…")?"""
    return bool(set(tokens) & _SELF_TOKENS) or any(p in joined for p in _SELF_PHRASES)


def route_intent(question: str) -> str | None:
    """Định tuyến BA TRẠNG THÁI — tầng 1 của bộ lọc lai (25/07/2026).

    Trả về:
    - `"salutation"` / `"thanks"` / `"capability"` — luật CHẮC CHẮN, dùng preset ngay (6µs);
    - `None` — luật CHẮC CHẮN đây là câu tra cứu, đi pipeline (6µs);
    - `AMBIGUOUS` — luật lưỡng lự, nhường `GeminiClient.classify_intent()` phán.

    Vì sao lai chứ không giao hết cho model: đo 25/07/2026 trên 84 ca nhãn tay, sàn
    round‑trip của `gemini-2.5-flash-lite` là **1.433–1.685 ms** kể cả với prompt rỗng và
    1 token output — đó là mạng + TTFT, không cắt được. Giao hết cho model nghĩa là cộng
    ~1,45s vào MỌI câu, kể cả câu tra cứu thật (15,9s → 17,4s). Tệ hơn nữa, precision của
    model trên chính tập đó chỉ **91,5%** so với **97,6%** của luật: nó gạt nhầm
    "cảm ơn vì tin về mã nguồn mở" thành `thanks`. Luật thắng ở ca rõ ràng, model thắng ở
    ca mập mờ — nên mỗi bên làm phần mình giỏi. Ca mập mờ đo được là **3/84 ≈ 3,5%**,
    tức ~96,5% câu hỏi không tốn thêm mili‑giây nào.
    """
    tokens = _tokens(question)
    if not tokens:
        return None

    present = set(tokens)
    joined = " ".join(tokens)
    remaining = [t for t in tokens if t not in _INTENT_TOKENS and t not in STOPWORDS]
    has_capability_phrase = any(phrase in joined for phrase in _CAPABILITY_PHRASES)
    self_ref = _is_self_referential(tokens, joined)
    anaphora = bool(present & _ANAPHORA_TOKENS)

    if remaining:
        if not has_capability_phrase:
            return None  # còn nội dung thực chất, không có dấu hiệu meta nào → câu thật
        leftover = [t for t in remaining if t not in _CAPABILITY_CONTENT_TOKENS]
        if anaphora and not self_ref:
            return None  # "công cụ này hỗ trợ gì" — hỏi về thứ trong bài
        if leftover and not self_ref:
            return None  # "API mới của OpenAI dùng để làm gì" — còn danh từ riêng, không nói về bot
        if not leftover and self_ref:
            return "capability"  # "bạn hoạt động thế nào"
        return AMBIGUOUS  # tự quy chiếu nhưng còn token lạ: "bot này dùng để làm gì"

    # Phần còn lại rỗng → chỉ là chào/meta. Ưu tiên: capability (cụm) > thanks > salutation.
    if has_capability_phrase:
        if anaphora and not self_ref:
            return None  # "nó là ai" — hỏi về nhân vật/tổ chức trong bài
        if self_ref:
            return "capability"
        return AMBIGUOUS  # "giới thiệu đi", "để làm gì" — thiếu chủ ngữ, luật không đoán bừa

    if present & _THANKS_TOKENS:
        return "thanks"
    if present & _SALUTATION_TOKENS:
        return "salutation"
    return None


def classify_intent(question: str) -> str | None:
    """Phần TẤT ĐỊNH thuần của bộ định tuyến: `AMBIGUOUS` quy về `None` (đi pipeline).

    Dùng khi không có/không muốn dùng model nhẹ — ví dụ test, hoặc khi tầng 2 lỗi. Giữ
    đúng bias fall‑through của design D2: lưỡng lự thì đi pipeline, không đoán bừa.
    """
    intent = route_intent(question)
    return None if intent == AMBIGUOUS else intent
