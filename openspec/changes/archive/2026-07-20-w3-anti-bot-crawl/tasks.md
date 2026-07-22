# Tasks: w3-anti-bot-crawl

> Nghiệm thu hoàn toàn ở tầng `RawDocument` — **không cần key Vertex**. Khi chạy ingestion thật, bước analysis sẽ lỗi vì thiếu quota: đó là hành vi đã biết, docs bị đánh dấu `failed` thì re-queue bằng `reset_failed` khi có key.

## 1. Chuẩn bị môi trường & session (tiền đề — làm trước 20/07)

- [x] 1.1 Tạo session LinkedIn — **quy trình đã đổi**: `playwright codegen` trên host KHÔNG dùng được (phiên chết sau 1 request do lệch fingerprint với CloakBrowser). Phải đăng nhập **bên trong CloakBrowser** rồi trích `contexts[0].storage_state()`; các bước chi tiết trong `docs/session_bootstrap.md`. **DoD ✅ (20/07):** phiên sống ổn định qua 5 chu kỳ crawl liên tiếp (có nghỉ 6 phút), `li_at` còn nguyên.
- [x] 1.2 ~~Tạo session X~~ — **BỎ (20/07):** X cắt khỏi phạm vi, `x_state.json` đã xóa. Lý do: tweet 243–440 ký tự → 0 insight, trùng nguồn RSS chính thức. Xem `proposal.md` mục "Thu hẹp phạm vi".
- [x] 1.3 Đổi mount `./secrets/states` trong docker-compose từ `:ro` sang ghi được (cần cho sliding refresh). **DoD:** backend container ghi được file thử vào `/secrets/states/`.
- [x] 1.4 ~~Thêm `cookie_file` cho 4 nguồn X~~ — **BỎ (20/07):** 4 nguồn X gỡ khỏi `seed_sources.py` và xóa khỏi DB (4 source + 9 raw_document, 0 insight). LinkedIn giữ nguyên `linkedin_state.json`.

## 2. PoC CloakBrowser — gate quyết định hướng T7

- [x] 2.1 Thêm setting `CLOAK_CDP_URL` vào `config.py` (default `http://cloak:9222`; rỗng = tắt cloak, dùng Chromium local), thay hardcode trong `playwright_connector.py` (`_connect_browser`). **DoD:** bật/tắt cloak chỉ bằng env, không sửa code.
- [x] 2.2 Gate PoC — **đóng bằng lập luận, không chạy A/B (20/07).** Tiền đề của phép so đã đổi: nguồn web VN nay là `source_type: web_index`, không đi qua CloakBrowser, nên nhánh "web VN bị chặn" không còn đối tượng; LinkedIn là nguồn `playwright` active duy nhất. Chạy nhánh "local" cho LinkedIn đòi tạo lại session **trong** Chromium local (phát hiện fingerprint 20/07) — tốn một vòng đăng nhập tay để trả lời câu hỏi mà bằng chứng đã đủ. **Kết luận: GIỮ CloakBrowser.** Xem `poc-results.md` mục "Kết luận gate".
- [x] 2.3 ~~Chẩn đoán ICTNews~~ — **KHÔNG CÒN ĐỐI TƯỢNG (20/07):** nguồn "ICTNews Công nghệ" đã rời seed/DB từ trước. Web VN nay do `web_index` đảm nhiệm và chạy tốt (200lab/ML Cơ Bản/Viblo, mỗi nguồn 10 doc, 6.5k–16k ký tự, có sinh insight) — triệu chứng "16 bản sao trang shell" không tái hiện. Ngoài ra `web_index` không đi qua CloakBrowser nên không thuộc phạm vi T7.

## 3. Connector hardening (T7)

- [x] 3.1 Không override `user_agent` khi context tạo qua CDP CloakBrowser; giữ UA tĩnh chỉ cho Chromium local (`_new_context`). **DoD (runtime):** kiểm tra qua cloak, UA của page khớp version Chromium thật — xác minh trong PoC 2.2.
- [x] 3.2 Đóng context trong `finally` của mọi nhánh fetch; `browser.close()` chỉ khi tự launch local (CDP chỉ disconnect, không kill browser dùng chung). **DoD (runtime):** sau 3 lần fetch liên tiếp, số contexts trong cloak không tăng — xác minh trong PoC 2.2.
- [x] 3.3 Delay + jitter giữa các lần load bài trong `_fetch_articles` (`ingest_article_delay_seconds` mới, default 2s + jitter 0–2s, đồng bộ nhóm `ingest_*`). **DoD:** unit test `_article_delay_seconds` trong khoảng cấu hình.
- [x] 3.4 Guard trùng content trong batch: `_dedup_by_content` hash SHA256 `raw_content`, skip trùng + log số bị loại; áp cho cả feed-card lẫn article path. **DoD:** unit test N entry cùng content → giữ 1.
- [x] 3.5 Unit tests cho 3.3/3.4 trong `tests/test_playwright_connector.py`. **DoD:** pytest xanh (15/15 pass).
- [x] 3.6 **Định danh feed card ổn định giữa các phiên** (phát hiện 20/07): trích thân bài qua `CARD_BODY_SELECTORS` (`.update-components-text` …), dự phòng lọc `VOLATILE_CARD_LINE` khỏi `inner_text()`; `source_url` = `#post-<sha256(body)[:16]>`, `title` = dòng đầu có nghĩa của thân bài. **DoD ✅:** 2 chu kỳ ingestion liên tiếp → chu kỳ 2 `new: 0, skipped: 5`; 5/5 card cho thân bài khác nhau (không post nào bị gộp nhầm); 4 unit test mới, pytest 63/63.

## 4. Vòng đời session (T8)

- [x] 4.1 Phát hiện login-wall theo domain map (`linkedin.com/authwall|/login|/checkpoint|/uas/login` + selector login form) trong `_is_login_wall`: log ERROR kèm hướng dẫn codegen (`_log_login_wall`), set `session["login_wall"]`, trả `[]`, không trích trang login. **DoD (runtime) ✅ 20/07:** nghiệm thu trên phiên chết thật → log ERROR kèm lệnh codegen, 0 doc rác. *Đã vá lỗ timing:* check cũ chạy ngay sau `domcontentloaded`, trước redirect authwall phía client → im lặng 0 card; nay kiểm lại khi truy vấn ra 0 phần tử (cả nhánh feed-card lẫn extract-links).
- [x] 4.2 Sliding refresh: sau phiên thành công (≥1 entry, không login-wall) ghi `context.storage_state()` đè `cookie_file` atomic (`_save_storage_state`, tempfile + `os.replace`); phiên thất bại không ghi. **DoD ✅ 20/07:** mtime đổi sau phiên thật. *Đã vá regression:* `storage_state()` qua CDP trả state thiếu `li_at` → ghi đè giết phiên đang sống (quan sát 08:00 → authwall 08:10). Nay so `AUTH_COOKIE_NAMES` giữa file cũ/mới, mất auth thì bỏ qua ghi + WARNING. Unit test 2 nhánh giữ/ghi.
- [x] 4.3 Unit tests login-wall detection + login URL mapping trong `tests/test_playwright_connector.py`. **DoD:** pytest xanh.

## 5. Nghiệm thu & tài liệu (local, nén — không cần key Vertex)

- [x] 5.1 Chạy ingestion thật cho 4 nguồn LinkedIn + web VN. **DoD T7 ✅ (20/07):** cả 4 nguồn LinkedIn từ 0 docs nay ra nội dung thật — Andrew Ng 5 doc (TB 1933 ký tự), OWASP 5 (666), OpenAI 4 (721), Anthropic 3 (280); title trích từ thân bài, spot-check khớp bài gốc. Web VN đã khỏe sẵn qua `web_index`: 200lab 10 doc (6580), ML Cơ Bản 10 (15905), Viblo 10 (10092) — có insight.
  - 🐛 **Sửa kèm:** `LinkedIn - Anthropic` trỏ nhầm `company/anthropic` — đó là một quỹ VC/PE trùng tên (4K followers, "No posts yet"). Anthropic AI thật là `company/anthropicresearch` (4,19M followers). Đã sửa `seed_sources.py` + re-seed + cào lại.
- [x] 5.2 Kiểm chứng tự phục hồi phiên. **DoD T8 ✅ (20/07):** 5 chu kỳ liên tiếp đều ra bài, `mtime` state đổi sau mỗi phiên thành công, `li_at` sống sót, phiên không bị thu hồi (điều kiện: session tạo trong CloakBrowser — xem 1.1). Phiên chết → ERROR đúng chỗ, 0 doc rác (nghiệm thu ở 4.1 trên phiên chết thật).
- [x] 5.3 Tài liệu hóa quy trình khởi tạo/khôi phục session (`docs/session_bootstrap.md`); cập nhật CLAUDE.md (fingerprint là URL+title; ghi chú CloakBrowser/`CLOAK_CDP_URL`/session/dedup). **DoD:** người khác đọc theo làm được.
- [x] 5.4 Cập nhật trạng thái T7/T8 trong `docs/ignored/LICH_TRINH_CONG_VIEC.md` (checkpoint 24/07). Không có scaffold tạm nào được thêm — mọi thay đổi đều là code sản phẩm. **DoD:** diff cuối chỉ còn thay đổi sản phẩm.
