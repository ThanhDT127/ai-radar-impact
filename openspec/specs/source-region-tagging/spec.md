# source-region-tagging Specification

## Purpose
TBD - created by archiving change add-china-ai-sources. Update Purpose after archive.
## Requirements
### Requirement: Source phải có thuộc tính `region`

Mọi source trong `sources` table MUST có giá trị `region` thuộc closed set.

#### Scenario: Region values
- **WHEN** tạo hoặc cập nhật source
- **THEN** `region` ∈ {`global`, `china`, `vietnam`}
- **THEN** mặc định = `global` nếu không truyền

#### Scenario: Backfill 18 sources cũ
- **WHEN** migration được chạy
- **THEN** mọi source cũ có `region` = `global` (trừ VnExpress Số hóa = `vietnam`)

### Requirement: Source phải có thuộc tính `target_roles`

Source MUST có ARRAY các vai trò mà nguồn này phục vụ chính. Giá trị `target_roles` MUST thuộc bộ
**TARGET_ROLE_TAXONOMY** (13 vai trò theo chức năng phòng ban, định nghĩa tại
`app/scripts/audit_target_roles.py`).

> Bộ này **khác** `ALLOWED_ROLES` (9 chức danh) dùng cho `insights.affected_roles` — xem spec
> `ai-analysis`. Không dùng lẫn: `target_roles` là metadata chiến lược nguồn, không hiển thị trên insight.

#### Scenario: Target roles closed set (TARGET_ROLE_TAXONOMY)
- **WHEN** tạo hoặc cập nhật source với `target_roles`
- **THEN** mỗi role thuộc closed set: `Executive`, `Engineering`, `Data/AI`, `Product`, `Content/Marketing`, `Legal/Compliance`, `HR/L&D`, `DevOps`, `Infrastructure`, `Security`, `BA/QA`, `Designer/UX`, `Toàn công ty`

#### Scenario: Không dùng chức danh của ALLOWED_ROLES
- **WHEN** seed dùng chức danh thuộc `ALLOWED_ROLES` (`Tech Lead`, `Data Scientist`, `AI Engineer`, `Data Engineer`, `Dev`)
- **THEN** phải ánh xạ về TARGET_ROLE_TAXONOMY trước khi lưu: `Tech Lead`→`Engineering`; `Data Scientist`/`AI Engineer`/`Data Engineer`→`Data/AI`; `Dev`→`Engineering`

#### Scenario: Target roles mặc định rỗng
- **WHEN** tạo source không truyền `target_roles`
- **THEN** value = `[]` (không null)

### Requirement: Source response API trả `region` và `target_roles`

Admin API MUST trả `region` và `target_roles` trong source response.

#### Scenario: Admin GET source
- **WHEN** admin gọi `GET /api/v1/admin/sources`
- **THEN** mỗi source trong response có `region` và `target_roles`

### Requirement: Backfill target_roles cho nguồn chưa gắn

Mọi source active MUST có `target_roles` không rỗng để đo được độ phủ vai trò. Các nguồn cũ chưa gắn (arXiv, OpenAI Blog, HackerNews, Reddit…) MUST được backfill bằng TARGET_ROLE_TAXONOMY phù hợp nội dung.

#### Scenario: Backfill nguồn thiếu tag
- **WHEN** chạy seed/backfill trên nguồn có `target_roles = []`
- **THEN** nguồn được gán ≥1 role thuộc TARGET_ROLE_TAXONOMY phản ánh đúng nội dung (ví dụ `arXiv CS.CL` → `{Data/AI, Engineering}`)
- **THEN** sau backfill, mọi source active có `target_roles` không rỗng

### Requirement: Audit độ phủ vai trò

Hệ thống MUST cung cấp cách đếm số nguồn active theo từng vai trò để đánh giá độ phủ. Mỗi vai trò kỹ thuật trong phạm vi triển khai SHOULD đạt ngưỡng độ phủ đã chốt (mục tiêu ≥5 nguồn khi khả thi), và MUST không có vai trò kỹ thuật nào 0 nguồn sau backfill.

#### Scenario: Bảng độ phủ vai trò
- **WHEN** chạy audit sau khi backfill
- **THEN** sinh được bảng "vai trò → số nguồn active" cho toàn bộ TARGET_ROLE_TAXONOMY
- **THEN** không vai trò kỹ thuật nào (Engineering, Data/AI, Security, DevOps, Infrastructure, BA/QA) có 0 nguồn

#### Scenario: Vai trò ngoài phạm vi ưu tiên
- **WHEN** vai trò `Content/Marketing` hoặc `HR/L&D` chưa đạt 5 nguồn
- **THEN** được phép < 5 nếu công ty không ưu tiên (quyết định phạm vi ghi trong change), không tính là thất bại DoD

