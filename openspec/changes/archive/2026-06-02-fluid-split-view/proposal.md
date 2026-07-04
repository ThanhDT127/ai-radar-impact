## Why

Hiện tại, trang chi tiết bản tin `InsightDetail` (Module M6) chỉ có bố cục cố định 50/50 (chia đôi màn hình cho phân tích AI bên trái và bài viết gốc bên phải). Bố cục cứng nhắc này gây ra một số bất tiện về mặt trải nghiệm người dùng (UX):
* Khi người dùng chỉ muốn tập trung đọc phân tích tiếng Việt của AI, cột bài viết gốc bên phải chiếm quá nhiều diện tích thừa thãi.
* Ngược lại, khi người dùng muốn nghiên cứu sâu bài viết gốc hoặc các tài liệu kỹ thuật phức tạp bằng tiếng Anh, không gian cột phải 50% lại quá hẹp và khó theo dõi.

Cần một cơ chế **Bố cục Đọc linh hoạt (Fluid Split-View)** cho phép người dùng chủ động điều khiển và chuyển đổi qua lại giữa 3 chế độ đọc tùy nhu cầu:
1. **Split View (50/50):** Xem song song cả phân tích AI tiếng Việt và bài gốc tiếng Anh (Mặc định).
2. **Focus AI (80/20):** Dành 80% không gian cho cột phân tích AI, thu hẹp cột bài viết gốc bên phải thành một thanh sidebar nhỏ (chỉ hiển thị metadata, các liên kết nhanh và nút mở rộng lại).
3. **Focus Original (20/80):** Dành 80% không gian cho cột bài gốc, thu hẹp cột phân tích AI bên trái thành sidebar.

## What Changes

1. **Frontend Page (`InsightDetail.tsx`):**
   - Thêm trạng thái `viewMode` (kiểu dữ liệu `'split' | 'focus-ai' | 'focus-original'`) với giá trị mặc định là `'split'`.
   - Bổ sung một thanh công cụ nhỏ (toolbar) chứa 3 nút biểu tượng đại diện cho 3 chế độ đọc ở góc trên của trang chi tiết.
   - Gán CSS classes tương ứng lên phần tử container chứa grid dựa vào trạng thái `viewMode` hiện tại.
   - Cải tiến phần hiển thị của cột phải (khi ở chế độ `Focus AI`, nội dung iframe sẽ được ẩn đi hoặc thu gọn để thay thế bằng các liên kết nhanh và nút bấm "Mở rộng bài gốc").

2. **Frontend CSS (`insights.module.css`):**
   - Định nghĩa các grid layout động dựa trên CSS classes:
     * Chế độ Split: `grid-template-columns: 1fr 1fr;`
     * Chế độ Focus AI: `grid-template-columns: 4fr 1fr;`
     * Chế độ Focus Original: `grid-template-columns: 1fr 4fr;`
   - Bổ sung các hiệu ứng transition mượt mà (`transition: grid-template-columns 0.3s ease;`) khi thay đổi chế độ đọc để tạo cảm giác trơn tru, cao cấp.

## Capabilities

### New Capabilities
- `fluid-split-view`: Cung cấp tính năng chuyển đổi linh hoạt 3 chế độ đọc (Split 50/50, Focus AI 80/20, Focus Original 20/80) trên trang chi tiết bản tin.

### Modified Capabilities
- `insight-detail-layout`: Thay đổi cách dựng layout trang chi tiết để hỗ trợ bố cục cột động và transition mượt mà.

## Impact

- **Frontend:**
  - File [InsightDetail.tsx](file:///d:/Works/AI%20Radar%20Impact/frontend/src/pages/InsightDetail.tsx) — Bổ sung toolbar chuyển đổi chế độ đọc và logic gán class.
  - File [insights.module.css](file:///d:/Works/AI%20Radar%20Impact/frontend/src/styles/insights.module.css) — Thiết lập CSS grid động và transitions.

- **Backend:** Không thay đổi.

- **Non-goals:**
  - Không lưu trạng thái `viewMode` vào Database (chỉ lưu cục bộ ở Client thông qua `useState` hoặc `localStorage`).
  - Không thay đổi hành vi trên thiết bị di động (ở màn hình di động, layout vẫn luôn xếp chồng dọc cố định).
