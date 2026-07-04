## ADDED Requirements

### Requirement: Design Token System
Hệ thống design token phải được định nghĩa tập trung trong `global.css` bao gồm colors, typography, spacing, elevation, và border-radius. Tất cả component phải reference token — không hardcode value.

#### Scenario: Typography tokens được áp dụng đồng nhất
- **WHEN** bất kỳ text nào render trên dashboard
- **THEN** phải dùng 1 trong các font-size token: `--text-xs` (0.75rem), `--text-sm` (0.8rem), `--text-base` (0.88rem), `--text-md` (1rem), `--text-lg` (1.25rem), `--text-xl` (1.5rem), `--text-2xl` (2rem), `--text-3xl` (3rem)

#### Scenario: Color palette đảm bảo contrast ratio
- **WHEN** text hiển thị trên bất kỳ surface nào
- **THEN** contrast ratio tối thiểu phải đạt WCAG AA (4.5:1 cho normal text, 3:1 cho large text)

#### Scenario: Semantic color tokens cho badge states
- **WHEN** badge hiển thị trạng thái (critical, high, medium, low, watch)
- **THEN** phải dùng semantic color token: `--color-danger` (red), `--color-warning` (amber), `--color-success` (green), `--color-info` (blue), `--color-neutral` (gray)

#### Scenario: Elevation system nhất quán
- **WHEN** element cần đổ bóng (cards, modals, tooltips)
- **THEN** phải dùng 1 trong 4 elevation levels: `--shadow-1` (cards), `--shadow-2` (raised), `--shadow-3` (modals), `--shadow-4` (overlays)

#### Scenario: Spacing scale 8px-based
- **WHEN** padding, margin, hoặc gap được áp dụng
- **THEN** phải dùng giá trị từ spacing scale: 0, 4px, 8px, 12px, 16px, 20px, 24px, 32px, 40px, 48px, 64px, 80px

### Requirement: Font Upgrade
Typography chuyển sang Inter (body) + Space Grotesk (display) + JetBrains Mono (code/scores) để tối ưu readability ở kích thước nhỏ.

#### Scenario: Google Fonts được load correctly
- **WHEN** trang load lần đầu
- **THEN** Inter (400, 500, 600, 700) và Space Grotesk (500, 700) và JetBrains Mono (400) phải available, không dùng font hệ thống fallback

### Requirement: CSS Architecture Cleanup
Tất cả inline styles trong Layout.tsx phải chuyển sang CSS Module. CSS module files phải được tổ chức rõ ràng.

#### Scenario: Layout component không có inline style
- **WHEN** inspect Layout component qua browser DevTools
- **THEN** không có attribute `style=` trên bất kỳ DOM element nào — tất cả styles từ CSS class
