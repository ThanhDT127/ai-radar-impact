# Đo phân bố `recommendations[role].urgency` — task 2.1 / 2.2

**Ngày đo:** 2026-07-20 · **Mẫu:** 30 raw_document `analyzed` mới nhất, gọi Gemini thật với prompt
mới · **Cách đo:** script thuần đọc, không ghi DB (đã xoá sau khi đo).

## Phân bố trên từng cặp vai-trò–khuyến-nghị

| urgency | Số cặp | Tỉ lệ |
|---|---|---|
| high | 4 | **4.8%** |
| medium | 49 | 59.0% |
| low | 30 | 36.1% |
| **Tổng** | **83** | |

## Theo vai trò

| Vai trò | high | medium | low |
|---|---|---|---|
| AI Engineer | 2 | 19 | 4 |
| Tech Lead | 0 | 10 | 13 |
| Dev | 0 | 12 | 11 |
| Security | 2 | 6 | 1 |
| Data Scientist | 0 | 2 | 1 |

**Doc có ≥1 vai trò `high`: 4/30 (13%)**

## Kiểm tra chất lượng đầu ra

| Chỉ số | Kết quả |
|---|---|
| Entry Gemini trả thiếu khoá `urgency` | **0** |
| Lỗi parse/analyze | **0** |
| Role ngoài `ALLOWED_ROLES` | **không có** |

Hai chỉ số cuối xác nhận task 1.4: trước khi sửa few-shot, DB thật có 8 insight mang
`affected_roles = DevOps` (giá trị của taxonomy `target_roles`). Sau khi sửa, 30/30 doc không còn
giá trị ngoài tập đóng.

Vẫn còn 2 lần `Dropping recommendation for role 'Tech Lead' (invalid action_type='Assess'/'assess')`
— đây là vấn đề của change `gemini-structured-output` (ràng buộc enum ở tầng API), ngoài phạm vi
change này.

## Kết luận gate (task 2.2) — ĐẠT, giữ ngưỡng `high`

**Không spam.** 13% doc có ≥1 vai trò `high`, xấp xỉ tỉ lệ alert hiện hành (10/90 = 11% insight
`critical`). Lượng alert giữ nguyên bậc độ lớn, nên không cần đụng `DELIVERY_MAX_ALERTS_PER_HOUR`.

**Không câm.** `high` phân bố đúng chỗ mong đợi và **đã mở đường cho vai trò phi bảo mật**: AI
Engineer nhận 2 `high` — điều mà chuỗi cũ (`Cảnh báo bảo mật` → `critical`) vĩnh viễn không tạo được.
Đây chính là "gửi thiếu" mà proposal nêu.

**Chấm có phân biệt, không tràn lan.** AI Engineer 2 `high` / 25 entry; Security 2 / 9. Tech Lead và
Dev **0 `high`** trên toàn mẫu — hợp lý vì đây là vai trò rộng, ít khi một tin đơn lẻ buộc họ đọc
ngay. Cần theo dõi: subscriber chỉ chọn Tech Lead hoặc Dev có thể nhận rất ít alert (vẫn nhận digest).
Mẫu 30 doc không chứa breaking-change/sự cố lớn — loại tin sẽ đẩy hai vai trò này lên `high`.

→ **Được phép làm nhóm 3.**

---

# Nghiệm thu trên dữ liệu thật (nhóm 4)

Sau khi triển khai nhóm 3: ingest 240 doc mới → `run_analysis` 1 batch → **16 insight mới,
16/16 mang khoá `urgency`**, 7 cái có ≥1 vai trò `high`.

Subscriber thật: 1 người, roles `{AI Engineer, Security}`.

| Bước | Kết quả |
|---|---|
| `run_delivery --alert` (insight cũ, trước khi có dữ liệu mới) | `sent=0` — không alert hồi tố (4.2) |
| `run_delivery --alert` (sau khi có insight mới) | **5 alert**, Telegram 200 |
| Đối chiếu 5 tin đã alert với DB | 5/5 có `AI Engineer` hoặc `Security` = `high` (4.1) |
| `run_delivery --digest` | 1 digest, Telegram 200 |
| Trùng alert↔digest, insight mới | **0** |
| Trùng alert↔digest, insight cũ | 13 → đã vá (xem dưới) |

## Bằng chứng change giải đúng vấn đề "gửi thiếu"

5 tin được alert có `insights.urgency` lần lượt là `low`, `low`, `low`, `low`, `medium` — **không cái
nào `critical`**. Dưới luật cũ (`urgency == 'critical'`) chúng vĩnh viễn không thể alert. Nay chúng
alert được vì Gemini chấm `AI Engineer`/`Security` ở mức `high` cho từng tin.

Ngược lại, các tin `Cảnh báo bảo mật` cũ (`urgency=critical`, không có role urgency) **không** alert
nữa — đúng thiết kế D4.

## Vấn đề phát hiện khi nghiệm thu và cách vá

13 insight cũ từng được alert theo luật `critical` đã lọt vào digest: chúng không có role urgency nên
`alert_roles_match` trả False, mà bộ lọc digest chỉ dựa vào đó. Đây là hiện tượng **chuyển đổi một
lần**, nhưng vẫn là gửi trùng với người dùng.

Đã vá: `run_digest` truy vấn thêm `delivery_log kind='alert'` và loại các insight đã alert cho chính
subscriber đó (test `test_digest_skips_insight_already_alerted_under_old_rule`). Digest đã gửi trước
khi vá vẫn chứa 13 tin này; các chu kỳ sau không tái diễn.
