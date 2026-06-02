## 1. Color Palette & Tokens

- [x] 1.1 Cập nhật toàn bộ CSS custom properties trong `frontend/src/styles/global.css`: đổi color palette từ Warm Earth sang Cool Neutral (background, surface, border, text, accent, semantic colors)
- [x] 1.2 Cập nhật shadow system trong `global.css`: tăng shadow intensity cho depth rõ ràng hơn
- [x] 1.3 Cập nhật glassmorphism tokens (`--glass-bg`, `--glass-border`) cho palette mới

## 2. Typography

- [x] 2.1 Thêm Google Fonts import mới vào `global.css`: Plus Jakarta Sans (display) + Geist hoặc Inter fallback (body)
- [x] 2.2 Cập nhật `--font-display` và `--font-body` trong `:root`
- [x] 2.3 Thêm `<link rel="preload">` cho fonts mới vào `frontend/index.html`

## 3. Card List Simplification

- [x] 3.1 Cập nhật `InsightCard.tsx`: bỏ bullet points, bỏ original title, chỉ giữ title + 1-line summary + source/time + max 2 badges
- [x] 3.2 Cập nhật CSS card trong `insights.module.css`: shadow-2 default, shadow-3 hover, border hover accent indigo, translateY(-6px) hover
- [x] 3.3 Cập nhật hero section styling cho palette mới (gradient mesh indigo → purple → blue thay vì cam → nâu)
- [x] 3.4 Cập nhật stats cards styling cho palette mới

## 4. Detail Page Polish

- [x] 4.1 Cập nhật metadata ribbon trong `InsightDetail.tsx`: bỏ section labels, badges xếp ngang liên tục 1 dòng
- [x] 4.2 Cập nhật CSS ribbon trong `insights.module.css`: bỏ grid sections, dùng flexbox wrap
- [x] 4.3 Cập nhật section cards (detailSection) colors cho palette mới

## 5. Component Badge Colors

- [x] 5.1 Cập nhật tier badges colors (Tactical, Operational, Strategic, Informational) cho palette mới
- [x] 5.2 Cập nhật urgency/impact badges colors cho semantic colors mới
- [x] 5.3 Cập nhật role badges colors
- [x] 5.4 Cập nhật momentum badges colors
- [x] 5.5 Cập nhật source pill, topic tag colors cho accent mới

## 6. Verification

- [x] 6.1 Build TypeScript — không lỗi
- [x] 6.2 Screenshot list page — verify palette mới, cards clean, depth rõ
- [x] 6.3 Screenshot detail page — verify ribbon compact, split view OK
- [x] 6.4 Kiểm tra font loading — Plus Jakarta Sans render đúng trên titles
