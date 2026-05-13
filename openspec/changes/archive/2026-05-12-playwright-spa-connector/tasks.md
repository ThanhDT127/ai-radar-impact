## 1. Chuẩn bị môi trường

- [x] 1.1 Thêm `playwright` và `playwright-stealth` vào `backend/requirements.txt`
- [x] 1.2 Cập nhật `backend/Dockerfile`: thêm system deps cho Chromium và chạy `playwright install chromium --with-deps`
- [x] 1.3 Rebuild backend image: `docker-compose build backend` và xác nhận container khởi động thành công

## 2. Implement PlaywrightConnector

- [x] 2.1 Tạo `backend/app/connectors/playwright_connector.py` với class `PlaywrightConnector(BaseConnector)`
- [x] 2.2 Implement `fetch()`: launch Chromium, áp dụng `stealth_sync()`, goto listing page, extract links theo `link_selector` + `link_pattern`
- [x] 2.3 Implement vòng lặp fetch từng bài: goto article URL, `page.content()` → `trafilatura.extract()` → `ConnectorEntry`
- [x] 2.4 Xử lý `wait_for` config: gọi `page.wait_for_selector()` nếu có
- [x] 2.5 Xử lý lỗi per-bài: try/except, log warning, tiếp tục batch
- [x] 2.6 Đảm bảo `browser.close()` luôn được gọi (dùng try/finally)
- [x] 2.7 Đăng ký: `ConnectorRegistry.register("playwright", PlaywrightConnector)` cuối file

## 3. Kết nối vào hệ thống

- [x] 3.1 Import `PlaywrightConnector` trong `backend/app/connectors/__init__.py`
- [x] 3.2 Thêm `"playwright"` vào `__all__`

## 4. Test thủ công VietTimes

- [x] 4.1 Tạo tạm một Source `playwright` cho VietTimes trong DB (qua script hoặc psql) để test trước khi seed chính thức
- [x] 4.2 Chạy `run_ingestion --source-id <UUID>` và xác nhận lấy được ít nhất 5 bài có `raw_content` không rỗng
- [x] 4.3 Kiểm tra log: không có exception uncaught, browser đóng sau fetch
- [x] 4.4 Nếu VietTimes thất bại: điều chỉnh `link_selector` / `wait_for` config và re-test

## 5. Seed nguồn VN SPA

- [x] 5.1 Thêm VietTimes vào `seed_sources.py` (sau khi test 4.2 pass)
- [x] 5.2 Thêm ICTNews vào `seed_sources.py`
- [x] 5.3 Thêm MLOpsVN vào `seed_sources.py` (nếu site còn hoạt động)
- [x] 5.4 Chạy `seed_sources` và xác nhận 3 source mới có trong DB

## 6. Xác nhận end-to-end

- [x] 6.1 Chạy `run_ingestion` cho cả 3 source mới, xác nhận raw_documents được lưu
- [x] 6.2 Chạy `run_analysis`, xác nhận insights được sinh ra từ bài VietTimes/ICTNews
- [x] 6.3 Kiểm tra dashboard: insights từ nguồn VN mới hiển thị đúng

## 7. Sửa các sources bị hỏng / chưa ingest

- [x] 7.1 Fix Hugging Face Blog RSS — đổi sang web_index (RSS trả về 0 chars content)
- [x] 7.2 Fix Machine Learning Cơ Bản — đổi sang web_index (RSS trả về 0 chars content)
- [x] 7.3 Fix Viblo — đổi sang web_index (RSS summary 153 chars < threshold 200)
- [x] 7.4 Chạy ingest cho arXiv CS.IR, CS.SE, CS.CR (đã seed nhưng chưa ingest lần nào)
- [x] 7.5 Điều tra AWS Security Blog fail 80% — root cause: 429 RESOURCE_EXHAUSTED (rate limit Vertex AI trong batch lớn, không phải content issue). Fix: thêm retry với exponential backoff (5s/15s/45s) trong GeminiClient.analyze(); reset 93 failed docs về pending và re-analyze
