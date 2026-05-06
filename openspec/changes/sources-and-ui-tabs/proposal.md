# Proposal: Expand Sources & UI Tabs Redesign

## Vấn đề

1. **Nguồn dữ liệu hạn chế:** Hệ thống hiện chỉ có 1 nguồn (GitHub Changelog). Theo spec `07_source_strategy`, Phase 1 cần tối thiểu 15-30 nguồn để đảm bảo coverage đa lĩnh vực: AI vendors, tech press, arXiv, nguồn tiếng Việt.

2. **UI không đáp ứng nhu cầu phân loại:** Dashboard hiện tại chỉ là 1 list phẳng, không có:
   - Tab phân loại theo nguồn, vai trò
   - KPI summary (tổng insights, critical, opportunities)
   - Sort options (mới nhất, ảnh hưởng cao nhất)
   - Filter chips cho multi-select
   - Hiển thị thời gian publish

## Giải pháp

### Vấn đề 1 — Mở rộng nguồn
- Seed thêm 14 nguồn RSS vào database (tổng 15 nguồn)
- Bao gồm: AI vendors (OpenAI, Anthropic, Google AI, DeepMind), Cloud (AWS), arXiv (3 categories), Tech press (IEEE, Ars Technica), nguồn Việt (VnExpress)
- Tạo script verify RSS URLs trước khi seed
- Verify ingestion hoạt động với tất cả sources

### Vấn đề 2 — UI Tabs Redesign
- Redesign frontend với 3 tabs: Tổng quan / Theo nguồn / Theo vai trò
- Thêm KPI summary bar
- Sort dropdown cho mỗi tab
- Filter chips multi-select cho nguồn và vai trò
- Insight card redesign: thêm published_at, source name, role badges
- Responsive design

## Phạm vi

- Backend: seed script, verify script, API endpoint `/sources`
- Frontend: toàn bộ UI refactor
- Phụ thuộc: Change `vi-taxonomy-and-roles` phải hoàn thành trước (cần roles + published_at + tiếng Việt)

## Phụ thuộc

> Change này phụ thuộc `vi-taxonomy-and-roles` đã merge — cần:
> - Taxonomy tiếng Việt (hiển thị trên UI)
> - `affected_roles` field (tab Theo vai trò)
> - `published_at` field (hiển thị thời gian publish)
> - API filter/sort params (role, sort_by)
