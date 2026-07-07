## ADDED Requirements

### Requirement: Daily analysis cap persist qua Database

Hệ thống SHALL giới hạn số tài liệu phân tích mỗi ngày (`max_daily_analysis`, mặc định 500) bằng bộ đếm **persist trong DB**, đúng xuyên nhiều tiến trình và sống sót qua restart. Bộ đếm SHALL tính **mọi** tài liệu đã gọi Gemini (đạt trạng thái terminal `analyzed`, `low_signal`, hoặc `failed`), không chỉ tài liệu tạo được insight.

#### Scenario: Cap không reset giữa các lần chạy

- **WHEN** một tiến trình `run_analysis`/scheduler mới khởi động trong cùng ngày
- **THEN** số đã dùng được đọc từ DB (`COUNT(*) WHERE analyzed_at::date = today`), KHÔNG reset về 0
- **AND** `daily_remaining = max_daily_analysis - daily_used` phản ánh đúng tổng đã xử lý trong ngày

#### Scenario: Đếm cả doc bị gate loại và failed

- **WHEN** một tài liệu bị gate loại (`low_signal`) hoặc `failed` (vẫn tốn ≥1 gate call)
- **THEN** `analyzed_at` được set và tài liệu đó được tính vào cap trong ngày

#### Scenario: Dừng khi chạm cap

- **WHEN** `daily_used >= max_daily_analysis`
- **THEN** bước analysis dừng, log cảnh báo, KHÔNG gọi Gemini thêm cho tới ngày hôm sau

#### Scenario: Reset theo ngày

- **WHEN** sang ngày mới (theo UTC)
- **THEN** `daily_used` tính lại từ 0 do đếm theo `analyzed_at::date = today`
