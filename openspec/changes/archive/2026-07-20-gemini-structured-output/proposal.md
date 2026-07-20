## Why

Hình dạng JSON và các tập đóng (`action_type`, `event_type`, `content_type`…) hiện **chỉ được ép bằng
chữ trong prompt**. `GeminiClient` có đặt `response_mime_type="application/json"` nhưng **không đặt
`response_schema`** — mime type chỉ gợi ý định dạng, không ràng buộc cấu trúc. Hậu quả đo được khi chạy
438 document ngày 20/07/2026:

**1. Gate trả JSON hỏng, tần suất tăng dần và phụ thuộc nội dung**

| Vòng (50 doc) | Lỗi parse JSON của gate |
|---|---|
| 1 | 3 |
| 2 | 4 |
| 3 | 4 |
| 4 | **9** |

Lỗi luôn là `Expecting ',' delimiter`, vỡ ở vị trí khác nhau tuỳ bài (char 517 với doc này, 1308 với
doc khác) — dấu hiệu sinh JSON không ràng buộc chứ không phải lỗi cố định.

**2. Fail-open làm sai lệch chính số liệu dùng để ra quyết định**

Khi gate lỗi, code fail-open cho doc đi thẳng vào deep analysis. Đúng về mặt không mất dữ liệu, nhưng
doc đó **chưa từng được gate chấm** lại được đếm như "qua gate". Kiểm chứng: `created = (số qua gate
thật) + (số lỗi gate)` khớp cả 4 vòng.

| Vòng | Tỉ lệ qua gate **thô** | Tỉ lệ **thật** |
|---|---|---|
| 1 | 18% | 13% |
| 2 | 24% | 17% |
| 3 | 26% | 20% |
| 4 | **36%** | **22%** |

Sai lệch tới gần gấp rưỡi. Bảng tỉ lệ theo nguồn — thứ dùng để quyết định giữ/cắt nguồn — vì thế
không tin được nếu không tách phần fail-open ra.

**3. Tập đóng bị vi phạm ở nhánh deep analysis**

Lặp lại nhiều lần trong log: `Dropping recommendation for role 'Tech Lead' (invalid
action_type='assess')`. `assess` không thuộc `ALLOWED_ACTION_TYPES`. Backend bắt được và drop, nhưng
insight mất recommendation cho vai trò đó mà không ai biết ngoài dòng log.

**4. Log cắt quá ngắn để chẩn đoán**

Khi parse lỗi, code log `text[:200]` trong khi chỗ vỡ ở char 517+ — không bao giờ nhìn thấy nguyên
nhân thật, phải suy từ vị trí lỗi.

## What Changes

- Khai báo `response_schema` cho lần gọi **`gate_analyze`**, để API ép cấu trúc và enum thay vì tin
  vào chữ trong prompt.
- Đưa tập đóng `content_type` vào schema dưới dạng enum (thêm hằng số `ALLOWED_CONTENT_TYPES`, trước
  đó bị hardcode ở cả prompt lẫn `_parse_gate_response`), giữ prompt làm phần giải thích ngữ nghĩa.

> **Phạm vi thu hẹp sau khi đo (20/07/2026):** ban đầu định áp `response_schema` cho **cả hai** lần
> gọi. Đã dựng schema cho `analyze`, bật, đo 2 batch rồi **bỏ**: schema khiến model sinh
> `why_it_matters` lặp vô nghĩa tới ~6500 ký tự cho tới khi chạm `max_output_tokens` → 16/16 doc qua
> gate lỗi parse, 0 insight tạo được. Thứ nó mua (0 vi phạm `action_type`, ~2 lần/30 doc) đã được
> `_validate_recommendations` xử lý an toàn từ trước. Chi tiết + hướng đi tiếp: `measurement.md`.
- Ghi lại **số lần fail-open** để tỉ lệ qua gate còn tính đúng được về sau: thêm cột đánh dấu doc đã
  bỏ qua gate, hoặc lưu kết quả gate xuống DB.
- Nâng độ dài log raw khi parse lỗi, đủ để thấy chỗ vỡ.
- **Không** đổi ngưỡng gate, không đổi nội dung prompt về mặt tiêu chí đánh giá — chỉ đổi cách ràng
  buộc đầu ra.

## Capabilities

### New Capabilities
_(không có — siết độ tin cậy của capability hiện hữu)_

### Modified Capabilities
- `ai-analysis`: đầu ra của Gemini phải được ràng buộc bằng schema ở tầng API, không chỉ bằng prompt;
  fail-open phải để lại dấu vết phân biệt được với "qua gate thật".

## Impact

- **Code**: `backend/app/ai/gemini_client.py` (schema cho 2 lần gọi, log dài hơn),
  `backend/app/ai/prompts.py` (tập đóng dùng chung cho schema), `backend/app/services/analyzer.py`
  (đánh dấu fail-open).
- **DB**: cần một chỗ ghi dấu fail-open. Phương án rẻ nhất là cột boolean trên `raw_documents`
  (`gate_skipped`) — cần migration nhẹ. Chốt trong design.
- **Chi phí**: giảm. Mỗi lần gate lỗi hiện tốn thêm một lượt deep analysis đắt tiền; vòng 4 có 9 lượt
  như vậy trên 50 doc.
- **Rủi ro**: `response_schema` ràng buộc chặt có thể khiến model trả về giá trị rỗng thay vì đoán bừa
  — cần đo lại tỉ lệ qua gate sau khi bật, vì con số sẽ đổi (và lần này mới là con số thật).
