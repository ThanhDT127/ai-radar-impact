## 1. Backend — README enrichment (AI pipeline)

- [ ] 1.1 Thêm helper `_fetch_readme(owner, repo)` trong `github_trending_connector.py`: thử lần lượt `raw.githubusercontent.com/{o}/{r}/HEAD/{README.md,README.markdown,README.rst,readme.md}`, timeout 5s, trả text hoặc `None`. **DoD:** repo có README → trả text; repo không có → `None`, không raise. (P1)
- [ ] 1.2 Thêm hằng `README_MAX_CHARS = 4000`; cắt README trước khi ghép. **DoD:** README > 4000 ký tự bị cắt đúng ngưỡng. (P1)
- [ ] 1.3 Ghép README vào `content_parts` **sau** khối metadata; đọc config `fetch_readme` (default True), `readme_max_chars` (default 4000). **DoD:** content chứa đoạn "README: ..." khi bật; không chứa khi `fetch_readme=False`. (P1)
- [ ] 1.4 Fail-safe: mọi lỗi fetch README → giữ content mô tả cũ, log debug, entry vẫn trả về. **DoD:** mock 404/timeout → entry vẫn hợp lệ, pipeline không crash. (P1)

## 2. Backend — Seed monthly source (DB/seed)

- [ ] 2.1 Thêm entry `GitHub Trending — Monthly All` (`since="monthly"`, `region="global"`, `target_roles ⊇ {Engineering, Data/AI}`) vào `seed_sources.py`. **DoD:** chạy seed tạo được source; fetch `?since=monthly` trả entries. (P1)

## 3. Test

- [ ] 3.1 Test README enrichment: mock `raw.githubusercontent` trả README → assert `raw_content` chứa nội dung README (đã cắt ≤ 4000). **DoD:** test pass. (P1)
- [ ] 3.2 Test fail-safe: mock tất cả filename 404 → entry vẫn có content mô tả cũ, không exception. **DoD:** test pass. (P1)
- [ ] 3.3 Test dedup xuyên cửa sổ: 2 `ConnectorEntry` cùng `owner/repo`, khác `since` → `make_fingerprint` bằng nhau (README không đổi fingerprint). **DoD:** assert equal; test pass. (P1)

## 4. Verification

- [ ] 4.1 Chạy `run_ingestion --source-id <monthly source>` local → xác nhận log fetch README, số raw doc mới hợp lý. **DoD:** ≥1 repo có README trong content. (P1)
- [ ] 4.2 Chạy `run_analysis` trên vài doc github_trending → insight dẫn được chi tiết từ README (không chỉ tên repo). **DoD:** rà 3 insight, nội dung phản ánh README. (P1)
- [ ] 4.3 Xác nhận không rò rỉ quota: repo trùng ở daily + weekly/monthly không tạo raw doc trùng. **DoD:** query DB, không có 2 raw doc cùng fingerprint. (P1)
