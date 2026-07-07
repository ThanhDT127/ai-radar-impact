## ADDED Requirements

### Requirement: Chạy pipeline tự động theo lịch

Hệ thống SHALL tự động chạy ingest → analysis 2–4 lần/ngày qua APScheduler nhúng trong backend, không cần thao tác tay. Scheduler SHALL bật/tắt được qua flag `ENABLE_SCHEDULER`.

#### Scenario: Chạy đúng lịch

- **WHEN** đến mốc thời gian cấu hình (mặc định 3 mốc/ngày) và `ENABLE_SCHEDULER=true`
- **THEN** hệ thống chạy `IngestionService.run()` cho toàn bộ nguồn active, tiếp nối bằng bước analysis
- **AND** ghi log xác nhận số nguồn cào và số doc mới

#### Scenario: Scheduler tắt ở môi trường dev

- **WHEN** `ENABLE_SCHEDULER=false` (hoặc chạy dưới `uvicorn --reload`)
- **THEN** scheduler KHÔNG khởi động, tránh chạy trùng job

#### Scenario: Không chồng lấn job

- **WHEN** một lần chạy scheduler chưa kết thúc mà tới mốc kế tiếp
- **THEN** job mới bị bỏ qua/gộp (`max_instances=1`, `coalesce=true`), không chạy song song trùng

### Requirement: Rate-limit tránh bị chặn

Khi cào nhiều nguồn trong một lần chạy, hệ thống SHALL giãn request (jitter/delay giữa các nguồn) để tránh 429/403, đặc biệt với X/LinkedIn/Reddit/báo VN.

#### Scenario: Giãn request giữa các nguồn

- **WHEN** scheduler cào lần lượt nhiều nguồn
- **THEN** có delay/jitter giữa các lần fetch theo cấu hình
- **AND** trong thời gian quan sát không nguồn nào bị 429/403

#### Scenario: Backoff khi bị chặn

- **WHEN** một nguồn trả 429 hoặc 403
- **THEN** hệ thống lùi thời gian thử lại (exponential backoff) thay vì fetch dồn dập
