## Context

`InsightList.tsx` (376 LOC) quản lý `activeTab` state để quyết định hiện source chips hay role chips. Xóa tab = bỏ `activeTab`, bỏ `useEffect` reset filters khi chuyển tab, luôn pass `source_id` và `role` vào API call.

`TabBar.tsx` (34 LOC) sẽ bị xóa.

API `fetchInsights` đã hỗ trợ cả `source_id` và `role` cùng lúc — không cần backend change.

## Goals / Non-Goals

**Goals:**
- Xóa TabBar, xóa `activeTab` state
- Gộp source + role filters luôn hiện trong filter panel
- Filter panel: compact layout, tự mở khi có filter active, "Xóa tất cả" khi có selections
- Toolbar: Sort + Quick presets + Search box + Active filter count
- Source filter: giữ search input + show more/less logic hiện có
- Role filter: chip row giống urgency/momentum

**Non-Goals:**
- Không thêm topic filter (backend chưa support filter by topic)
- Không thêm date range picker (backend chưa support)
- Không sửa card layout

## Decisions

### 1. Xóa TabBar hoàn toàn
```diff
- import TabBar from '../components/TabBar';
- import type { InsightTab } from '../components/TabBar';
- const [activeTab, setActiveTab] = useState<InsightTab>('overview');
```
TabBar.tsx file giữ lại nhưng không import nữa (xóa file khi cleanup).

### 2. Filter panel layout mới
```
┌────────────────────────────────────────────────┐
│ 🔍 Search  | Sort ▾ | 🔥 | 🇻🇳 | 📈 | Clear  │  ← Toolbar
├────────────────────────────────────────────────┤
│ Phân tầng: [🎯] [⚙️] [🔭] [ℹ️]                │
│ Mức độ:    [Khẩn cấp] [Cao] [TB] [Thấp]       │
│ Xu hướng:  [Mới] [Đang nổi] [Ổn định]         │
│ Việt Nam:  [Liên quan cao] [Vừa] [Thấp]       │
│ Vai trò:   [Engineering] [Data/AI] [Product].. │
│ Nguồn:  🔍 [arXiv] [AWS] [Google] [+12 more]  │
└────────────────────────────────────────────────┘
```

### 3. API call always sends all filters
```typescript
fetchInsights({
  source_id: selectedSourceIds.length > 0 ? selectedSourceIds : null,
  role: selectedRoles.length > 0 ? selectedRoles : null,
  // ...rest unchanged
});
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Filter panel quá dài trên mobile | Collapsible sections, ẩn nguồn/vai trò sau toggle |
| Mất khả năng xem "theo nguồn" riêng | Source filter chips đã có sẵn trong unified panel |

## Module ảnh hưởng
- **M6: Dashboard** — frontend only
- **API endpoints**: Không thay đổi
- **Bảng DB**: Không thay đổi
