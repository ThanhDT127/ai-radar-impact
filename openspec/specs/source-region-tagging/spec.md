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

Source MUST có ARRAY các vai trò mà nguồn này phục vụ chính.

#### Scenario: Target roles closed set
- **WHEN** tạo source với `target_roles`
- **THEN** mỗi role thuộc closed set: `Executive`, `Engineering`, `Data/AI`, `Product`, `Content/Marketing`, `Legal/Compliance`, `HR/L&D`, `Toàn công ty`

#### Scenario: Target roles mặc định rỗng
- **WHEN** tạo source không truyền `target_roles`
- **THEN** value = `[]` (không null)

### Requirement: Source response API trả `region` và `target_roles`

Admin API MUST trả `region` và `target_roles` trong source response.

#### Scenario: Admin GET source
- **WHEN** admin gọi `GET /api/v1/admin/sources`
- **THEN** mỗi source trong response có `region` và `target_roles`

