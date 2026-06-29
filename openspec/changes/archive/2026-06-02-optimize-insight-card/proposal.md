## Why

Hiện tại, thẻ thông tin bản tin (`InsightCard`) hiển thị tiêu đề và nội dung gạch đầu dòng (`bullets`) bị trùng lặp thông tin trực quan. Đối với các bài viết có tiêu đề gốc là tiếng Anh, hệ thống sử dụng trường `summary_short` làm tiêu đề hiển thị trên UI. Tuy nhiên, ở phần gạch đầu dòng tóm tắt bên dưới, hàm `generateCardBullets` vẫn tiếp tục sinh ra bullet point từ chính `summary_short` đó. Điều này gây lãng phí không gian hiển thị, làm giảm độ thẩm mỹ và tính chuyên nghiệp của Dashboard.

## What Changes

- **Frontend Component (`InsightCard.tsx`):**
  - Cải tiến hàm `generateCardBullets` để tự động lọc bỏ `summary_short` khỏi mảng bullets được hiển thị trên thẻ nếu `summary_short` đã được chọn làm tiêu đề hiển thị (`displayTitle`).
  - Đảm bảo cơ chế fallback vẫn hoạt động bình thường, giữ nguyên giới hạn tối đa 5 gạch đầu dòng của thẻ nhưng không chứa văn bản lặp lại tiêu đề.

### Non-goals
- Không sửa đổi cấu trúc dữ liệu lưu trong Database hay API payload trả về.
- Không thay đổi prompt sinh dữ liệu của Gemini trong backend ở đề xuất này.

### Phase áp dụng: Phase 1 (MVP)

### Dependencies
- Phụ thuộc vào Module M6 (Dashboard - InsightCard).

## Capabilities

### New Capabilities
- Không có.

### Modified Capabilities
- `insight-dashboard`: Thay đổi cách hiển thị các gạch đầu dòng (`bullets`) trên thẻ `InsightCard` để loại bỏ trùng lặp với tiêu đề dịch.

## Impact

- **Frontend:** File [InsightCard.tsx](file:///d:/Works/AI%20Radar%20Impact/frontend/src/components/InsightCard.tsx).
