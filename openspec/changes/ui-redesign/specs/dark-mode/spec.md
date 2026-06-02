## ADDED Requirements

### Requirement: Theme Toggle Button
Header phải có nút toggle dark/light mode với icon sun (☀️) cho light mode và moon (🌙) cho dark mode. Nút phải accessible và có tooltip.

#### Scenario: Toggle chuyển từ light sang dark
- **WHEN** người dùng đang ở light mode và click nút toggle
- **THEN** icon chuyển từ sun sang moon, `data-theme="dark"` được set trên `<html>`, toàn bộ giao diện chuyển sang dark palette

#### Scenario: Toggle chuyển từ dark sang light
- **WHEN** người dùng đang ở dark mode và click nút toggle
- **THEN** icon chuyển từ moon sang sun, `data-theme="light"` được set trên `<html>`, toàn bộ giao diện chuyển sang light palette

#### Scenario: Toggle button accessible
- **WHEN** inspect toggle button qua screen reader
- **THEN** button có `aria-label` mô tả hành động ("Chuyển sang chế độ tối" / "Chuyển sang chế độ sáng")

### Requirement: CSS Custom Property Overrides
Dark mode phải override tất cả CSS custom properties (design tokens) — background, text, surface, border, shadow — qua selector `[data-theme="dark"]`. Không dùng separate stylesheet.

#### Scenario: Dark palette override đầy đủ
- **WHEN** `data-theme="dark"` active trên `<html>`
- **THEN** các token `--color-bg`, `--color-surface`, `--color-text`, `--color-border`, `--color-text-muted` đều có giá trị dark tương ứng (background tối, text sáng)

#### Scenario: Contrast ratio đảm bảo trong dark mode
- **WHEN** text hiển thị trên dark surface
- **THEN** contrast ratio tối thiểu đạt WCAG AA (4.5:1 cho normal text, 3:1 cho large text)

### Requirement: localStorage Persistence
Theme preference phải được lưu vào `localStorage` và khôi phục khi reload trang.

#### Scenario: Lưu preference khi toggle
- **WHEN** người dùng toggle theme
- **THEN** giá trị "dark" hoặc "light" được lưu vào `localStorage` key `theme`

#### Scenario: Khôi phục preference khi reload
- **WHEN** trang load lại và `localStorage` có key `theme` = "dark"
- **THEN** giao diện render ngay ở dark mode, không flash light mode trước

### Requirement: Auto-detection prefers-color-scheme
Lần truy cập đầu tiên (chưa có localStorage), hệ thống tự phát hiện preference từ OS qua `prefers-color-scheme` media query.

#### Scenario: OS prefer dark, first visit
- **WHEN** người dùng lần đầu truy cập và OS setting là dark mode
- **THEN** giao diện tự động hiển thị dark mode, `localStorage` key `theme` được set = "dark"

#### Scenario: OS prefer light, first visit
- **WHEN** người dùng lần đầu truy cập và OS setting là light mode (hoặc không có preference)
- **THEN** giao diện hiển thị light mode mặc định

### Requirement: Smooth Transition
Chuyển đổi theme phải có transition 0.3s mượt, không bị giật hoặc flash.

#### Scenario: Transition mượt khi chuyển theme
- **WHEN** người dùng toggle theme
- **THEN** `background-color`, `color`, và `border-color` chuyển đổi với `transition: 0.3s ease`, không có khung hình bị thiếu

### Requirement: Component Adaptation
Tất cả component (cards, badges, KPI panels, filter bar, detail page, pagination) phải adapt chính xác trong dark mode.

#### Scenario: Cards adapt dark mode
- **WHEN** dark mode active
- **THEN** card background dùng `--color-surface`, text dùng `--color-text`, left border tier colors vẫn đúng, shadow giảm opacity

#### Scenario: Badges adapt dark mode
- **WHEN** dark mode active
- **THEN** badge background và text color điều chỉnh để contrast đủ trên dark surface, semantic colors (danger, warning, success) giữ nhận diện

#### Scenario: KPI panels adapt dark mode
- **WHEN** dark mode active
- **THEN** KPI card background, icon colors, và value text đều readable trên nền tối
