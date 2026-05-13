## 1. Fix sort "Ảnh hưởng cao nhất"

- [x] 1.1 Trong `frontend/src/components/SortDropdown.tsx`: đổi `value: 'impact_label'` → `value: 'urgency'` cho option "Ảnh hưởng cao nhất"
- [x] 1.2 Trong `frontend/src/api/insights.ts`: thêm `'urgency'` vào union type `FetchInsightsParams.sort_by` (nếu chưa có)
- [x] 1.3 Verify trên browser: chọn "Ảnh hưởng cao nhất" → badge "KHẨN CẤP" xuất hiện trước "CAO" trước "TRUNG BÌNH"

## 2. Thêm filter urgency

- [x] 2.1 Trong `InsightList.tsx`: thêm state `const [selectedUrgency, setSelectedUrgency] = useState<string[]>([])`
- [x] 2.2 Định nghĩa `urgencyItems: FilterChipItem[]` với 4 values: `critical/high/medium/low` và labels: `Khẩn cấp/Cao/Trung bình/Thấp`
- [x] 2.3 Thêm `FilterChips` cho urgency vào JSX (hiển thị luôn, không phụ thuộc tab)
- [x] 2.4 Truyền `urgency: selectedUrgency` vào `fetchInsights` params
- [x] 2.5 Thêm `selectedUrgency` vào `useEffect` dependency array reset page
- [x] 2.6 Reset `selectedUrgency` khi đổi tab (thêm vào `useEffect` reset khi `activeTab` đổi)

## 3. Thêm filter momentum

- [x] 3.1 Thêm state `const [selectedMomentum, setSelectedMomentum] = useState<string[]>([])`
- [x] 3.2 Định nghĩa `momentumItems` với 3 values: `new/rising/mature` và labels: `Mới/Đang nổi/Ổn định`
- [x] 3.3 Thêm `FilterChips` cho momentum vào JSX
- [x] 3.4 Truyền `momentum: selectedMomentum` vào `fetchInsights` params
- [x] 3.5 Thêm vào dependency arrays (page reset + tab reset)

## 4. Thêm filter vietnam_relevance

- [x] 4.1 Thêm state `const [selectedVietnamRelevance, setSelectedVietnamRelevance] = useState<string[]>([])`
- [x] 4.2 Định nghĩa `vietnamRelevanceItems` với 3 values: `high/medium/low` và labels: `Liên quan cao/Liên quan vừa/Thấp`
- [x] 4.3 Thêm `FilterChips` cho vietnam_relevance vào JSX
- [x] 4.4 Truyền `vietnam_relevance: selectedVietnamRelevance` vào `fetchInsights` params
- [x] 4.5 Thêm vào dependency arrays (page reset + tab reset)

## 5. Fix role count

- [x] 5.1 Trong `InsightList.tsx` dòng tính `roleItems`: đổi `count: overviewQuery.data?.items.filter(...).length` thành `count: undefined`

## 6. Verify end-to-end

- [x] 6.1 Chạy frontend dev server, kiểm tra sort urgency hoạt động đúng thứ tự
- [x] 6.2 Test filter urgency: chọn "Khẩn cấp" → chỉ hiện critical insights
- [x] 6.3 Test filter kết hợp: urgency + momentum + vietnam_relevance cùng lúc
- [x] 6.4 Test reset: đổi tab → tất cả filter chips bị bỏ chọn
- [x] 6.5 Test role tab: chips không hiện số đếm
- [x] 6.6 Test empty state: chọn combination không có kết quả → hiện empty state đúng

## 7. Redesign filter UX (added in implementation)

- [x] 7.1 Filter panel ẩn mặc định, toggle button "⚙ Bộ lọc" với badge count
- [x] 7.2 Thêm 3 preset shortcuts: 🔥 Khẩn cấp / 🇻🇳 Việt Nam / 📈 Đang nổi
- [x] 7.3 Source filter: search input + top 12 chips + "Xem tất cả / Thu gọn"
- [x] 7.4 Source row: label + content column thẳng hàng (align-items flex-start)
- [x] 7.5 Compact pill chip style (`.filterChip`) thay cho large source chips
- [x] 7.6 Clear all filters button khi có active filters
- [x] 7.7 Fix Vite HMR cho Docker (usePolling: true)
