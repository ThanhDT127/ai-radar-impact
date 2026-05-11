## Why

Hệ thống đang phục vụ team Việt Nam (Rạng Đông) nhưng chỉ có **1 nguồn Việt** (VnExpress Số hóa) trong 18 nguồn gốc. Điều này nghĩa là radar gần như không bắt được:
- Chính sách AI/dữ liệu trong nước
- Xu hướng dev cộng đồng VN
- Doanh nghiệp Việt triển khai AI
- Tài liệu/khoá học/best practice tiếng Việt

Phase 2B lấp khoảng trống này bằng nguồn VN có RSS sạch (defer scraper-required sources cho `expand-source-coverage-2c` sau này).

## What Changes

Thêm **~12 nguồn Việt** vào `seed_sources.py`, chia 2 cluster:

**Cluster VN News (5-6)**:
- GenK
- VietnamNet ICT
- ICT News
- VnExpress AI4VN section (nếu có RSS riêng) — hoặc skip nếu trùng với VnExpress Số hóa
- CafeF Kinh tế số (nếu có RSS)
- VietTimes (verify)

**Cluster VN Community (6-7)**:
- Viblo (top posts feed)
- Daynhauhoc (Discourse forum, có RSS)
- MLOpsVN
- Machine Learning Cơ Bản
- 200lab Blog
- AI Vietnam (HuggingFace org page)
- AIO Conquer Blog (verify)

Tất cả `region = "vietnam"`. `target_roles` mở rộng vì community VN cover nhiều role hơn US-centric sources.

**Verify**: dùng `verify_feeds.py` đã tạo từ change 2.

## Capabilities

### Modified Capabilities
- `rss-ingestion`: Mở rộng seed với 2 cluster VN

## Impact

- **Backend code**: `scripts/seed_sources.py` (chỉ data)
- **Database**: Không thay đổi schema (đã có `region`/`target_roles`)
- **Frontend**: Không đổi
- **API**: Không đổi
- **Dependencies**: Không thêm
- **Phase**: Phase 2

## Non-goals

- Không thêm web scraper cho nguồn không có RSS (Bộ KH&CN, Thư viện Pháp luật, FPT.AI, VinAI...) — defer cho `expand-source-coverage-2c`
- Không refactor frontend để filter theo `region` (defer)
- Không build dashboard "Tin Việt Nam" tab riêng (defer)
- Không ingest Facebook Groups (KHÔNG khả thi, đã quyết định)

## Lưu ý quan trọng

- **Phụ thuộc**: Phase này phải chạy **sau** `add-china-ai-sources` vì cần `region`/`target_roles` columns
- VnExpress AI4VN có thể không có RSS riêng — verify; nếu không, skip và relying on existing VnExpress Số hóa feed
- Một số blog VN dùng platform Substack/Medium/Wordpress chuẩn → RSS đơn giản
- Daynhauhoc là Discourse forum — RSS feed thường ở `<URL>/latest.rss` hoặc `/posts.rss`
- Viblo có RSS chính thức tại `viblo.asia/rss` (verified theo announcement)
- Trust tier khuyến nghị thấp hơn nguồn quốc tế (medium thay vì high) vì content community-driven, độ kiểm chứng thấp hơn
