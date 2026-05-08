# AI Radar Impact - Tổng Quan Hệ Thống

## 1. Mục đích của bản hiện tại

Bản hiện tại là một vertical slice MVP để chứng minh một luồng end-to-end hoạt động được:

1. Lấy tin từ nguồn RSS
2. Chuẩn hóa nội dung
3. Lưu vào database
4. Gọi AI để phân tích và tạo insight
5. Hiển thị insight trên giao diện web

Phạm vi hiện tại:

- 18 nguồn seed: 15 RSS (GitHub, OpenAI, Google AI, AWS, NVIDIA...) + HackerNews + Reddit r/MachineLearning + Reddit r/artificial
- 3 loại connector: `rss`, `hackernews`, `reddit`
- 2 màn hình frontend: danh sách insight và chi tiết insight
- 2 API nghiệp vụ chính: list insight và detail insight
- Ingestion đang được chạy thủ công bằng script, chưa có scheduler tự động


## 2. Kiến trúc tổng quan

```text
RSS Feed / HN Firebase API / Reddit .json / Web URL
  ->
ConnectorRegistry (lookup by source_type)
  ->
Connector (RSSConnector / HackerNewsConnector / RedditConnector)
  ->
WebArticleConnector (trafilatura — dùng bởi HN và Reddit)
  ->
Normalizer
  ->
raw_documents (PostgreSQL)
  ->
Gemini / Vertex AI Analysis
  ->
insights (PostgreSQL)
  ->
FastAPI
  ->
React Dashboard
```

Thành phần chính:

- `backend`: FastAPI, SQLAlchemy, repository/service pattern
- `db`: PostgreSQL
- `frontend`: React + Vite + React Query
- `Vertex AI`: dùng Gemini để classify và summarize
- `ConnectorRegistry`: registry-based pattern ánh xạ `source_type → ConnectorClass`, cho phép mở rộng connector không cần sửa pipeline

Runtime local:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Health check: `http://localhost:8000/api/v1/health`


## 3. Luồng dữ liệu: lấy, chuẩn hóa, lưu trữ, hiển thị

### 3.1 Lấy dữ liệu

Bước lấy dữ liệu nằm trong RSS pipeline.

File liên quan:

- `backend/app/connectors/rss_connector.py`
- `backend/app/connectors/hackernews_connector.py`
- `backend/app/connectors/reddit_connector.py`
- `backend/app/connectors/web_article_connector.py`
- `backend/app/services/ingestion.py`
- `backend/app/scripts/run_ingestion.py`
- `backend/app/scripts/seed_sources.py`

Cách nó hoạt động:

1. Bảng `sources` lưu danh sách nguồn được phép ingest
2. `run_ingestion.py` gọi `IngestionService.run()`
3. `IngestionService` lấy tất cả source có `status = active`
4. Với mỗi source, gọi `ConnectorRegistry.get(source.source_type)` để lấy đúng connector
5. Registry tra cứu connector đã đăng ký theo `source_type`:
   - `"rss"` → `RSSConnector` (feedparser)
   - `"hackernews"` → `HackerNewsConnector` (HN Firebase API + trafilatura)
   - `"reddit"` → `RedditConnector` (Reddit .json endpoint + trafilatura)
6. Connector trả về danh sách `ConnectorEntry` — cấu trúc chung cho mọi loại connector
7. `IngestionService` áp dụng `min_content_length` filter — bài quá ngắn bị skip trước khi lưu
8. Nếu `source_type` chưa có connector đăng ký, hệ thống log warning và bỏ qua source đó

Connector tự đăng ký vào registry khi module được import (`connectors/__init__.py` import tất cả connector → trigger `ConnectorRegistry.register(...)`). Thêm connector mới chỉ cần tạo class kế thừa `BaseConnector` và thêm 1 dòng import — không cần sửa `IngestionService`.

Output của bước này chưa phải insight. Đây mới là dữ liệu gốc lấy từ feed:

- `source_url`
- `title`
- `raw_content`
- `author`
- `published_at`


### 3.2 Chuẩn hóa dữ liệu

File liên quan:

- `backend/app/services/normalizer.py`

Sau khi lấy entry từ RSS, hệ thống chuẩn hóa để đưa về dạng có thể xử lý ổn định:

1. Loại bỏ HTML tags bằng BeautifulSoup
2. Xóa script/style/iframe/no-script
3. Collapse khoảng trắng
4. Cắt nội dung đến giới hạn độ dài
5. Tạo `fingerprint` SHA-256 từ `source_url + title`

Mục tiêu của fingerprint:

- tránh lưu trùng bản ghi trùng lặp
- giúp pipeline ingest lại nhiều lần mà không tạo duplicate

Output của bước này:

- `normalized_content`
- `fingerprint`


### 3.3 Lưu trữ dữ liệu

Hệ thống hiện tại dùng 3 bảng chính:

#### `sources`

Lưu danh sách nguồn cho phép ingest.

Thông tin chính:

- tên nguồn
- loại nguồn (`rss`, `hackernews`, `reddit`)
- `feed_url` (null với HN/Reddit, dùng `config.subreddit` thay thế)
- `trust_tier`
- `topics`
- `status`
- `config`

#### `raw_documents`

Lưu tài liệu gốc sau khi đã lấy và chuẩn hóa.

Thông tin chính:

- `source_id`
- `source_url`
- `title`
- `raw_content`
- `normalized_content`
- `author`
- `published_at`
- `fingerprint`
- `processing_status`

Ý nghĩa `processing_status`:

- `pending`: vừa ingest xong, chưa phân tích
- `analyzed`: đã phân tích xong và tạo insight
- `failed`: phân tích lỗi hoặc không đạt điều kiện

#### `insights`

Lưu kết quả phân tích cuối cùng để frontend đọc và hiển thị.

Thông tin chính:

- `raw_document_id`
- `title`
- `summary_short`
- `summary_medium`
- `topics`
- `event_type`
- `nature`
- `trust_score`
- `impact_label`
- `source_url`
- `confidence`
- `status`
- `ai_raw_response`


### 3.4 Phân tích AI và tạo insight

File liên quan:

- `backend/app/ai/prompts.py`
- `backend/app/ai/gemini_client.py`
- `backend/app/services/analyzer.py`
- `backend/app/scripts/run_analysis.py`

Luồng xử lý:

1. Analyzer lấy tất cả `raw_documents` có `processing_status = pending` (tối đa `MAX_DAILY_ANALYSIS = 500` mỗi ngày)
2. Lấy nội dung ưu tiên `normalized_content`, fallback sang `raw_content`
3. Gọi Gemini qua `GeminiClient.analyze(title, content)`
4. Prompt yêu cầu model trả về JSON có cấu trúc
5. Kết quả được parse thành `AnalysisResult`
6. Nếu có lỗi hoặc confidence thấp hơn ngưỡng, document được đánh `failed`
7. Nếu hợp lệ, hệ thống:
   - map `trust_tier -> trust_score`
   - map `event_type -> impact_label`
   - tạo 1 record trong bảng `insights`
   - cập nhật `raw_document.processing_status = analyzed`

Hệ thống hiện tại dùng kết hợp:

- AI cho classify và summarize
- rule-based logic cho `trust_score` và `impact_label`

Điều này có nghĩa:

- AI không quyết định toàn bộ
- một phần chuyển sang logic backend để dễ kiểm soát hơn


### 3.5 Xem thông tin đã lấy được

Frontend không tự đi crawl hay gọi AI. Frontend chỉ đọc dữ liệu đã được backend xử lý xong.

File liên quan:

- `frontend/src/api/insights.ts`
- `frontend/src/pages/InsightList.tsx`
- `frontend/src/pages/InsightDetail.tsx`
- `backend/app/routes/insights.py`

API public (frontend):

- `GET /api/v1/insights` — danh sách insight có pagination, chỉ `status = published`
- `GET /api/v1/insights/{id}` — chi tiết 1 insight

API admin (yêu cầu `Authorization: Bearer <ADMIN_API_KEY>`):

- `POST /api/v1/admin/ingest` — trigger ingestion, optional `?source_id=<UUID>`
- `POST /api/v1/admin/analyze` — trigger AI analysis cho pending documents (có daily cap → 429 khi vượt)
- `GET /api/v1/admin/sources` — danh sách sources với insight count
- `POST /api/v1/admin/sources` — thêm source mới

Frontend hiển thị:

- Trang `/`
  - list insight cards
  - summary ngắn
  - topics
  - impact badge
- Trang `/insights/:id`
  - title
  - summary ngắn
  - summary đầy đủ hơn
  - topics
  - event type
  - nature
  - confidence
  - link tới bài gốc


## 4. Cách vận hành hệ thống hiện tại

### Khởi động hệ thống

```powershell
docker-compose up -d
```

### Seed source

```powershell
docker-compose exec backend python -m app.scripts.seed_sources
```

### Chạy ingestion

```powershell
docker-compose exec backend python -m app.scripts.run_ingestion
```

### Chạy lại phân tích cho các document pending

```powershell
docker-compose exec backend python -m app.scripts.run_analysis
```

### Đưa các document failed về pending để phân tích lại

```powershell
docker-compose exec backend python -m app.scripts.reset_failed
```

### Trigger ingestion qua Admin API

```powershell
# Tất cả sources
curl -X POST http://localhost:8000/api/v1/admin/ingest -H "Authorization: Bearer changeme"

# Một source cụ thể
curl -X POST "http://localhost:8000/api/v1/admin/ingest?source_id=<UUID>" -H "Authorization: Bearer changeme"
```

### Trigger analysis qua Admin API

```powershell
curl -X POST http://localhost:8000/api/v1/admin/analyze -H "Authorization: Bearer changeme"
```

### Thêm source mới qua Admin API

```powershell
curl -X POST http://localhost:8000/api/v1/admin/sources `
  -H "Authorization: Bearer changeme" `
  -H "Content-Type: application/json" `
  -d '{"name":"My Feed","source_type":"rss","feed_url":"https://...","trust_tier":"medium","topics":["Công nghệ"]}'
```

### Xem danh sách sources qua Admin API

```powershell
curl http://localhost:8000/api/v1/admin/sources -H "Authorization: Bearer changeme"
```

### Xem kết quả

- UI: `http://localhost:5173`
- Health: `http://localhost:8000/api/v1/health`
- API list: `http://localhost:8000/api/v1/insights`
- Admin API: `http://localhost:8000/api/v1/admin/` (Bearer token required)


## 5. Cách hiểu dữ liệu trong hệ thống

Nếu muốn đọc hệ thống theo đúng thứ tự nghiệp vụ, hãy hiểu như sau:

### A. Source

Nguồn nào được phép lấy dữ liệu?

Trả lời nằm ở bảng `sources`.

### B. Raw document

Hệ thống đã lấy được bài nào từ nguồn?

Trả lời nằm ở bảng `raw_documents`.

Nếu trong bảng này có dữ liệu thì chứng tỏ connector + ingestion đang chạy.

### C. Insight

Hệ thống đã biến bài viết đó thành insight để user xem chưa?

Trả lời nằm ở bảng `insights`.

Nếu `raw_documents` có nhiều mà `insights` ít, thì vấn đề nằm ở bước AI analysis hoặc parser.


## 6. Giới hạn của bản hiện tại

Bản này chưa phải nền tảng hoàn chỉnh. Các phần sau chưa có hoặc chưa đầy đủ:

- chưa có auth / RBAC cho public API
- đã có Admin API (Bearer token) cho ingestion, analysis, source management — chưa có Admin UI
- chưa có scheduler tự động
- chưa có search / filter nâng cao
- chưa có notification
- chưa có workflow review / approve
- đã có HackerNews, Reddit, Web article connector — 18 nguồn đang active
- parser output AI chưa đủ cứng, vẫn có khả năng fail nếu JSON model trả về bị cắt


## 7. Tóm tắt ngắn

Nếu cần nhìn hệ thống bằng 1 câu:

> Đây là một MVP ingest RSS, chuẩn hóa nội dung, lưu raw document, dùng Gemini tạo insight, rồi cho frontend đọc insight để hiển thị.

Và nếu cần nhớ bằng 4 dòng:

```text
Lấy dữ liệu      -> RSS / HackerNews / Reddit / Web
Chuẩn hóa        -> clean HTML + fingerprint + min_content_length filter
Lưu trữ          -> sources / raw_documents / insights
Xem kết quả      -> API insights + dashboard web
```
