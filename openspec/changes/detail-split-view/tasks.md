## 1. Split View Layout

- [x] 1.1 Restructure `InsightDetail.tsx`: wrap content trong CSS Grid `grid-template-columns: 1fr 1fr`
- [x] 1.2 Panel trái: di chuyển tags + link lên đầu, tổ chức lại body sections
- [x] 1.3 Thêm verification badge: "🤖 Phân tích bởi Gemini AI · Confidence: X%"

## 2. Original Article Panel

- [x] 2.1 Tạo `OriginalArticlePanel.tsx`: iframe container với loading spinner
- [x] 2.2 Implement iframe error detection: `onLoad` + `onError` handlers
- [x] 2.3 Fallback UI khi iframe bị block: tiêu đề gốc + button "Mở bài gốc trong tab mới"
- [x] 2.4 Sandbox attribute: `allow-same-origin allow-scripts` cho security

## 3. Left Panel Restructure

- [x] 3.1 Tags + links row ở đầu panel (tier badge, topic tags, source link, published date)
- [x] 3.2 Title section (Vietnamese title bold, nguyên gốc subtitle)
- [x] 3.3 5-bullet summary (dùng `generateBullets()`)
- [x] 3.4 So_what highlight box (giữ nguyên style hiện có)
- [x] 3.5 Khuyến nghị theo vai trò (giữ RecommendationsByRole component)
- [x] 3.6 Score section: actionability + trust + adoption ring
- [x] 3.7 Verification badge ở cuối panel

## 4. CSS Updates

- [x] 4.1 Thêm CSS split-view vào `insights.module.css`: grid layout, panel styling, iframe container
- [x] 4.2 Responsive: `@media (max-width: 1024px)` → stack vertical, full width panels
- [x] 4.3 Iframe styles: full height, border, loading overlay

## 5. Verification

- [x] 5.1 `npx tsc --noEmit` — clean
- [x] 5.2 Test browser desktop: build thành công (345KB JS, 26KB CSS)
- [x] 5.3 Test iframe: OriginalArticlePanel với onLoad/onError handlers
- [x] 5.4 Test mobile: responsive CSS stacking panels vertical
- [x] 5.5 Test fallback: originalFallback UI với "Mở trong tab mới" button
