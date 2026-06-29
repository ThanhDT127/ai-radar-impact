## Context

Hiện tại, trong Dashboard của hệ thống **AI Radar Impact** (Module M6), thẻ thông tin `InsightCard` đang gặp vấn đề trùng lặp nội dung hiển thị giữa Tiêu đề hiển thị (`displayTitle`) và các dòng gạch đầu dòng tóm tắt (`bullets`). 

Cụ thể, khi một bản tin có tiêu đề gốc bằng tiếng Anh (không có tiếng Việt), hệ thống sử dụng trường `summary_short` làm tiêu đề hiển thị trên UI thông qua hàm `makeDisplayTitle`. Tuy nhiên, trong hàm `generateCardBullets`, trường `summary_short` lại tiếp tục được phân tách thành các câu độc lập và thêm vào danh sách `bullets`. Điều này dẫn đến việc tiêu đề của thẻ và các bullet points của thẻ hiển thị cùng một nội dung (hoặc các câu trích xuất từ cùng một đoạn văn), gây rối mắt và làm giảm tính chuyên nghiệp của giao diện.

## Goals / Non-Goals

**Goals:**
- Loại bỏ sự trùng lặp thông tin giữa tiêu đề hiển thị (`displayTitle`) và danh sách gạch đầu dòng (`bullets`) trên thẻ `InsightCard`.
- Sửa đổi hàm `generateCardBullets` trong [InsightCard.tsx](file:///d:/Works/AI%20Radar%20Impact/frontend/src/components/InsightCard.tsx) để nhận thêm tham số `displayTitle` và lọc bỏ các câu thuộc `summary_short` nếu trường này đã được sử dụng làm `displayTitle`.
- Đảm bảo thẻ vẫn hiển thị tối đa 5 gạch đầu dòng chất lượng từ các trường dữ liệu khác (`signal`, `so_what`, `why_it_matters`).

**Non-Goals:**
- Không thay đổi cấu trúc DB hay dữ liệu trả về từ API Backend.
- Không sửa đổi prompt hay logic phân tích của mô hình AI Gemini.
- Không thay đổi giao diện chung hay CSS của `InsightCard`.

## Decisions

### 1. Cải tiến hàm `generateCardBullets`
Chúng ta sẽ thay đổi chữ ký hàm `generateCardBullets` để nhận thêm tham số `displayTitle`:
```typescript
function generateCardBullets(insight: InsightListItem, displayTitle?: string): string[]
```
Bên trong hàm, ta sẽ kiểm tra điều kiện:
Nếu `insight.summary_short` bằng với `displayTitle`, ta sẽ bỏ qua bước phân tách và thêm các câu từ `summary_short` vào mảng `bullets`. Điều này giúp tránh trùng lặp hoàn toàn khi `summary_short` được dùng làm tiêu đề hiển thị.

### 2. Cập nhật nơi gọi hàm trong `InsightCard`
Trong component `InsightCard`, ta sẽ truyền giá trị `displayTitle` đã được tính toán từ trước vào hàm `generateCardBullets`:
```typescript
const displayTitle = makeDisplayTitle(insight);
const bullets = generateCardBullets(insight, displayTitle);
```

### 3. Module ảnh hưởng
- **Module M6: Dashboard (InsightCard)**.

## Risks / Trade-offs

- **Giảm số lượng bullet points:** Khi bỏ qua `summary_short`, số lượng bullets của một số thẻ có thể giảm xuống (chỉ còn từ các trường `signal`, `so_what`, `why_it_matters`). Tuy nhiên, điều này hoàn toàn được chấp nhận vì chất lượng thông tin hiển thị sẽ tinh gọn hơn, tránh trùng lặp dư thừa. Nếu một bản tin thiếu cả 3 trường `signal`, `so_what`, `why_it_matters` (trường hợp rất hiếm do AI phân tích luôn bắt buộc các trường này), thẻ sẽ chỉ hiển thị ít bullet points hơn hoặc không hiển thị phần bullets, điều này cũng giúp giao diện gọn gàng hơn.
