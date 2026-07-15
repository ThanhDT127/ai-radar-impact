# Proposal: w3-anti-bot-crawl

> Sprint W3 (20–24/07/2026) — Phase 1. Task T7 (CloakBrowser) + T8 (cookie tự làm mới + kiểm soát số bài/lần).

## Why

Nhóm nguồn web VN và mạng xã hội (X/LinkedIn) hiện **không sinh ra nội dung hữu ích nào**: 8 nguồn X/LinkedIn = 0 documents (X thiếu cookie config, LinkedIn thiếu file session); ICTNews cào ra 16 bản sao của cùng một trang listing (629 chars, đều `failed`). Hạ tầng CloakBrowser đã được tích hợp một phần (service `cloak` trong docker-compose, CDP connect trong `PlaywrightConnector`) nhưng **chưa được kiểm chứng** là lấy được nội dung thật. Cookie session hiện là file tĩnh nạp một lần — khi hết hạn, crawl gãy âm thầm (0 bài, không cảnh báo).

## What Changes

**T7 — CloakBrowser hoạt động thật (không chỉ nối dây):**
- PoC benchmark CloakBrowser vs Chromium local trên 2–3 nguồn đại diện (web VN bị chặn + X/LinkedIn) — đây là **gate**: nếu CloakBrowser không cải thiện rõ, giữ Playwright làm chính và dồn effort vào cookie (T8).
- CDP URL cấu hình được qua settings (`CLOAK_CDP_URL`), thay vì hardcode `http://cloak:9222`.
- Fix context leak: `context.close()` sau mỗi fetch (contexts hiện tích tụ trong container cloak chạy dài hạn).
- Không override user-agent khi đi qua CloakBrowser (UA lệch version Chromium thật là tín hiệu bot).
- Giải quyết spec drift: spec `playwright-ingestion` yêu cầu `playwright-stealth` nhưng code chỉ có init-script — cập nhật spec theo thực tế (stealth do CloakBrowser đảm nhiệm, init-script là fallback).

**T8 — Session bền + nhịp cào an toàn:**
- Phát hiện login-wall sau khi load trang: đánh dấu nguồn degraded + log cảnh báo rõ ràng thay vì âm thầm trả 0 bài.
- Sliding refresh: sau phiên cào thành công, lưu lại `storage_state` mới để gia hạn cookie liên tục (đổi mount `secrets/states` từ `:ro` sang ghi được).
- Thêm `cookie_file` cho các nguồn X trong seed (`x_state.json`) — hiện X không có config cookie nên chắc chắn 0 bài.
- Tài liệu hóa quy trình khởi tạo session bằng `playwright codegen --save-storage` (LinkedIn + X).
- Delay + jitter giữa các lần load bài **trong cùng phiên** (jitter W1 chỉ giãn giữa các nguồn).
- Guard chống trùng nội dung trong batch: bỏ qua entry có content trùng hệt entry trước đó trong cùng lần cào (chặn kiểu "16 bản sao trang listing" lọt qua fingerprint URL+title, tránh đốt quota Gemini).

## Capabilities

### New Capabilities
_(không có — toàn bộ là thay đổi hành vi của capabilities hiện hữu)_

### Modified Capabilities
- `playwright-ingestion`: thêm requirement routing qua CloakBrowser CDP (URL cấu hình được, fallback Chromium local), đóng context sau fetch, UA passthrough khi dùng cloak, delay giữa các bài trong phiên, guard trùng content trong batch; sửa requirement stealth theo thực tế.
- `social-media-ingestion`: thay requirement "Session Cookies Injection" (nạp tĩnh) bằng vòng đời session đầy đủ — nạp, phát hiện login-wall, sliding refresh sau phiên thành công, cảnh báo khi phiên chết.

## Non-goals

- **Không** auto re-login bằng username/password (rủi ro 2FA/captcha/khóa tài khoản).
- **Không** thêm nguồn MXH mới — chỉ làm 8 nguồn X/LinkedIn + web VN đã seed chạy được.
- **Không** đụng pipeline phân tích AI — nghiệm thu hoàn toàn ở tầng `RawDocument` (không cần key Vertex; task 4.2 của W2 vẫn treo chờ quota riêng).
- **Không** giải quyết proxy/IP rotation (nếu PoC cho thấy cần, ghi nhận làm đề xuất riêng).

## Impact

- **Code**: `backend/app/connectors/playwright_connector.py` (chính), `backend/app/config.py` (settings mới), `backend/app/scripts/seed_sources.py` (config nguồn X), `docker-compose.yml` (mount rw cho states).
- **Specs**: delta cho `playwright-ingestion`, `social-media-ingestion`.
- **Dependency**: cần tài khoản X/LinkedIn hợp lệ để tạo session lần đầu (chuẩn bị trước 20/07); image `cloakhq/cloakbrowser` đã pull sẵn. Thuộc module M2 (Ingestion); không phụ thuộc Epic khác.
- **Vận hành**: crawl MXH bằng tài khoản đăng nhập vi phạm ToS X/LinkedIn — dùng tài khoản riêng, chấp nhận rủi ro bị khóa.
