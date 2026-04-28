# 05. DATA MODEL, ERD & API SPEC — AI IMPACT RADAR

## 1. Thiết kế dữ liệu mức khái niệm

### 1.1 Entity chính
#### Source
- source_id
- name
- source_type
- domain
- access_method
- trust_tier_default
- category_tags
- crawl_schedule
- status

#### RawDocument
- document_id
- source_id
- url
- title
- raw_content
- language
- published_at
- fetched_at
- author
- metadata_json
- fingerprint
- processing_status

#### EventCluster
- event_id
- title
- canonical_topic
- first_seen_at
- last_seen_at
- confidence

#### Insight
- insight_id
- event_id (nullable phase 1)
- title
- summary_short
- summary_medium
- summary_role_based_json
- topic
- event_type
- trust_score
- impact_score
- impact_label
- impact_departments_json
- nature
- priority
- recommendation
- status
- created_at

#### InsightSourceLink
- insight_id
- document_id
- relation_type (primary/corroborating/reference)

#### DeliveryRule
- rule_id
- audience_type
- audience_ref
- topics
- min_impact
- channels
- schedule
- status

#### DeliveryLog
- delivery_id
- insight_id
- channel
- recipient_group
- sent_at
- status

#### Feedback
- feedback_id
- insight_id
- user_id
- rating
- reason_code
- comment
- created_at

#### UserRoleMapping
- user_id
- role
- department
- permission_set

#### TaxonomyConfig
- taxonomy_id
- taxonomy_type
- code
- label
- parent_code
- active

---

## 2. ERD chi tiết và quan hệ dữ liệu

### 2.1 Quan hệ chính
- **Source** 1 - N **RawDocument**
- **RawDocument** 1 - 0..1 **NormalizedDocument**
- **NormalizedDocument** N - 1 **EventCluster** (phase 2 trở lên)
- **EventCluster** 1 - N **Insight** hoặc 1 cluster tạo ra 1 insight canonical tùy design cụ thể
- **Insight** N - N **NormalizedDocument** thông qua **InsightSourceLink**
- **Insight** 1 - N **InsightDepartment**
- **Insight** 1 - N **Delivery**
- **Insight** 1 - N **Feedback**
- **User** 1 - N **UserRole**
- **DeliveryRule** 1 - N **Delivery**
- **Taxonomy** được tham chiếu bởi Source, Insight, Rule, Department mapping

### 2.2 Ràng buộc logic
- Một insight bắt buộc phải có ít nhất một source link
- Một raw document có thể bị đánh dấu duplicate và không tạo normalized document mới nếu áp dụng cơ chế hợp nhất sớm
- Một delivery phải gắn với ít nhất một insight và một rule hoặc lý do gửi trực tiếp
- Feedback phải gắn user và insight

### 2.3 Chỉ mục nên có
- Index theo topic, impact_label, trust_label trên bảng insights
- Index theo source_id và fetched_at trên raw_documents
- Index theo published_at trên normalized_documents
- Index theo department_code trên insight_departments
- Full-text hoặc vector index cho summary/title/body_cleaned

---

## 3. Database schema sơ bộ chi tiết

### 3.1 Bảng sources
- id
- code
- name
- source_type
- source_subtype
- base_url
- access_method
- auth_config_json
- crawl_schedule
- default_topic
- default_trust_tier
- status
- created_by
- created_at
- updated_at

### 3.2 Bảng raw_documents
- id
- source_id
- external_ref
- url
- title_raw
- content_raw
- author_raw
- published_at_raw
- language_detected
- metadata_json
- fetched_at
- fingerprint
- ingest_status
- error_message

### 3.3 Bảng normalized_documents
- id
- raw_document_id
- title
- body_cleaned
- summary_extract
- published_at
- author
- source_domain
- language
- dedup_group_key
- normalized_status
- created_at

### 3.4 Bảng event_clusters
- id
- canonical_title
- canonical_topic
- canonical_event_type
- first_seen_at
- last_seen_at
- cluster_confidence
- status

### 3.5 Bảng insights
- id
- event_cluster_id
- title
- summary_short
- summary_medium
- summary_role_json
- topic
- event_type
- trust_score
- trust_label
- impact_score
- impact_label
- nature
- recommendation_text
- priority_label
- status
- created_at
- updated_at

### 3.6 Bảng insight_source_links
- id
- insight_id
- normalized_document_id
- relation_type
- weight

### 3.7 Bảng insight_departments
- id
- insight_id
- department_code
- role_code
- relevance_score

### 3.8 Bảng delivery_rules
- id
- name
- audience_type
- audience_ref
- topics_json
- min_impact
- trust_threshold
- channels_json
- digest_type
- schedule
- active_flag
- created_at
- updated_at

### 3.9 Bảng deliveries
- id
- insight_id
- rule_id
- channel
- recipient_group
- payload_snapshot_json
- sent_at
- delivery_status
- error_message

### 3.10 Bảng feedbacks
- id
- insight_id
- user_id
- feedback_type
- rating
- comment
- created_at

### 3.11 Bảng users
- id
- username/email
- display_name
- department_code
- status

### 3.12 Bảng user_roles
- id
- user_id
- role_code
- assigned_at

### 3.13 Bảng taxonomies
- id
- taxonomy_type
- code
- label
- parent_code
- active_flag

### 3.14 Bảng job_logs
- id
- job_type
- source_id
- started_at
- finished_at
- job_status
- records_processed
- error_message

### 3.15 Bảng audit_logs
- id
- actor_id
- action_type
- entity_type
- entity_id
- before_json
- after_json
- created_at

---

## 4. DDL định hướng sơ bộ

### 4.1 sources
- id UUID PK
- code VARCHAR UNIQUE
- name VARCHAR NOT NULL
- source_type VARCHAR NOT NULL
- source_subtype VARCHAR NULL
- base_url TEXT NOT NULL
- access_method VARCHAR NOT NULL
- auth_config_json JSONB NULL
- crawl_schedule VARCHAR NOT NULL
- default_topic VARCHAR NULL
- default_trust_tier VARCHAR NOT NULL
- status VARCHAR NOT NULL
- created_by UUID NULL
- created_at TIMESTAMP NOT NULL
- updated_at TIMESTAMP NOT NULL

### 4.2 raw_documents
- id UUID PK
- source_id UUID FK -> sources.id
- external_ref VARCHAR NULL
- url TEXT NOT NULL
- title_raw TEXT NULL
- content_raw TEXT NULL
- author_raw TEXT NULL
- published_at_raw TEXT NULL
- language_detected VARCHAR NULL
- metadata_json JSONB NULL
- fetched_at TIMESTAMP NOT NULL
- fingerprint VARCHAR NOT NULL
- ingest_status VARCHAR NOT NULL
- error_message TEXT NULL

### 4.3 normalized_documents
- id UUID PK
- raw_document_id UUID FK -> raw_documents.id
- title TEXT NULL
- body_cleaned TEXT NULL
- summary_extract TEXT NULL
- published_at TIMESTAMP NULL
- author TEXT NULL
- source_domain VARCHAR NULL
- language VARCHAR NULL
- dedup_group_key VARCHAR NULL
- normalized_status VARCHAR NOT NULL
- created_at TIMESTAMP NOT NULL

### 4.4 event_clusters
- id UUID PK
- canonical_title TEXT NOT NULL
- canonical_topic VARCHAR NOT NULL
- canonical_event_type VARCHAR NOT NULL
- first_seen_at TIMESTAMP NOT NULL
- last_seen_at TIMESTAMP NOT NULL
- cluster_confidence NUMERIC(5,2) NULL
- status VARCHAR NOT NULL

### 4.5 insights
- id UUID PK
- event_cluster_id UUID NULL FK -> event_clusters.id
- title TEXT NOT NULL
- summary_short TEXT NOT NULL
- summary_medium TEXT NULL
- summary_role_json JSONB NULL
- topic VARCHAR NOT NULL
- event_type VARCHAR NOT NULL
- trust_score NUMERIC(5,2) NOT NULL
- trust_label VARCHAR NOT NULL
- impact_score NUMERIC(5,2) NOT NULL
- impact_label VARCHAR NOT NULL
- nature VARCHAR NOT NULL
- recommendation_text TEXT NULL
- priority_label VARCHAR NOT NULL
- status VARCHAR NOT NULL
- created_at TIMESTAMP NOT NULL
- updated_at TIMESTAMP NOT NULL

### 4.6 insight_source_links
- id UUID PK
- insight_id UUID FK -> insights.id
- normalized_document_id UUID FK -> normalized_documents.id
- relation_type VARCHAR NOT NULL
- weight NUMERIC(5,2) NULL

### 4.7 insight_departments
- id UUID PK
- insight_id UUID FK -> insights.id
- department_code VARCHAR NOT NULL
- role_code VARCHAR NULL
- relevance_score NUMERIC(5,2) NULL

### 4.8 delivery_rules
- id UUID PK
- name VARCHAR NOT NULL
- audience_type VARCHAR NOT NULL
- audience_ref VARCHAR NOT NULL
- topics_json JSONB NULL
- min_impact VARCHAR NOT NULL
- trust_threshold VARCHAR NULL
- channels_json JSONB NOT NULL
- digest_type VARCHAR NOT NULL
- schedule VARCHAR NOT NULL
- active_flag BOOLEAN NOT NULL
- created_at TIMESTAMP NOT NULL
- updated_at TIMESTAMP NOT NULL

### 4.9 deliveries
- id UUID PK
- insight_id UUID FK -> insights.id
- rule_id UUID NULL FK -> delivery_rules.id
- channel VARCHAR NOT NULL
- recipient_group VARCHAR NOT NULL
- payload_snapshot_json JSONB NULL
- sent_at TIMESTAMP NULL
- delivery_status VARCHAR NOT NULL
- error_message TEXT NULL

### 4.10 feedbacks
- id UUID PK
- insight_id UUID FK -> insights.id
- user_id UUID FK -> users.id
- feedback_type VARCHAR NOT NULL
- rating INTEGER NULL
- comment TEXT NULL
- created_at TIMESTAMP NOT NULL

### 4.11 users
- id UUID PK
- account_key VARCHAR UNIQUE NOT NULL
- display_name VARCHAR NOT NULL
- department_code VARCHAR NULL
- status VARCHAR NOT NULL

### 4.12 user_roles
- id UUID PK
- user_id UUID FK -> users.id
- role_code VARCHAR NOT NULL
- assigned_at TIMESTAMP NOT NULL

### 4.13 taxonomies
- id UUID PK
- taxonomy_type VARCHAR NOT NULL
- code VARCHAR NOT NULL
- label VARCHAR NOT NULL
- parent_code VARCHAR NULL
- active_flag BOOLEAN NOT NULL

### 4.14 job_logs
- id UUID PK
- job_type VARCHAR NOT NULL
- source_id UUID NULL FK -> sources.id
- started_at TIMESTAMP NOT NULL
- finished_at TIMESTAMP NULL
- job_status VARCHAR NOT NULL
- records_processed INTEGER NULL
- error_message TEXT NULL

### 4.15 audit_logs
- id UUID PK
- actor_id UUID NULL FK -> users.id
- action_type VARCHAR NOT NULL
- entity_type VARCHAR NOT NULL
- entity_id UUID NULL
- before_json JSONB NULL
- after_json JSONB NULL
- created_at TIMESTAMP NOT NULL

---

## 5. API sơ bộ

### 5.1 API dashboard
- GET /insights
- GET /insights/{id}
- GET /dashboard/summary
- GET /dashboard/executive
- GET /topics
- GET /departments

### 5.2 API admin
- GET /sources
- POST /sources
- PUT /sources/{id}
- POST /sources/{id}/enable
- POST /sources/{id}/disable
- GET /delivery-rules
- POST /delivery-rules
- PUT /delivery-rules/{id}

### 5.3 API processing/ops
- POST /jobs/ingest/run
- GET /jobs/status
- GET /health
- GET /logs/summary

### 5.4 API feedback
- POST /insights/{id}/feedback
- GET /feedback/stats

### 5.5 API chatbot
- POST /chat/query
- GET /chat/history

---

## 6. API spec chi tiết hơn

### 6.1 API - Sources
#### GET /api/v1/sources
Mục đích: lấy danh sách nguồn
Query params:
- status
- source_type
- keyword

Response fields:
- id, name, type, schedule, trust tier, status, last run status

#### POST /api/v1/sources
Request body:
- name
- source_type
- base_url
- access_method
- crawl_schedule
- default_topic
- default_trust_tier
- status

Validation:
- name không rỗng
- base_url hợp lệ
- crawl_schedule hợp lệ

#### PUT /api/v1/sources/{id}
Cập nhật nguồn

#### POST /api/v1/sources/{id}/test
Chạy test ingest cho nguồn

#### POST /api/v1/sources/{id}/toggle
Bật/tắt nguồn

### 6.2 API - Insights
#### GET /api/v1/insights
Query params:
- topic
- impact_label
- trust_label
- department
- from_date
- to_date
- keyword
- page
- size

#### GET /api/v1/insights/{id}
Trả chi tiết insight gồm:
- summary
- source links
- trust/impact
- department mapping
- recommendation
- timeline

### 6.3 API - Dashboard
#### GET /api/v1/dashboard/overview
Trả về:
- total insights period
- top risks
- top opportunities
- top compliance alerts
- trend counts by topic

#### GET /api/v1/dashboard/executive
Trả về summary đã tối ưu cho executive

### 6.4 API - Delivery rules
- GET /api/v1/delivery-rules
- POST /api/v1/delivery-rules
- PUT /api/v1/delivery-rules/{id}
- DELETE /api/v1/delivery-rules/{id}

### 6.5 API - Feedback
#### POST /api/v1/insights/{id}/feedback
Request body:
- feedback_type
- rating
- comment

#### GET /api/v1/feedback/summary

### 6.6 API - Chat
#### POST /api/v1/chat/query
Request body:
- question
- filters(optional)

Response:
- answer
- cited_insight_ids
- cited_sources
- confidence_note

### 6.7 API - Ops
- GET /api/v1/ops/jobs
- GET /api/v1/ops/jobs/{id}
- GET /api/v1/health
- GET /api/v1/ops/metrics

---

## 7. API contract request/response chi tiết

### 7.1 GET /api/v1/insights
#### Request query
- page: number
- size: number
- keyword: string
- topic: string
- impact_label: string
- trust_label: string
- department: string
- event_type: string
- nature: string
- from_date: ISO datetime/date
- to_date: ISO datetime/date
- sort_by: newest|impact|trust

#### Response mẫu
```json
{
  "page": 1,
  "size": 20,
  "total": 132,
  "items": [
    {
      "id": "uuid",
      "title": "Google updates AI usage policy",
      "summary_short": "...",
      "topic": "AI",
      "event_type": "Policy change",
      "trust_label": "High",
      "impact_label": "High",
      "nature": "Compliance",
      "departments": ["Legal", "Data/AI"],
      "source_count": 3,
      "published_at": "2026-04-20T10:00:00Z",
      "first_seen_at": "2026-04-20T12:00:00Z"
    }
  ]
}
```

### 7.2 GET /api/v1/insights/{id}
#### Response mẫu
```json
{
  "id": "uuid",
  "title": "...",
  "summary_short": "...",
  "summary_medium": "...",
  "summary_role": {
    "manager": "...",
    "developer": "...",
    "legal": "..."
  },
  "topic": "AI",
  "event_type": "Policy change",
  "trust_score": 82.5,
  "trust_label": "High",
  "impact_score": 88.0,
  "impact_label": "Critical",
  "nature": "Compliance",
  "priority_label": "P1",
  "departments": [
    {"department": "Legal", "relevance_score": 0.92},
    {"department": "Data/AI", "relevance_score": 0.81}
  ],
  "recommendation_text": "...",
  "sources": [
    {
      "type": "primary",
      "title": "...",
      "url": "...",
      "domain": "...",
      "published_at": "..."
    }
  ],
  "timeline": [
    {"time": "...", "event": "first_seen"}
  ],
  "feedback_summary": {
    "useful": 10,
    "not_useful": 2
  }
}
```

### 7.3 POST /api/v1/sources
#### Request body mẫu
```json
{
  "name": "OpenAI Blog",
  "source_type": "official",
  "base_url": "https://openai.com/news",
  "access_method": "rss",
  "crawl_schedule": "0 */6 * * *",
  "default_topic": "AI",
  "default_trust_tier": "Very High",
  "status": "active"
}
```

#### Response mẫu
```json
{
  "id": "uuid",
  "message": "Source created successfully"
}
```

### 7.4 POST /api/v1/insights/{id}/feedback
#### Request body mẫu
```json
{
  "feedback_type": "wrong_target",
  "rating": 2,
  "comment": "Nội dung này phù hợp legal hơn là engineering"
}
```

#### Response mẫu
```json
{
  "message": "Feedback saved successfully"
}
```

### 7.5 POST /api/v1/chat/query
#### Request body mẫu
```json
{
  "question": "Tuần này có gì ảnh hưởng team engineering?",
  "filters": {
    "department": "Engineering",
    "from_date": "2026-04-15",
    "to_date": "2026-04-22"
  }
}
```

#### Response mẫu
```json
{
  "answer": "Trong 7 ngày gần đây có 3 thay đổi đáng chú ý ảnh hưởng Engineering...",
  "cited_insights": [
    {"id": "uuid1", "title": "..."},
    {"id": "uuid2", "title": "..."}
  ],
  "sources": [
    {"title": "...", "url": "..."}
  ],
  "confidence_note": "Dựa trên 3 insight đã được xử lý và 5 nguồn liên quan"
}
```

---

## 8. Mapping UI với API
- Dashboard overview -> GET /dashboard/overview, GET /insights?filters...
- Insight detail -> GET /insights/{id}, POST /insights/{id}/feedback
- Source management -> GET/POST/PUT /sources, POST /sources/{id}/test, POST /sources/{id}/toggle
- Delivery rules -> GET/POST/PUT /delivery-rules
- Chatbot -> POST /chat/query

---

## 9. Dashboard metrics chi tiết

### 9.1 Business dashboard metrics
- total_insights_current_period
- high_impact_insights_count
- critical_alerts_count
- compliance_alerts_count
- unique_active_sources_count
- average_user_feedback_rating

### 9.2 Operations dashboard metrics
- ingest_jobs_success_rate
- processing_jobs_success_rate
- delivery_success_rate
- failed_connectors_count
- queue_backlog_size
- average_chat_response_time

---

## 10. Định nghĩa trạng thái chính

### 10.1 Insight status
- new
- reviewed
- watch
- archived

### 10.2 Job status
- queued
- running
- success
- failed
- partial_success

### 10.3 Source status
- draft
- active
- inactive
- error

### 10.4 Delivery status
- pending
- sent
- failed
- skipped

