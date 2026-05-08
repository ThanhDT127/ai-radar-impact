## Why

Khi có nhiều nguồn (RSS, HN, Reddit), cùng một sự kiện (ví dụ: "GPT-5 release") sẽ xuất hiện ở nhiều nơi. Hiện tại mỗi bài → 1 insight riêng, gây trùng lặp trên dashboard.

Change này implement **semantic dedup engine**: phát hiện bài viết về cùng sự kiện, nhóm thành cluster, chọn bài "Primary" (từ nguồn uy tín nhất) và liệt kê các bài khác là "References".

## What Changes

- Tạo `DeduplicationEngine` — dùng TF-IDF + Cosine Similarity để tìm semantic duplicates
- Thêm `cluster_id` và `is_primary` vào bảng `insights`
- Tích hợp dedup vào pipeline sau khi tạo insight
- API trả kèm references khi xem insight detail
- Frontend hiển thị "Bài viết liên quan từ nguồn khác"
- Cập nhật `docs/system_overview.md`

## Capabilities

### New Capabilities
- `semantic-dedup`: Phát hiện duplicate cross-source bằng TF-IDF similarity, nhóm thành cluster Primary + References

### Modified Capabilities
- `insight-api`: API detail trả kèm references array
- `insight-dashboard`: InsightDetail hiển thị references

## Impact

- **Backend code:** Thêm `services/dedup_engine.py`, sửa `models/insight.py`, `schemas/`, `routes/`, `repositories/`
- **Database:** Thêm cột `cluster_id` (UUID, nullable) và `is_primary` (Boolean) vào bảng `insights`
- **Frontend:** Sửa `InsightDetail.tsx` hiển thị references
- **API:** `GET /insights/{id}` trả kèm `references` array
- **Dependencies:** Thêm `scikit-learn`
- **Dependency:** Cần Change 2 hoàn thành (có nhiều nguồn tạo duplicate thực tế)
- **Phase:** Phase 1

## Non-goals

- Không implement real-time dedup (chạy batch sau ingestion)
- Không dùng vector embedding (dùng TF-IDF đơn giản hơn, đủ cho Phase 1)
- Không merge insights — chỉ nhóm và chọn primary
- Không thay đổi InsightList UI — chỉ sửa InsightDetail
