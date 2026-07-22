# Proposal: delivery-telegram

**Phase áp dụng:** Phase 1→2 (M7 Delivery Module — kênh chat bot thay cho email/Teams webhook do ràng buộc môi trường: chưa deploy prod, Telegram long-polling chạy được hoàn toàn local).

## Why

Hệ thống hiện tại "câm": insight được curate nhưng không ai được báo — user phải tự mở dashboard. BRD yêu cầu phân phối chủ động đúng người/đúng lúc (digest cho tin thường, alert cho tin critical); task hiện tại yêu cầu cụ thể kênh bot trên ứng dụng chat (Telegram, Zalo…). Telegram Bot API là kênh khả thi duy nhất với ràng buộc hiện tại: long-polling không cần webhook public, token free, chạy trong docker-compose local.

## What Changes

- **Delivery Engine** (push, rule-based) đọc insight mới từ repository và quyết định gửi theo nguyên tắc BRD "không spam":
  - **Alert tức thời**: insight có `urgency = critical` (vd. Cảnh báo bảo mật) gửi ngay khi xuất hiện.
  - **Digest hàng ngày**: các insight còn lại gom thành 1 bản tin buổi sáng (giờ cấu hình được), nhóm theo topic/urgency.
  - Format message Telegram (title, signal, why_it_matters, link về dashboard) — insight fields đã đủ, không gọi thêm Gemini.
- **Subscription cá nhân theo role**: bảng `subscribers` (`chat_id`, `roles[]`, trạng thái); flow đăng ký qua bot: `/start` → `/subscribe` chọn role (từ 9 `ALLOWED_ROLES`: AI Engineer, Dev, Security, Data Analyst…) → nhận tin lọc theo `affected_roles` giao với roles đã đăng ký; `/unsubscribe`, `/status`.
- **Channel Adapter interface**: trừu tượng hóa kênh gửi (pattern tương tự `ConnectorRegistry` ở tầng ingest) — Telegram là adapter đầu tiên; Zalo/Teams cắm sau không sửa Delivery Engine.
- **Telegram bot transport**: worker long-polling chạy trong backend container (hoặc service riêng trong docker-compose), nhận update (message, callback) và route: lệnh subscribe → subscription flow; tin nhắn tự do + callback "Hỏi về tin này" → chuyển cho `chat-telegram-surface` (change `chatbot-qa`).
- **Nút inline "💬 Hỏi về tin này"** đính kèm mỗi tin push — cầu nối sang chatbot chế độ B, khép vòng "bot báo tin → người đọc hỏi ngay tại chỗ".
- **Delivery log**: bảng ghi lại đã gửi gì cho ai lúc nào — chống gửi trùng, phục vụ audit.

## Capabilities

### New Capabilities
- `delivery-engine`: rule digest/alert, chọn recipient theo role, format message, delivery log chống trùng.
- `telegram-bot-transport`: long-polling worker, gửi/nhận message, inline keyboard, routing update cho các consumer (subscription, chat).
- `delivery-subscription`: đăng ký/hủy nhận tin theo role qua lệnh bot, lưu `subscribers`.

### Modified Capabilities
_(không có — không đổi requirement của capability hiện hữu)_

## Non-goals

- **Không** Zalo trong change này — Zalo OA cần đăng ký doanh nghiệp + webhook HTTPS public, không chạy local được; chờ xác nhận mentor. Adapter interface bảo đảm cắm sau không đập lại.
- **Không** email/Teams/n8n — kênh theo BRD gốc nhưng ngoài phạm vi task hiện tại; adapter interface chừa chỗ.
- **Không** delivery rule engine cấu hình qua Admin UI — v1 rule đơn giản (critical→alert, còn lại→digest) đặt trong config; UI config là bước sau khi rule ổn định.
- **Không** nút "gửi insight này" thủ công trên web UI — add-on rẻ, để sau khi có adapter (chỉ là 1 nút gọi cùng đường gửi).
- **Không** cá nhân hóa nội dung bằng AI (digest tóm tắt riêng cho từng người) — format thuần template từ fields có sẵn, $0 chi phí Gemini.

## Dependencies

- **`chatbot-qa`**: consumer của `telegram-bot-transport` cho phần Q&A; nút inline "Hỏi về tin này" trỏ sang `chat-telegram-surface`. Delivery Engine + subscription hoạt động độc lập được nếu chatbot chưa xong (nút inline ẩn hoặc link về dashboard).
- **Insight schema v2/v3**: dùng `signal`, `why_it_matters`, `urgency`, `affected_roles` — đã có sẵn.
- **Không phụ thuộc Vertex AI key** — delivery thuần rule + template, có thể dev/test ngay trong khi chờ key (khác với `chatbot-qa`).

## Impact

- **Backend**: mới `services/delivery_engine.py`, `channels/` (adapter interface + `TelegramAdapter`), worker long-polling, scheduler job digest (APScheduler đã có trong stack); bảng mới `subscribers`, `delivery_log` (+ migration Alembic).
- **Docker Compose**: env `TELEGRAM_BOT_TOKEN`; có thể thêm service `bot-worker` hoặc chạy chung backend process.
- **Chi phí vận hành**: $0 phía Telegram (API free); $0 Gemini (không gọi AI); rủi ro chính là spam — delivery log + rule digest là chốt chặn.
