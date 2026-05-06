# Proposal: Vietnamese Taxonomy & Roles/Published_at

## Vấn đề

1. **Ngôn ngữ:** Hiện tại toàn bộ output AI (summary, topics, event_type, nature) đều bằng tiếng Anh. Người dùng chính là người Việt — cần chuyển sang tiếng Việt hoàn toàn.

2. **Thiếu dữ liệu phân loại:** Model Insight chưa có field `affected_roles` (vai trò/phòng ban bị ảnh hưởng) và `published_at` (thời điểm bài viết gốc được công bố). Đây là 2 fields quan trọng theo spec FR-16, FR-07 và wireframe 7.2.

## Giải pháp

### Vấn đề 1 — Tiếng Việt
- Chuyển toàn bộ taxonomy (topics, event_types, natures) sang tiếng Việt
- Sửa prompt Gemini yêu cầu trả kết quả bằng tiếng Việt
- Sửa impact labels sang tiếng Việt: "Nghiêm trọng / Cao / Trung bình / Thấp / Theo dõi"
- Cập nhật UI labels frontend sang tiếng Việt

### Vấn đề 2 — Roles & Published_at
- Thêm `affected_roles` (ARRAY String) vào model Insight
- Thêm `published_at` (DateTime nullable) vào model Insight
- Sửa prompt Gemini thêm output field `affected_roles`
- Tạo Alembic migration cho 2 columns mới
- Cập nhật API schemas và routes hỗ trợ filter theo role, sort theo published_at

## Phạm vi

- Backend: prompts.py, models, migration, schemas, routes, analyzer
- Frontend: labels tiếng Việt, types update
- Không thay đổi UI layout/design (để change 2)

## Dữ liệu cũ

- Insights đã có giữ nguyên (tiếng Anh)
- Chỉ insights mới sau deploy sẽ là tiếng Việt + có roles
- Nếu muốn re-analyze: chạy `reset_failed` → `run_analysis`
