# AI Radar Impact

> Hệ thống theo dõi và phân tích tác động của AI theo lĩnh vực, nghề nghiệp và thời gian — powered by Vertex AI (Gemini).

## Kiến trúc

```
┌─────────────────────────────────────────────────────────┐
│                    AI Radar Impact                      │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │ RSS Feed │───▶│ Ingestion│───▶│  Vertex AI       │  │
│  │ Sources  │    │ Pipeline │    │  (Gemini Flash)  │  │
│  └──────────┘    └──────────┘    └────────┬─────────┘  │
│                                           │             │
│  ┌──────────┐    ┌──────────┐    ┌────────▼─────────┐  │
│  │ React    │◀───│ FastAPI  │◀───│  PostgreSQL       │  │
│  │ Frontend │    │ Backend  │    │  (Insights DB)   │  │
│  └──────────┘    └──────────┘    └──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Cấu trúc thư mục

```
ai-radar-impact/
├── backend/
│   ├── app/
│   │   ├── ai/                  # Vertex AI client + prompts
│   │   ├── connectors/          # RSS connector
│   │   ├── models/              # SQLAlchemy models
│   │   ├── repositories/        # Data access layer
│   │   ├── routes/              # FastAPI routes
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── scripts/             # CLI scripts (ingestion, analysis, seed)
│   │   ├── services/            # Business logic
│   │   ├── config.py            # Settings (env vars)
│   │   ├── database.py          # SQLAlchemy async engine
│   │   └── main.py              # FastAPI app factory
│   ├── alembic/                 # DB migrations
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/                 # API client functions
│       ├── components/          # React components
│       ├── pages/               # InsightList, InsightDetail
│       ├── styles/              # Global + module CSS
│       └── types/               # TypeScript interfaces
├── secrets/                     # SA key (gitignored)
│   └── sa-key.json
├── docker-compose.yml
├── .env                         # Local config (gitignored)
└── .env.example                 # Template config
```

## Prerequisites

- **Docker Desktop** — https://www.docker.com/products/docker-desktop
- **Google Cloud Project** với Vertex AI API enabled
- **Service Account JSON key** có role `Vertex AI User`

## Setup

### 1. Clone và cấu hình env

```bash
git clone https://github.com/ThanhDT127/ai-radar-impact.git
cd ai-radar-impact
cp .env.example .env
```

Chỉnh `.env`:
```env
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_USE_VERTEXAI=True
```

### 2. Thêm Service Account key

Tạo SA trên GCP với role **Vertex AI User**, download JSON key và đặt vào:
```
secrets/sa-key.json
```

### 3. Khởi động services

```bash
docker-compose up -d
```

### 4. Chạy migration + seed

```bash
# Chạy migration tạo schema
docker-compose exec backend alembic upgrade head

# Seed sources (GitHub Changelog RSS)
docker-compose exec backend python -m app.scripts.seed_sources
```

## Chạy ingestion pipeline

```bash
# Thu thập tất cả sources
docker-compose exec backend python -m app.scripts.run_ingestion

# Thu thập 1 source cụ thể
docker-compose exec backend python -m app.scripts.run_ingestion --source-id <UUID>
```

## Chạy AI analysis

```bash
# Phân tích tất cả documents pending
docker-compose exec backend python -m app.scripts.run_analysis
```

## Dev workflow

```bash
# Backend API (hot-reload)
docker-compose up backend

# Frontend (Vite dev server)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

## API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/insights` | List insights (paginated) |
| GET | `/api/v1/insights/{id}` | Chi tiết insight |

Query params cho list: `page` (default: 1), `size` (default: 20)

## Troubleshooting

**Lỗi 404 Vertex AI model**: Kiểm tra `GOOGLE_CLOUD_LOCATION` phải là region cụ thể (ví dụ `us-central1`), không phải `global`.

**Lỗi auth Vertex AI**: Kiểm tra `secrets/sa-key.json` tồn tại và SA có role `Vertex AI User`.

**Container không start**: Chạy `docker-compose logs backend` để xem lỗi chi tiết.
