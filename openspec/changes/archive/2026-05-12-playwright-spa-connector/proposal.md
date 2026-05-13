## Why

Một số nguồn tin quan trọng của Việt Nam (VietTimes, ICTNews, MLOpsVN) không có RSS feed và render nội dung bằng JavaScript — `trafilatura` và `httpx` chỉ tải về HTML skeleton rỗng, không lấy được bài viết. Cần một connector có thể điều khiển trình duyệt thật để render trang SPA trước khi extract nội dung.

## What Changes

- Thêm `PlaywrightConnector` — connector mới dùng Playwright Python (`sync_playwright`) để render trang JavaScript, sau đó extract bài viết qua trafilatura
- `playwright-stealth` được áp dụng để bypass fingerprint detection cơ bản
- `backend/Dockerfile` cài thêm Playwright + Chromium
- Seed thêm 3–4 nguồn VN SPA với `source_type = "playwright"`
- `source_type` mới: `playwright`

## Capabilities

### New Capabilities
- `playwright-ingestion`: ConnectorEntry fetching từ các trang SPA/JavaScript-render qua headless Chromium; config-driven (link_selector, link_pattern, wait_for, max_items)

### Modified Capabilities
- `connector-registry`: Đăng ký thêm `source_type = "playwright"` vào ConnectorRegistry

## Impact

- `backend/Dockerfile` — thêm system deps cho Chromium, `pip install playwright playwright-stealth`, `playwright install chromium`
- `backend/app/connectors/playwright_connector.py` — file mới
- `backend/app/connectors/__init__.py` — import PlaywrightConnector
- `backend/app/scripts/seed_sources.py` — thêm 3–4 nguồn VN SPA
- Docker image backend tăng ~700MB do Chromium
- Không ảnh hưởng các connector hiện tại hay API routes

## Non-goals

- Không xử lý CAPTCHA hay Cloudflare Turnstile (CafeF để sau)
- Không thêm Playwright service riêng (sidecar) — inline trong backend
- Không hỗ trợ login/cookie-based scraping trong phase này
- Không thay thế WebIndexConnector — chỉ dùng khi trang cần JavaScript render
