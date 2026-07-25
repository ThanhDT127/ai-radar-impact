# Design: chat-intent-hybrid-filter

## Context

`chat-intent-router` (24/07) đặt một bộ phân loại tất định trước cửa quota trong `ChatService.answer()`.
Đo lại 25/07 phát hiện hai chuyện: recall chỉ 73,7%, và 14/17 cụm năng lực là **code chết** vì thứ tự
kiểm tra — cổng "phần còn lại rỗng" chạy trước phần khớp cụm.

Hung yêu cầu thay bằng model nhẹ trên Vertex, ưu tiên độ trễ thấp nhất. Toàn bộ thiết kế dưới đây dựa
trên số đo thật lấy trước khi viết code, không dựa trên ước lượng.

**Module ảnh hưởng:** M8 (Chatbot) — thuần backend.
**API endpoints:** `POST /api/v1/chat` — không đổi shape.
**Bảng DB:** không đụng, không migration.
**AI/LLM:** thêm một model thứ hai (`gemini-2.5-flash-lite`) dùng riêng cho phân loại.

## Goals / Non-Goals

**Goals:**
- Sửa recall mà **không** hy sinh precision (false-positive vẫn là hướng hỏng đắt nhất).
- Giữ độ trễ thêm ở mức ~0 cho đại đa số câu.
- Làm cho lỗi "cụm chết" không thể tái sinh khi ai đó thêm cụm mới.

**Non-Goals:**
- Không đuổi theo 100% recall — ca thiếu chủ ngữ ("giới thiệu đi") mơ hồ thật.
- Không tối ưu chi phí tầng 2 (đã là $0,026/1000 câu).

## Số đo nền (25/07/2026, 84 ca nhãn tay)

| Phương án | precision | recall | đúng hoàn toàn | độ trễ thêm |
|---|---|---|---|---|
| Luật cũ (24/07) | 100% | 73,7% | 85,7% | 0 |
| Luật đã vá | 97,6% | 95,3% | 96,5% | 0 |
| flash-lite cho mọi câu | 91,5% | 100% | 95,2% | **+1.450 ms mọi câu** |
| **Lai (chọn)** | **100%** | **97,7%** | **98,8%** | 0 cho 96,4%; ~1,6s cho 3,6% |

Sàn round-trip flash-lite: **1.433 / 1.536 / 1.685 ms** (min/p50/max) với prompt rỗng + 1 token output.

## Decisions

### D1: Lai hai tầng, không giao hết cho model

**Chọn:** luật quyết ca rõ ràng; model chỉ phán ca luật tự nhận lưỡng lự.

**Vì sao:** sàn 1,45s là mạng + TTFT nên không cắt được bằng model nhỏ hơn — giao hết cho model là cộng
ngần ấy vào *mọi* câu tra cứu thật, trong khi mục tiêu ban đầu của cả cụm chat là **cắt** độ trễ. Tệ hơn,
precision của model *thấp hơn* luật trên cùng tập đo. Không có chiều nào model thắng toàn cục.

**Đánh đổi:** hai đường code thay vì một; tập "lưỡng lự" phải được canh bằng test, nếu không nó âm thầm
phình ra và biến chat thành chậm hơn 1,5s cho mọi câu. Đó là lý do có
`test_ti_le_luong_lu_phai_hiem` (ngưỡng ≤10%).

### D2: `gemini-2.5-flash-lite`, không phải `gemini-2.5-flash`

**Vì sao:** đo thật — `gemini-2.5-flash` với `max_output_tokens=8` trả text **rỗng** vì thinking tokens
ăn sạch ngân sách output (cùng cái bẫy đã ghi trong `gemini-thinking-tokens`). flash-lite không bật
thinking mặc định nên trả đúng nhãn. Nó cũng là model lite **duy nhất khả dụng** ở `us-central1` của
project này — `gemini-2.0-flash-lite` và bản preview đều 404.

### D3: Ba tối ưu độ trễ, tất cả nhắm vào TTFT

Nhãn **một ký tự** (`S`/`T`/`C`/`Q`) → đúng 1 token output; `max_output_tokens=4`; `temperature=0`.
Vì sàn với prompt rỗng đã là 1.433 ms, **prompt dài thêm gần như miễn phí** — nên phần "QUY TẮC" trong
`INTENT_CLASSIFIER_PROMPT` được viết đầy đủ thay vì cắt cho ngắn.

**KHÔNG retry.** Retry ở đây cộng thẳng vài giây vào thời gian chờ để cứu một phân loại mà fallback đã
xử lý đúng rồi.

### D4: Luật hồi chỉ là của TẦNG 1, không nhường model

**Chọn:** `_ANAPHORA_TOKENS` (`nó`, `này`, `cái`, `bài`, `tin`…) + **không** có tự-quy-chiếu
(`bạn`/`bot`/`trợ lý`) ⇒ câu tra cứu, quyết dứt điểm ở tầng 1.

**Vì sao:** "nó là ai" là ca **cả hai phương án đều sai**. flash-lite trả `capability` **ngay cả khi
`INTENT_CLASSIFIER_PROMPT` nêu thẳng ca đó là Q**. Đây là bằng chứng cụ thể rằng "cứ đưa cho model là
xong" không đúng — nơi nào luật diễn đạt được chính xác thì luật đáng tin hơn.

Tự-quy-chiếu là tín hiệu phân biệt "hỏi về bot" với "hỏi về sản phẩm trong bài", và trước đây nó bị
**mất** vì `bạn`/`bot` nằm trong `_FILLER_TOKENS` rồi bị xoá. `trợ lý` phải khớp theo **cụm**: token
`trợ` đơn lẻ còn nằm trong "hỗ trợ", nên coi nó là tự-quy-chiếu sẽ gạt nhầm "hỗ trợ gì".

### D5: `_CAPABILITY_CONTENT_TOKENS` suy ra tự động

**Chọn:** derive từ `_CAPABILITY_PHRASES` trừ đi `STOPWORDS`/chào/cảm-ơn/filler, không viết tay.

**Vì sao:** lỗi gốc là **danh sách cụm và cổng lọc trôi khỏi nhau** — 14/17 cụm không bao giờ được so tới
mà không có gì báo. Suy ra tự động biến hai thứ đó thành một nguồn sự thật: thêm cụm mới là tự động thêm
token nội dung của nó, không thể tái sinh cụm chết.

### D6: Tầng 2 không tính vào `model_calls`

**Chọn:** `MAX_DAILY_CHAT_CALLS` vẫn chỉ đếm lượt gọi trả lời.

**Vì sao:** bộ đếm đó canh budget của lượt gọi `gemini-2.5-flash` với prompt ~19k token. Tầng 2 là ~259
token vào + 1 token ra trên model rẻ hơn một bậc. Trộn hai đơn vị vào một bộ đếm sẽ để lượt gọi rẻ bào
mòn budget đắt — đúng cái bẫy "đơn vị budget khác nhau" đã ghi trong `CLAUDE.md`.

**Đánh đổi:** chi phí tầng 2 không hiện trong bộ đếm hiện có. Chấp nhận được ở mức $0,026/1000 câu; nếu
sau này tỉ lệ lưỡng lự tăng thì thêm cột riêng, **đừng** nhập vào `model_calls`.

### D7: Fail-safe về phía pipeline

Mọi lỗi, timeout, hay nhãn lạ của tầng 2 → `None` → đi pipeline. Câu chào lọt lưới chỉ tốn thêm một lượt
gọi; gạt nhầm câu hỏi thật thành preset mới là hỏng thật. Giữ nguyên bias fall-through của design D2 gốc.

## Risks / Trade-offs

- **Tập "lưỡng lự" phình ra theo thời gian** khi ai đó thêm cụm/token → mỗi ca thêm là +1,5s. Chặn bằng
  test ngưỡng ≤10%.
- **Phụ thuộc một model thứ hai** → thêm một điểm hỏng. Giảm nhẹ bằng D7 (fail-safe) và
  `INTENT_CLASSIFIER_ENABLED=false` để tắt hẳn.
- **`giới thiệu đi` vẫn miss** (flash-lite phán Q). Câu này thiếu chủ ngữ nên mơ hồ thật — cố ý không ép
  prompt khớp tập đo.

## Open Questions

- Có nên log riêng số lượt gọi tầng 2 để theo dõi tỉ lệ lưỡng lự trên traffic thật? Hiện chỉ có
  `logger.info`. Chờ xem tần suất thật trước khi thêm cột.
