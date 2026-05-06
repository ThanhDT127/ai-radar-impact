## Why

Dự án AI Impact Radar hiện chỉ có tài liệu spec — chưa có dòng code nào. Với team 1 người, cần chứng minh pipeline hoạt động end-to-end (từ thu thập nguồn → AI phân tích → hiển thị insight) trước khi mở rộng. Change này tạo skeleton dự án và **vertical slice đầu tiên** — 1 nguồn RSS thật, xuyên suốt toàn bộ pipeline, hiển thị kết quả trên giao diện web.

## What Changes

**Giai đoạn 0 — Project Skeleton:**
- Khởi tạo Backend FastAPI với cấu trúc route → service → repository
- Khởi tạo Frontend React (Vite + TypeScript)
- Docker Compose: backend + PostgreSQL
- DB migration cơ bản (Alembic) với các bảng `sources`, `raw_documents`, `insights`
- Health check endpoint `GET /api/v1/health`

**Giai đoạn 1 — Vertical Slice (1 nguồn RSS → Insight → Dashboard):**
- RSS connector đọc GitHub Changelog (`https://github.blog/changelog/feed/`)
- Normalizer: clean HTML, extract title/date/body, fingerprint dedup
- AI analysis: gọi Gemini Flash 2.0 — classify topic, event_type, sinh summary
- Trust/impact scoring cơ bản (rule-based theo source tier, không cần LLM)
- Lưu insight vào PostgreSQL
- API `GET /api/v1/insights` với pagination
- API `GET /api/v1/insights/:id` chi tiết
- React page: danh sách insight cards + trang chi tiết
- CLI/script trigger ingestion thủ công (chưa cần scheduler tự động)

**Phase:** Phase 1 (MVP)

**Dependency:** Không có — đây là change đầu tiên của dự án.

## Capabilities

### New Capabilities
- `project-setup`: Skeleton dự án (FastAPI, React, Docker Compose, DB migration, project structure)
- `rss-ingestion`: RSS connector + normalizer — fetch, parse, clean, dedup, lưu raw document
- `ai-analysis`: Gọi Gemini Flash 2.0 classify + summarize, sinh insight từ raw document
- `insight-api`: REST API cho insight (list + detail + pagination)
- `insight-dashboard`: React UI hiển thị danh sách insight và trang chi tiết

### Modified Capabilities
_(Chưa có capability nào tồn tại — đây là change đầu tiên)_

## Non-goals

- **Không** làm auth/RBAC — truy cập tự do trong giai đoạn này
- **Không** làm email digest hay Teams notification
- **Không** làm admin UI quản lý nguồn — nguồn được seed trực tiếp vào DB
- **Không** làm chatbot/vector search
- **Không** làm scheduler tự động — trigger ingestion bằng CLI/script
- **Không** làm feedback loop
- **Không** xử lý nhiều loại connector (chỉ RSS)
- **Không** deploy lên VPS — chạy local Docker Compose

## Impact

- **Code:** Tạo mới toàn bộ — backend (`/backend`), frontend (`/frontend`), infra (`docker-compose.yml`)
- **Database:** 3 bảng mới: `sources`, `raw_documents`, `insights`
- **API:** 3 endpoints mới: `/health`, `/insights`, `/insights/:id`
- **Dependencies:** FastAPI, SQLAlchemy, Alembic, feedparser, google-genai SDK, React, Vite, TanStack Query
- **AI:** Cần API key cho Gemini Flash 2.0 (biến môi trường `GEMINI_API_KEY`)
