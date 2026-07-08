## 1. T4 — Tinh gọn arXiv (DB/seed)

- [x] 1.1 Thêm 4 nguồn arXiv vào `seed_sources.py`: `cs.CV`, `eess.AS`, `cs.RO`, `cs.HC` (host `rss.arxiv.org`, `status="active"`, `target_roles` phù hợp). **DoD:** 4 entry mới; feed fetch trả bài. (P1)
- [x] 1.2 Đặt `status="inactive"` cho `arXiv CS.SE` và `arXiv CS.CR`. **DoD:** hai nguồn không còn được ingest sau re-seed. (P1)
- [x] 1.3 Chuẩn hoá host `arXiv CS.IR` từ `export.arxiv.org` → `rss.arxiv.org`. **DoD:** feed_url mới trả bài. (P1)

## 2. T4 — Sửa bug seed() bỏ qua status (Backend)

- [x] 2.1 Thêm `existing.status = data.get("status", "active")` vào nhánh update của `seed()` (`seed_sources.py:867–876`). **DoD:** re-seed nguồn có `status="inactive"` → row DB chuyển inactive; nguồn `active` giữ active. (P1)
- [x] 2.2 Chạy re-seed local, xác nhận cs.SE/cs.CR chuyển `inactive` trong DB. **DoD:** query DB xác nhận; `run_ingestion` bỏ qua hai nguồn. (P1)

## 3. T6 — Hợp nhất & backfill target_roles (DB/seed)

- [x] 3.1 Cập nhật closed set `target_roles` = 13 ALLOWED_ROLES trong spec `source-region-tagging` (đã ADDED/MODIFIED ở specs của change này). **DoD:** spec liệt đủ 13 role. (P1)
- [x] 3.2 Thay tag chức danh trong seed bằng ALLOWED_ROLES (Tech Lead→Engineering; Data Scientist/AI Engineer/Data Engineer→Data/AI; Dev→Engineering). **DoD:** grep seed không còn tag chức danh ngoài ALLOWED_ROLES. (P1)
- [x] 3.3 Backfill `target_roles` cho 19 nguồn chưa gắn (arXiv, OpenAI Blog, HackerNews, Reddit…), dùng ALLOWED_ROLES. **DoD:** 70/70 nguồn có `target_roles` không rỗng. (P1)

## 4. T6 — Audit & seed bù (DB/seed)

- [x] 4.1 Viết audit đếm số nguồn active theo từng vai trò → bảng độ phủ (script hoặc query SQL). **DoD:** có bảng "vai trò → số nguồn". (P1)
- [x] 4.2 Chốt phạm vi vai trò cần phủ với Hưng/anh Thanh (quyết định mở ở design §5). **DoD:** danh sách vai trò mục tiêu được xác nhận. (P1) → **Chốt:** chỉ phủ vai trò kỹ thuật (bỏ Content/Marketing & HR/L&D); nâng vai trò kỹ thuật mỏng lên ≥5.
- [x] 4.3 Seed bù tối thiểu cho vai trò mỏng (Infrastructure/Legal/BA-QA/Product/Designer-UX theo dự kiến); mỗi nguồn mới verify feed chạy thật. **DoD:** vai trò mục tiêu đạt ngưỡng đã chốt; nguồn mới cào được dữ liệu. (P1)

## 5. Verification

- [x] 5.1 Chạy `seed_sources` local end-to-end không lỗi. **DoD:** log "Seed complete", không exception. (P1)
- [x] 5.2 Verify arXiv: 4 nhánh mới trả bài; cs.SE/cs.CR không ingest. **DoD:** kiểm tra raw_documents theo source. (P1)
- [x] 5.3 In lại bảng độ phủ sau seed bù, đối chiếu mục tiêu. **DoD:** bảng cuối đạt DoD của T6. (P1)
