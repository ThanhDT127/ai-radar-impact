## Context

`InsightCard.tsx` (127 LOC) hiện render: header (source pill + title + badges) → "Điểm chính" text block → "Đáng chú ý" text block → topic tags → role badges → meta row (time + trust + actionability). Layout dọc, text-heavy.

API trả về tất cả fields cần thiết: `signal`, `so_what`, `why_it_matters`, `summary_short`, `summary_medium` — đủ để tách thành bullet points.

## Goals / Non-Goals

**Goals:**
- Tier badge + RelativeTime lên Row 1 (đầu card)
- Topic tags + event type lên Row 2
- Title block: source + Vietnamese title + English subtitle (nếu khác)
- Body: tối đa 5 bullet points thay vì 2 text blocks
- Footer compact: score + trust + adoption + momentum
- Tooltips trên badges (dùng `<Tooltip>` từ change tooltip-annotation-system)

**Non-Goals:**
- Không thêm thumbnail (cần backend change riêng)
- Không sửa grid layout (3/2/1 columns responsive vẫn giữ)

## Decisions

### 1. Bullet generation logic (frontend-only)
```typescript
function generateBullets(insight: InsightListItem): string[] {
  const bullets: string[] = [];
  if (insight.signal) bullets.push(insight.signal);
  if (insight.so_what) bullets.push(insight.so_what);
  if (insight.why_it_matters) bullets.push(insight.why_it_matters);
  if (insight.summary_short && bullets.length < 5) {
    const sentences = insight.summary_short
      .split(/(?<=[.。!?])\s+/)
      .filter(s => s.length > 10);
    bullets.push(...sentences.slice(0, 5 - bullets.length));
  }
  return bullets.slice(0, 5);
}
```
**Rationale:** Không cần backend change. Sử dụng 4 AI fields đã có, split sentences nếu thiếu.

### 2. Xóa "Ai bị ảnh hưởng" block trên card
Roles chỉ hiện trên detail page. Card quá nhỏ để chứa cả roles — gây visual noise.

### 3. Footer layout — flex row compact
```
⚡ 73%  ·  🛡️ 80%  ·  [Adopt]  ·  🔥 Đang nổi
```
Tất cả metrics trên 1 dòng, dùng dot separator.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Bullets quá dài → card cao không đều | Max 2 dòng/bullet, text-overflow ellipsis |
| Insight cũ thiếu signal/so_what → ít bullets | Fallback: split summary_short thành sentences |
| Mất "Ai bị ảnh hưởng" trên card | Vẫn hiện trên detail page, card chỉ preview |

## Module ảnh hưởng
- **M6: Dashboard** — frontend only
- **API endpoints**: Không thay đổi
- **Bảng DB**: Không thay đổi
