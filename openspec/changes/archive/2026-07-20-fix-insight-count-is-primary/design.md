## Context

`DeduplicationEngine` gom insight trùng ngữ nghĩa thành cụm: mỗi cụm có một đại diện
(`is_primary = true`), các bản còn lại `is_primary = false` + `cluster_id` trỏ về cụm. Tầng đọc hiện
lọc `is_primary` **không nhất quán**:

| Hàm | Lọc `is_primary`? | Dùng cho |
|---|---|---|
| `insight_repo.list_paginated` (dòng 145) | ✅ có | danh sách dashboard |
| `insight_repo.list_for_delivery` (dòng 210) | ✅ có | Telegram digest/alert |
| `insight_repo.get_stats` (dòng 266) | ❌ **không** | KPI cards |
| `source_repo.list_with_insight_counts` (dòng 72–76) | ❌ **không** | chip lọc nguồn |

Hai hàm dưới đếm mọi insight `published`, nên số hiển thị lớn hơn số bản ghi người dùng thực sự xem
được. Lỗi này có sẵn từ trước (3 nguồn HuggingFace đã lệch), chỉ vừa lộ rõ khi nguồn LinkedIn sinh
nhiều bản trùng cùng lúc.

## Goals / Non-Goals

**Goals:**
- Con số đếm hướng người dùng khớp chính xác với số bản ghi bấm vào xem được.
- Ràng buộc ở tầng spec để chỗ đếm mới sau này không lặp lại lỗi.

**Non-Goals:**
- Không đổi thuật toán gom cụm hay ngưỡng dedup — cách gom hiện tại được coi là đúng.
- Không đổi shape response của API; không migration dữ liệu.
- Không sửa frontend.
- Không đụng bug dedup của connector LinkedIn (sinh document trùng ở tầng `RawDocument`) — đó là
  nguyên nhân *tại sao* có nhiều bản trùng, thuộc change `w3-anti-bot-crawl`, độc lập với change này.

## Decisions

**D1 — Sửa ở tầng repository, không ở route/service.**
Cả hai chỗ lỗi đều là câu query trong repository; đây là tầng sở hữu ngữ nghĩa "insight nào được coi
là hiện hữu với người dùng". Sửa tại chỗ giữ mọi caller đúng tự động.
*Alternative:* lọc ở tầng route — bỏ, vì phải lặp lại ở mọi endpoint và chính đó là cách lỗi phát sinh.

**D2 — `list_with_insight_counts`: đặt `is_primary` vào điều kiện `outerjoin`, KHÔNG vào `where`.**
Query đang outer join Source → RawDocument → Insight để nguồn 0 insight vẫn xuất hiện với count 0.
Nếu thêm `is_primary` vào `where`, mọi nguồn không có insight primary sẽ **biến mất khỏi response**,
làm hỏng dòng "N nguồn chưa có insight" trên UI. Đặt vào `ON` của outer join giữ nguyên hàng, chỉ
đưa count về 0 — đúng hành vi mong muốn (xem scenario "Nguồn chỉ toàn bản trùng").

**D3 — `get_stats`: thêm `is_primary` vào mệnh đề `where` chung.**
Ở đây không có ràng buộc "giữ hàng" như D2; cả 3 aggregate đều đếm trên cùng tập insight, nên thêm
một điều kiện `where` là đủ và ít rủi ro nhất.

**D4 — Coi `is_primary = true` là điều kiện đủ, không cần `OR cluster_id IS NULL`.**
Model đặt `default=True` + `server_default="true"`, và `dedup_engine` reset về `is_primary=True` khi
gỡ cụm. Nên insight chưa từng vào cụm luôn có `is_primary = true`; thêm `OR cluster_id IS NULL` là
thừa. `list_paginated` cũng đang chỉ dùng `is_primary` — giữ nhất quán.

## Risks / Trade-offs

- **[Số KPI tụt xuống, người dùng tưởng mất dữ liệu]** → nêu rõ trong changelog: dữ liệu không đổi,
  chỉ là trước đây đếm nhầm cả bản trùng. Kèm số trước/sau (71→64) để đối chiếu.
- **[D2 làm sai nếu đặt nhầm vào `where`]** → có scenario riêng ("Nguồn chỉ toàn bản trùng") và task
  kiểm chứng số nguồn trả về không đổi trước/sau fix.
- **[Còn chỗ đếm khác chưa phát hiện]** → task 1.1 rà toàn bộ `func.count(Insight` trong repo trước
  khi sửa, không chỉ sửa hai chỗ đã biết.

## Migration Plan

Không có migration. Thay đổi thuần query, có hiệu lực ngay khi backend reload. Rollback = revert commit.

## Open Questions

- Nguồn mà toàn bộ insight đều là bản trùng sẽ tụt xuống nhóm "chưa có insight" — đúng về mặt kỹ
  thuật, nhưng có gây khó hiểu cho người vận hành không (nguồn *có* cào được bài, chỉ là trùng nguồn
  khác)? Nếu có, cân nhắc phân biệt "chưa có insight" và "chỉ có bài trùng" ở UI — **ngoài phạm vi
  change này**, ghi lại để cân nhắc sau.
