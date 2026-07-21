## Why

Transport Telegram đã bị gỡ ngày 21/07/2026, để lại engine delivery **không có kênh nào**:
`ChannelRegistry.get("email")` (`channels/base.py:56-60`) raise ngay vì chưa adapter nào đăng ký key
`"email"`. Toàn bộ M7 Delivery hiện là code chết — insight chỉ tồn tại trên dashboard.

Change này nối lại kênh phân phối bằng Gmail, đồng thời sửa cả nhịp gửi: email 5 phút/lần (nhịp alert
cũ) là công thức chắc chắn để bị Gmail xếp spam, phá luôn kênh định kỳ.

## What Changes

- **BREAKING** — Định danh người nhận đổi từ Telegram `chat_id` (BigInteger PK) sang `email`:
  `subscribers` khoá lại bằng `id UUID`, thêm `email` UNIQUE + `unsubscribe_token`;
  `delivery_log.chat_id` → `subscriber_id UUID FK`, unique thành `(insight_id, subscriber_id, kind)`.
  Migration 010 (head hiện tại: 009). Dữ liệu hiện có: 1 subscriber test, `delivery_log` rỗng.
- **BREAKING** — Bỏ hẳn alert tức thời: xoá job 5 phút, `run_alert_cycle`, trần alert/giờ và các env
  `DELIVERY_ALERT_*`. Tiêu chí `recommendations[role].urgency = "high"` không mất đi mà được nâng
  thành **bậc 1** của bản tin định kỳ.
- Digest hàng ngày nhóm theo topic → **bản tin Thứ Hai + Thứ Năm nhóm theo vai trò**, mỗi người chỉ
  nhận phần liên quan tới role mình đăng ký, chỉ gồm tin nổi bật/ảnh hưởng cao (không phải mọi tin
  khớp role như digest cũ).
- `EmailAdapter` (SMTP + App Password) đăng ký key `"email"`; `DeliveryMessage` thêm `html_body`
  (multipart/alternative + header `List-Unsubscribe`).
- REST CRUD `/api/v1/subscribers` + **tab "Người nhận"** trên dashboard để quản lý email ↔ roles.
  Layout hiện chưa có nav tab nào nên thêm nav Insights | Người nhận.
- Dọn nợ chặn đường: xoá `backend/tests/test_bot_router.py` (import `app.bot.router` đã xoá → pytest
  lỗi collection, cả suite đang gãy); `main.py:32` hardcode `include_delivery=False` → đọc
  `settings.delivery_enabled` (hiện là config chết, không nơi nào đọc).

## Non-goals

- Không làm self-serve đăng ký, magic-link, double opt-in (`verified_at`) — để change sau.
- Không auth/RBAC trên tab quản lý người nhận: MVP chạy nội bộ, siết sau bằng
  `Depends(verify_admin_key)` đã có ở `routes/admin.py:19-23`.
- Không làm bảng `delivery_batch`: `delivery_log` unique đã đủ idempotent cho MVP; bảng audit để sau.
- Không đụng OAuth2/Gmail API/service account, không dùng n8n, không Teams.
- Không đổi cách sinh insight (gate, prompt, dedup giữ nguyên).

## Capabilities

### New Capabilities
- `gmail-transport`: gửi insight qua Gmail — `EmailAdapter` (SMTP + App Password), render HTML +
  plain-text, định danh người nhận bằng email, CRUD người nhận qua API + tab dashboard, unsubscribe.

### Modified Capabilities
- `delivery-engine`: bỏ requirement "Alert tức thời"; "Digest hàng ngày" → "Bản tin định kỳ nhóm
  theo vai trò" (Mon/Thu, chỉ tin ảnh hưởng cao); `delivery_log` đổi khoá `chat_id` →
  `subscriber_id`; bỏ nút inline "Hỏi về tin này" (khái niệm Telegram).

## Impact

- **Phase**: Phase 1 (M7 Delivery).
- **Backend**: `channels/` (thêm `email.py`), `services/delivery_engine.py`, `models/subscriber.py`,
  `models/delivery_log.py`, `repositories/subscriber_repo.py` + `delivery_log_repo.py`,
  `routes/subscribers.py` (mới), `scheduler.py`, `main.py`, `config.py`, alembic `010`.
- **Frontend**: `App.tsx`, `components/Layout.tsx`, `pages/Subscribers.tsx` (mới),
  `api/subscribers.ts` (mới); dùng lại `ROLE_DISPLAY_LABEL` trong `components/RoleBadge.tsx`.
- **Dependency mới**: `aiosmtplib`. **Env mới**: `SMTP_*`, `EMAIL_FROM*`, `PUBLIC_API_BASE_URL`.
- **Change liên quan**: `chatbot-qa` (đang mở) giả định nút `ask:` và `app.state.bot_router` — cả hai
  biến mất sau change này, cần respec.
