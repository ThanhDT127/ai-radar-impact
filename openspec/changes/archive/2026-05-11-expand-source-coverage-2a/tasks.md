## 1. Verify Feed URLs

- [x] 1.1 Chuẩn bị danh sách 13 URL từ design.md D1
- [x] 1.2 Chạy `python -m app.scripts.verify_feeds` (tạo từ change 2) cho 13 URL
- [x] 1.3 Lưu kết quả: URL nào pass / fail, sample title của mỗi feed
- [x] 1.4 Với URL fail: thử biến thể (vd Anthropic có thể là `/feed.xml`, `/news/feed`, `/rss`); document URL cuối cùng

## 2. Update Seed Sources — Cluster Global AI

- [x] 2.1 Thêm Anthropic vào `seed_sources.py` với feed URL đã verify, `region="global"`, `trust_tier="very_high"`, `topics=["Trí tuệ nhân tạo"]`, `target_roles=["Engineering","Data/AI"]`
- [x] 2.2 Thêm Hugging Face Blog: `region="global"`, `trust_tier="very_high"`, topics+roles tương tự
- [x] 2.3 Thêm Papers With Code: `region="global"`, `trust_tier="high"`, `topics=["Trí tuệ nhân tạo","Dữ liệu"]`, roles tương tự

## 3. Update Seed Sources — Cluster Dev/DevOps

- [x] 3.1 Thêm Stack Overflow Blog: `region="global"`, `trust_tier="high"`, `topics=["Quy trình phần mềm","Công nghệ"]`, `target_roles=["Engineering"]`
- [x] 3.2 Thêm dev.to AI tag feed: `trust_tier="medium"`, `max_items: 10`
- [x] 3.3 Thêm dev.to ML tag feed: same
- [x] 3.4 Thêm JetBrains Blog: `trust_tier="high"`
- [x] 3.5 Thêm Docker Blog: `trust_tier="very_high"`, `target_roles=["Engineering","Toàn công ty"]`
- [x] 3.6 Thêm Kubernetes Blog: `trust_tier="very_high"`, roles tương tự Docker

## 4. Update Seed Sources — Cluster Security

- [x] 4.1 Thêm KrebsOnSecurity: `trust_tier="very_high"`, `topics=["An ninh mạng"]`, `target_roles=["Engineering","Legal/Compliance","Toàn công ty"]`
- [x] 4.2 Thêm BleepingComputer: `trust_tier="high"`, topics+roles tương tự
- [x] 4.3 Thêm Microsoft Security Blog: `trust_tier="very_high"`, topics+roles tương tự
- [x] 4.4 Thêm GitHub Security Lab: `trust_tier="very_high"`, `topics=["An ninh mạng","Quy trình phần mềm"]`, `target_roles=["Engineering"]`

## 5. Run Seed & Verify

- [x] 5.1 Chạy `docker-compose exec backend python -m app.scripts.seed_sources` — 12-13 sources mới được tạo
- [x] 5.2 Chạy `run_ingestion` lần đầu — verify ít nhất 10/13 nguồn trả entries
- [x] 5.3 Spot-check 1 raw_document từ mỗi cluster: title/content có nội dung thực
- [x] 5.4 Verify analyzer xử lý: `run_analysis` không lỗi với content kỹ thuật/security

## 6. Documentation

- [x] 6.1 Cập nhật `docs/system_overview.md` — note 3 cluster mới (Global AI/Dev/Security)
- [x] 6.2 Cập nhật `docs/specs/07_source_strategy_and_source_catalog_v_1.md` (nếu tồn tại) — phản ánh 41-source catalog
- [x] 6.3 Update `CLAUDE.md` "Vietnamese Taxonomy" section nếu phát hiện gap topic mapping mới

## 7. Verification

- [x] 7.1 Sau 24h ingestion: query DB count insights theo `topics` — `An ninh mạng` có insights ≠ 0 (trước đây gần như không có)
- [x] 7.2 Spot-check 3-5 insights cho mỗi cluster mới — chất lượng phân tích chấp nhận được
- [x] 7.3 Document URL nào fail trong PR description; nếu cần follow-up change, tạo riêng
