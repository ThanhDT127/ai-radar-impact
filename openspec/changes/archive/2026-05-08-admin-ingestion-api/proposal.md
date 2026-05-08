## Why

Hiện tại mọi thao tác ingestion/analysis đều phải chạy script qua Docker exec:
```
docker-compose exec backend python -m app.scripts.run_ingestion
docker-compose exec backend python -m app.scripts.run_analysis
```

Điều này không thuận tiện và không thể tích hợp vào workflow khác. Change này tạo Admin API endpoints để trigger thủ công qua HTTP, có authentication và rate limiting.

## What Changes

- Tạo Admin API router với 4 endpoints: trigger ingest, trigger analyze, list sources, add source
- API key authentication (Bearer token) cho admin endpoints
- Rate limiting: `MAX_DAILY_ANALYSIS` cap
- Cập nhật `docs/system_overview.md`

## Capabilities

### New Capabilities
- `admin-api`: Admin HTTP endpoints để quản lý ingestion, analysis, và sources — có API key auth và rate limiting

### Modified Capabilities
Không có

## Impact

- **Backend code:** Thêm `routes/admin.py`, `middleware/admin_auth.py`, sửa `config.py`, `main.py`
- **Database:** Không thay đổi schema
- **Frontend:** Không thay đổi (admin API dùng qua curl/Postman)
- **API:** Thêm 4 endpoints dưới `/api/v1/admin/`
- **Dependencies:** Không thêm dependency mới
- **Dependency:** Có thể làm song song với Change 2 hoặc 3
- **Phase:** Phase 1

## Non-goals

- Không tạo Admin UI (dùng qua curl/Postman)
- Không implement scheduler tự động (APScheduler deferred)
- Không implement full RBAC — chỉ API key đơn giản
- Không implement webhook/callback sau khi ingestion xong
