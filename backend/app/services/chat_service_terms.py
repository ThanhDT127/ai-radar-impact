"""Từ vựng dùng chung cho pipeline chat — tách ra để tránh import vòng.

`chat_service` (xếp hạng) và `chat_intent` (định tuyến ý định) đều cần `STOPWORDS`. Đặt ở
module trung lập này để `chat_intent` không phải import ngược `chat_service`.
"""

# Từ xuất hiện trong hầu hết câu hỏi nên không phân biệt được tin nào liên quan.
STOPWORDS = {
    "này", "nào", "gì", "có", "không", "cho", "của", "các", "những", "một", "và",
    "là", "với", "về", "trong", "đến", "tới", "được", "bị", "thì", "mà", "hay",
    "hoặc", "tôi", "mình", "team", "công", "ty", "hệ", "thống", "tin", "tức",
    "tuần", "nay", "hôm", "vừa", "rồi", "đang", "sẽ", "cần", "nên", "phải",
    "đáng", "chú", "ý", "quan", "tâm", "nhất", "gấp", "mới", "đọc", "xem",
    "liên", "quan", "nói", "gì", "ra", "sao", "thế", "làm", "khi", "nếu",
    # 2 ký tự — cần liệt kê vì ngưỡng độ dài đã hạ xuống 2
    "ở", "đi", "ta", "họ", "nó", "ai", "ừ", "à", "ạ", "đó", "kia", "ấy", "vì",
    "do", "nên", "tuy", "dù", "chỉ", "cả", "còn", "đã", "sẽ", "vẫn", "cũng",
}
