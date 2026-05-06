## Context

Đây là change đầu tiên của dự án AI Impact Radar — tạo skeleton project và vertical slice end-to-end: 1 nguồn RSS (GitHub Changelog) → AI analysis (Gemini Flash) → Insight → React dashboard. Chưa có code nào tồn tại, cần thiết kế từ đầu nhưng phải đảm bảo mở rộng được cho Phase 2/3 mà không phải refactor lại kiến trúc.

**Modules bị ảnh hưởng:** M1 (Source), M2 (Ingestion), M3 (Normalization), M4 (AI Analysis), M5 (Insight Repository), M6 (Dashboard)

## Goals / Non-Goals

**Goals:**
- Thiết kế cấu trúc code backend/frontend rõ ràng, dễ mở rộng
- Định nghĩa DB schema tối thiểu (3 bảng) đủ cho vertical slice
- Thiết kế pipeline ingestion → analysis thành các bước tách rời (pluggable)
- Chọn cách gọi Gemini API hiệu quả nhất

**Non-Goals:**
- Không thiết kế auth/RBAC, scheduler tự động, delivery, feedback
- Không thiết kế event clustering, vector search, chatbot
- Không tối ưu performance hay caching — chạy đúng trước

---

## Decisions

### D1. Monorepo structure

```
ai-radar-impact/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app factory
│   │   ├── config.py               # Pydantic Settings
│   │   ├── database.py             # SQLAlchemy async engine + session
│   │   ├── models/                 # SQLAlchemy models
│   │   │   ├── source.py
│   │   │   ├── raw_document.py
│   │   │   └── insight.py
│   │   ├── schemas/                # Pydantic response/request schemas
│   │   │   ├── insight.py
│   │   │   └── common.py
│   │   ├── routes/                 # FastAPI routers
│   │   │   ├── health.py
│   │   │   └── insights.py
│   │   ├── services/               # Business logic
│   │   │   ├── ingestion.py
│   │   │   ├── normalizer.py
│   │   │   └── analyzer.py
│   │   ├── repositories/           # DB queries
│   │   │   ├── source_repo.py
│   │   │   ├── raw_document_repo.py
│   │   │   └── insight_repo.py
│   │   ├── connectors/             # Source-specific fetchers
│   │   │   └── rss_connector.py
│   │   ├── ai/                     # LLM integration
│   │   │   ├── gemini_client.py
│   │   │   └── prompts.py
│   │   └── scripts/                # CLI entrypoints
│   │       ├── run_ingestion.py
│   │       └── seed_sources.py
│   ├── alembic/                    # DB migrations
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── pages/
│   │   │   ├── InsightList.tsx
│   │   │   └── InsightDetail.tsx
│   │   ├── components/
│   │   │   ├── InsightCard.tsx
│   │   │   ├── ImpactBadge.tsx
│   │   │   ├── Pagination.tsx
│   │   │   └── Layout.tsx
│   │   ├── api/
│   │   │   └── insights.ts
│   │   ├── types/
│   │   │   └── insight.ts
│   │   └── styles/
│   │       ├── global.css
│   │       └── insights.module.css
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── docker-compose.yml
├── .env.example
└── docs/
```

**Rationale:** Monorepo đơn giản — 1 repo, 2 thư mục. Không dùng monorepo tools (nx, turborepo) vì solo dev, không cần.

### D2. Database schema (3 bảng tối thiểu)

```sql
-- sources: metadata nguồn đã whitelist
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,        -- 'rss', 'api', 'web'
    feed_url TEXT,
    trust_tier VARCHAR(20) NOT NULL,          -- 'very_high', 'high', 'medium', 'low'
    topics TEXT[] DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

-- raw_documents: nội dung thô đã fetch
CREATE TABLE raw_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES sources(id),
    source_url TEXT NOT NULL,
    title VARCHAR(500),
    raw_content TEXT,
    normalized_content TEXT,
    author VARCHAR(255),
    published_at TIMESTAMP,
    fetched_at TIMESTAMP NOT NULL DEFAULT now(),
    fingerprint VARCHAR(64) NOT NULL,          -- SHA-256
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now(),
    UNIQUE(fingerprint)
);

-- insights: kết quả AI analysis
CREATE TABLE insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_document_id UUID NOT NULL REFERENCES raw_documents(id),
    title VARCHAR(500) NOT NULL,
    summary_short VARCHAR(300),
    summary_medium TEXT,
    topics TEXT[] DEFAULT '{}',
    event_type VARCHAR(50),
    nature VARCHAR(50),
    trust_score FLOAT DEFAULT 0.0,
    impact_label VARCHAR(20),
    source_url TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.0,
    status VARCHAR(20) NOT NULL DEFAULT 'published',
    ai_raw_response JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_insights_created_at ON insights(created_at DESC);
CREATE INDEX idx_raw_documents_fingerprint ON raw_documents(fingerprint);
CREATE INDEX idx_raw_documents_source_id ON raw_documents(source_id);
```

**Rationale:** Giữ đơn giản — không dùng bảng join `InsightSourceLink` ở giai đoạn này vì mỗi insight chỉ từ 1 raw document. Khi cần event clustering (Phase 2), thêm bảng join lúc đó. Field `ai_raw_response` JSONB lưu full LLM response để debug.

### D3. Pipeline architecture (pluggable steps)

```
run_ingestion.py
    │
    ▼
IngestionService.run(source_id?)
    │
    ├── 1. source_repo.get_active_sources()
    │
    ├── 2. For each source:
    │       connector = ConnectorFactory.get(source.source_type)
    │       raw_entries = connector.fetch(source)      ← RSSConnector
    │
    ├── 3. For each entry:
    │       fingerprint = hash(source_url + title)
    │       if raw_document_repo.exists(fingerprint): skip
    │       normalized = normalizer.clean(entry)
    │       raw_doc = raw_document_repo.create(entry + normalized)
    │
    ├── 4. For each new raw_doc:
    │       analysis = analyzer.analyze(raw_doc)       ← Gemini Flash
    │       insight = insight_repo.create(analysis)
    │
    └── 5. Return summary: { new: N, skipped: N, errors: N }
```

**Rationale:** Mỗi bước (fetch → normalize → analyze) là 1 service riêng, gọi tuần tự. Không dùng queue hay async pipeline ở Phase 1 — đơn giản, dễ debug. `ConnectorFactory` pattern cho phép thêm connector mới (Web, API) sau mà không sửa pipeline core.

### D4. Gemini Flash integration

- **SDK:** `google-genai` (official Python SDK)
- **Model:** `gemini-2.0-flash`
- **Approach:** Single API call kết hợp classify + summarize trong 1 prompt
- **Output format:** Yêu cầu JSON structured output với schema validation

```python
# Prompt structure (simplified)
ANALYSIS_PROMPT = """
Analyze this article and return JSON:
{
  "topics": ["<from allowed list>"],
  "event_type": "<from allowed list>",
  "nature": "<Risk|Opportunity|Compliance|Informational|Watchlist>",
  "summary_short": "<1-2 sentences, max 200 chars>",
  "summary_medium": "<1 paragraph, max 500 chars>",
  "confidence": <0.0-1.0>
}

Allowed topics: AI, Technology, Data, Software Process, Security, ...
Allowed event_types: New release, Policy change, ...

Rules:
- Only use information from the article
- Do not speculate or add external knowledge
- If uncertain, set confidence below 0.5

Article title: {title}
Article content: {content}
"""
```

**Rationale:** 1 API call thay vì 2 (classify riêng + summarize riêng) — tiết kiệm API cost và latency. Gemini Flash đủ giỏi để xử lý cả 2 task cùng lúc. Dùng JSON mode của Gemini để enforce output format.

### D5. Trust/Impact scoring (rule-based)

Không cần LLM cho scoring ở giai đoạn này:

| Source trust_tier | trust_score |
|---|---|
| very_high | 0.95 |
| high | 0.80 |
| medium | 0.60 |
| low | 0.40 |

| event_type | impact_label mặc định |
|---|---|
| Security alert | High |
| Deprecation | High |
| Policy change | High |
| Regulation update | High |
| New release | Medium |
| Operational incident | Medium |
| Research update | Low |
| Trend signal | Low |
| Community discussion | Watch |

**Rationale:** Rule-based đủ cho Phase 1 với 1 nguồn. Phase 2 sẽ dùng LLM scoring kết hợp internal context.

### D6. Frontend architecture

- **Data fetching:** TanStack Query — tự quản lý cache, loading, error states
- **Routing:** React Router v6 — 2 routes: `/` (list) và `/insights/:id` (detail)
- **Styling:** CSS Modules — scoped styles, không conflict, không cần build tool đặc biệt
- **No state management library** — TanStack Query đã quản lý server state, không cần Zustand ở giai đoạn này

### D7. API endpoints

| Method | Path | Mô tả | Response |
|---|---|---|---|
| GET | `/api/v1/health` | Health check | `{ status, db }` |
| GET | `/api/v1/insights` | List insights (paginated) | `{ page, size, total, items }` |
| GET | `/api/v1/insights/:id` | Insight detail | Insight object |

**Không có POST/PUT/DELETE** ở giai đoạn này — dữ liệu chỉ được tạo qua ingestion pipeline.

### D8. Docker Compose

```yaml
services:
  db:
    image: postgres:16-alpine
    ports: ["5432:5432"]
    environment:
      POSTGRES_DB: ai_radar
      POSTGRES_USER: radar
      POSTGRES_PASSWORD: radar_dev
    volumes:
      - pgdata:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [db]
    env_file: .env
    volumes:
      - ./backend:/app  # hot reload

volumes:
  pgdata:
```

**Rationale:** Chỉ 2 service. Frontend chạy Vite dev server ngoài Docker (hot reload nhanh hơn). n8n chưa cần ở giai đoạn này.

---

## Risks / Trade-offs

| Risk | Mitigation |
|---|---|
| Gemini API rate limit / quota hết | Xử lý graceful error, raw_doc giữ status=pending để retry |
| RSS feed thay đổi format | feedparser library đã xử lý hầu hết RSS/Atom variants |
| 1 API call classify+summarize có thể cho kết quả kém hơn 2 calls riêng | Monitor confidence score, nếu < 0.5 thì tách 2 calls ở iteration sau |
| Schema 3 bảng quá đơn giản cho Phase 2 | Thiết kế để thêm bảng join, bảng mới không cần sửa bảng cũ |
| Không có auth → ai cũng truy cập được | Chấp nhận ở vertical slice (local dev only), thêm auth ở change tiếp theo |
