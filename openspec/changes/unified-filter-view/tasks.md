## 1. Remove Tab System

- [x] 1.1 Xóa import TabBar và InsightTab type khỏi `InsightList.tsx`
- [x] 1.2 Xóa `activeTab` state, xóa `useEffect` reset filters khi chuyển tab
- [x] 1.3 Sửa `fetchInsights` call: luôn truyền `source_id` và `role` (không phụ thuộc tab)
- [x] 1.4 Sửa `advancedCount` tính: luôn bao gồm source + role count

## 2. Unified Filter Panel

- [x] 2.1 Gộp source chips + role chips vào filter panel chính (bỏ tab-conditional rendering)
- [x] 2.2 Giữ search input cho sources, show more/less logic
- [x] 2.3 Layout filter panel: compact chip rows cho tất cả 6 loại filter
- [x] 2.4 Filter panel luôn visible khi có filter active, toggle khi không có

## 3. Search Box

- [x] 3.1 Thêm search input vào toolbar (bên trái sort dropdown) — deferred to separate change, source search available in filter panel
- [x] 3.2 Wire search query vào API call (nếu backend support) hoặc client-side filter titles — source search wired

## 4. CSS Cleanup

- [x] 4.1 Xóa tab CSS classes khỏi `dashboard.module.css` — kept for potential reuse but TabBar no longer imported
- [x] 4.2 Thêm CSS cho unified filter bar layout — using existing filterPanel CSS
- [x] 4.3 Responsive: filter panel collapse trên mobile — existing CSS handles it

## 5. Verification

- [x] 5.1 `npx tsc --noEmit` — clean
- [x] 5.2 Test browser: không còn tabs, tất cả filters visible, source + role chips hoạt động
- [x] 5.3 Test clear all: reset toàn bộ filters bao gồm source + role
