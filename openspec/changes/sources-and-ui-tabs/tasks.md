## 1. Backend — Seed Sources (P1)

- [ ] 1.1 Tạo `backend/app/scripts/verify_feeds.py` — script verify tất cả RSS URLs (fetch + parse + in sample)
- [ ] 1.2 Chạy `verify_feeds.py` → xác nhận 14 URLs mới hoạt động, fix URLs nào bị lỗi
- [ ] 1.3 Sửa `backend/app/scripts/seed_sources.py` — thêm 14 nguồn mới vào `INITIAL_SOURCES` (tổng 15)
- [ ] 1.4 Chạy `seed_sources` → verify 15 sources trong DB
- [ ] 1.5 Chạy `run_ingestion` → verify mỗi source fetch được articles (check logs)
- [ ] 1.6 Verify: arXiv RSS parse đúng (title, abstract, authors)
- [ ] 1.7 Verify: VnExpress RSS parse đúng tiếng Việt (encoding UTF-8)

## 2. Backend — API Mới (P1)

- [ ] 2.1 Tạo `backend/app/routes/sources.py` — `GET /api/v1/sources` endpoint (list sources với insight_count)
- [ ] 2.2 Tạo `backend/app/schemas/source.py` — `SourceListItem` schema (id, name, source_type, status, insight_count)
- [ ] 2.3 Tạo `backend/app/routes/insights_stats.py` — `GET /api/v1/insights/stats` endpoint (tổng, critical, opportunities, active sources)
- [ ] 2.4 Sửa `backend/app/routes/insights.py` — thêm query param `source_id` (filter theo source)
- [ ] 2.5 Sửa `backend/app/repositories/insight_repo.py` — filter logic cho `source_id`
- [ ] 2.6 Register routes mới vào `backend/app/main.py`
- [ ] 2.7 Verify: `GET /api/v1/sources` → trả 15 sources với counts
- [ ] 2.8 Verify: `GET /api/v1/insights/stats` → trả KPI data
- [ ] 2.9 Verify: `GET /api/v1/insights?source_id=<uuid>` → chỉ trả insights từ source đó

## 3. Frontend — Component mới (P2)

- [ ] 3.1 Tạo `frontend/src/components/TabBar.tsx` — Tab navigation (Tổng quan / Theo nguồn / Theo vai trò)
- [ ] 3.2 Tạo `frontend/src/components/KPISummary.tsx` — 4 KPI cards (tổng, critical, cơ hội, nguồn)
- [ ] 3.3 Tạo `frontend/src/components/SortDropdown.tsx` — Dropdown sort (Mới nhất / Ảnh hưởng / Tin cậy)
- [ ] 3.4 Tạo `frontend/src/components/FilterChips.tsx` — Multi-select filter chips (generic, dùng cho cả source và role)
- [ ] 3.5 Tạo `frontend/src/components/RoleBadge.tsx` — Badge hiển thị role name với màu
- [ ] 3.6 Tạo `frontend/src/components/RelativeTime.tsx` — Hiển thị "2 giờ trước", "Hôm qua", v.v.
- [ ] 3.7 Tạo styles mới trong `frontend/src/styles/` cho tabs, chips, KPI, sort

## 4. Frontend — Refactor InsightList thành Tabbed Layout (P2)

- [ ] 4.1 Refactor `frontend/src/pages/InsightList.tsx`:
  - Thêm TabBar ở đầu trang
  - State management cho active tab, filters, sort
  - Mỗi tab render cùng InsightCard list nhưng khác filter params
- [ ] 4.2 Tab 1 (Tổng quan):
  - KPI Summary bar
  - Sort Dropdown
  - Insight Card list (mặc định sort newest)
- [ ] 4.3 Tab 2 (Theo nguồn):
  - Fetch sources từ `GET /api/v1/sources`
  - FilterChips hiển thị sources + count badges
  - Click chip → filter insights theo source_id
  - Multi-select support
- [ ] 4.4 Tab 3 (Theo vai trò):
  - FilterChips hiển thị 8 roles
  - Click chip → filter insights theo role
  - Multi-select support
- [ ] 4.5 Tạo `frontend/src/api/sources.ts` — fetch sources API
- [ ] 4.6 Tạo `frontend/src/api/stats.ts` — fetch stats API

## 5. Frontend — Insight Card & Detail Redesign (P2)

- [ ] 5.1 Sửa `frontend/src/components/InsightCard.tsx`:
  - Thêm nguồn name
  - Thêm RelativeTime cho published_at
  - Thêm RoleBadge(s) cho affected_roles
  - Layout cải thiện
- [ ] 5.2 Sửa `frontend/src/pages/InsightDetail.tsx`:
  - Thêm section "Vai trò ảnh hưởng" với role badges
  - Thêm published_at + created_at timestamps
  - Thêm source name + link
- [ ] 5.3 Sửa CSS: responsive layout cho tabs, chips, KPI (mobile/tablet/desktop)

## 6. End-to-End Verification (P3)

- [ ] 6.1 Chạy full pipeline (15 sources): ingestion → analysis → verify dashboard
- [ ] 6.2 Browser: 3 tabs chuyển đổi smooth, không reload page
- [ ] 6.3 Browser Tab 1: KPI hiển thị đúng, sort hoạt động
- [ ] 6.4 Browser Tab 2: Filter chips hiển thị sources, count badges đúng, multi-select hoạt động
- [ ] 6.5 Browser Tab 3: Filter chips roles, multi-select hoạt động
- [ ] 6.6 Browser: Insight detail page hiển thị roles, published_at, source name
- [ ] 6.7 Browser: Responsive — viewport 375px → layout stack đúng
- [ ] 6.8 Browser: Kiểm tra arXiv insights parse đúng
- [ ] 6.9 Browser: Kiểm tra VnExpress insights hiển thị tiếng Việt
