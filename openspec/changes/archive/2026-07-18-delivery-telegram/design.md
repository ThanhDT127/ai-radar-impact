# Design: delivery-telegram

## Context

Hệ thống chưa có bất kỳ cơ chế phân phối chủ động nào — insight chỉ xem được qua dashboard. BRD/architecture định nghĩa M7 Delivery (digest/alert theo rule, "không spam") nhưng kênh email/Teams/n8n chưa khả thi với ràng buộc hiện tại: **chưa deploy prod, toàn bộ chạy docker-compose local**. Telegram Bot API là kênh duy nhất thỏa mãn: long-polling (không cần webhook public/domain), token free, thư viện Python trưởng thành.

Hiện trạng tận dụng được:
- Insight fields v2/v3 (`signal`, `why_it_matters`, `urgency`, `affected_roles`) đủ để format message đẹp **không cần gọi Gemini**.
- APScheduler đã trong stack (scheduled ingestion) — digest job cắm vào cùng cơ chế.
- Pattern registry (`ConnectorRegistry`) tái dùng cho channel adapter.

**Module ảnh hưởng:** M7 Delivery (chính), M5 Insight Repository (đọc), M1 Source (đọc trust_tier nếu cần lọc), điểm nối M8 (nút inline → `chatbot-qa`). **Không dùng n8n** — BRD gốc đề xuất n8n cho email digest, nhưng kênh Telegram gọi Bot API trực tiếp từ backend đơn giản hơn nhiều (một HTTP call), thêm n8n lúc này là thêm một moving part không có người hưởng lợi; khi nào làm email digest thật thì cân nhắc lại.

## Goals / Non-Goals

**Goals:**
- Insight `critical` đến tay đúng người trong vòng vài phút; tin còn lại gom digest sáng — đúng nguyên tắc BRD "không spam".
- Cá nhân subscribe theo role qua lệnh bot, không cần auth/user management mới.
- Channel adapter interface để Zalo/Teams cắm sau không sửa engine.
- Chạy hoàn toàn local, không phụ thuộc Vertex key (dev được ngay, song song với `chatbot-qa`).

**Non-Goals:**
- Zalo (cần OA + webhook public — chờ mentor); email/Teams/n8n; rule engine cấu hình qua Admin UI (v1 rule trong config); nút share thủ công trên web UI; digest cá nhân hóa bằng AI.

## Decisions

### D1. Long-polling worker, không webhook
`getUpdates` long-polling chạy như một asyncio task trong backend container (hoặc service `bot-worker` riêng trong docker-compose nếu cần isolation — quyết định lúc implement, ưu tiên chung process cho đơn giản trước). *Alternative bị loại:* webhook — cần HTTPS public, vô nghĩa với môi trường local; chuyển sang webhook sau này chỉ là đổi cách nhận update, không đụng handler.

### D2. Channel adapter interface theo pattern registry hiện có
```
class ChannelAdapter(Protocol):
    channel_type: str
    async def send(recipient_ref, message: DeliveryMessage) -> SendResult
```
`DeliveryMessage` trung lập kênh (title, body, url, buttons?); `TelegramAdapter` render sang Telegram formatting (MarkdownV2/HTML) + inline keyboard. Engine chỉ biết interface. *Alternative bị loại:* gọi thẳng Telegram API từ engine — nhanh hơn 1 ngày nhưng đóng cứng kênh, phản bội đúng lý do Zalo bị hoãn.

### D3. Rule v1 trong config, không rule engine
Hai rule cứng: (1) `urgency == critical` → alert ngay; (2) còn lại → digest hàng ngày lúc `DELIVERY_DIGEST_HOUR` (default 08:00 VN, cron theo timezone `Asia/Ho_Chi_Minh`). Recipient = subscribers có giao khác rỗng giữa `roles[]` đăng ký và `affected_roles` của insight; insight có `Toàn công ty` gửi mọi subscriber. **Lookback window thay cho "mốc bật delivery"**: alert chỉ xét insight có `created_at` trong `DELIVERY_ALERT_LOOKBACK_HOURS` (default 24h), digest trong `DELIVERY_DIGEST_LOOKBACK_HOURS` (default 48h) — không cần lưu state thời điểm bật, restart an toàn, lần chạy đầu không quét lịch sử. *Alternative bị loại:* rule engine data-driven (bảng rules + evaluator) — BRD muốn về lâu dài nhưng 1-dev + rule thực tế mới có 2 dòng, YAGNI; interface engine viết sao cho rule tách hàm riêng, nâng cấp sau không đập.

### D4. Chống gửi trùng bằng `delivery_log`
Bảng `delivery_log (id, insight_id, chat_id, kind alert|digest, sent_at)` với unique `(insight_id, chat_id, kind)`. Alert job quét insight `critical` trong lookback chưa có log; digest job gom insight trong lookback chưa gửi cho từng subscriber. Digest ghi log cho **mọi** insight khớp trong kỳ, kể cả phần vượt cap 15 hiển thị "+N tin khác" — digest là bản tin, không phải hàng đợi; tin dư không dồn sang hôm sau. Restart/chạy lại job không gửi lại tin cũ — idempotent theo DB, không theo memory.

### D5. Alert trigger: polling định kỳ, không hook vào AnalyzerService
Job APScheduler mỗi 5 phút quét insight `critical` mới thay vì gọi delivery từ trong analyzer. Giữ analyzer thuần (không side-effect gửi tin), độ trễ ≤5 phút chấp nhận được cho "tức thời" v1, và lỗi Telegram không bao giờ làm hỏng transaction analysis. *Alternative bị loại:* event/callback từ analyzer — coupling 2 service, lỗi gửi tin lẫn vào pipeline phân tích.

### D6. Subscription flow bằng lệnh bot + inline keyboard, định danh bằng chat_id
`/start` → giới thiệu + upsert bản ghi `subscribers (chat_id, roles=[], active=true)` nếu chưa có — bản ghi này đồng thời là dấu vết "chat đã `/start`" cho consumer khác (chatbot-qa cần phân biệt chat lạ); `/subscribe` → inline keyboard đa chọn các role (từ `ALLOWED_ROLES` — 9 job-title roles trong `prompts.py`, không phải 13 `target_roles` của Source; hai taxonomy này khác nhau); `/status`, `/unsubscribe`. Bảng `subscribers (chat_id PK, roles TEXT[], display_name, active, created_at, updated_at)`. Không cần map vào user hệ thống — chưa có auth, `chat_id` là danh tính đủ dùng.

### D7. Format message thuần template, $0 AI
Alert: emoji theo urgency + title + `signal` + `why_it_matters` + link dashboard + nút "💬 Hỏi về tin này" (callback `ask:<insight_id>`). Digest: nhóm theo topic, mỗi insight 1 dòng (title + urgency badge), cap ~15 insight/digest, phần dư ghi "+N tin khác, xem dashboard". Không gọi Gemini ở bất kỳ đâu trong delivery.

### D8. Nút inline hoạt động độc lập với tiến độ chatbot
Callback `ask:<insight_id>`, text tự do và lệnh `/reset` do transport nhận; nếu `chat-telegram-surface` (change `chatbot-qa`) chưa implement, cả ba nhận trả lời tạm "tính năng hỏi đáp sắp ra mắt" + link dashboard. Delivery ship được trước chatbot mà không chờ.

## Risks / Trade-offs

- [Spam khi backfill/regenerate tạo loạt insight critical] → lookback window + delivery_log idempotent; lưu ý regenerate tạo `created_at` MỚI nên lookback không đủ — trần N alert/giờ (vượt thì gom thành 1 tin tổng hợp) là chốt chặn chính.
- [Long-polling worker chết im lặng] → task tự restart với backoff; log heartbeat; `/status` của bot là cách kiểm tra sống nhanh.
- [Token bot lộ trong repo] → `TELEGRAM_BOT_TOKEN` qua env/.env (gitignored), như pattern secrets hiện có.
- [Message vượt giới hạn 4096 chars của Telegram] → digest cap 15 insight + truncate body; adapter chịu trách nhiệm split an toàn.
- [MarkdownV2 escape lỗi làm gãy tin] → dùng HTML parse mode (ít ký tự phải escape hơn); test với title chứa ký tự đặc biệt.
- [Hai change cùng đụng bot transport] → transport thuộc change này, `chatbot-qa` chỉ đăng ký handler; ranh giới ghi rõ trong cả hai proposal.

## Migration Plan

1. Migration Alembic thêm `subscribers`, `delivery_log` — thuần additive, không đụng bảng cũ.
2. Bật bằng env `TELEGRAM_BOT_TOKEN` + `DELIVERY_ENABLED=true`; thiếu token → worker không start, hệ thống còn lại chạy bình thường (delivery là tính năng cộng thêm, rollback = tắt flag).
3. Test cục bộ với bot token dev + group test riêng trước khi trỏ vào group/subscriber thật.

## Open Questions

- Zalo bắt buộc hay minh họa? (chờ mentor — adapter interface đã chừa chỗ)
- Digest giờ nào phù hợp team + có cần digest tuần cho tin `low` không? (v1: chỉ digest ngày, chỉnh qua config)
- Có cần admin xem danh sách subscribers trên web không? (v1: query DB tay, thêm route admin nếu có nhu cầu thật)
