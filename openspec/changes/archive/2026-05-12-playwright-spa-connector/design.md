## Context

Hiện tại `IngestionService` dispatch connector qua `ConnectorRegistry` theo `source_type`. Mọi connector (RSS, HackerNews, GitHub Trending, HuggingFace, WebIndex) đều implement `BaseConnector.fetch(source) -> list[ConnectorEntry]` — interface đồng bộ (sync). `WebIndexConnector` dùng `httpx` + `trafilatura` để fetch và extract nội dung, nhưng không xử lý được trang SPA render bằng JavaScript.

Module bị ảnh hưởng: **M2 (Ingestion)**.

## Goals / Non-Goals

**Goals:**
- Thêm `source_type = "playwright"` vào ConnectorRegistry
- `PlaywrightConnector` render trang SPA bằng headless Chromium, extract bài viết qua trafilatura
- Cài Playwright + Chromium trong backend container (inline, không thêm service mới)
- Seed 3–4 nguồn VN SPA ban đầu

**Non-Goals:**
- Không xử lý CAPTCHA / Cloudflare Turnstile
- Không login/cookie session
- Không thêm sidecar Playwright service
- Không thay đổi database schema hay API routes

## Decisions

**D1 — Inline trong backend container thay vì sidecar service**
Sidecar cần thêm HTTP API, health check, service dependency trong docker-compose, và tăng độ phức tạp vận hành. Inline giữ đúng pattern hiện tại: connector là một Python class, không cần network hop. Trade-off: backend image nặng hơn ~700MB, nhưng chấp nhận được vì chỉ ảnh hưởng build time.

**D2 — `sync_playwright()` thay vì async**
`BaseConnector.fetch()` là sync. Dùng `async_playwright` sẽ phá vỡ interface hiện tại và yêu cầu refactor `IngestionService`. `sync_playwright()` của Playwright Python hoạt động tốt trong sync context, không cần thay đổi gì.

**D3 — Mở browser mới cho mỗi lần `fetch()` thay vì reuse**
Browser reuse cần quản lý lifecycle phức tạp (khi nào close? crash recovery?). Mở/đóng trong một `fetch()` call đơn giản hơn và tránh memory leak. Overhead ~1s/lần chấp nhận được.

**D4 — playwright-stealth để bypass fingerprint detection cơ bản**
Các site như VietTimes, ICTNews có thể reject headless browser qua `navigator.webdriver` flag. `playwright-stealth` patch các thuộc tính này. Không đảm bảo bypass Cloudflare WAF nhưng đủ cho phần lớn site thông thường.

**D5 — trafilatura extract nội dung từ HTML đã render**
Tái dụng `WebArticleConnector.extract_from_html()` sau khi Playwright đã render — tránh duplicate logic extraction.

## Flow

```
PlaywrightConnector.fetch(source)
  ├─ launch headless Chromium
  ├─ new_page() + stealth_sync()
  ├─ goto(source.feed_url, wait_until="networkidle")
  ├─ extract article links (link_selector hoặc link_pattern)
  ├─ for each link:
  │    ├─ page.goto(link)
  │    ├─ page.content() → HTML string
  │    └─ trafilatura.extract(html) → ConnectorEntry
  └─ browser.close()
```

## Config fields (source.config)

| Key | Type | Default | Mô tả |
|-----|------|---------|-------|
| `link_selector` | str | `"a"` | CSS selector để tìm article links trên trang listing |
| `link_pattern` | str | `""` | Regex filter URL — chỉ lấy links match pattern |
| `max_items` | int | `10` | Giới hạn số bài per run |
| `wait_for` | str | `""` | CSS selector để `page.wait_for_selector()` trước khi extract |
| `wait_timeout` | int | `10000` | Timeout ms cho wait_for |

## Risks / Trade-offs

- **Image size tăng ~700MB** → Chấp nhận được, chỉ ảnh hưởng build. Nếu thành vấn đề sau này có thể tách Dockerfile multi-stage.
- **Ingestion chậm hơn: ~5–8s/bài** → Chạy nền qua `run_ingestion` script, không blocking API. Đặt `max_items=10` mặc định.
- **Chromium crash trong container** → Playwright tự restart process. Lỗi ở cấp bài viết được catch và log, không làm hỏng toàn bộ batch.
- **CafeF có Cloudflare JS challenge** → Không đưa CafeF vào Phase 1. Seed VietTimes, ICTNews, MLOpsVN trước — ít anti-bot hơn.
- **`wait_until="networkidle"` có thể timeout với SPA phức tạp** → Fallback sang `domcontentloaded` nếu timeout; thêm `wait_for` selector config để kiểm soát per-source.

## Migration Plan

1. Update `backend/Dockerfile` — thêm Playwright deps
2. Viết `playwright_connector.py`
3. Import trong `connectors/__init__.py`
4. Rebuild backend image: `docker-compose build backend`
5. Seed nguồn mới: `docker-compose exec backend python -m app.scripts.seed_sources`
6. Test: `docker-compose exec backend python -m app.scripts.run_ingestion --source-id <UUID>`

Rollback: xóa import trong `__init__.py` + remove Playwright khỏi Dockerfile → rebuild.

## Open Questions

- VietTimes hiện tại có thực sự cần JS render không, hay `WebIndexConnector` đã đủ? → Cần test thực tế trước khi seed.
- `wait_until="networkidle"` vs `"load"` — site nào cần networkidle? → Test per-site.
