# Tasks: w3-anti-bot-crawl

> Nghiệm thu hoàn toàn ở tầng `RawDocument` — **không cần key Vertex**. Khi chạy ingestion thật, bước analysis sẽ lỗi vì thiếu quota: đó là hành vi đã biết, docs bị đánh dấu `failed` thì re-queue bằng `reset_failed` khi có key.

## 1. Chuẩn bị môi trường & session (tiền đề — làm trước 20/07)

- [ ] 1.1 ⏸️ **CẦN NGƯỜI DÙNG** (login GUI) — Playwright CLI đã cài sẵn trên host. Tạo session LinkedIn: `playwright codegen --save-storage=secrets/states/linkedin_state.json https://www.linkedin.com/login` (chạy từ gốc repo, login tay, lướt feed vài giây, đóng cửa sổ). **DoD:** file tồn tại, chứa cookie `li_at`. Xem `docs/session_bootstrap.md`.
- [ ] 1.2 ⏸️ **CẦN NGƯỜI DÙNG** — Tạo session X: `playwright codegen --save-storage=secrets/states/x_state.json https://x.com/login`. **DoD:** file chứa cookie `auth_token`.
- [x] 1.3 Đổi mount `./secrets/states` trong docker-compose từ `:ro` sang ghi được (cần cho sliding refresh). **DoD:** backend container ghi được file thử vào `/secrets/states/`.
- [x] 1.4 Thêm `cookie_file: /secrets/states/x_state.json` cho 4 nguồn X trong `seed_sources.py`; xác nhận `seed()` **update** `config` cho nguồn đã tồn tại (dòng ~1080) → chỉ cần chạy lại seed, không cần backfill SQL. **DoD:** query DB thấy `config.cookie_file` trên cả 4 nguồn X (sau khi chạy seed).

## 2. PoC CloakBrowser — gate quyết định hướng T7

- [x] 2.1 Thêm setting `CLOAK_CDP_URL` vào `config.py` (default `http://cloak:9222`; rỗng = tắt cloak, dùng Chromium local), thay hardcode trong `playwright_connector.py` (`_connect_browser`). **DoD:** bật/tắt cloak chỉ bằng env, không sửa code.
- [ ] 2.2 ⏸️ **CẦN SESSION + CLOAK CHẠY** (gate PoC) — Benchmark A/B: ICTNews + 1 nguồn X + 1 nguồn LinkedIn, mỗi nguồn 2 chế độ (cloak/local), điền `poc-results.md` (template đã tạo). **DoD:** bảng so sánh + kết luận giữ/bỏ cloak.
- [ ] 2.3 ⏸️ **CẦN CRAWL THẬT** — Chẩn đoán ICTNews: 16 bản sao trang shell (629 chars) do anti-bot hay `link_selector`/`link_pattern` sai; nếu config sai thì fix. **DoD:** ICTNews trả bài thật, hoặc ghi bằng chứng "cần anti-bot" trong poc-results.md.

## 3. Connector hardening (T7)

- [x] 3.1 Không override `user_agent` khi context tạo qua CDP CloakBrowser; giữ UA tĩnh chỉ cho Chromium local (`_new_context`). **DoD (runtime):** kiểm tra qua cloak, UA của page khớp version Chromium thật — xác minh trong PoC 2.2.
- [x] 3.2 Đóng context trong `finally` của mọi nhánh fetch; `browser.close()` chỉ khi tự launch local (CDP chỉ disconnect, không kill browser dùng chung). **DoD (runtime):** sau 3 lần fetch liên tiếp, số contexts trong cloak không tăng — xác minh trong PoC 2.2.
- [x] 3.3 Delay + jitter giữa các lần load bài trong `_fetch_articles` (`ingest_article_delay_seconds` mới, default 2s + jitter 0–2s, đồng bộ nhóm `ingest_*`). **DoD:** unit test `_article_delay_seconds` trong khoảng cấu hình.
- [x] 3.4 Guard trùng content trong batch: `_dedup_by_content` hash SHA256 `raw_content`, skip trùng + log số bị loại; áp cho cả feed-card lẫn article path. **DoD:** unit test N entry cùng content → giữ 1.
- [x] 3.5 Unit tests cho 3.3/3.4 trong `tests/test_playwright_connector.py`. **DoD:** pytest xanh (15/15 pass).

## 4. Vòng đời session (T8)

- [x] 4.1 Phát hiện login-wall theo domain map (`linkedin.com/authwall|/login`, `x.com/i/flow/login|/login` + selector login form) trong `_is_login_wall`: log ERROR kèm hướng dẫn codegen (`_log_login_wall`), set `session["login_wall"]`, trả `[]`, không trích trang login. **DoD (runtime):** xóa tạm cookie → fetch → thấy ERROR, 0 doc rác — xác minh ở 5.2.
- [x] 4.2 Sliding refresh: sau phiên thành công (≥1 entry, không login-wall) ghi `context.storage_state()` đè `cookie_file` atomic (`_save_storage_state`, tempfile + `os.replace`); phiên thất bại không ghi. **DoD:** unit test 2 nhánh ghi/lỗi; mtime file đổi sau phiên thật — xác minh ở 5.2.
- [x] 4.3 Unit tests login-wall detection + login URL mapping trong `tests/test_playwright_connector.py`. **DoD:** pytest xanh.

## 5. Nghiệm thu & tài liệu (local, nén — không cần key Vertex)

- [ ] 5.1 ⏸️ **CẦN SESSION + CRAWL THẬT** — Chạy ingestion thật cho 8 nguồn X/LinkedIn + ICTNews; spot-check 5–10 bài so bản gốc. **DoD T7:** nguồn từng 0 docs nay có nội dung thật, đầy đủ.
- [ ] 5.2 ⏸️ **CẦN SESSION + CRAWL THẬT** — Kiểm chứng tự phục hồi phiên: chạy 2 chu kỳ liên tiếp, xác nhận file state gia hạn (mtime đổi) và phiên còn sống; giả lập cookie chết → báo ERROR đúng chỗ. **DoD T8:** cookie tự làm mới, phiên chết không âm thầm.
- [x] 5.3 Tài liệu hóa quy trình khởi tạo/khôi phục session (`docs/session_bootstrap.md`); cập nhật CLAUDE.md (fingerprint là URL+title; ghi chú CloakBrowser/`CLOAK_CDP_URL`/session/dedup). **DoD:** người khác đọc theo làm được.
- [x] 5.4 Cập nhật trạng thái T7/T8 trong `docs/ignored/LICH_TRINH_CONG_VIEC.md` (checkpoint 24/07). Không có scaffold tạm nào được thêm — mọi thay đổi đều là code sản phẩm. **DoD:** diff cuối chỉ còn thay đổi sản phẩm.
