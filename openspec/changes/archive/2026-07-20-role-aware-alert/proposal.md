## Why

Alert Telegram hiện chỉ bắn khi `urgency = critical`. Nhưng `urgency` được suy ra tất định từ
`event_type`, và **chỉ hai** event_type chạm được mức `Nghiêm trọng` → `critical`: `Cảnh báo bảo mật`
và `Breaking Change`. Đo trên DB (20/07/2026): **10/10 insight critical đều là `Cảnh báo bảo mật`**.

Hệ thống vì thế đang đo **loại tin**, không đo **mức ảnh hưởng tới vai trò người nhận**. Hai hậu quả
ngược chiều nhau:

- **Gửi thừa:** người trong `affected_roles` bị ping cả khi tin không phải việc của họ. Ví dụ thật:
  *"New Windows LegacyHive zero-day"* gán `[Security, Tech Lead, Dev]` — Dev nhận alert cho một lỗ hổng
  họ không vá được.
- **Gửi thiếu:** tin thực sự quan trọng với vai trò khác **không bao giờ** alert được. Một model
  release lớn (`Phát hành mới` → `Trung bình`) rất đáng đọc ngay với AI Engineer, nhưng theo chuỗi hiện
  tại nó vĩnh viễn không chạm ngưỡng.

Ngữ nghĩa alert cũng cần phát biểu lại cho đúng thực tế mong muốn: alert **không phải** "khẩn cấp, vá
ngay" mà là **"tin có ảnh hưởng lớn tới vai trò của bạn, đáng đọc ngay"**.

Điểm mấu chốt khiến thay đổi này rẻ: chiều theo-vai-trò **đã tồn tại** trong cột `insights.recommendations`
(JSONB `{role: {action_type, note}}`) và đang được phủ **100%** (90/90 insight published, 221 cặp
vai-trò–hành động). Gemini vốn đã phân biệt: cùng một tin, `DevOps → test`, `Tech Lead → roadmap`.
Chưa ai dùng tín hiệu đó để quyết định gửi.

## What Changes

- **Ngữ nghĩa alert đổi:** từ "insight critical" sang "insight có ảnh hưởng cao **với vai trò người
  nhận**". Digest giữ nguyên vai trò gom phần còn lại.
- `recommendations` thêm khoá `urgency` cho mỗi vai trò: `{role: {action_type, note, urgency}}`.
  JSONB nên **không cần migration**.
- Prompt phân tích yêu cầu Gemini chấm `urgency` riêng cho từng vai trò trong `affected_roles`, theo
  tập đóng `high | medium | low`.
- `list_for_delivery` / `DeliveryEngine` chọn người nhận alert theo `recommendations[role].urgency`
  thay vì lọc `Insight.urgency == 'critical'` toàn cục.
- Backfill: insight cũ chưa có `urgency` trong `recommendations` được coi như `medium` (không alert),
  tránh bắn hàng loạt alert hồi tố.
- **Không** đụng cột `insights.urgency` vô hướng — nó vẫn phục vụ dashboard/sort. Việc nó trùng lặp
  `impact_label` là vấn đề riêng, ngoài phạm vi change này.

## Capabilities

### New Capabilities
_(không có — siết ngữ nghĩa của capability hiện hữu)_

### Modified Capabilities
- `delivery-engine`: điều kiện chọn insight để alert và điều kiện chọn người nhận đổi từ "urgency
  toàn cục = critical" sang "urgency của chính vai trò người nhận đủ cao".
- `ai-analysis`: prompt phải sinh thêm `urgency` cho từng vai trò trong `recommendations`; backend
  validate giá trị thuộc tập đóng.

## Impact

- **Code**: `backend/app/ai/prompts.py` (prompt + tập đóng mới), `backend/app/services/analyzer.py`
  (validate `recommendations`), `backend/app/repositories/insight_repo.py` (`list_for_delivery`),
  `backend/app/services/delivery_engine.py` (chọn người nhận).
- **DB**: không migration (JSONB). Không backfill dữ liệu — insight cũ mặc định không alert.
- **Vận hành**: lượng alert sẽ thay đổi cả chiều tăng lẫn giảm. Cần theo dõi vài ngày đầu; nếu tăng
  đột biến thì trần alert/giờ hiện có (`DELIVERY_MAX_ALERTS_PER_HOUR`) vẫn là lưới an toàn.
- **Rủi ro**: Gemini chấm `urgency` rộng tay → spam alert. Giảm thiểu bằng hướng dẫn prompt nghiêm
  ngặt + trần alert/giờ + đo thực tế trước khi bật rộng.
