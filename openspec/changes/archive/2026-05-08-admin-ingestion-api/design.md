## Context

Hiện tại admin phải SSH/Docker exec vào container để chạy ingestion/analysis scripts. Change này cung cấp HTTP API endpoints để trigger thủ công, có auth bảo vệ.

### Modules bị ảnh hưởng
- **M10 (Admin & Governance):** Thêm admin API endpoints
- **M2 (Ingestion):** Expose ingestion trigger qua API
- **M4 (AI Analysis):** Expose analysis trigger qua API
- **M1 (Source Management):** CRUD source qua API

## Goals / Non-Goals

**Goals:**
- 4 Admin API endpoints (ingest, analyze, list sources, add source)
- API key authentication
- Rate limiting (daily analysis cap)
- Cập nhật `docs/system_overview.md`

**Non-Goals:**
- Không tạo Admin UI
- Không implement scheduler
- Không implement full RBAC/JWT

## Decisions

### D1: Admin API endpoints

| Method | Path | Description |
|:---|:---|:---|
| `POST` | `/api/v1/admin/ingest` | Trigger ingestion (all sources hoặc `?source_id=`) |
| `POST` | `/api/v1/admin/analyze` | Trigger analysis cho pending documents |
| `GET` | `/api/v1/admin/sources` | List sources với stats (doc count, last ingest) |
| `POST` | `/api/v1/admin/sources` | Thêm source mới |

### D2: Authentication — API Key
```python
# middleware/admin_auth.py
async def verify_admin_key(authorization: str = Header()):
    if authorization != f"Bearer {settings.ADMIN_API_KEY}":
        raise HTTPException(401, "Invalid admin API key")
```

`ADMIN_API_KEY` config qua env var. Đơn giản, đủ cho 1-dev team.

### D3: Rate limiting
Dùng in-memory counter (dict) cho daily analysis cap:
```python
_daily_counts: dict[str, int] = {}  # date_str -> count

def check_daily_limit():
    today = date.today().isoformat()
    if _daily_counts.get(today, 0) >= settings.MAX_DAILY_ANALYSIS:
        raise HTTPException(429, "Daily analysis limit reached")
```

### D4: Ingest endpoint response
```json
{
  "status": "completed",
  "summary": {
    "new": 15,
    "skipped": 42,
    "errors": 2,
    "insights_created": 12
  }
}
```

### API endpoints mới
- `POST /api/v1/admin/ingest`
- `POST /api/v1/admin/analyze`
- `GET /api/v1/admin/sources`
- `POST /api/v1/admin/sources`

### Bảng DB bị ảnh hưởng
Không thay đổi schema.

## Risks / Trade-offs

| Risk | Mitigation |
|:---|:---|
| API key simple auth — không production-grade | Đủ cho Phase 1 solo dev, upgrade JWT/RBAC sau |
| In-memory rate limit reset khi restart | Acceptable cho manual triggering |
| Long-running ingest request timeout | Set timeout cao (300s), trả summary khi xong |
