# Khởi tạo & khôi phục session crawl MXH (X / LinkedIn)

> Liên quan: OpenSpec change `w3-anti-bot-crawl` (T7/T8). Các nguồn X và LinkedIn bị chặn xem
> nội dung khi ẩn danh (login-wall). Hệ thống vượt rào bằng cách **nạp trạng thái đăng nhập**
> của một tài khoản thật vào trình duyệt (`storage_state`), không dùng username/password trong code.

## 1. Tài khoản dùng để cào

- **Không cần follow ai cả.** Mỗi nguồn LinkedIn/X trỏ tới trang bài đăng của một chủ thể cụ thể
  (ví dụ `linkedin.com/company/openai/posts/`, `x.com/OpenAI`), không phải feed cá nhân. Bất kỳ
  tài khoản đã đăng nhập nào cũng xem được các trang này.
- **Nên dùng tài khoản riêng (throwaway)** cho việc cào: crawl bằng automation vi phạm ToS của
  X/LinkedIn và có thể bị khóa. Dùng tài khoản riêng để không ảnh hưởng tài khoản chính.

## 2. Tạo session lần đầu (chạy trên máy có GUI, từ thư mục gốc repo)

```bash
# Cài Playwright CLI (một lần)
npx playwright install chromium        # hoặc: playwright install chromium (nếu đã cài bản Python)

# LinkedIn — login tay, lướt feed vài giây, rồi ĐÓNG cửa sổ để file được ghi
playwright codegen --save-storage=secrets/states/linkedin_state.json https://www.linkedin.com/login

# X (Twitter) — tương tự
playwright codegen --save-storage=secrets/states/x_state.json https://x.com/login
```

Kiểm tra thành công:
- `secrets/states/linkedin_state.json` tồn tại và chứa cookie `li_at`.
- `secrets/states/x_state.json` tồn tại và chứa cookie `auth_token`.

File được mount vào container tại `/secrets/states/` (khớp `cookie_file` trong `seed_sources.py`).
Không cần restart backend — lần cào kế tiếp tự nạp. **Không commit các file này** (`secrets/` đã gitignore;
chúng tương đương mật khẩu tài khoản).

## 3. Cookie tự làm mới (sliding refresh)

Sau mỗi phiên cào **thành công** (lấy được ≥ 1 bài, không dính login-wall), connector ghi đè lại
`cookie_file` bằng `storage_state` mới nhất → cookie được server gia hạn liên tục, phiên không hết hạn
khi được dùng đều đặn. Yêu cầu mount `./secrets/states` ở chế độ ghi (đã cấu hình trong
`docker-compose.yml`).

## 4. Khi phiên chết (login-wall)

Nếu tài khoản bị đăng xuất/khóa, connector phát hiện login-wall và **log ERROR** dạng:

```
Login-wall tại nguồn 'LinkedIn - OpenAI' (https://www.linkedin.com/company/openai/posts/) —
phiên đăng nhập hết hạn hoặc thiếu. Tạo lại session:
playwright codegen --save-storage=/secrets/states/linkedin_state.json https://www.linkedin.com/login
```

Không có document rác nào được tạo. Khắc phục: chạy lại lệnh `codegen` ở mục 2 (bằng đường dẫn host
tương ứng, không phải đường dẫn `/secrets/...` trong container) để tạo lại file session.

## 5. Bật/tắt CloakBrowser (cho PoC)

- `CLOAK_CDP_URL` (mặc định `http://cloak:9222`): connector ưu tiên nối CloakBrowser qua CDP, tự
  fallback Chromium local nếu không nối được.
- Đặt `CLOAK_CDP_URL=` (rỗng) trong `.env` để **tắt** CloakBrowser, cào bằng Chromium local — dùng
  khi so sánh A/B trong PoC (`openspec/changes/w3-anti-bot-crawl/poc-results.md`).

## 6. Kiểm soát số bài/lần

- `max_items` (per-source, mặc định 5 cho MXH): số bài tối đa mỗi lần cào.
- `INGEST_ARTICLE_DELAY_SECONDS` (mặc định 2s) + `INGEST_JITTER_SECONDS` (mặc định 2s): nghỉ ngẫu
  nhiên giữa các bài trong cùng phiên để giống người, tránh bị chặn.
