## ADDED Requirements

### Requirement: Tải đầy đủ nội dung bài viết từ trang gốc cho các nguồn tin RSS chỉ có tóm tắt ngắn
Khi nguồn tin RSS được cấu hình cờ `"fetch_full_content": true` trong config, hệ thống phải cào và trích xuất nội dung toàn văn từ trang đích thay vì chỉ lưu nội dung tóm tắt ngắn từ XML feed.

#### Scenario: Cào nội dung toàn văn thành công
- **WHEN** Connector thực hiện cào nguồn tin RSS có cờ `"fetch_full_content": true` và `WebArticleConnector` cào thành công bài viết gốc từ URL.
- **THEN** Trường `raw_content` và `author` của entry sẽ được cập nhật bằng nội dung đầy đủ cào được, trước khi đi vào Normalizer và lưu vào DB.

#### Scenario: Cào nội dung thất bại và tự động fallback về tóm tắt ngắn
- **WHEN** Connector thực hiện cào nguồn tin RSS có cờ `"fetch_full_content": true` nhưng `WebArticleConnector` cào thất bại (lỗi mạng, bị block hoặc trả về rỗng).
- **THEN** Hệ thống giữ nguyên nội dung tóm tắt ngắn từ XML feed để lưu làm `raw_content`, đảm bảo tiến trình ingestion không bị gián đoạn.
