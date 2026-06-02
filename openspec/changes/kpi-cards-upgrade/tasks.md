## 1. KPI Component Update

- [x] 1.1 Cập nhật `KPI_ITEMS` array: thêm `subtitle`, `tooltip`, `color` cho mỗi item
- [x] 1.2 Đổi labels: "Mức ảnh hưởng cao" → "Ảnh hưởng cao", "Cơ hội" → "Cơ hội hành động"
- [x] 1.3 Render subtitle dưới số, icon ⓘ bên cạnh label, wrap ⓘ bằng `<Tooltip>`
- [x] 1.4 Thêm semantic color class cho từng card type (danger, success, neutral)

## 2. CSS Updates

- [x] 2.1 Thêm CSS classes vào `dashboard.module.css`: `.kpiSubtitle`, `.kpiInfoIcon`, `.kpiDanger`, `.kpiSuccess`
- [x] 2.2 Responsive: subtitle ẩn trên mobile (< 767px) để card không quá cao

## 3. Verification

- [x] 3.1 Chạy `npx tsc --noEmit` — clean
- [x] 3.2 Test browser: 4 cards hiện subtitle + tooltip khi hover ⓘ
