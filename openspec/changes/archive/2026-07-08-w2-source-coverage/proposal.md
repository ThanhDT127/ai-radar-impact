## Why

Hai vấn đề chất lượng & độ phủ nguồn (task **T4** + **T6** của sprint W2, `note/LICH_TRINH_CONG_VIEC.md`):

- **arXiv lẫn nhánh hàn lâm**: đang bật `cs.SE` (quy trình phần mềm) và `cs.CR` (mật mã) — nặng lý thuyết, tốn quota mà ít giá trị áp dụng; thiếu các nhánh thực dụng cho Smart City/IoT (thị giác, âm thanh, robotics, HCI). Host feed cũng không nhất quán (`export.arxiv.org` cũ vs `rss.arxiv.org`).
- **Không đo được độ phủ vai trò**: 19/70 nguồn **chưa gắn `target_roles`**; các tag hiện có **trộn 2 bộ từ vựng** — vừa ALLOWED_ROLES (`Engineering`, `Data/AI`, `Security`…) vừa chức danh (`Tech Lead`, `Data Scientist`, `AI Engineer`, `Data Engineer`, `Dev`). Closed set `target_roles` trong spec cũ chỉ 8 vai trò, **thiếu 5 vai trò kỹ thuật** đã có trong ALLOWED_ROLES. ⇒ không thể kết luận "mỗi vai trò đủ mấy nguồn".

## What Changes

**T4 — arXiv:**
1. Thêm `cs.CV`, `eess.AS`, `cs.RO`, `cs.HC`; **tắt** `cs.SE`, `cs.CR` (`status="inactive"`); chuẩn hoá host về `rss.arxiv.org`.
2. **Sửa bug**: `seed()` bỏ qua `status` khi update nguồn cũ (`seed_sources.py:867–876`) ⇒ lệnh tắt nguồn không có hiệu lực khi re-seed. Thêm `status` vào nhánh upsert.

**T6 — độ phủ vai trò:**
3. Hợp nhất `target_roles` về **bộ ALLOWED_ROLES (13 vai trò)**; thay tag chức danh bằng ALLOWED_ROLES tương ứng (Tech Lead→Engineering; Data Scientist/AI Engineer/Data Engineer→Data/AI; Dev→Engineering).
4. **Backfill** `target_roles` cho 19 nguồn còn thiếu.
5. **Audit** độ phủ theo vai trò; **seed bù tối thiểu** cho vai trò thật sự mỏng.

## Capabilities

### Modified Capabilities
- `source-region-tagging`: mở rộng closed set `target_roles` = ALLOWED_ROLES (13); backfill nguồn chưa gắn; yêu cầu audit độ phủ vai trò.

### New Capabilities
- `source-catalog-curation`: quy tắc tinh gọn danh mục arXiv (bật/tắt nhánh) và seed upsert cập nhật được `status`.

## Impact

**Backend files:**
- `app/scripts/seed_sources.py` — MODIFY: arXiv (thêm 4/tắt 2/chuẩn host); `seed()` upsert `status`; backfill + hợp nhất `target_roles`; seed bù vai trò mỏng
- `openspec/specs/source-region-tagging` — closed set `target_roles` cập nhật (qua archive change)

**Backend (không đổi):** không đụng connector; không migration schema (`target_roles`, `status` đã có cột); không đổi taxonomy `affected_roles` của Gemini.

**Non-goals:**
- Không sửa closed set `affected_roles` (Gemini sinh) — chỉ đụng `target_roles` (metadata nguồn)
- Không seed ồ ạt nguồn mới gây áp lực quota — ưu tiên **dán nhãn trước, seed bù sau**
- Không đụng connector code hay prompt template
- Không tự động phủ đủ 5 nguồn cho `Content/Marketing` và `HR/L&D` nếu công ty không ưu tiên (xem Design — quyết định mở)

**Phase:** Phase 1
**Dependency:** `w1-quota-guard` (giữ trong hạn mức quota — phần lớn là dán nhãn, gần như 0 quota)
