## Context

`KPISummary.tsx` (30 LOC) hiện chỉ render 4 ô: label + số. Dùng `KPI_ITEMS` array và `InsightStats` type. Data từ `GET /api/v1/insights/stats`. CSS ở `dashboard.module.css` class `.kpiGrid` + `.kpiCard`.

## Goals / Non-Goals

**Goals:**
- Mỗi KPI card có: label + ⓘ tooltip icon + big number + subtitle mô tả
- Tooltip dùng `<Tooltip>` component từ change `tooltip-annotation-system`
- Semantic color: critical_high dùng màu đỏ/cam, opportunities dùng xanh
- Label rõ nghĩa hơn

**Non-Goals:**
- Không thêm API endpoint mới
- Không thêm sparkline/chart
- Không thêm delta comparison

## Decisions

### 1. Mở rộng KPI_ITEMS array
```typescript
const KPI_ITEMS = [
  { key: 'total', label: 'Tổng bản tin', subtitle: 'Bài đã qua AI phân tích', 
    tooltip: 'Tổng số bài viết đã được Gemini AI phân tích...', color: 'neutral' },
  { key: 'critical_high', label: 'Ảnh hưởng cao', subtitle: 'Cần chú ý ngay',
    tooltip: 'Bài có urgency = Critical hoặc High...', color: 'danger' },
  ...
] as const;
```

### 2. Tooltip icon ⓘ position
Đặt inline bên phải label, opacity 0.5, hover opacity 1.0. Không chiếm không gian layout.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Subtitle dài quá → card bị lệch | Max 2 dòng, `text-overflow: ellipsis` |
| Color quá sặc sỡ | Dùng subtle colors, chỉ tô nhẹ background |

## Module ảnh hưởng
- **M6: Dashboard** — frontend only
- **API endpoints**: Không thay đổi
- **Bảng DB**: Không thay đổi
