## Why

Detail page hiện là 1 cột dọc dài — user đọc AI summary tiếng Việt nhưng không thấy bài gốc tiếng Anh để so sánh hoặc đọc sâu. Phải bấm "Xem bài gốc" ở cuối trang để mở tab mới. Cần **split-view**: trái = AI summary VN, phải = bài gốc EN — user đọc song song, verify thông tin.

## What Changes

1. **Split detail page 50/50**: trái = "Tóm tắt AI" (Vietnamese), phải = "Bài gốc" (iframe hoặc fallback link)
2. **Panel trái**: Tags + link ở đầu → title → 5 bullet tóm tắt → khuyến nghị → scoring → "🤖 Phân tích bởi Gemini AI" verification badge
3. **Panel phải**: iframe nhúng `source_url` → nếu iframe bị block → fallback: tiêu đề gốc + "Mở bài gốc trong tab mới" button
4. **Mobile**: stack vertical (AI trên, bài gốc dưới)
5. Tạo component mới `OriginalArticlePanel.tsx`

## Capabilities

### New Capabilities
- `detail-split-view`: Chi tiết bài viết hiển thị dạng chia đôi — AI summary bên trái, bài gốc bên phải, với iframe fallback và AI verification badge

### Modified Capabilities
_(Không thay đổi requirements — thêm panel phải, không sửa nội dung panel trái)_

## Impact

**Frontend files:**
- `pages/InsightDetail.tsx` — MODIFY: restructure thành split-view CSS Grid
- `components/OriginalArticlePanel.tsx` — NEW: iframe panel cho bài gốc
- `styles/insights.module.css` — MODIFY: split-view grid, panel styles, iframe container

**Backend:** Không thay đổi (dùng `source_url` đã có)

**Non-goals:**
- Không fetch/cache HTML bài gốc vào DB (quá phức tạp cho Phase 1)
- Không render bài gốc server-side
- Không parse và hiển thị images từ bài gốc (Phase 2)
- Không resizable divider (fixed 50/50)

**Phase:** Phase 1
**Dependency:** `tooltip-annotation-system`, `insight-card-redesign` (bullet generation logic tái sử dụng)
