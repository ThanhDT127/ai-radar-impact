## MODIFIED Requirements

### Requirement: Dashboard chỉ hiện primary
`GET /api/v1/insights` mặc định MUST chỉ trả primary insights. Ràng buộc "chỉ tính primary" áp cho **mọi**
bề mặt hướng người dùng của insight — cả danh sách lẫn **các con số đếm**. Bất kỳ endpoint nào trả về
số lượng insight cho người dùng (KPI thống kê, số insight theo nguồn) MUST đếm theo đại diện cụm
(`is_primary = true`), KHÔNG được đếm bản trùng đã bị gộp. Số hiển thị và số bản ghi người dùng bấm
vào xem được MUST khớp nhau.

#### Scenario: Default list
- **WHEN** gọi `GET /api/v1/insights` không có filter đặc biệt
- **THEN** chỉ trả insights có `is_primary = true` hoặc `cluster_id IS NULL`

#### Scenario: KPI thống kê không đếm bản trùng
- **WHEN** gọi `GET /api/v1/insights/stats` trong lúc DB có insight `published` với `is_primary = false`
- **THEN** cả `total`, `critical_high` và `opportunities` chỉ đếm insight `is_primary = true`

#### Scenario: Đếm insight theo nguồn khớp với danh sách
- **WHEN** gọi `GET /api/v1/sources` và một nguồn có N insight `published` trong đó chỉ M cái `is_primary = true` (M < N)
- **THEN** `insight_count` của nguồn đó bằng **M**, đúng bằng `total` mà `GET /api/v1/insights?source_id=<nguồn>` trả về

#### Scenario: Nguồn chỉ toàn bản trùng
- **WHEN** một nguồn có insight `published` nhưng tất cả đều `is_primary = false`
- **THEN** `insight_count` của nguồn đó bằng `0` (nguồn được xếp vào nhóm "chưa có insight", không thành chip lọc rỗng)
