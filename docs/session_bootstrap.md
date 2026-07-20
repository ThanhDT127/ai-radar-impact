# Khởi tạo & khôi phục session crawl MXH (LinkedIn)

> Liên quan: OpenSpec change `w3-anti-bot-crawl` (T7/T8). Các nguồn LinkedIn bị chặn xem
> nội dung khi ẩn danh (login-wall). Hệ thống vượt rào bằng cách **nạp trạng thái đăng nhập**
> của một tài khoản thật vào trình duyệt (`storage_state`), không dùng username/password trong code.

## 1. Tài khoản dùng để cào

- **Không cần follow ai cả.** Mỗi nguồn LinkedIn trỏ tới trang bài đăng của một chủ thể cụ thể
  (ví dụ `linkedin.com/company/openai/posts/`), không phải feed cá nhân. Bất kỳ
  tài khoản đã đăng nhập nào cũng xem được các trang này.
- **Nên dùng tài khoản riêng (throwaway)** cho việc cào: crawl bằng automation vi phạm ToS của
  LinkedIn và có thể bị khóa. Dùng tài khoản riêng để không ảnh hưởng tài khoản chính.

## 2. Tạo session lần đầu — PHẢI đăng nhập BÊN TRONG CloakBrowser

> ⚠️ **`playwright codegen` trên host KHÔNG dùng được.** Đo 20/07: phiên tạo bằng codegen chỉ phục vụ
> đúng **một** request rồi authwall vĩnh viễn, dù `li_at` còn nguyên. Nguyên nhân: CloakBrowser chạy
> với `--fingerprint-platform=windows`, còn codegen dùng Chromium Linux trên host — LinkedIn thấy cùng
> `li_at` xuất hiện từ nền tảng khác và thu hồi phiên. Phiên tạo **trong chính CloakBrowser** chạy ổn
> qua 5 chu kỳ liên tiếp (có nghỉ 6 phút). Bằng chứng: `openspec/changes/w3-anti-bot-crawl/poc-results.md`.

CloakBrowser chạy headful trên Xvfb `:99` trong container nhưng **không có sẵn VNC**, nên cần dựng tạm
đường nhìn vào. Toàn bộ bước dưới dùng container tạm — **không** đụng `docker-compose.yml`.

```bash
# 1. Cài x11vnc vào container cloak + mở VNC trên Xvfb :99
docker compose exec -T cloak sh -c 'apt-get update -qq && apt-get install -y -qq x11vnc'
docker compose exec -d cloak x11vnc -display :99 -nopw -listen 0.0.0.0 -rfbport 5900 -forever -shared -quiet

# 2. Cầu noVNC (host không route thẳng vào docker bridge được)
docker run --rm -d --name w3_novnc --network ai-radar-impact_default -p 6080:6080 \
  --entrypoint sh theasp/novnc:latest -c 'websockify --web=/usr/share/novnc 6080 cloak:5900'
```

```python
# 3. Mở trang login trong context MẶC ĐỊNH của CloakBrowser (chạy trong container backend)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.connect_over_cdp("http://cloak:9222").contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
```

4. Mở **http://localhost:6080/vnc.html** → Connect → đăng nhập tay → đợi vào được `/feed/`.

```python
# 5. Trích storage_state ra cookie_file (chạy trong container backend)
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    ctx = pw.chromium.connect_over_cdp("http://cloak:9222").contexts[0]
    ctx.storage_state(path="/secrets/states/linkedin_state.json")
```

```bash
# 6. Dọn hạ tầng tạm
docker rm -f w3_novnc
docker compose exec -T cloak sh -c 'pkill x11vnc; apt-get remove -y -qq x11vnc'
```

Kiểm tra thành công:
- `secrets/states/linkedin_state.json` tồn tại và chứa cookie `li_at`.
- Chạy ingestion **hai** chu kỳ liên tiếp, cả hai đều ra bài → phiên khớp fingerprint, không bị thu hồi.

File được mount vào container tại `/secrets/states/` (khớp `cookie_file` trong `seed_sources.py`).
Không cần restart backend — lần cào kế tiếp tự nạp. **Không commit các file này** (`secrets/` đã gitignore;
chúng tương đương mật khẩu tài khoản).

> Nếu đổi `CLOAK_CDP_URL=` (rỗng, dùng Chromium local) thì phải tạo lại session bằng chính Chromium
> local đó — mọi lần đổi trình duyệt cào đều làm lệch fingerprint và giết phiên.

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
