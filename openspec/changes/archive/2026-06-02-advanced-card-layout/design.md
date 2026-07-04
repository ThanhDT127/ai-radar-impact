## Context

`InsightCard.tsx` hiện tại hiển thị danh sách dài các bullet points (tối đa 5 dòng) khiến thẻ chiếm nhiều diện tích dọc và khó quét thông tin nhanh. Các thuộc tính thực hành có giá trị kỹ thuật cao như `has_code_example`, `has_benchmark`, `has_api_change`, và `has_security_patch` (được trả về trong API payload dưới dạng boolean) hiện chưa được làm nổi bật trên giao diện thẻ.

Việc thiết kế lại thẻ theo mô hình 2 vùng chuyên biệt sẽ giúp tận dụng tối đa các thuộc tính này, biến chúng thành các "tín hiệu dẫn đường" trực quan cho kỹ sư trước khi họ quyết định đọc chi tiết bài viết.

## Goals / Non-Goals

**Goals:**
- Tái cấu trúc giao diện thẻ để chừa không gian hiển thị hàng "Tín hiệu Kỹ thuật" nằm ngay dưới Tiêu đề.
- Hiển thị trực quan các badge tín hiệu kỹ thuật (`Có code mẫu`, `Có benchmark`, `Thay đổi API`, `Bảo mật`) nếu trường dữ liệu tương ứng có giá trị là `true`.
- Giới hạn số lượng bullet points tối đa trên thẻ xuống còn 3 dòng thay vì 5 dòng để đảm bảo tính scannable.

**Non-Goals:**
- Không thay đổi thiết kế trang chi tiết (`InsightDetail`).
- Không thêm các bộ lọc hay tính năng tìm kiếm mới.

## Decisions

### 1. Hiển thị hàng Tín hiệu Kỹ thuật (Technical Signals Row)
Ta sẽ định nghĩa một component phụ hoặc một khối JSX trong `InsightCard` để hiển thị các tín hiệu kỹ thuật:
```tsx
const hasSignals = insight.has_code_example || insight.has_benchmark || insight.has_api_change || insight.has_security_patch;

{hasSignals && (
  <div className={styles.technicalSignalsRow}>
    {insight.has_code_example && <span className={styles.signalBadge}>💻 Có code mẫu</span>}
    {insight.has_benchmark && <span className={styles.signalBadge}>📊 Có benchmark</span>}
    {insight.has_api_change && <span className={styles.signalBadge}>🔗 Thay đổi API</span>}
    {insight.has_security_patch && <span className={styles.signalBadge}>🛡️ Bảo mật</span>}
  </div>
)}
```

### 2. Tinh gọn số lượng gạch đầu dòng (Bullets Reduction)
Hàm `generateCardBullets` (hoặc logic lấy bullets) sẽ được tinh chỉnh lại để chỉ trả về tối đa 3 dòng:
```typescript
return bullets.slice(0, 3);
```
Điều này đảm bảo chiều cao của các thẻ trên Dashboard luôn đồng đều và cân đối, ngay cả khi hiển thị thêm hàng tín hiệu kỹ thuật.

### 3. Module ảnh hưởng
- **M6: Dashboard (InsightCard)**.

## Risks / Trade-offs

- **Giảm số lượng bullet points trên card:** Việc chỉ hiện tối đa 3 bullets có thể làm bớt đi một số thông tin chi tiết. Tuy nhiên, người dùng hoàn toàn có thể xem đầy đủ các phân tích sâu hơn ở trang chi tiết (`InsightDetail`). Lợi ích mang lại là giao diện Dashboard gọn gàng, thoáng đãng và có tính định hướng kỹ thuật cao hơn nhiều.
