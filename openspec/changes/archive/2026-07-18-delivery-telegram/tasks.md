# Tasks: delivery-telegram

> Không phụ thuộc Vertex key — dev/test được ngay. Thứ tự: nền tảng → transport + subscription (bot sống trước) → engine push → tích hợp. Test cục bộ bằng bot token dev + group test riêng.

## 1. Nền tảng

- [x] 1.1 Migration Alembic: bảng `subscribers` (chat_id PK, roles TEXT[], display_name, active, created_at, updated_at) và `delivery_log` (id, insight_id, chat_id, kind, sent_at, unique(insight_id, chat_id, kind))
- [x] 1.2 Config: `TELEGRAM_BOT_TOKEN`, `DELIVERY_ENABLED`, `DELIVERY_DIGEST_HOUR` (default 8, giờ VN), `DELIVERY_ALERT_INTERVAL_MINUTES` (default 5), trần alert/giờ, `DELIVERY_ALERT_LOOKBACK_HOURS` (24), `DELIVERY_DIGEST_LOOKBACK_HOURS` (48), `DASHBOARD_BASE_URL`; cập nhật `.env.example` + docker-compose env
- [x] 1.3 `ChannelAdapter` interface + `DeliveryMessage` dataclass (title, body, url, buttons?) theo pattern registry hiện có

## 2. Telegram transport

- [x] 2.1 `TelegramAdapter.send()`: gọi Bot API, HTML parse mode, escape nội dung động, split message >4096 chars
- [x] 2.2 Long-polling worker (`getUpdates`): asyncio task trong backend, tự restart với backoff, log heartbeat; không start khi thiếu token hoặc `DELIVERY_ENABLED=false`
- [x] 2.3 Router update: lệnh → handler tương ứng; callback `ask:<insight_id>`, text tự do và `/reset` → chat handler nếu có, chưa có thì phản hồi tạm "sắp ra mắt" + link dashboard
- [x] 2.4 Unit test adapter: escape ký tự đặc biệt, split message dài, build inline keyboard

## 3. Subscription

- [x] 3.1 `/start`: giới thiệu bot + hướng dẫn lệnh + upsert `subscribers` (roles=[], active=true) làm dấu "đã /start"
- [x] 3.2 `/subscribe`: inline keyboard đa chọn 9 role từ `ALLOWED_ROLES` (prompts.py — không dùng nhầm 13 `target_roles` của Source), lưu/cập nhật `subscribers`, xác nhận
- [x] 3.3 `/unsubscribe` (active=false, giữ bản ghi) và `/status` (liệt kê role + trạng thái)
- [x] 3.4 Test flow trên Telegram thật: đăng ký mới → sửa role → status → unsubscribe → subscribe lại — ✅ 18/07 @test1airadarbot: /start+/subscribe tạo subscriber (AI Engineer); /subscribe lại thêm Security → {AI Engineer, Security} không tạo bản ghi trùng; /status, /unsubscribe, /subscribe lại đều đúng; nút "Hỏi về tin này" → placeholder "sắp ra mắt" + link.

## 4. Delivery engine

- [x] 4.1 Recipient resolver: subscriber active có role giao `affected_roles`; "Toàn công ty" → mọi subscriber active
- [x] 4.2 Template render: alert (emoji urgency + title + signal + why_it_matters + link dashboard + nút "💬 Hỏi về tin này") và digest (nhóm topic, 1 dòng/insight, cap 15 + "+N tin khác") — thuần template, không gọi Gemini
- [x] 4.3 Alert job (APScheduler, mỗi 5 phút): quét insight critical có `created_at` trong lookback 24h, chưa có delivery_log; ghi log sau khi gửi; trần alert/giờ → gom tin tổng hợp
- [x] 4.4 Digest job (APScheduler, giờ config theo VN): gom insight không critical trong lookback 48h chưa gửi theo từng subscriber, bỏ qua subscriber không có tin mới, ghi delivery_log cho MỌI insight khớp (kể cả phần "+N tin khác")
- [x] 4.5 Unit test engine: recipient matching (khớp một phần, Toàn công ty), idempotent qua delivery_log, digest rỗng không gửi, cap 15
- [x] 4.6 Test chống trùng: chạy alert job 2 lần liên tiếp + restart service giữa chừng → không tin nào gửi 2 lần

## 5. Tích hợp & hoàn tất

- [x] 5.1 Test E2E local: seed insight critical giả → alert đến group test trong ≤5 phút; chạy digest tay → nhận digest đúng role — ✅ 18/07 với bot @test1airadarbot: alert tin critical TP-Link gửi `sent=1` tới subscriber khớp role Security; digest gửi `digests=1` gom 52 insight theo role AI Engineer. Dùng insight critical THẬT thay vì seed giả.
- [x] 5.2 Test kịch bản backfill: regenerate insights cũ → xác nhận không có bão alert — ✅ 18/07: seed 12 tin critical giả (nhãn ZZZ-STORM-TEST) → `run_delivery --alert` → recent(1)+todo(12)=13 > trần 10 → gom thành 1 tin tổng hợp thay vì 12 tin lẻ; delivery_log +12, dọn sạch data giả sau test (main_page về 56).
- [x] 5.3 Khớp ranh giới với `chatbot-qa`: transport expose hook đăng ký chat handler; xác nhận callback `ask:` hoạt động ở chế độ "chưa có chatbot"
- [x] 5.4 Cập nhật CLAUDE.md (env mới, lệnh bot, kiến trúc delivery) + `docs/system_overview.md`
- [x] 5.5 `openspec validate` + verify spec scenarios trước khi archive — ✅ 18/07 `openspec validate delivery-telegram --strict` PASS; scenario verify qua test thật: recipient-matching theo role, alert critical, digest gom topic, idempotency alert+digest (0 gửi lần 2/3), unique constraint 0 trùng, sửa role không tạo bản ghi trùng.
