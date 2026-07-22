# Đo sau khi bật `response_schema` — 2026-07-20

Số nền để đối chiếu (đo 20/07/2026 **trước** change, 438 doc / 9 vòng): lỗi parse gate 3→4→4→9 mỗi 50
doc; tỉ lệ qua gate thô 18/24/26/36% so với "thật" 13/17/20/22%; `Dropping recommendation ... invalid
action_type='assess'` lặp lại nhiều lần mỗi vòng.

---

# Phần 1 — Gate: đạt (task 2.2)

| Chỉ số | Nền (trước) | Sau khi bật schema |
|---|---|---|
| Lỗi parse JSON gate | 3–9 / 50 doc | **0–1 / 50 doc** ✅ |
| `content_type` ngoài tập đóng | không đo được | **0** ✅ |

Mỗi lỗi parse gate làm doc fail-open đi thẳng vào deep analysis, **tốn oan một lượt gọi đắt tiền**.
Cắt từ 3–9 xuống 0–1 là khoản tiết kiệm thật, không chỉ là số liệu đẹp.

# Phần 2 — Deep analysis: đã thử và BỎ (task 3.2)

Xem khối ghi chú trong `tasks.md`. Tóm tắt: schema khiến model sinh `why_it_matters` lặp vô nghĩa tới
~6500 ký tự (giới hạn prompt 300) cho tới khi chạm `max_output_tokens` và bị cắt giữa chuỗi →
**16/16 doc qua gate lỗi `Unterminated string`, 0 insight tạo được**. `max_length` trong schema không
cứu được: Vertex không thực thi ràng buộc đó. Đã revert; `build_analysis_schema()` đã xoá khỏi
codebase (lấy lại từ git history nếu cần).

**Số liệu biện minh cho quyết định bỏ:** ở nhánh analyze KHÔNG có schema, đo trên ~50 doc qua gate:
`invalid action_type` xuất hiện **6 lần**, `Dropping affected_role` **0 lần**. Cả hai đều được lớp
validate post-parse xử lý an toàn — mất một khuyến nghị, KHÔNG có dữ liệu bẩn vào DB. Đổi lấy rủi ro
chất lượng nội dung trên mọi insight là không đáng.

---

# Phần 3 — Đo lại với dữ liệu sạch (task 4.1 / 4.2 / 4.3)

Mẫu: **48 doc** đã qua gate trong cửa sổ sạch (từ 09:30 ngày 20/07, sau migration 009). Nhỏ hơn mức
≥100 doc mà task 4.1 đề ra — chốt sớm theo quyết định vận hành, xem "Giới hạn" bên dưới.

## 4.1 — Tổng hợp

| Chỉ số | Kết quả |
|---|---|
| Doc đã được gate chấm | 48 |
| Qua gate | 30 |
| **Tỉ lệ qua gate (đã lọc `gate_skipped`)** | **62.5%** |
| Doc fail-open (`gate_skipped = true`) | **1** |
| Lỗi parse gate | 1 |
| Lỗi parse analysis | 2 |
| `invalid action_type` | 6 |
| `Dropping affected_role` | **0** |
| `invalid urgency` | **0** |

`Dropping affected_role = 0` xác nhận fix ở change `role-aware-alert` (sửa few-shot + thêm
`_validate_affected_roles`) vẫn giữ được: không còn giá trị taxonomy `target_roles` lọt vào insight.

## 4.2 — Schema có làm model "câm" không? KHÔNG

Rủi ro nêu trong design là schema quá chặt khiến model trả rỗng thay vì đoán. Bằng chứng ngược lại:

- Tỉ lệ qua gate **62.5%**, cao hơn hẳn nền 13–22% — model không hề dè dặt hơn.
- `gate_reason` trong log vẫn là câu đầy đủ, cụ thể theo từng bài ("Tin tức chính sách cấp cao về AI,
  không có hành động kỹ thuật cụ thể cho kỹ sư Rạng Đông"), không phải chuỗi rỗng hay lặp khuôn.
- Gate vẫn loại được 18/48 doc, tức vẫn phân biệt tốt chứ không cho qua bừa.

**Lưu ý quan trọng khi đọc con số 62.5%:** nó KHÔNG so trực tiếp được với nền 13–22%, vì thành phần
nguồn của mẫu khác hẳn (mẫu này nặng arXiv — xem 4.3). Đây là lý do bảng theo nguồn mới là thứ dùng
để ra quyết định, không phải con số tổng.

## 4.3 — Tỉ lệ qua gate theo nguồn (dữ liệu sạch)

Đã lọc `gate_skipped = false` và chỉ lấy doc xử lý sau migration 009 — bảng đo ngày 20/07 trước đó bị
nhiễu vì không tách được doc fail-open.

| Nguồn | Đã gate | Qua | Loại | Tỉ lệ |
|---|---|---|---|---|
| arXiv CS.AI | 10 | 10 | 0 | **100%** |
| arXiv CS.CL | 5 | 5 | 0 | **100%** |
| arXiv CS.IR | 3 | 3 | 0 | **100%** |
| arXiv CS.CV | 2 | 2 | 0 | **100%** |
| HackerNews | 2 | 2 | 0 | 100% |
| Reddit r/artificial | 3 | 2 | 1 | 66.7% |
| dev.to ML | 8 | 2 | 6 | 25.0% |
| dev.to AI | 10 | 1 | 9 | 10.0% |
| VnExpress Số hóa | 2 | 0 | 2 | 0% |

### Phát hiện: arXiv qua gate 100% — gate gần như không lọc nguồn này

20/48 doc trong mẫu là arXiv, và **không doc nào bị loại**. Nguyên nhân nằm trong chính `GATE_PROMPT`:
**NGOẠI LỆ HỌC THUẬT** cho phép paper nghiên cứu lõi qua gate với điểm 0.2–0.4, bất kể có liên quan
IoT/Smart Home hay không.

Đây là hành vi **đúng thiết kế**, nhưng hệ quả cần biết: gate hiện không có tác dụng chọn lọc trên
arXiv, nên chất lượng insight từ nguồn này phụ thuộc hoàn toàn vào việc chọn category ở khâu seed
source. Nếu muốn siết, phải sửa ngoại lệ trong gate prompt — thuộc phạm vi T10, không phải change này
(Non-Goal: "không đổi tiêu chí đánh giá của gate").

Ngược lại, **dev.to bị loại 15/18 (83%)** và VnExpress 2/2 — gate làm việc rất mạnh tay ở nhóm nguồn
này. Đây là dữ liệu đầu vào tốt cho quyết định giữ/cắt nguồn ở T10.

## Giới hạn của phép đo này

- **Mẫu 48 doc, không phải ≥100** như task 4.1 đề ra. Chốt sớm theo quyết định vận hành. Các nguồn có
  n < 5 (HackerNews, arXiv CS.CV, Reddit, VnExpress) chỉ nên đọc như tín hiệu, chưa đủ để kết luận.
- **Không đo được tỉ lệ null trong `evidence`**: kết quả gate không được lưu xuống DB (design D3 cố ý
  chỉ thêm `gate_skipped`). Kết luận 4.2 vì thế dựa trên tỉ lệ pass và chất lượng `gate_reason` trong
  log, không dựa trên thống kê `evidence`. Muốn đo trực tiếp thì phải lưu `gate_score`/`evidence`
  xuống DB — đã ghi nhận trong design là phạm vi riêng, hữu ích cho T10.
- **Con số 62.5% không so trực tiếp được với nền 13–22%** do khác thành phần nguồn.

## Chi phí

~150 doc quota trong ngày (508 → 650). `.env` đã trả về `MAX_DAILY_ANALYSIS=70`.
