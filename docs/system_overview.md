# AI Radar Impact - Tổng Quan Hệ Thống

## 1. Mục đích của bản hiện tại

Bản hiện tại là một vertical slice MVP để chứng minh một luồng end-to-end hoạt động được:

1. Lấy tin từ nguồn RSS
2. Chuẩn hóa nội dung
3. Lưu vào database
4. Gọi AI để phân tích và tạo insight
5. Hiển thị insight trên giao diện web

Phạm vi hiện tại còn hẹp và có chủ ý:

- 1 nguồn seed sẵn: `GitHub Changelog`
- 1 loại connector: `rss`
- 2 màn hình frontend: danh sách insight và chi tiết insight
- 2 API nghiệp vụ chính: list insight và detail insight
- Ingestion đang được chạy thủ công bằng script, chưa có scheduler tự động


## 2. Kiến trúc tổng quan

```text
RSS Feed
  ->
RSS Connector
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

Runtime local:

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Health check: `http://localhost:8000/api/v1/health`


## 3. Luồng dữ liệu: lấy, chuẩn hóa, lưu trữ, hiển thị

### 3.1 Lấy dữ liệu

Bước lấy dữ liệu nằm trong RSS pipeline.

File liên quan:

- `backend/app/connectors/rss_connector.py`
- `backend/app/services/ingestion.py`
- `backend/app/scripts/run_ingestion.py`
- `backend/app/scripts/seed_sources.py`

Cách nó hoạt động:

1. Bảng `sources` lưu danh sách nguồn được phép ingest
2. Hiện tại source được seed sẵn là `GitHub Changelog`
3. `run_ingestion.py` gọi `IngestionService.run()`
4. `IngestionService` lấy tất cả source có `status = active`
5. Nếu `source_type = rss` thì dùng `RSSConnector.fetch(...)`
6. Connector dùng `feedparser` để đọc RSS/Atom và trả về danh sách `FeedEntry`

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
- loại nguồn (`rss`, sau này có thể mở rộng `api`, `web`)
- `feed_url`
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

1. Analyzer lấy tất cả `raw_documents` có `processing_status = pending`
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

API hiện tại:

- `GET /api/v1/insights`
  - trả về danh sách insight có pagination
  - chỉ lấy các insight có `status = published`
- `GET /api/v1/insights/{id}`
  - trả về chi tiết 1 insight

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

### Xem kết quả

- UI: `http://localhost:5173`
- Health: `http://localhost:8000/api/v1/health`
- API list: `http://localhost:8000/api/v1/insights`


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

- chưa có auth / RBAC
- chưa có admin UI quản lý source
- chưa có scheduler tự động
- chưa có search / filter nâng cao
- chưa có notification
- chưa có workflow review / approve
- chưa có nhiều connector ngoài RSS
- parser output AI chưa đủ cứng, vẫn có khả năng fail nếu JSON model trả về bị cắt


## 7. Tóm tắt ngắn

Nếu cần nhìn hệ thống bằng 1 câu:

> Đây là một MVP ingest RSS, chuẩn hóa nội dung, lưu raw document, dùng Gemini tạo insight, rồi cho frontend đọc insight để hiển thị.

Và nếu cần nhớ bằng 4 dòng:

```text
Lấy dữ liệu      -> RSS feed
Chuẩn hóa        -> clean HTML + fingerprint
Lưu trữ          -> sources / raw_documents / insights
Xem kết quả      -> API insights + dashboard web
```
