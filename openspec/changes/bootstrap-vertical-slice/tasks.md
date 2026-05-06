## 1. DevOps — Project Skeleton (P1)

- [ ] 1.1 Tạo `docker-compose.yml` với 2 services: `db` (postgres:16-alpine) và `backend` (Dockerfile)
- [ ] 1.2 Tạo `.env.example` với: DATABASE_URL, GEMINI_API_KEY, BACKEND_PORT
- [ ] 1.3 Tạo `backend/Dockerfile` (Python 3.12, pip install, uvicorn)
- [ ] 1.4 Verify: `docker-compose up` khởi động cả backend + postgres thành công

## 2. Backend — FastAPI Skeleton (P1)

- [ ] 2.1 Tạo `backend/app/main.py` — FastAPI app factory với CORS middleware
- [ ] 2.2 Tạo `backend/app/config.py` — Pydantic Settings đọc từ `.env` (DATABASE_URL, GEMINI_API_KEY)
- [ ] 2.3 Tạo `backend/app/database.py` — SQLAlchemy async engine + session factory
- [ ] 2.4 Tạo `backend/app/routes/health.py` — `GET /api/v1/health` trả `{ status: "ok", db: "connected" }`
- [ ] 2.5 Tạo `backend/requirements.txt` — fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, pydantic-settings, alembic, feedparser, google-genai, beautifulsoup4
- [ ] 2.6 Verify: `GET /api/v1/health` trả 200 với db connected

## 3. Backend — Database Migration (P1)

- [ ] 3.1 Init Alembic: `alembic init alembic` + cấu hình async trong `env.py`
- [ ] 3.2 Tạo SQLAlchemy models: `models/source.py`, `models/raw_document.py`, `models/insight.py`
- [ ] 3.3 Tạo migration đầu tiên: `alembic revision --autogenerate -m "create sources raw_documents insights"`
- [ ] 3.4 Chạy migration: `alembic upgrade head` — verify 3 bảng + indexes được tạo
- [ ] 3.5 Tạo `backend/app/scripts/seed_sources.py` — seed 1 record GitHub Changelog RSS vào bảng `sources`
- [ ] 3.6 Verify: chạy seed script, query bảng sources thấy 1 row

## 4. Backend — RSS Ingestion Pipeline (P1)

- [ ] 4.1 Tạo `connectors/rss_connector.py` — fetch RSS feed bằng `feedparser`, trả list entries chuẩn hóa
- [ ] 4.2 Tạo `services/normalizer.py` — clean HTML bằng BeautifulSoup, extract title/date/body/author, sinh fingerprint SHA-256
- [ ] 4.3 Tạo `repositories/raw_document_repo.py` — create, exists_by_fingerprint, get_pending
- [ ] 4.4 Tạo `repositories/source_repo.py` — get_active_sources, get_by_id
- [ ] 4.5 Tạo `services/ingestion.py` — IngestionService.run(): fetch → normalize → dedup → lưu raw_documents
- [ ] 4.6 Tạo `scripts/run_ingestion.py` — CLI entrypoint: `python -m backend.app.scripts.run_ingestion [--source-id UUID]`
- [ ] 4.7 Verify: chạy ingestion script → log hiển thị "N new, M skipped", query raw_documents thấy records mới

## 5. Backend — AI Analysis (P1)

- [ ] 5.1 Tạo `ai/prompts.py` — ANALYSIS_PROMPT template với taxonomy lists, JSON output schema, grounding rules
- [ ] 5.2 Tạo `ai/gemini_client.py` — GeminiClient.analyze(content, title) gọi Gemini Flash 2.0, parse JSON response, handle errors/timeout
- [ ] 5.3 Tạo `services/analyzer.py` — AnalyzerService: lấy pending raw_docs, gọi Gemini, tính trust_score (rule-based từ source tier), tính impact_label (rule-based từ event_type), tạo insight
- [ ] 5.4 Tạo `repositories/insight_repo.py` — create, list_paginated, get_by_id
- [ ] 5.5 Tích hợp analyzer vào IngestionService.run() — sau bước lưu raw_doc, gọi analyze
- [ ] 5.6 Verify: chạy full pipeline → query bảng insights thấy records với summary, topics, impact_label

## 6. Backend — Insight API (P1)

- [ ] 6.1 Tạo `schemas/common.py` — PaginatedResponse, ErrorResponse Pydantic models
- [ ] 6.2 Tạo `schemas/insight.py` — InsightListItem, InsightDetail Pydantic models
- [ ] 6.3 Tạo `routes/insights.py` — `GET /api/v1/insights` (paginated list, created_at DESC)
- [ ] 6.4 Thêm route `GET /api/v1/insights/{id}` — detail với 404 handling
- [ ] 6.5 Verify: gọi API bằng curl/httpie, verify pagination response format đúng spec

## 7. Frontend — React Skeleton (P1)

- [ ] 7.1 Init Vite+React+TypeScript: `npm create vite@latest frontend -- --template react-ts`
- [ ] 7.2 Cài dependencies: `react-router-dom`, `@tanstack/react-query`, `axios`
- [ ] 7.3 Tạo `src/api/insights.ts` — fetchInsights(page, size), fetchInsightById(id) gọi backend API
- [ ] 7.4 Tạo `src/types/insight.ts` — TypeScript interfaces: Insight, PaginatedResponse
- [ ] 7.5 Setup React Router trong `App.tsx`: route `/` và `/insights/:id`
- [ ] 7.6 Setup QueryClientProvider trong `main.tsx`
- [ ] 7.7 Cấu hình Vite proxy: `/api` → `http://localhost:8000`
- [ ] 7.8 Verify: `npm run dev` chạy, truy cập localhost:5173 thấy React app

## 8. Frontend — Insight Dashboard UI (P1)

- [ ] 8.1 Tạo `components/Layout.tsx` — header với tên app, container layout
- [ ] 8.2 Tạo `components/ImpactBadge.tsx` — badge màu theo impact_label (Critical=đỏ, High=cam, Medium=vàng, Low=xanh, Watch=xám)
- [ ] 8.3 Tạo `components/InsightCard.tsx` — card hiển thị: title, summary_short, topics tags, impact badge, relative time
- [ ] 8.4 Tạo `pages/InsightList.tsx` — useQuery fetch insights, render InsightCard list, loading skeleton, empty state, error state
- [ ] 8.5 Tạo `components/Pagination.tsx` — Previous/Next buttons, current page indicator
- [ ] 8.6 Tạo `pages/InsightDetail.tsx` — useQuery fetch insight by id, hiển thị full detail, source_url link (target=_blank), 404 handling
- [ ] 8.7 Tạo `styles/global.css` — typography, color palette, CSS variables cho impact colors
- [ ] 8.8 Tạo `styles/insights.module.css` — card styles, list layout, responsive breakpoints
- [ ] 8.9 Verify: truy cập localhost:5173, thấy danh sách insight cards từ dữ liệu thật, click vào 1 card thấy trang detail

## 9. End-to-End Verification (P1)

- [ ] 9.1 Full pipeline test: `docker-compose up` → seed sources → run ingestion → mở browser → thấy insights
- [ ] 9.2 Verify dedup: chạy ingestion lần 2 → log hiển thị "0 new, N skipped"
- [ ] 9.3 Verify error handling: đổi GEMINI_API_KEY thành invalid → pipeline log error nhưng không crash
- [ ] 9.4 Verify responsive: mở browser ở viewport 375px → cards hiển thị 1 cột
- [ ] 9.5 Viết README.md: hướng dẫn setup, chạy dev, chạy ingestion, cấu trúc thư mục
