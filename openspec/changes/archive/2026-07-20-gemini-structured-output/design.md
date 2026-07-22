## Context

`GeminiClient` gọi Gemini hai lần cho mỗi document:

```
raw_doc ──► gate_analyze()  ──┬── pass_gate=false ──► low_signal (dừng, rẻ)
                              ├── pass_gate=true  ──► analyze() ──► Insight
                              └── LỖI PARSE ───────► analyze()  ──► Insight   ◄── fail-open
                                                                      ▲
                                        không phân biệt được với nhánh "pass_gate=true"
```

Cả hai lần gọi đều đặt `response_mime_type="application/json"` nhưng không có `response_schema`
(`gemini_client.py:85` và `:152`). Parse bằng `json.loads` trần, lỗi thì trả `GateResult(pass_gate=True,
error=...)` — fail-open.

Fail-open là quyết định đúng (không mất nội dung vì lỗi tạm thời), nhưng nó **không để lại dấu vết**
trong DB. `raw_documents.processing_status` chỉ có `analyzed`, nên doc bỏ qua gate trông y hệt doc
qua gate thật.

## Goals / Non-Goals

**Goals:**
- Gemini không còn trả JSON hỏng hoặc giá trị ngoài tập đóng.
- Phân biệt được "qua gate thật" với "bỏ qua gate do lỗi", để tỉ lệ theo nguồn tin được.
- Giữ nguyên fail-open — không đánh đổi tính sẵn sàng lấy tính chặt chẽ.

**Non-Goals:**
- Không đổi tiêu chí đánh giá của gate (ngưỡng 0.4, bối cảnh công ty, các ngoại lệ). Đó là change
  `widen-gate-company-context`, chưa mở.
- Không đổi `IMPACT_LABEL_MAP`, `_compute_urgency`, hay logic delivery.
- Không thêm retry khi parse lỗi — schema nên loại bỏ phần lớn nguyên nhân; retry là bước sau nếu
  vẫn còn lỗi.

## Decisions

**D1 — Dùng `response_schema` của google-genai, không tự viết bộ sửa JSON.**
Từng cân nhắc dùng thư viện kiểu `json_repair` để vá đầu ra hỏng. Bỏ: nó chữa triệu chứng, và một
JSON "sửa được" vẫn có thể sai ngữ nghĩa (mất phần tử, ghép nhầm chuỗi). Ràng buộc ở tầng API ngăn
lỗi phát sinh ngay từ đầu, đồng thời ép luôn enum cho các tập đóng — giải quyết cả lỗi `action_type='assess'`.

**D2 — Tập đóng khai báo một lần trong `prompts.py`, schema dựng từ đó.**
Hiện các tập đóng đã nằm ở `prompts.py` (`ALLOWED_ACTION_TYPES`, `ALLOWED_EVENT_TYPES`, …). Schema
phải sinh từ chính các hằng số đó, không chép tay — nếu không sẽ trôi khỏi nhau, đúng kiểu drift đã
xảy ra giữa `CLAUDE.md` và `prompts.py`.

**D3 — Đánh dấu fail-open bằng cột boolean trên `raw_documents`, không lưu toàn bộ kết quả gate.**
Nhu cầu trước mắt chỉ là *tách* doc bỏ qua gate ra khỏi thống kê. Một cột `gate_skipped BOOLEAN
DEFAULT false` đủ, migration nhẹ, truy vấn đơn giản.
*Alternative:* lưu cả `gate_score`/`gate_reason`/`evidence` xuống DB — giá trị cao hơn nhiều cho việc
đánh giá gate (T10 của W4), nhưng là phạm vi riêng. Ghi nhận, không làm ở đây.

**D4 — Giữ fail-open, không đổi thành fail-closed.**
Lỗi parse không phải bằng chứng nội dung xấu. Chuyển sang fail-closed sẽ âm thầm vứt nội dung tốt —
đắt hơn nhiều so với việc tốn thêm một lượt deep analysis.

**D5 — Nâng log raw lên đủ dài để thấy chỗ vỡ (đề xuất 2000 ký tự), chỉ ở nhánh lỗi.**
Chỗ vỡ quan sát được ở char 517 và 1308; `text[:200]` không bao giờ chạm tới. Chỉ log dài ở nhánh
exception nên không ảnh hưởng khối lượng log lúc chạy bình thường.

## Risks / Trade-offs

- **[Schema quá chặt ⇒ model trả rỗng thay vì đoán]** → sau khi bật, đo lại phân bố `pass_gate` và tỉ
  lệ trường null trên mẫu thật; so với số liệu nền đã có (13/17/20/22%).
- **[Số liệu tỉ lệ qua gate sẽ đổi sau change]** → đó là mục đích. Cần nói rõ trong tài liệu rằng số
  trước và sau change không so trực tiếp được.
- **[Migration thêm cột]** → nhỏ, có default, không backfill. Doc cũ mang `false`, tức bị coi như "qua
  gate thật" — sai với các doc đã fail-open trước đây. Chấp nhận: không truy ngược được, và ghi chú
  rằng thống kê trước 20/07 có nhiễu.

## Migration Plan

1. Thêm cột `gate_skipped` (migration Alembic, default false, nullable=false).
2. Bật `response_schema` cho `gate_analyze` trước, đo trên mẫu nhỏ.
3. Bật cho `analyze` sau khi gate ổn định.
Rollback: revert commit; cột thừa vô hại.

## Open Questions

- Có nên lưu luôn `gate_score`/`gate_reason` xuống DB trong cùng change này không? Nó là tiền đề cho
  T10 (đánh giá độ chính xác gate) của W4. Tách riêng cho gọn, nhưng làm cùng lúc thì đỡ một lần
  migration.
- Sau khi có schema, phần hướng dẫn định dạng JSON trong prompt có còn cần không, hay rút gọn được để
  tiết kiệm token?
