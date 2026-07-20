## Why

`GitHubTrendingConnector` hiện chỉ cào **tên repo + 1 dòng mô tả + số sao** từ trang trending. Content gửi cho Gemini quá nghèo (thường < 200 ký tự) → insight chung chung kiểu *"một repo Python đang được chú ý"*, không nói được repo **làm gì**, giải quyết vấn đề gì, có đáng quan tâm không. Ngoài ra mới có khung `daily` + `weekly`, thiếu `monthly` để bắt tín hiệu xu hướng dài hơi hơn.

Đây là task **T5** trong sprint W2 (`note/LICH_TRINH_CONG_VIEC.md`).

## What Changes

1. **Đọc README mỗi repo trending**: connector fetch file README của từng repo qua `raw.githubusercontent.com` và nhét vào `raw_content`, có **cắt theo ngân sách** để tổng content không vượt giới hạn prompt (6000 ký tự) — Gemini phân tích trúng nội dung thay vì chỉ đoán từ tên repo.
2. **Thêm khung monthly**: seed source `GitHub Trending — Monthly All` (`since="monthly"`).
3. **Dedup theo owner/repo (xác nhận + khoá)**: fingerprint hiện tại `SHA256(source_url + title)` đã **độc lập với cửa sổ trend** (cùng `owner/repo` ⇒ cùng fingerprint) nên một repo trending ở cả daily/weekly/monthly chỉ tạo **1 raw document**. README **không** được đưa vào fingerprint. Thêm test khoá hành vi này để tránh rò rỉ quota ×2–3.
4. **Chịu lỗi**: README fetch thất bại (404/timeout) → fallback về content mô tả cũ, không crash pipeline.

## Capabilities

### Modified Capabilities
- `github-trending-ingestion`: connector đọc README repo trending làm giàu content; thêm seed source monthly; đảm bảo dedup theo `owner/repo` xuyên cửa sổ.

## Impact

**Backend files:**
- `app/connectors/github_trending_connector.py` — MODIFY: thêm bước fetch README + ghép vào content
- `app/scripts/seed_sources.py` — MODIFY: thêm source `GitHub Trending — Monthly All`
- `tests/` — NEW: test README enrichment + test dedup xuyên cửa sổ

**Backend (không đổi):** không thêm/sửa API endpoint; không migration DB; không đổi schema `RawDocument`.

**Non-goals:**
- Không fetch README cho nguồn không phải `github_trending`
- Không parse/render Markdown README (đưa raw text, để Gemini tự hiểu)
- Không lưu README thành cột/bảng riêng trong DB (chỉ nằm trong `raw_content`)
- Không dịch README sang tiếng Việt ở bước ingest
- Không dùng GitHub REST API cho README (tránh rate limit 60 req/giờ)

**Phase:** Phase 1
**Dependency:** `w1-quota-guard` (README enrichment phải nằm trong hạn mức quota mà W1 đã dựng — dedup + daily cap 500 docs)
