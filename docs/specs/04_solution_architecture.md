# 04. SOLUTION ARCHITECTURE — AI IMPACT RADAR

## 1. Kiến trúc hệ thống tổng thể

### 1.1 Kiến trúc logic
Hệ thống gồm 7 lớp chính:
1. Source Connector Layer
2. Ingestion & Normalization Layer
3. Knowledge & Storage Layer
4. AI Analysis Layer
5. Business Rules & Scoring Layer
6. Delivery & Experience Layer
7. Governance & Operations Layer

### 1.2 Mô tả từng lớp
#### 1. Source Connector Layer
Chức năng:
- Kết nối nguồn web, RSS, API, GitHub, nguồn pháp lý, nguồn nội bộ
- Quản lý lịch lấy dữ liệu
- Ghi log crawl

#### 2. Ingestion & Normalization Layer
Chức năng:
- Clean text/HTML
- Chuẩn hóa metadata
- Language detection
- Dedup fingerprint
- Chunking nếu cần cho chatbot/search

#### 3. Knowledge & Storage Layer
Chức năng:
- Lưu raw documents
- Lưu metadata
- Lưu curated insights
- Lưu taxonomy, rule, feedback
- Lưu vector index cho search/chatbot nếu áp dụng

#### 4. AI Analysis Layer
Chức năng:
- Classifier
- Summarizer
- Impact analyzer
- Role-based summarizer
- Event clustering

#### 5. Business Rules & Scoring Layer
Chức năng:
- Trust score
- Impact score
- Department mapping
- Priority/routing rule
- Approval rule

#### 6. Delivery & Experience Layer
Chức năng:
- Web dashboard
- Insight detail page
- Teams/Email digest
- Chatbot
- Admin console

#### 7. Governance & Operations Layer
Chức năng:
- Auth, RBAC
- Audit log
- Job monitoring
- Error handling
- Metrics and health check

---

## 2. Kiến trúc triển khai đề xuất

### 2.1 Thành phần vật lý chính
- Frontend Web App
- Backend API Service
- Ingestion Worker / Scheduler
- AI Processing Worker
- Database quan hệ
- Object storage/raw storage
- Vector database hoặc search index (phase 2)
- Queue/job broker
- Notification service
- Monitoring/logging stack

### 2.2 Gợi ý công nghệ
#### Frontend
- React / Next.js
- UI library phù hợp doanh nghiệp

#### Backend
- Python FastAPI hoặc Node.js NestJS
- REST API

#### Processing
- Python workers
- n8n cho một số luồng tự động hóa đơn giản

#### Database
- PostgreSQL cho dữ liệu nghiệp vụ và cấu hình
- Object storage cho raw content
- Redis/Queue cho job queue
- Vector DB hoặc pgvector/OpenSearch phase 2

#### Integration
- Microsoft Teams webhook/bot
- SMTP/Email service
- GitHub API
- RSS/Web parser/API connectors

#### Monitoring
- Logging tập trung
- Dashboard sức khỏe pipeline

---

## 3. Các module hệ thống

### M1. Source Management Module
Quản trị nguồn, lịch crawl, trust tier, tag chủ đề

### M2. Ingestion Module
Kéo dữ liệu, parse dữ liệu, lưu raw, ghi log

### M3. Normalization Module
Chuẩn hóa nội dung, metadata, dedup

### M4. Analysis Module
Classify, summarize, impact scoring, trust scoring, event clustering

### M5. Insight Repository Module
Lưu insight curated, mapping với source, tags, score

### M6. Dashboard Module
Danh sách insight, filter, detail, executive view

### M7. Delivery Module
Email digest, Teams alert, routing rules

### M8. Chatbot/Search Module
Semantic search, retrieval, grounded Q&A

### M9. Feedback Module
Lưu feedback, stats đánh giá, cải thiện relevance

### M10. Admin & Governance Module
RBAC, audit, taxonomy, settings, observability

---

## 4. Data Flow chính

### 4.1 Flow ingest đến insight
1. Scheduler kích hoạt job theo lịch
2. Connector lấy dữ liệu từ nguồn
3. Dữ liệu raw được lưu và ghi metadata ban đầu
4. Normalizer làm sạch, chuẩn hóa, chống trùng
5. Analysis module phân loại và tóm tắt
6. Rule engine chấm trust/impact/priority
7. Insight được lưu vào curated repository
8. Delivery engine xét rule để gửi digest/alert
9. Dashboard và chatbot truy cập insight repository

### 4.2 Flow chatbot
1. User nhập câu hỏi
2. Hệ thống kiểm tra quyền và bối cảnh
3. Search/retrieval lấy insight/source phù hợp
4. LLM tạo câu trả lời grounded
5. Trả lời kèm nguồn và mốc thời gian
6. Người dùng phản hồi chất lượng trả lời

### 4.3 Flow feedback learning
1. User đánh giá insight
2. Hệ thống lưu feedback
3. Module analytics tổng hợp feedback
4. Admin hoặc rule engine điều chỉnh trọng số/rule

---

## 5. Logic scoring đề xuất

### 5.1 Trust score sơ bộ
Điểm trust có thể tính từ:
- Tier nguồn mặc định
- Tính chính thức của domain
- Có xác minh chéo hay không
- Số nguồn độc lập xác nhận
- Độ mới của thông tin
- Có phải nguồn chỉ là opinion/community hay không

Ví dụ nhãn:
- 90-100: Official / Very High
- 75-89: High
- 55-74: Medium
- 35-54: Low
- <35: Unverified

### 5.2 Impact score sơ bộ
Điểm impact có thể tính từ:
- Chủ đề và loại sự kiện
- Số phòng ban bị ảnh hưởng
- Có liên quan compliance/security không
- Có liên quan tool/quy trình công ty đang dùng không
- Tính khẩn cấp theo deadline/regulation/deprecation

Ví dụ nhãn:
- 85-100: Critical
- 70-84: High
- 45-69: Medium
- 20-44: Low
- <20: Watch

---

## 6. Rule phân phối đề xuất

### 6.1 Nguyên tắc
- Không spam
- Đúng người, đúng lúc, đúng mức độ
- Digest cho tin thường, alert cho tin critical/high theo rule

### 6.2 Rule ví dụ
- Insight loại Security + Impact >= High => gửi Teams alert cho Engineering lead
- Insight loại Legal/Compliance + Impact >= Medium => gửi digest ngày cho Legal + Management
- Insight AI trend + Opportunity >= Medium => vào digest tuần cho Data/AI và Management
- Insight Content/SEO => gửi digest tuần cho Content/Marketing

---

## 7. Vai trò và trách nhiệm

| Vai trò | Trách nhiệm chính |
|---|---|
| Sponsor | phê duyệt mục tiêu, phạm vi, nguồn lực |
| Business Owner | xác nhận yêu cầu nghiệp vụ, UAT |
| BA/PM | khảo sát, đặc tả, điều phối |
| Solution Architect | kiến trúc, module, API, DB |
| UI/UX | wireframe, prototype |
| Dev FE | giao diện |
| Dev BE | API, xử lý nghiệp vụ |
| Data/AI | pipeline dữ liệu, AI analysis |
| QA/Tester | test case, test report |
| DevOps/Deploy | triển khai, cấu hình, monitoring |
| Admin/Vận hành | tiếp nhận sau go-live |

---

## 8. Role & Permission Matrix

### 8.1 Admin
- Toàn quyền quản trị nguồn
- Toàn quyền quản trị taxonomy
- Toàn quyền rule phân phối
- Xem log và health system
- Xem tất cả insight

### 8.2 Executive
- Xem executive dashboard
- Xem insight và report được phân quyền
- Không quản trị nguồn

### 8.3 Manager
- Xem dashboard team
- Xem insight liên quan team
- Nhận digest
- Gửi feedback

### 8.4 Specialist User
- Xem insight trong phạm vi được cấp
- Dùng chatbot
- Gửi feedback

### 8.5 Analyst
- Xem dashboard chuyên sâu
- Xem cluster/source chi tiết
- Không sửa nguồn nếu không có quyền admin

### 8.6 Ops/DevOps
- Xem job logs, metrics, health
- Không sửa nội dung insight nếu không có quyền bổ sung

---

## 9. Cổng duyệt giữa các giai đoạn

### Gate 1: Chốt yêu cầu
Chỉ qua Gate 1 khi có:
- biên bản khảo sát
- phạm vi MVP
- stakeholder
- pain point
- KPI

### Gate 2: Chốt đặc tả
Chỉ qua Gate 2 khi có:
- use case
- FR/NFR
- acceptance criteria
- data input/output sơ bộ

### Gate 3: Chốt thiết kế
Chỉ qua Gate 3 khi có:
- architecture
- API draft
- DB schema
- wireframe
- task breakdown

### Gate 4: Chốt release candidate
Chỉ qua Gate 4 khi có:
- build ổn định
- test report
- bug critical = 0 hoặc đã chấp thuận
- UAT đạt

### Gate 5: Chốt go-live và bàn giao
Chỉ qua Gate 5 khi có:
- deploy checklist
- tài liệu vận hành
- tài liệu người dùng
- nơi lưu repo/tài liệu/version
- đầu mối hỗ trợ

---

## 10. Rủi ro chính và biện pháp

### R1. Quá rộng phạm vi
Biện pháp: giới hạn nguồn và domain trong phase 1

### R2. Nhiễu từ nguồn cộng đồng
Biện pháp: tách tier, không broadcast rộng nếu chưa xác minh

### R3. AI summary sai ngữ cảnh
Biện pháp: luôn kèm source trace, feedback loop, approval rule cho critical insights

### R4. Khó map đúng phòng ban bị ảnh hưởng
Biện pháp: kết hợp taxonomy + rule + feedback người dùng

### R5. Spam alert
Biện pháp: delivery rule chặt, ưu tiên digest, rate limit alert

### R6. Thiếu owner sau bàn giao
Biện pháp: xác định rõ admin, ops, business owner từ đầu

