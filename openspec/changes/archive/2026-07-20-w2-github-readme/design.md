## Context

`GitHubTrendingConnector.fetch()` scrape `github.com/trending`, mỗi repo build `raw_content` từ: tên repo + mô tả 1 dòng + ngôn ngữ + số sao (`_parse_repo`, ~dòng 136–146). Không đọc README.

Hai ràng buộc nền:
- **Fingerprint**: `make_fingerprint(source_url, title)` = `SHA256(f"{url}::{title}".lower())` (`normalizer.py:40`). Với github_trending: `source_url="https://github.com/{owner}/{repo}"`, `title="{owner}/{repo}"` — **cả hai độc lập với `since`**. ⇒ dedup theo owner/repo **đã có sẵn** qua `exists_by_fingerprint` (`ingestion.py:154`).
- **Prompt truncation**: prompt cắt content ở **6000 ký tự** (`prompts.py:87`). README dài phải được cắt trước để không lấn át phần metadata tín hiệu.

## Goals / Non-Goals

**Goals:**
- README repo trending vào được content → insight dẫn thông tin cụ thể (repo làm gì, thay thế/đối thủ, use case)
- Thêm khung monthly
- Không phá dedup, không rò rỉ quota ×2–3 khi repo trend ở nhiều cửa sổ
- Fail-safe: lỗi README không làm hỏng entry hay pipeline

**Non-Goals:**
- Không GitHub REST API (rate limit); không render Markdown; không cột DB riêng cho README; không dịch README.

## Decisions

### 1. Nguồn README = `raw.githubusercontent.com` (không phải REST API)
GitHub REST `/repos/{o}/{r}/readme` giới hạn **60 req/giờ** khi không auth. Một lần cào ~25 repo × nhiều nguồn trending ⇒ **vượt hạn mức**. `raw.githubusercontent.com` **không giới hạn rate** cho file public.

Thứ tự thử (dừng ở lần đầu HTTP 200):
```
https://raw.githubusercontent.com/{owner}/{repo}/HEAD/README.md
                                             .../HEAD/README.markdown
                                             .../HEAD/README.rst
                                             .../HEAD/readme.md
```
`HEAD` tự trỏ nhánh mặc định (main/master) nên không cần đoán branch.

### 2. Ngân sách README (không tràn prompt 6000)
- Cắt README ở **~4000 ký tự** (`README_MAX_CHARS`), bỏ khối code/badge lặp đầu file nếu rẻ để làm.
- Đặt README **sau** khối metadata chính (tên/mô tả/sao) để nếu prompt cắt 6000 thì phần bị mất là đuôi README, không phải tín hiệu cốt lõi.
- Config theo source: `config.fetch_readme` (mặc định `True`), `config.readme_max_chars` (mặc định 4000).

### 3. Dedup: KHÔNG thêm logic mới — chỉ xác nhận + test
Fingerprint đã key theo `owner/repo`. Ràng buộc: **README không được đưa vào `title`/`source_url`** ⇒ không ảnh hưởng fingerprint (README chỉ nằm trong `raw_content`). Thêm regression test: 2 entry cùng repo, khác `since`, cùng fingerprint ⇒ raw doc thứ hai bị skip.

### 4. Chịu lỗi & timeout
Mỗi README fetch dùng client timeout ngắn (~5s). Bất kỳ lỗi (404 mọi filename, timeout, 5xx) ⇒ log debug, giữ nguyên content mô tả cũ, entry vẫn hợp lệ. README fetch **không** được nhân số request quá đáng: chỉ fetch cho repo thực sự nằm trong `max_items`.

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| README fetch làm chậm mỗi lần cào (N repo × HTTP) | Timeout ngắn 5s/repo; chỉ fetch trong `max_items`; có thể tắt qua `fetch_readme=False` |
| README rỗng/chỉ badge (ít tín hiệu) | Vẫn giữ metadata cũ; content không tệ hơn hiện tại |
| `raw.githubusercontent.com` đổi/chặn | Fallback nhiều filename; lỗi → content mô tả cũ |
| README quá dài lấn prompt | Cắt 4000 ký tự, đặt sau metadata |

## Module ảnh hưởng
- **M2: Ingestion** — connector github_trending
- **M3: Normalization** — content dài hơn nhưng fingerprint không đổi
- **API endpoints**: không đổi
- **Bảng DB**: không đổi
- **AI/LLM**: vẫn Gemini Flash, grounding bám README (không suy diễn ngoài nội dung)
