## ADDED Requirements

### Requirement: Project structure và skeleton

Dự án phải có cấu trúc monorepo đơn giản với 2 thư mục chính: `backend/` (Python FastAPI) và `frontend/` (React Vite TypeScript), cùng `docker-compose.yml` ở root.

#### Scenario: Backend skeleton chạy được
- **WHEN** developer chạy `docker-compose up`
- **THEN** FastAPI server khởi động thành công trên port 8000 và PostgreSQL trên port 5432

#### Scenario: Frontend skeleton chạy được
- **WHEN** developer chạy `npm run dev` trong thư mục `frontend/`
- **THEN** Vite dev server khởi động trên port 5173 với trang React mặc định

#### Scenario: Health check endpoint
- **WHEN** gọi `GET /api/v1/health`
- **THEN** trả về `200 OK` với body `{ "status": "ok", "db": "connected" }`

### Requirement: Database migration cơ bản

Hệ thống sử dụng Alembic để quản lý migration. Lần chạy đầu tiên phải tạo 3 bảng: `sources`, `raw_documents`, `insights`.

#### Scenario: Migration chạy lần đầu
- **WHEN** chạy `alembic upgrade head` trên database trống
- **THEN** 3 bảng `sources`, `raw_documents`, `insights` được tạo với đầy đủ columns và constraints

#### Scenario: Seed data nguồn mặc định
- **WHEN** chạy script `python -m backend.scripts.seed_sources`
- **THEN** Bảng `sources` có 1 record: GitHub Changelog (RSS, trust_tier=High, status=active)

### Requirement: Backend code structure

Backend FastAPI phải theo pattern route → service → repository, tách rõ 3 lớp.

#### Scenario: Tách lớp đúng
- **WHEN** developer thêm 1 endpoint mới
- **THEN** code được tổ chức thành: `routes/<domain>.py` → `services/<domain>.py` → `repositories/<domain>.py`

### Requirement: Environment configuration

Tất cả config nhạy cảm (DB URL, API keys) phải dùng biến môi trường, không hardcode.

#### Scenario: Config từ environment
- **WHEN** backend khởi động
- **THEN** đọc config từ `.env` file thông qua Pydantic Settings (`DATABASE_URL`, `GEMINI_API_KEY`)
