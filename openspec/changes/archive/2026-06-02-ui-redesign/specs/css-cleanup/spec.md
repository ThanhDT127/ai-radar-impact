## ADDED Requirements

### Requirement: CSS Module Splitting
File `insights.module.css` monolithic phải được tách thành các module nhỏ theo concern: `card.module.css`, `detail.module.css`, `badges.module.css`, `pagination.module.css`.

#### Scenario: Module files tồn tại sau refactor
- **WHEN** refactor hoàn tất
- **THEN** tồn tại 4 file CSS Module: `card.module.css`, `detail.module.css`, `badges.module.css`, `pagination.module.css` trong thư mục styles hoặc cùng cấp component

#### Scenario: Không có class bị mất sau split
- **WHEN** so sánh tổng số CSS class trước và sau refactor
- **THEN** tất cả class đang được sử dụng trong code đều tồn tại trong 1 trong 4 module mới, không class nào bị thiếu

#### Scenario: Import paths cập nhật đúng
- **WHEN** component import CSS Module
- **THEN** import path trỏ đúng file module mới (ví dụ: `import styles from './card.module.css'`), không import từ `insights.module.css` cũ

#### Scenario: File insights.module.css cũ bị xóa
- **WHEN** refactor hoàn tất
- **THEN** file `insights.module.css` gốc không còn tồn tại, không component nào reference đến nó

### Requirement: Dead CSS Removal
Xóa các CSS class không sử dụng từ các iteration v1-v3: `detailBody` warm-toned styles, old `splitView` layout, `cardFeatured` unused variant.

#### Scenario: Warm-toned detailBody class bị xóa
- **WHEN** search codebase cho class `detailBody` với warm-tone colors
- **THEN** không tìm thấy definition — class đã bị xóa hoàn toàn

#### Scenario: Old splitView class bị xóa
- **WHEN** search codebase cho class `splitView` (layout 50/50 cũ)
- **THEN** không tìm thấy definition trong CSS, component sử dụng layout 70/30 mới

#### Scenario: cardFeatured variant bị xóa
- **WHEN** search codebase cho class `cardFeatured`
- **THEN** không tìm thấy definition trong CSS cũng như reference trong JSX/TSX

### Requirement: Fix Warm-tone Remnants
Thay thế tất cả hardcoded warm-tone colors (`rgba(120,99,77,...)`, `rgba(255,251,246,...)`) bằng cool palette equivalents sử dụng CSS custom properties.

#### Scenario: Không còn warm-tone rgba trong CSS
- **WHEN** search toàn bộ CSS files cho pattern `rgba(120,99,77` hoặc `rgba(255,251,246`
- **THEN** không tìm thấy kết quả — tất cả đã được thay bằng CSS custom property (ví dụ: `var(--color-text-muted)`, `var(--color-bg)`)

#### Scenario: Visual regression check
- **WHEN** so sánh UI trước và sau fix warm-tone
- **THEN** không có element nào bị mất màu hoặc hiển thị sai — tất cả dùng cool indigo palette nhất quán

### Requirement: Axios Instance Consolidation
Gộp 3 Axios instance riêng lẻ thành 1 shared client duy nhất tại `src/api/client.ts`.

#### Scenario: Single Axios client tồn tại
- **WHEN** kiểm tra file `src/api/client.ts`
- **THEN** file export 1 Axios instance duy nhất với `baseURL`, `timeout`, và default headers được cấu hình

#### Scenario: Tất cả API modules dùng shared client
- **WHEN** search codebase cho `axios.create(`
- **THEN** chỉ tìm thấy 1 instance duy nhất trong `client.ts`, không có instance nào khác trong các API module

#### Scenario: API calls hoạt động bình thường sau consolidation
- **WHEN** gọi bất kỳ API endpoint nào (insights list, insight detail, stats)
- **THEN** response trả về đúng data, không lỗi baseURL hoặc header

### Requirement: Dead Component Removal
Xóa component không sử dụng: `ImpactBadge.tsx` và `OriginalArticlePanel.tsx`.

#### Scenario: ImpactBadge.tsx bị xóa
- **WHEN** search codebase cho file `ImpactBadge.tsx`
- **THEN** file không tồn tại, không import nào reference đến `ImpactBadge`

#### Scenario: OriginalArticlePanel.tsx bị xóa
- **WHEN** search codebase cho file `OriginalArticlePanel.tsx`
- **THEN** file không tồn tại, không import nào reference đến `OriginalArticlePanel`

#### Scenario: Không có broken import sau xóa
- **WHEN** chạy TypeScript compiler (`tsc --noEmit`)
- **THEN** không có lỗi "Module not found" liên quan đến ImpactBadge hoặc OriginalArticlePanel

### Requirement: TypeScript Fix — primary_image
Xóa cast `(insight as any).primary_image` và thêm field `primary_image` vào type `InsightListItem`.

#### Scenario: primary_image có trong InsightListItem type
- **WHEN** kiểm tra type definition `InsightListItem`
- **THEN** field `primary_image: string | null` tồn tại trong type definition

#### Scenario: Không còn `as any` cast cho primary_image
- **WHEN** search codebase cho pattern `as any).primary_image`
- **THEN** không tìm thấy kết quả — tất cả access `primary_image` đều type-safe

#### Scenario: TypeScript compile thành công
- **WHEN** chạy `tsc --noEmit`
- **THEN** không có type error liên quan đến `primary_image`

### Requirement: Error Boundary Component
Thêm Error Boundary component vào `App.tsx` để catch runtime errors và hiển thị fallback UI thay vì white screen.

#### Scenario: Error Boundary wrap toàn bộ app
- **WHEN** kiểm tra component tree trong `App.tsx`
- **THEN** `ErrorBoundary` component wrap toàn bộ route content, nằm bên ngoài `<Routes>`

#### Scenario: Error Boundary catch render error
- **WHEN** một component con throw error trong render phase
- **THEN** Error Boundary hiển thị fallback UI với message "Đã xảy ra lỗi" và nút "Tải lại trang", không hiển thị white screen

#### Scenario: Error Boundary không ảnh hưởng render bình thường
- **WHEN** không có error nào xảy ra
- **THEN** Error Boundary transparent — render children bình thường, không ảnh hưởng performance
