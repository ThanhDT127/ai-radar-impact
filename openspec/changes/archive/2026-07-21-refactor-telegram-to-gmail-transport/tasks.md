## 1. Dọn nợ chặn đường

- [x] 1.1 Xoá `backend/tests/test_bot_router.py` (import `app.bot.router` đã bị gỡ → pytest lỗi collection, cả suite đang gãy); chạy `pytest` xác nhận suite thu thập được
- [x] 1.2 Sửa `main.py:32` truyền `include_delivery=settings.delivery_enabled` thay cho `False` hardcode; mặc định `DELIVERY_ENABLED=false`
- [x] 1.3 Dọn `.env.example`: xoá `TELEGRAM_BOT_TOKEN` còn sót, thêm `DASHBOARD_BASE_URL`

## 2. Schema (migration 010)

- [x] 2.1 Sửa `models/subscriber.py`: bỏ `chat_id`, thêm `id UUID PK`, `email VARCHAR(320)` unique, `unsubscribe_token VARCHAR(64)` unique; giữ `roles[]`, `display_name`, `active`
- [x] 2.2 Sửa `models/delivery_log.py`: `chat_id` → `subscriber_id UUID FK subscribers(id) ON DELETE CASCADE`, unique `(insight_id, subscriber_id, kind)`, `kind` → `String(16)`
- [x] 2.3 Viết migration `alembic/versions/010_*.py` (head hiện tại `009`) gồm cả `downgrade()`; xoá bản ghi subscriber test trong bước upgrade
- [x] 2.4 Chạy `alembic upgrade head` rồi `alembic downgrade -1` rồi upgrade lại — xác nhận cả hai chiều chạy sạch
- [x] 2.5 Cập nhật `repositories/subscriber_repo.py`: `list_active()` lọc `active AND roles <> '{}'`, thêm `get_by_email`, `get_by_unsubscribe_token`, CRUD; `repositories/delivery_log_repo.py` đổi `chat_id` → `subscriber_id`

## 3. EmailAdapter

- [x] 3.1 Thêm `aiosmtplib` vào `backend/requirements.txt`
- [x] 3.2 Thêm config SMTP vào `config.py` + `.env.example`: `SMTP_HOST/PORT/USER/PASSWORD`, `EMAIL_FROM`, `EMAIL_FROM_NAME`, `EMAIL_REPLY_TO`, `PUBLIC_API_BASE_URL`
- [x] 3.3 Thêm hook no-op `async def open()` / `async def close()` vào `ChannelAdapter` (`channels/base.py`); engine gọi bao quanh mỗi run
- [x] 3.4 Thêm `html_body: str | None` vào `DeliveryMessage`
- [x] 3.5 Viết `channels/email.py::EmailAdapter` (`channel_type = "email"`): STARTTLS, một email/một địa chỉ `To:` (không BCC), `multipart/alternative`, header `List-Unsubscribe` + `List-Unsubscribe-Post`; đăng ký vào `ChannelRegistry`
- [x] 3.6 Trả kết quả thất bại khi SMTP lỗi (không raise) để engine không ghi `delivery_log`
- [x] 3.7 Test gửi thật một email tới hộp thư của bạn bằng script tạm — xác nhận không rơi spam

## 4. Render bản tin

- [x] 4.1 Viết `channels/email_templates.py` trả `(subject, text_body, html_body)` bằng f-string; HTML dùng CSS inline + layout `<table>`
- [x] 4.2 Dùng lại `display_title()` và `shorten()` trong `delivery_engine.py` cho tiêu đề tin (luật khớp dashboard)
- [x] 4.3 Render card chi tiết mỗi tin: tiêu đề đầy đủ **không cắt**, badge `impact_label`/`intelligence_tier`/`adoption_ring` + `practical_indicators`, `signal`, `so_what`, `why_it_matters`, `summary_medium`, khuyến nghị đúng vai trò (`action_type` + `note`), `risks`, link `{DASHBOARD_BASE_URL}/insights/{id}`; bỏ trường thiếu, không render placeholder
- [x] 4.4 Dựng subject từ tiêu đề tin xếp hạng cao nhất + "+N tin khác", cắt ở ranh giới từ, không viết HOA toàn bộ
- [x] 4.5 Thêm footer: link hủy nhận (`PUBLIC_API_BASE_URL`) + một dòng giải thích vì sao nhận được mail
- [x] 4.6 Bỏ nút inline "Hỏi về tin này" (`MessageButton(callback_data="ask:...")`)
- [x] 4.7 Unit test render: tiêu đề tiếng Anh → dùng `summary_short`; tiêu đề tiếng Việt → giữ `title`; tiêu đề >110 ký tự không bị cắt trong thân email; insight thiếu `so_what`/`risks` không sinh nhãn rỗng; bản plain-text đọc được độc lập

## 5. Engine — bản tin định kỳ theo vai trò

- [x] 5.1 Viết `score_for_role(insight, role)` theo thứ tự ưu tiên: `recommendations[role].urgency` (high>medium>low, thiếu khoá → medium) → `impact_label` → có `practical_indicators` cụ thể → `actionability_score` → `intelligence_tier == "Strategic"` → `trust_score` → `published_at`; dùng lại `alert_roles_match`/`matched_alert_roles` (`delivery_engine.py:88-120`) cho phần đọc urgency thay vì viết lại
- [x] 5.2 Xếp hạng **mọi** tin khớp vai trò rồi lấy top-N (không lọc ngưỡng): `DELIVERY_MAX_ITEMS_PER_ROLE` (2) và `DELIVERY_MAX_ITEMS_PER_EMAIL` (3) — trần email áp lên tổng, không cộng dồn theo số vai trò
- [x] 5.3 Sắp thứ tự hiển thị từ khẩn cấp cao xuống thấp: tin trong section giảm dần theo điểm, section vai trò sắp theo tin đứng đầu của mình; tin số 1 của email là tin khẩn cấp nhất toàn email
- [x] 5.4 Tin khớp nhiều vai trò của cùng một người chỉ render một lần, ở vai trò có điểm cao hơn
- [x] 5.5 Ghi `delivery_log` **chỉ cho tin thực sự gửi** (bỏ luật cũ "ghi cả phần vượt cap"), và chỉ khi adapter báo gửi OK; phần dư ghi "+N tin khác" + link dashboard
- [x] 5.6 Test bằng dữ liệu thật: vai trò `Security` (26 tin `high` trong 108h) chỉ ra 2 tin; vai trò `Data Scientist` (0 tin `high`, 29 tin khớp) vẫn ra 2 tin
- [x] 5.7 Không có tin → không gửi email rỗng
- [x] 5.8 Mask email trong log (`ab***@domain`) thay cho log định danh trần
- [x] 5.10 Chốt chặn chu kỳ `sent_within()` + cờ `--force`: unique constraint chỉ chặn gửi lại CÙNG một tin, không chặn được lần chạy thừa lấy lô kế tiếp (phát hiện khi chạy thật 21/07)
- [x] 5.9 Xoá `run_alert_cycle`, `_alert_subscriber`, `render_alert`, `render_alert_summary`, `count_alerts_last_hour` và các env `DELIVERY_ALERT_*`, `DELIVERY_MAX_ALERTS_PER_HOUR`

## 6. Scheduler & CLI

- [x] 6.1 Xoá job alert 5 phút trong `scheduler.py`; đăng ký cron `day_of_week="mon,thu"` giờ `DELIVERY_DIGEST_HOUR` với `timezone=Asia/Ho_Chi_Minh`
- [x] 6.5 Test `tests/test_scheduler_delivery_job.py` khoá cấu hình cron: là CronTrigger không phải IntervalTrigger, `day` để `*` (không rơi bẫy day-of-month), timezone VN, không còn job alert
- [x] 6.2 Đổi mặc định `DELIVERY_DIGEST_LOOKBACK_HOURS` 48 → 108
- [x] 6.3 Viết lại `app/scripts/run_delivery.py` với `--dry-run` (in ra nội dung, không gửi, không ghi log) và `--send`
- [x] 6.4 Chạy `--dry-run` trên dữ liệu thật một kỳ; đối chiếu số tin/vai trò với cap để chỉnh nếu lệch

## 7. API quản lý người nhận

- [x] 7.1 Viết `schemas/subscriber.py` (Create/Update/ListItem), validate `roles ⊆ ALLOWED_ROLES` từ `ai/prompts.py`, normalize email lowercase
- [x] 7.2 Viết `routes/subscribers.py`: GET list, POST, PATCH `{id}`, DELETE `{id}` — **không** gắn `verify_admin_key`; đăng ký router trong `main.py`
- [x] 7.3 Viết `GET`/`POST /api/v1/unsubscribe?token=` — GET trả trang xác nhận HTML tối giản, POST đặt `active=false` trả 200; token sai → 404
- [x] 7.4 Test tự động `tests/test_subscribers_api.py` (18 test): email trùng khác hoa thường → 409; role ngoài tập đóng + taxonomy phòng ban → từ chối; token sai → 404; hủy nhận đặt active=false mà không xoá bản ghi

## 8. Tab "Người nhận" trên dashboard

- [x] 8.1 Viết `frontend/src/api/subscribers.ts` (không gọi axios trực tiếp trong component)
- [x] 8.2 Thêm nav 2 tab **Insights | Người nhận** vào `components/Layout.tsx` + `styles/layout.module.css` (hiện chưa có nav nào); highlight tab đang mở
- [x] 8.3 Thêm route `/subscribers` vào `App.tsx`
- [x] 8.4 Viết `pages/Subscribers.tsx`: bảng danh sách + form thêm (email, chọn nhiều vai trò, tên) + toggle `active` + xoá, dùng TanStack Query mutations
- [x] 8.5 Dùng lại `ROLE_DISPLAY_LABEL` trong `components/RoleBadge.tsx` cho nhãn 9 vai trò — không hardcode danh sách mới
- [x] 8.6 Hiển thị chú ý cho `Data Analyst` và `Người dùng phổ thông` (hiện chưa có insight nào gắn 2 vai trò này)
- [x] 8.7 `npm run build` chạy sạch (tsc + vite)

## 9. Kiểm chứng end-to-end

- [x] 9.1 Thêm 2 người nhận với vai trò khác nhau qua tab, chạy `run_delivery --send`, xác nhận mỗi người nhận đúng phần vai trò của mình
- [x] 9.2 Chạy lại `--send` ngay sau đó — xác nhận không ai nhận email thứ hai (`delivery_log` chặn)
- [x] 9.3 Bấm link hủy nhận trong email thật → `active=false`, kỳ sau không nhận
- [x] 9.4 Chạy toàn bộ `pytest` xanh; xoá script tạm ở 3.7
