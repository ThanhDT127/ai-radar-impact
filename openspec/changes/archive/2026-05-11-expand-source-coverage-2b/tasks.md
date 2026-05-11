## 1. Verify Feed URLs

- [x] 1.1 Chuẩn bị danh sách 12 URL từ design.md D1
- [x] 1.2 Chạy `verify_feeds.py` cho 12 URL VN
- [x] 1.3 Lưu kết quả: URL nào pass / fail, sample title (verify đúng tiếng Việt, không mojibake)
- [x] 1.4 Với URL fail: thử biến thể (vd VietnamNet có thể là `/rss/cong-nghe.rss` hoặc `/cong-nghe/rss`)
- [x] 1.5 Nếu encoding issue: test với `feedparser` + force `response_encoding="utf-8"`

## 2. Update Seed Sources — Cluster VN News

- [x] 2.1 Thêm GenK: `region="vietnam"`, `trust_tier="medium"`, `topics=["Công nghệ","Trí tuệ nhân tạo"]`, `target_roles=["Engineering","Product","Content/Marketing","Toàn công ty"]`, `config.language="vi"`
- [x] 2.2 Thêm VietnamNet ICT (nếu pass): tương tự GenK
- [x] 2.3 Thêm ICT News (nếu pass): tương tự
- [x] 2.4 Thêm CafeF Kinh tế số (nếu pass): `topics=["Thị trường/Đối thủ","Công nghệ"]`, `target_roles=["Executive","Product","Toàn công ty"]`
- [x] 2.5 Thêm VietTimes (nếu pass): tương tự GenK

## 3. Update Seed Sources — Cluster VN Community

- [x] 3.1 Thêm Viblo: `trust_tier="medium"`, `topics=["Công nghệ","Quy trình phần mềm"]`, `target_roles=["Engineering","Data/AI"]`
- [x] 3.2 Thêm Daynhauhoc: tương tự Viblo, `max_items: 10` (giảm noise)
- [x] 3.3 Thêm MLOpsVN (nếu pass): `trust_tier="high"`, `topics=["Trí tuệ nhân tạo","Quy trình phần mềm","Dữ liệu"]`, `target_roles=["Engineering","Data/AI"]`
- [x] 3.4 Thêm Machine Learning Cơ Bản (nếu pass): `trust_tier="high"`, tương tự MLOpsVN
- [x] 3.5 Thêm 200lab Blog (nếu pass): `trust_tier="high"`
- [x] 3.6 Thêm AI Vietnam HuggingFace (nếu accessible): `trust_tier="high"`, `topics=["Trí tuệ nhân tạo","Dữ liệu"]`, `language="en"` (papers chủ yếu tiếng Anh)
- [x] 3.7 Thêm AIO Conquer Blog (nếu RSS tồn tại) — optional

## 4. Run Seed & Verify

- [x] 4.1 Chạy `seed_sources` — sources mới được tạo
- [x] 4.2 Chạy `run_ingestion` lần đầu — verify ít nhất 8/12 nguồn VN trả entries
- [x] 4.3 Spot-check 1 raw_document từ mỗi cluster: title/content tiếng Việt đúng UTF-8 (không mojibake)
- [x] 4.4 Verify analyzer xử lý tiếng Việt: `run_analysis` tạo insights với `summary_*` đúng tiếng Việt; không lỗi parse JSON

## 5. Documentation

- [x] 5.1 Cập nhật `docs/system_overview.md` — note layer "Vietnam News + Community"
- [x] 5.2 Cập nhật `docs/specs/07_source_strategy_and_source_catalog_v_1.md` (nếu tồn tại) — full ~53-source catalog
- [x] 5.3 Update `CLAUDE.md` "Known Gotchas" — note Vietnamese RSS encoding nếu phát hiện issue mới

## 6. Verification

- [x] 6.1 Sau 24h ingestion: query DB count insights theo `region` — `vietnam` có ≥10 insights
- [x] 6.2 Spot-check 5-10 insights VN: chất lượng phân tích Gemini không tệ với content tiếng Việt
- [x] 6.3 Theo dõi confidence distribution của VN insights vs global — nếu confidence trung bình thấp hơn nhiều, tạo follow-up về VN-specific prompt
- [x] 6.4 Document URL fail trong PR description; có thể tạo follow-up change với endpoint khác hoặc scraper

## 7. Future Considerations (out of scope)

- Frontend filter "Theo region" (vn / global / china)
- VN-specific prompt cho Gemini nếu confidence VN content thấp đáng kể
- RSSHub deploy để mở rộng nguồn không có RSS chính thức
