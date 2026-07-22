## MODIFIED Requirements

### Requirement: Source phải có thuộc tính `target_roles`

Source MUST có ARRAY các vai trò mà nguồn này phục vụ chính. Giá trị `target_roles` MUST thuộc bộ **ALLOWED_ROLES** đầy đủ (13 vai trò) — thống nhất với taxonomy vai trò của hệ thống, không dùng chức danh ngoài bộ này.

#### Scenario: Target roles closed set (ALLOWED_ROLES đầy đủ)
- **WHEN** tạo hoặc cập nhật source với `target_roles`
- **THEN** mỗi role thuộc closed set: `Executive`, `Engineering`, `Data/AI`, `Product`, `Content/Marketing`, `Legal/Compliance`, `HR/L&D`, `DevOps`, `Infrastructure`, `Security`, `BA/QA`, `Designer/UX`, `Toàn công ty`

#### Scenario: Không dùng tag chức danh
- **WHEN** seed dùng tag chức danh cũ (`Tech Lead`, `Data Scientist`, `AI Engineer`, `Data Engineer`, `Dev`)
- **THEN** phải ánh xạ về ALLOWED_ROLES trước khi lưu: `Tech Lead`→`Engineering`; `Data Scientist`/`AI Engineer`/`Data Engineer`→`Data/AI`; `Dev`→`Engineering`

#### Scenario: Target roles mặc định rỗng
- **WHEN** tạo source không truyền `target_roles`
- **THEN** value = `[]` (không null)

## ADDED Requirements

### Requirement: Backfill target_roles cho nguồn chưa gắn

Mọi source active MUST có `target_roles` không rỗng để đo được độ phủ vai trò. Các nguồn cũ chưa gắn (arXiv, OpenAI Blog, HackerNews, Reddit…) MUST được backfill bằng ALLOWED_ROLES phù hợp nội dung.

#### Scenario: Backfill nguồn thiếu tag
- **WHEN** chạy seed/backfill trên nguồn có `target_roles = []`
- **THEN** nguồn được gán ≥1 role thuộc ALLOWED_ROLES phản ánh đúng nội dung (ví dụ `arXiv CS.CL` → `{Data/AI, Engineering}`)
- **THEN** sau backfill, mọi source active có `target_roles` không rỗng

### Requirement: Audit độ phủ vai trò

Hệ thống MUST cung cấp cách đếm số nguồn active theo từng vai trò để đánh giá độ phủ. Mỗi vai trò kỹ thuật trong phạm vi triển khai SHOULD đạt ngưỡng độ phủ đã chốt (mục tiêu ≥5 nguồn khi khả thi), và MUST không có vai trò kỹ thuật nào 0 nguồn sau backfill.

#### Scenario: Bảng độ phủ vai trò
- **WHEN** chạy audit sau khi backfill
- **THEN** sinh được bảng "vai trò → số nguồn active" cho toàn bộ ALLOWED_ROLES
- **THEN** không vai trò kỹ thuật nào (Engineering, Data/AI, Security, DevOps, Infrastructure, BA/QA) có 0 nguồn

#### Scenario: Vai trò ngoài phạm vi ưu tiên
- **WHEN** vai trò `Content/Marketing` hoặc `HR/L&D` chưa đạt 5 nguồn
- **THEN** được phép < 5 nếu công ty không ưu tiên (quyết định phạm vi ghi trong change), không tính là thất bại DoD
