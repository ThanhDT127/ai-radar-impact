## Context

Chuỗi quyết định alert hiện tại hoàn toàn tất định và **không có chiều vai trò**:

```
Gemini ─► event_type ──IMPACT_LABEL_MAP──► impact_label ──_compute_urgency──► urgency
                                                                                 │
                                          list_for_delivery(critical=True) ◄─────┘
                                                    │  WHERE urgency = 'critical'
                                                    ▼
                                          roles_match(subscriber, affected_roles)
```

Chỉ `Cảnh báo bảo mật` và `Breaking Change` map tới `Nghiêm trọng` → `critical`. Mọi event_type khác
không có lối ra alert. `roles_match` chỉ kiểm giao tập vai trò — không biết tin đó quan trọng tới đâu
với từng vai trò cụ thể.

Trong khi đó `insights.recommendations` (JSONB) đã mang sẵn cấu trúc theo vai trò và phủ 100%:

```json
{
  "DevOps":    {"action_type": "test",    "note": "Thử nghiệm cấu hình aft_customization_triggers…"},
  "Security":  {"action_type": "read",    "note": "Đánh giá lại baseline bảo mật…"},
  "Tech Lead": {"action_type": "roadmap", "note": "Xem xét đưa vào chiến lược…"}
}
```

## Goals / Non-Goals

**Goals:**
- Người nhận chỉ bị ping khi tin thực sự quan trọng **với vai trò của họ**.
- Tin quan trọng với vai trò phi bảo mật có đường ra alert.
- Không migration DB, không backfill.

**Non-Goals:**
- Không sửa cột `insights.urgency` vô hướng (dashboard/sort vẫn dùng). Việc nó trùng `impact_label`
  là nợ riêng, ghi nhận nhưng không xử ở đây.
- Không đổi digest — digest vẫn gom phần còn lại theo vai trò như cũ.
- Không đụng bối cảnh công ty trong gate prompt (đó là change `widen-gate-company-context`, chưa tạo
  vì còn thiếu danh sách phòng ban).
- Không đổi `IMPACT_LABEL_MAP` hay `_compute_urgency`.

## Decisions

**D1 — Nhét `urgency` vào `recommendations` thay vì tạo bảng/cột mới.**
`recommendations` đã là JSONB có khoá theo vai trò và phủ 100%. Thêm một khoá con là thay đổi không
migration, không đụng schema, và giữ mọi thông tin theo-vai-trò ở cùng một chỗ.
*Alternatives:* (a) cột `urgency_by_role` JSONB riêng — tách đôi thông tin cùng bản chất, không lợi
gì; (b) bảng `insight_role_urgency` — đúng chuẩn quan hệ nhưng thêm join vào đường nóng của delivery
để đổi lấy một giá trị enum, không đáng.

**D2 — Tập đóng `high | medium | low`, KHÔNG tái dùng 4 mức của `urgency` vô hướng.**
Cố ý dùng tập khác để không ai nhầm hai khái niệm: `insights.urgency` là "mức ảnh hưởng của tin nói
chung", còn `recommendations[role].urgency` là "mức ảnh hưởng tới riêng vai trò này". Bỏ `critical`
vì ngữ nghĩa alert đã được phát biểu lại là "đáng đọc ngay", không phải "khẩn cấp vá ngay".

**D3 — Ngưỡng alert = `high`.** Chỉ `high` mới bắn alert; `medium`/`low` rơi vào digest. Giữ một ngưỡng
duy nhất, dễ giải thích và dễ chỉnh nếu thực tế lệch.

**D4 — Thiếu khoá `urgency` ⇒ coi như `medium` (không alert).**
Insight cũ (90 cái) không có khoá này. Mặc định "không alert" đảm bảo bật change lên không gây bão
alert hồi tố. Đây cũng là hành vi an toàn khi Gemini trả thiếu trường.

**D5 — Không suy `urgency` từ `action_type`.**
Từng cân nhắc map `test/PoC → high`, `read → medium`, `watch/roadmap → low` để khỏi đụng prompt.
Bỏ, vì `action_type` trả lời "làm gì", không trả lời "gấp tới đâu" — một `read` hoàn toàn có thể
khẩn. Suy diễn như vậy sẽ tạo tương quan giả và khó gỡ về sau.

**D6 — Người nhận phải có vai trò xuất hiện trong `recommendations`, không chỉ trong `affected_roles`.**
Ngưỡng lọc mới đọc `recommendations[role]`. Nếu vai trò có trong `affected_roles` nhưng vắng trong
`recommendations` thì coi như không đủ tín hiệu ⇒ không alert (rơi về digest).

## Risks / Trade-offs

- **[Gemini chấm `high` rộng tay ⇒ spam alert]** → hướng dẫn prompt nêu rõ tiêu chí và yêu cầu tiết
  kiệm; trần `DELIVERY_MAX_ALERTS_PER_HOUR` hiện có vẫn là lưới an toàn; nghiệm thu bằng cách đo tỉ lệ
  `high` trên một mẫu thật trước khi coi là xong.
- **[Ngược lại: chấm quá chặt ⇒ không còn alert nào]** → cùng phép đo ở trên bắt được cả hai chiều.
- **[Hai khái niệm urgency dễ gây nhầm cho người đọc code]** → D2 chọn tập giá trị khác nhau; thêm
  ghi chú vào `CLAUDE.md`.
- **[Insight cũ im lặng vĩnh viễn]** → chấp nhận. Chúng đã quá cửa sổ lookback (24h) nên không alert
  được nữa dù có backfill.

## Migration Plan

Không migration. Thứ tự triển khai: sửa prompt + validate trước (insight mới bắt đầu có dữ liệu), rồi
mới đổi điều kiện chọn người nhận. Làm ngược lại sẽ có giai đoạn không insight nào đủ điều kiện alert.
Rollback = revert commit; dữ liệu `recommendations` thừa khoá `urgency` vô hại với code cũ.

## Open Questions

- Ngưỡng `high` có đúng không, hay cần cả `medium` cho một số vai trò? Chỉ trả lời được sau khi đo
  phân bố thực tế trên mẫu — đưa vào task nghiệm thu.
- Có nên cho người dùng tự chọn ngưỡng nhận alert theo vai trò của họ (subscriber preference) không?
  Ngoài phạm vi change này, ghi lại để cân nhắc sau.
