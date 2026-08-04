"""Từ vựng dùng chung cho pipeline chat — tách ra để tránh import vòng.

`chat_service` (xếp hạng) và `chat_intent` (định tuyến ý định) đều cần `STOPWORDS`. Đặt ở
module trung lập này để `chat_intent` không phải import ngược `chat_service`.
"""

# Từ xuất hiện trong hầu hết câu hỏi nên không phân biệt được tin nào liên quan.
#
# Giữ danh sách KHÔNG TRÙNG LẶP: `set` nuốt bản trùng nên chúng vô hại về hành vi, nhưng
# chúng làm người đọc tưởng đây là hai nhóm khác nhau và che mất việc một từ đã có rồi.
# (`quan`, `gì`, `nên`, `sẽ` từng xuất hiện hai lần.)
STOPWORDS = {
    "này", "nào", "gì", "có", "không", "cho", "của", "các", "những", "một", "và",
    "là", "với", "về", "trong", "đến", "tới", "được", "bị", "thì", "mà", "hay",
    "hoặc", "tôi", "mình", "team", "công", "ty", "hệ", "thống", "tin", "tức",
    "tuần", "nay", "hôm", "vừa", "rồi", "đang", "sẽ", "cần", "nên", "phải",
    "đáng", "chú", "ý", "quan", "tâm", "nhất", "gấp", "mới", "đọc", "xem",
    "liên", "nói", "ra", "sao", "thế", "làm", "khi", "nếu",
    # 2 ký tự — cần liệt kê vì ngưỡng độ dài đã hạ xuống 2.
    # ⚠️ `ai` ở đây là ĐẠI TỪ tiếng Việt, nhưng nó cũng nuốt luôn từ khoá "AI" — câu
    # "Có tin AI nào không?" cho `_question_terms` = [] và tầng độ liên quan hoà toàn bộ.
    # Đó là đánh đổi có chủ đích, được khoá bằng kịch bản `rank-ascii-ai-blind`; gỡ `ai`
    # khỏi đây sẽ đổi recall của nhiều câu khác, đừng gỡ mà không chạy `chat_rank_harness`.
    "ở", "đi", "ta", "họ", "nó", "ai", "ừ", "à", "ạ", "đó", "kia", "ấy", "vì",
    "do", "tuy", "dù", "chỉ", "cả", "còn", "đã", "vẫn", "cũng",
    # Từ khung của câu HỒI CHỈ — "so sánh hai bài vừa rồi", "hai cái này khác nhau chỗ nào".
    # Chúng không nói gì về nội dung, nhưng trước 28/07/2026 chúng lọt qua `_question_terms`
    # nên cổng `if not terms → tắt tầng vector` KHÔNG BAO GIỜ bắn cho loại câu này: hệ thống
    # đi embed một câu rỗng nghĩa rồi xếp hạng 179 tin theo nhiễu đó. Đo được: cùng câu hỏi,
    # tắt/bật tầng vector cho thứ hạng nhảy loạn không theo hướng nào (141↔105, 22↔66, 45↔1)
    # — chữ ký của nhiễu, đúng chế độ hỏng mà `rank-generic` đã phải chặn một lần.
    #
    # Không chữa được ca so sánh hồi chỉ (thông tin "hai bài nào" vốn không có trong câu
    # hỏi — đó là việc của working set), nhưng dừng việc xếp hạng bằng nhiễu.
    "hai", "cái", "bài", "chỗ", "khác", "sánh", "nhau",
}
