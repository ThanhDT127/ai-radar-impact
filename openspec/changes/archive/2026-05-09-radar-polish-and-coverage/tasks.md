## 1. Bug fix: Card duplicate badge

- [x] 1.1 Cập nhật `frontend/src/components/InsightCard.tsx` — render conditional: `urgency ? <UrgencyBadge> : <ImpactBadge>`
- [x] 1.2 Cập nhật `frontend/src/pages/InsightDetail.tsx` — same logic ở header
- [x] 1.3 Verify visual: insight cũ (urgency=null) vẫn hiện ImpactBadge; insight mới chỉ hiện UrgencyBadge

## 2. Bug fix: MomentumIndicator chỉ render rising

- [x] 2.1 Cập nhật `frontend/src/components/MomentumIndicator.tsx` — early return null cho `new` và `mature`
- [x] 2.2 Xóa entry `new` khỏi `MOMENTUM_LABEL` map (không còn dùng)
- [x] 2.3 Verify: card không còn hiện "✨ Mới" pill; chỉ "🔥 Đang nổi lên" cho insight rising

## 3. Mở rộng ALLOWED_ROLES (5 vai trò mới)

- [x] 3.1 Cập nhật `backend/app/ai/prompts.py` — `ALLOWED_ROLES` thêm: `DevOps`, `Infrastructure`, `Security`, `BA/QA`, `Designer/UX` (tổng 13)
- [x] 3.2 Cập nhật prompt template — đảm bảo `{roles}` chứa 13 giá trị mới
- [x] 3.3 Cập nhật `CLAUDE.md` Section "Vietnamese Taxonomy" — liệt kê 13 roles + mô tả phân biệt với Engineering

## 4. RoleBadge hỗ trợ 5 role mới

- [x] 4.1 Cập nhật `frontend/src/components/RoleBadge.tsx` — thêm color mapping cho 5 role: DevOps (cyan), Infrastructure (indigo), Security (red-orange), BA/QA (emerald), Designer/UX (fuchsia)
- [x] 4.2 Cập nhật `frontend/src/styles/insights.module.css` — thêm class `roleDevops`, `roleInfrastructure`, `roleSecurity`, `roleBaqa`, `roleDesigner`
- [x] 4.3 Verify role label render đúng trong card + detail page

## 5. Seed sub-channel sources

- [x] 5.1 Verify URL hoạt động cho 6 endpoints (chạy `verify_feeds.py` hoặc curl):
  - https://aws.amazon.com/blogs/security/feed/
  - https://aws.amazon.com/blogs/compute/feed/
  - https://export.arxiv.org/rss/cs.IR
  - https://export.arxiv.org/rss/cs.SE
  - https://export.arxiv.org/rss/cs.CR
  - HF Papers (cần điều tra endpoint)
- [x] 5.2 Cập nhật `backend/app/scripts/seed_sources.py` — thêm 5-6 sources mới (idempotent)
- [x] 5.3 Mỗi source có `target_roles` chính xác (theo bảng trong design D5)
- [x] 5.4 HF Papers: nếu không có RSS chính thức, skip + log; document trong system_overview.md

## 6. Ingestion + Verification

- [x] 6.1 Chạy `seed_sources` trên dev DB — verify 5-6 rows mới hoặc skipped đúng
- [x] 6.2 Chạy `run_ingestion --source-id <new>` cho 1-2 source mới — verify raw_documents được tạo
- [x] 6.3 Chạy `run_analysis` — verify Gemini trả role mới (DevOps/Security) trong `affected_roles`
- [x] 6.4 Verify frontend render insight có role mới với màu đúng

## 7. Documentation

- [x] 7.1 Cập nhật `CLAUDE.md` Section "Affected Roles" — 13 roles
- [x] 7.2 Cập nhật `docs/system_overview.md` — note về sub-channel sources và momentum UI behavior
- [x] 7.3 Cập nhật `openspec/specs/ai-analysis/spec.md` (sync sau archive)
- [x] 7.4 Cập nhật `openspec/specs/insight-dashboard/spec.md` (sync sau archive)
- [x] 7.5 Cập nhật `openspec/specs/rss-ingestion/spec.md` (sync sau archive)

## 8. Verification cuối

- [x] 8.1 Build backend: `docker-compose up -d --build backend` — không lỗi
- [x] 8.2 Build frontend: TypeScript check clean
- [x] 8.3 Mắt thấy: card không còn duplicate badge "TRUNG BÌNH"
- [x] 8.4 Mắt thấy: pill "Mới" không xuất hiện; chỉ "Đang nổi lên" khi có
- [x] 8.5 Mắt thấy: insight về security có RoleBadge "Security" màu red-orange
- [x] 8.6 Sau 24h ingestion: query DB count raw_documents từ 5-6 source mới ≠ 0
