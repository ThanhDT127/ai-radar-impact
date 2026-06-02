## 1. Card Layout Restructure

- [x] 1.1 Di chuyển tier badge + RelativeTime lên Row 1 (đầu card, flex space-between)
- [x] 1.2 Di chuyển topic tags + event_type tag lên Row 2
- [x] 1.3 Restructure title block: source pill → Vietnamese title (h3 bold) → English subtitle (p muted)

## 2. Bullet Points Body

- [x] 2.1 Tạo helper function `generateBullets(insight)`: tách signal, so_what, why_it_matters, summary_short thành max 5 bullets
- [x] 2.2 Render bullets dưới dạng `<ul>` list thay vì 2 text blocks ("Điểm chính" + "Đáng chú ý")
- [x] 2.3 CSS cho bullet list: compact spacing, max 2 dòng/bullet, text-overflow ellipsis

## 3. Footer Compact

- [x] 3.1 Footer row: actionability score (⚡ mini bar) + trust score + adoption ring badge + MomentumIndicator
- [x] 3.2 Xóa block "Ai bị ảnh hưởng" khỏi card (chỉ giữ trên detail page)
- [x] 3.3 Wrap scores bằng Tooltip (dùng content từ TooltipContent.ts)

## 4. CSS Updates

- [x] 4.1 Cập nhật `insights.module.css`: card header mới, bullet list styles, compact footer
- [x] 4.2 Responsive: bullets giảm còn 3 trên mobile, footer wrap 2 dòng

## 5. Verification

- [x] 5.1 `npx tsc --noEmit` — clean
- [x] 5.2 Test browser: card layout mới — tags+time đầu, bullets body, score footer
- [x] 5.3 Test insights cũ (không có so_what/signal): fallback bullets từ summary_short
