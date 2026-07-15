# Design: w3-anti-bot-crawl

## Context

`PlaywrightConnector` đã có sẵn: CDP connect tới CloakBrowser (`http://cloak:9222` hardcode, fallback Chromium local), cookie injection qua `storage_state`, feed-card mode cho MXH. Service `cloak` (image `cloakhq/cloakbrowser`) đã khai báo trong docker-compose với healthcheck, backend `depends_on` cloak.

Hiện trạng đo được (10/07): 8 nguồn X/LinkedIn = 0 documents; ICTNews = 16 documents trùng hệt nhau (title trang listing, 629 chars, đều `failed`). Nguyên nhân theo tầng: (1) X không có `cookie_file` trong config; (2) `linkedin_state.json` chưa được tạo (`secrets/states/` rỗng) và connector âm thầm chạy tiếp không auth; (3) link extraction ở web VN trả về trang shell nhưng vẫn lọt qua dedup vì fingerprint = SHA256(URL + title).

**Module ảnh hưởng:** M2 (Ingestion) — duy nhất. **API endpoints:** không thêm/sửa endpoint nào. **DB:** không đổi schema; chỉ cập nhật `sources.config` (JSONB) qua seed script. **AI/LLM:** không liên quan — pipeline phân tích giữ nguyên, nghiệm thu ở tầng `RawDocument`. **n8n/delivery:** không liên quan.

## Goals / Non-Goals

**Goals:**
- Có số liệu PoC trả lời được "CloakBrowser có đáng dùng không" trên nguồn thật.
- Crawl X/LinkedIn lấy được nội dung thật bằng session đăng nhập; session tự gia hạn, chết thì báo to.
- Nhịp cào trong phiên giống người (delay + jitter giữa các bài).
- Chặn kiểu lỗi "N bản sao trang listing" đốt quota.

**Non-Goals:**
- Auto re-login bằng credentials (2FA/captcha/ban risk).
- Proxy/IP rotation, giải captcha.
- Thêm nguồn MXH mới; sửa pipeline AI; alerting qua email/Teams (chỉ log).

## Decisions

### D1. CDP URL là setting, rỗng = tắt cloak
`CLOAK_CDP_URL` trong `config.py` (default `http://cloak:9222`). Giá trị rỗng → bỏ qua CDP, dùng Chromium local trực tiếp. **Why:** PoC cần bật/tắt cloak để so sánh A/B mà không sửa code; chạy backend ngoài Docker cần URL khác. *Alternative:* biến per-source trong config — quá hạt mịn, chưa cần.

### D2. Không override user-agent khi đi qua CloakBrowser
Khi connect CDP thành công, `new_context()` **không** truyền `user_agent` (để CloakBrowser tự quản fingerprint). Chỉ set UA tĩnh khi fallback Chromium local. **Why:** UA Chrome/120 tĩnh lệch với version Chromium thật trong cloak là tín hiệu bot kinh điển, phá chính giá trị của cloak.

### D3. Vòng đời context: luôn đóng, không giết browser dùng chung
`context.close()` trong `finally` của mỗi fetch. `browser.close()` chỉ gọi khi tự launch local (với CDP, close = disconnect khỏi browser dùng chung — không kill). **Why:** contexts đang tích tụ vô hạn trong container cloak chạy dài hạn qua mỗi chu kỳ scheduler.

### D4. Phát hiện login-wall bằng heuristic theo domain
Sau `goto`, kiểm tra: URL bị redirect sang trang login (`linkedin.com/authwall`, `linkedin.com/login`, `x.com/i/flow/login`) hoặc selector đặc trưng login form xuất hiện. Map heuristic theo domain, hardcode trong connector (Phase 1, chỉ 2 platform). Khi dính: log ERROR kèm hướng dẫn chạy lại codegen, trả `[]` cho nguồn đó — **không** trích nội dung trang login làm bài viết. *Alternative:* đánh dấu `source.status` trong DB — không làm, tránh side-effect ghi DB từ connector; log là đủ cho Phase 1.

### D5. Sliding refresh: lưu lại storage_state sau phiên thành công
Phiên "thành công" = trích được ≥1 entry và không dính login-wall. Khi đó gọi `context.storage_state(path=cookie_file)` để ghi đè file với cookie mới nhất (ghi atomic: tạm + rename). Yêu cầu đổi mount `./secrets/states` từ `:ro` → rw trong docker-compose. **Why:** server gia hạn cookie trong mỗi phiên hoạt động — dùng đều thì không bao giờ hết hạn; đây là "tự làm mới" khả thi duy nhất không đụng credentials. *Trade-off:* 4 nguồn LinkedIn dùng chung 1 file — chấp nhận last-writer-wins vì ingestion chạy các nguồn tuần tự trong 1 chu kỳ.

### D6. Nhịp cào trong phiên
Delay cấu hình được giữa các lần load bài trong `_fetch_articles` (default 2s + jitter 0–2s, qua `time.sleep` — code chạy trong thread riêng nên không block event loop). Đặt tên setting đồng bộ với nhóm `ingest_*` của W1.

### D7. Guard trùng content trong batch
Trong 1 lần fetch, giữ set hash SHA256 của `raw_content`; entry có content trùng entry trước → skip + log. **Why:** fingerprint hệ thống là URL+title nên N URL khác nhau cùng trả trang shell vẫn lọt hết vào DB rồi đốt N lượt Gemini. Guard này rẻ, không đụng schema dedup hiện có. *Alternative:* đổi fingerprint sang content-based — ảnh hưởng toàn hệ thống, ngoài scope W3.

### D8. PoC là gate, chạy trước khi commit effort
Task đầu tiên: benchmark cloak vs local trên ICTNews + 1 nguồn X + 1 nguồn LinkedIn (sau khi có cookie), ghi kết quả vào `poc-results.md` trong change. Nếu cloak không cải thiện rõ (số bài lấy được / độ đầy đủ nội dung), các task cloak-specific còn lại hạ ưu tiên, giữ Playwright + cookie làm đường chính — đúng phương án dự phòng trong lịch trình.

## Risks / Trade-offs

- [CloakBrowser không hiệu quả hoặc phát sinh license/tài nguyên] → D8 gate sớm trong 1 ngày đầu; fallback Playwright vẫn nguyên vẹn.
- [Tài khoản X/LinkedIn bị khóa do vi phạm ToS] → dùng tài khoản riêng cho crawl, `max_items=5`, delay D6; chấp nhận rủi ro đã ghi trong proposal.
- [X có thể chặn cả phiên đăng nhập hợp lệ khi cào bằng automation] → nếu PoC X thất bại hoàn toàn, thu hẹp DoD về LinkedIn + web VN, ghi nhận X là known limitation.
- [Mount rw cho `secrets/states` mở rộng bề mặt ghi từ container] → thư mục đã gitignore; chỉ chứa session files; ghi atomic tránh file hỏng.
- [Fetch treo quá `t.join(timeout=180)` → thread daemon chạy tiếp, phiên chồng phiên] → known limitation, ghi nhận; fix triệt để (cancel/kill browser theo timeout) ngoài scope 2 ngày của T8.

## Migration Plan

1. Thêm settings mới với default tương thích ngược (không set env vẫn chạy như cũ).
2. Sửa docker-compose mount rw — cần `docker compose up -d` lại backend.
3. Chạy lại `seed_sources` để cập nhật config nguồn X (xác nhận seed upsert config cho nguồn đã tồn tại).
4. Người vận hành chạy codegen tạo `linkedin_state.json` / `x_state.json` (tài liệu hóa trong README hoặc docs).
5. Rollback: revert compose + settings; connector giữ hành vi cũ khi thiếu config mới.

## Open Questions

- ICTNews: trang shell 629 chars là do anti-bot hay do `link_pattern` bắt sai URL? PoC sẽ trả lời (nếu là selector sai thì fix config nguồn, không phải việc của cloak).
- `CLOAK_HEADLESS=False` trong compose: image tự lo virtual display hay cần bật headless khi chạy trên server không GUI? Kiểm chứng trong PoC.
- Seed script có update `config` cho source đã tồn tại không, hay chỉ insert-if-missing? Quyết định cách backfill config nguồn X (seed vs SQL migration nhẹ).
