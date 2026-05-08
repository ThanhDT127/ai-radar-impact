## 1. Configuration

- [x] 1.1 Thêm `ADMIN_API_KEY` và `MAX_DAILY_ANALYSIS` vào `backend/app/config.py`
- [x] 1.2 Thêm `ADMIN_API_KEY` vào `docker-compose.yml` environment
- [x] 1.3 Thêm `ADMIN_API_KEY` vào `.env.example`

## 2. Authentication Middleware

- [x] 2.1 Tạo `backend/app/middleware/admin_auth.py` — dependency function `verify_admin_key()`
- [x] 2.2 Implement Bearer token check against `settings.ADMIN_API_KEY`

## 3. Admin Routes

- [x] 3.1 Tạo `backend/app/routes/admin.py` — router với prefix `/api/v1/admin`
- [x] 3.2 Implement `POST /admin/ingest` — trigger ingestion, optional `source_id` param
- [x] 3.3 Implement `POST /admin/analyze` — trigger analysis cho pending documents
- [x] 3.4 Implement `GET /admin/sources` — list sources với stats (doc count, insight count)
- [x] 3.5 Implement `POST /admin/sources` — add source mới (Pydantic schema validation)

## 4. Rate Limiting

- [x] 4.1 Implement in-memory daily counter trong `admin.py` hoặc separate module
- [x] 4.2 Check daily limit trước khi chạy analyze

## 5. App Integration

- [x] 5.1 Cập nhật `backend/app/main.py` — mount admin router

## 6. Documentation

- [x] 6.1 Đọc toàn bộ `docs/system_overview.md` và cập nhật chính xác: thêm Admin API vào Section 4 (vận hành), thêm endpoints vào danh sách API, cập nhật Section 6 (giới hạn)

## 7. Verification

- [x] 7.1 Test auth: request không có API key → 401
- [x] 7.2 Test auth: request có API key đúng → 200
- [x] 7.3 Test `POST /admin/ingest` → trigger ingestion thành công
- [x] 7.4 Test `POST /admin/analyze` → trigger analysis thành công
- [x] 7.5 Test `GET /admin/sources` → trả danh sách sources
- [x] 7.6 Test `POST /admin/sources` → tạo source mới
- [x] 7.7 Test rate limit: trigger analyze vượt `MAX_DAILY_ANALYSIS` → 429
