## Context

Trang chi tiết bản tin hiện tại render bằng layout Grid cố định 50/50 ở chế độ Desktop. Để hỗ trợ khả năng thay đổi kích thước cột động và mượt mà mà không gây ảnh hưởng lớn đến cấu trúc DOM, phương pháp tối ưu nhất là sử dụng một React State điều phối CSS class trên phần tử bao ngoài (wrapper container), kết hợp cùng CSS Transition trên thuộc tính `grid-template-columns`.

## Goals / Non-Goals

**Goals:**
- Tạo bộ điều khiển (Toolbar) trực quan dễ sử dụng để chuyển đổi 3 chế độ.
- Triển khai transition mượt mà cho việc chuyển đổi kích thước cột.
- Thiết kế nội dung tối giản cho cột bị thu nhỏ về 20% (sidebar) để không bị tràn hay lỗi hiển thị.
- Lưu trữ tùy chọn chế độ đọc của người dùng vào `localStorage`.

**Non-Goals:**
- Không hỗ trợ kéo thả tự do để thay đổi kích thước (resizable handle) ở Phase này nhằm giảm thiểu sự phức tạp và code JavaScript tính toán đắt đỏ.

## Decisions

### 1. Quản lý trạng thái và ghi nhớ tùy chọn (React State & LocalStorage)
Trong file [InsightDetail.tsx](file:///d:/Works/AI%20Radar%20Impact/frontend/src/pages/InsightDetail.tsx):
```typescript
const [viewMode, setViewMode] = useState<'split' | 'focus-ai' | 'focus-original'>(() => {
  return (localStorage.getItem('radar-view-mode') as any) || 'split';
});

const handleViewModeChange = (mode: 'split' | 'focus-ai' | 'focus-original') => {
  setViewMode(mode);
  localStorage.setItem('radar-view-mode', mode);
};
```

### 2. Thiết lập CSS Grid và Transition mượt mà
Trong file [insights.module.css](file:///d:/Works/AI%20Radar%20Impact/frontend/src/styles/insights.module.css):
```css
.detailContainer {
  display: grid;
  gap: var(--space-lg);
  transition: grid-template-columns 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.layoutSplit {
  grid-template-columns: 1fr 1fr;
}

.layoutFocusAI {
  grid-template-columns: 4fr 1fr; /* 80% - 20% */
}

.layoutFocusOriginal {
  grid-template-columns: 1fr 4fr; /* 20% - 80% */
}
```

### 3. Xử lý nội dung hiển thị trong Sidebar (Cột bị thu hẹp về 20%)

*   **Khi cột bài viết gốc (bên phải) bị thu hẹp thành 20% (chế độ Focus AI):**
    - Ẩn phần iframe tải trang gốc (vì 20% là quá hẹp để render web, gây ra lỗi hiển thị và scroll ngang).
    - Thay thế bằng một giao diện sidebar gọn gàng: icon bài viết lớn, link mở tab mới và nút bấm "Mở rộng ◀" hoặc nút "Đọc song song".
*   **Khi cột phân tích AI (bên trái) bị thu hẹp thành 20% (chế độ Focus Original):**
    - Chỉ hiển thị tiêu đề chính, các chỉ số điểm (score) và các icon/topics.
    - Ẩn hoàn toàn các phần văn bản dài (bullets, khuyến nghị chi tiết, rủi ro) để tránh cuộn trang vô tận trên một cột hẹp.
    - Hiển thị nút bấm "Mở rộng phân tích ▶".

## Risks / Trade-offs

*   **Hiệu năng tải lại iframe:** Khi chuyển đổi từ chế độ Focus AI (iframe bị ẩn khỏi DOM/display) sang chế độ khác, iframe có thể phải tải lại trang. 
    *   *Giải pháp:* Sử dụng CSS `visibility: hidden; position: absolute; width: 0; height: 0;` thay vì `display: none` hoặc ngắt render (`&&`) để giữ cho iframe chạy ngầm không bị load lại từ đầu khi người dùng chuyển chế độ.
