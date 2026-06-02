## Why

Insight cards hiện quá nặng text — 2 block dài "Điểm chính" + "Đáng chú ý" chiếm phần lớn card, tags và thời gian bị đẩy xuống cuối. User phải đọc hết card mới biết bài thuộc chủ đề gì, đăng lúc nào. Cần đảo ngược: **tags + time lên đầu** (scan nhanh) → title → **5 bullet points** (đọc nhanh) → score footer.

## What Changes

1. **Đảo layout card**: Row 1 = tier badge + thời gian, Row 2 = topic tags + event type
2. **Title block**: Source badge → Vietnamese title (bold) → English subtitle
3. **Body**: Thay 2 text blocks → **tối đa 5 bullet points** (tách từ signal + so_what + why_it_matters + summary_short)
4. **Footer**: Actionability score bar mini + trust score + adoption ring + momentum
5. Xóa block "Ai bị ảnh hưởng" trên card (chỉ hiện trên detail page — giảm noise)

## Capabilities

### New Capabilities
_(Không có capability mới — redesign component hiện có)_

### Modified Capabilities
_(Không thay đổi requirements — cùng data, khác presentation)_

## Impact

**Frontend files:**
- `components/InsightCard.tsx` — MODIFY: redesign toàn bộ layout
- `styles/insights.module.css` — MODIFY: CSS card layout mới, bullet list, compact footer

**Backend:** Không thay đổi

**Non-goals:**
- Không thêm thumbnail image (cần backend pipeline change)
- Không thay đổi card grid layout (vẫn 3 cột desktop)
- Không thêm country flags (data chưa có)

**Phase:** Phase 1
**Dependency:** `tooltip-annotation-system` (tooltips trên badges)
