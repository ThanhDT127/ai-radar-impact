## Purpose

Bộ filter UI cho phép người dùng dashboard lọc danh sách insight theo các trường actionable đã có ở backend (`urgency`, `momentum`, `vietnam_relevance`) thông qua chip controls. Các filter này được hiển thị trên tab `Tổng quan` của dashboard và reset khi đổi tab.

## Requirements

### Requirement: Filter urgency trên dashboard
Dashboard insight list MUST cho phép lọc insights theo mức urgency thông qua chip controls.

#### Scenario: Filter một mức urgency
- **WHEN** người dùng chọn chip "Khẩn cấp" (critical)
- **THEN** danh sách chỉ hiển thị insights có `urgency = "critical"`

#### Scenario: Filter nhiều mức urgency
- **WHEN** người dùng chọn nhiều chips urgency (vd: critical + high)
- **THEN** danh sách hiển thị insights có urgency thuộc một trong các giá trị đã chọn

#### Scenario: Bỏ chọn filter
- **WHEN** người dùng bỏ chọn tất cả urgency chips
- **THEN** filter urgency bị xóa, danh sách hiển thị không lọc theo urgency

### Requirement: Filter momentum trên dashboard
Dashboard insight list MUST cho phép lọc insights theo momentum.

#### Scenario: Filter momentum = rising
- **WHEN** người dùng chọn chip "Đang nổi" (rising)
- **THEN** danh sách chỉ hiển thị insights có `momentum = "rising"`

#### Scenario: Filter momentum = new
- **WHEN** người dùng chọn chip "Mới" (new)
- **THEN** danh sách chỉ hiển thị insights có `momentum = "new"`

#### Scenario: Filter nhiều momentum
- **WHEN** người dùng chọn nhiều momentum chips
- **THEN** danh sách hiển thị insights khớp với bất kỳ giá trị đã chọn

### Requirement: Filter vietnam_relevance trên dashboard
Dashboard insight list MUST cho phép lọc insights theo mức độ liên quan đến Việt Nam.

#### Scenario: Filter vietnam_relevance = high
- **WHEN** người dùng chọn chip "Liên quan cao"
- **THEN** danh sách chỉ hiển thị insights có `vietnam_relevance = "high"`

#### Scenario: Filter kết hợp với urgency
- **WHEN** người dùng chọn vietnam_relevance = high VÀ urgency = critical
- **THEN** danh sách chỉ hiển thị insights thỏa mãn cả hai điều kiện

### Requirement: Filter reset khi đổi tab
Các filter urgency, momentum, vietnam_relevance MUST được reset về rỗng khi người dùng chuyển tab (overview/sources/roles).

#### Scenario: Reset khi đổi tab
- **WHEN** người dùng đang có filter active và chuyển sang tab khác
- **THEN** tất cả chip filters được bỏ chọn và danh sách hiển thị không lọc
