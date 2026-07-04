## Approach

Sửa trực tiếp các components và CSS files. Không cần migration hay schema change.

## Technical Design

### 1. Label Localization Maps

Tạo shared label maps dùng chung giữa `InsightCard.tsx`, `InsightDetail.tsx`, `Breadcrumb.tsx`:

```tsx
// Dùng trực tiếp trong mỗi file (không tạo shared file — scope nhỏ)
const TIER_LABEL: Record<string, string> = {
  Tactical: 'Hành động ngay',
  Operational: 'Vận hành',
  Strategic: 'Chiến lược',
  Informational: 'Tham khảo',
};

const ADOPTION_LABEL: Record<string, string> = {
  Adopt: 'Áp dụng',
  Trial: 'Dùng thử',
  Assess: 'Đánh giá',
  Hold: 'Tạm hoãn',
};

const INDICATOR_LABEL: Record<string, { icon: string; label: string }> = {
  has_code_example: { icon: '💻', label: 'Mã nguồn' },
  has_benchmark: { icon: '📊', label: 'Benchmark' },
  has_api_change: { icon: '🔗', label: 'API' },
  has_migration_guide: { icon: '📖', label: 'Hướng dẫn chuyển đổi' },
  has_security_patch: { icon: '🛡️', label: 'Bản vá bảo mật' },
};
```

### 2. Detail Page Layout: 50/50 Split View

Chuyển từ `detailArticleLayout` (7fr 3fr) về `detailSplitView` (1fr 1fr):

- **Cột trái**: Phân tích AI (summary, bullets, recommendations, risks)
- **Cột phải**: Bài viết gốc (hiện luôn, không collapsible) — dùng lại `OriginalArticlePanel` nhưng truyền `collapsed={false}` hoặc render trực tiếp nội dung
- Xóa sticky sidebar hoàn toàn
- Di chuyển "Vai trò liên quan" vào metadata ribbon (đã có)
- Di chuyển "Nguồn gốc" link vào header (đã có `source_url`)

### 3. Card Thumbnail Placeholder

Khi `primaryImage` null hoặc load error → hiện placeholder:
```css
.cardThumbnailPlaceholder {
  width: 120px;
  height: 84px;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--color-accent-light), var(--color-surface-muted));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: var(--color-text-muted);
  flex-shrink: 0;
}
```

### 4. Dark Mode Polish

```css
html[data-theme="dark"] {
  /* KPI cards — tone down backgrounds */
  --kpi-danger-bg: rgba(239, 68, 68, 0.08);
  --kpi-success-bg: rgba(16, 185, 129, 0.08);
  --kpi-info-bg: rgba(59, 130, 246, 0.08);
}
```

Fix warm-tone remnants trong `dashboard.module.css`:
- `rgba(49, 35, 18, 0.04)` → `rgba(79, 70, 229, 0.04)`
- `rgba(184, 77, 30, ...)` → cool accent colors

### 5. Bỏ Score Bars

Xóa toàn bộ sidebar block L259-334 trong `InsightDetail.tsx`. Xóa biến `trustPct`, `actionPct`, `confidencePct`.

## Risks
- Breadcrumb tier labels phải đồng bộ với TIER_LABEL map
- OriginalArticlePanel khi mở sẵn cần kiểm tra `max-height` CSS animation (hiện dùng `max-height: 2000px` khi open)
