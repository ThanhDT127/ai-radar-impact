# 06. IMPLEMENTATION BACKLOG & ROADMAP — AI IMPACT RADAR

## 1. Backlog implementation theo Epic

### Mục tiêu
Chuyển tài liệu thiết kế thành cấu trúc triển khai thực tế cho đội dự án, giúp:
- phân rã công việc rõ ràng
- dễ chia sprint/phase
- xác định dependency
- xác định ưu tiên
- xác định Definition of Done

Nguyên tắc backlog:
- Epic = nhóm giá trị lớn
- Feature = khối chức năng cấp trung
- User Story = nhu cầu người dùng hoặc hành vi hệ thống
- Task = đầu việc kỹ thuật có thể giao thực hiện
- Mỗi item có priority, dependency, deliverable, acceptance

---

## 2. Danh sách Epic tổng thể
- E01. Foundation & Project Setup
- E02. Authentication, Authorization & User Management
- E03. Source Management
- E04. Ingestion Pipeline
- E05. Normalization & Deduplication
- E06. AI Analysis & Insight Generation
- E07. Scoring & Business Rules
- E08. Insight Repository & Search
- E09. Dashboard & Insight UI
- E10. Delivery & Notification
- E11. Feedback & Quality Loop
- E12. Chatbot & Retrieval
- E13. Admin Operations & Monitoring
- E14. Action Workflow & External Integrations
- E15. Reporting & Executive Pack
- E16. QA, UAT, Release & Handover

---

## 3. Phase mapping theo Epic

### Phase 1
- E01, E02, E03, E04, E05, E06, E07, E08, E09, E10, E11, E13, E16

### Phase 2
- E06 nâng cao, E07 nâng cao, E08 nâng cao, E09 mở rộng, E12, E13 nâng cao, E16

### Phase 3
- E14, E15, E07 mở rộng, E09 executive reporting nâng cao, E16

---

## 4. Epic chi tiết

### E01. Foundation & Project Setup
**Feature E01-F01: Repository & Branch Strategy**
Tasks:
- Tạo repository frontend
- Tạo repository backend hoặc monorepo theo quyết định kiến trúc
- Thiết lập branch strategy: main/develop/feature/hotfix
- Thiết lập PR template
- Thiết lập code review checklist
- Thiết lập README dự án
- Thiết lập convention commit message
DoD:
- Repo tạo xong
- Branch strategy được mô tả
- Team có thể clone và chạy skeleton app

**Feature E01-F02: Environment Setup**
Tasks:
- Thiết lập dev environment template
- Thiết lập env config structure
- Thiết lập local DB
- Thiết lập queue/cache local
- Thiết lập docker-compose local nếu dùng
DoD:
- Chạy được app frontend/backend local
- DB và queue local hoạt động

**Feature E01-F03: CI baseline**
Tasks:
- Thiết lập CI chạy lint
- Thiết lập CI chạy unit test cơ bản
- Thiết lập build check
DoD:
- PR chạy CI tự động
- Thất bại khi lint/test lỗi

### E02. Authentication, Authorization & User Management
**Feature E02-F01: Authentication**
Stories:
- Là user, tôi muốn đăng nhập hệ thống an toàn.
- Là admin, tôi muốn giới hạn người được truy cập.
Tasks:
- Chọn phương án auth: local auth hoặc SSO
- Thiết kế user session/token flow
- Xây API login/logout/refresh token
- Xây UI login
- Xử lý session timeout
DoD:
- User đăng nhập được
- API xác thực hoạt động
- Session được kiểm soát

**Feature E02-F02: RBAC**
Tasks:
- Thiết kế role model
- Tạo bảng users, roles, user_roles
- Middleware kiểm tra quyền
- Phân quyền route frontend
- Phân quyền API admin/user
DoD:
- Admin vào được khu admin
- User thường không truy cập được admin API

### E03. Source Management
**Feature E03-F01: Source CRUD API**
Tasks:
- Thiết kế schema sources
- Xây GET /sources
- Xây POST /sources
- Xây PUT /sources/{id}
- Xây toggle source status
- Xây validation nguồn
- Xây audit log khi sửa nguồn
DoD:
- CRUD nguồn hoạt động
- Có validation và audit log

**Feature E03-F02: Source Management UI**
Tasks:
- Xây danh sách nguồn
- Xây form thêm/sửa nguồn
- Hiển thị trạng thái nguồn
- Filter theo loại nguồn/trạng thái
DoD:
- Admin quản trị được nguồn từ UI

**Feature E03-F03: Test ingest preview**
Tasks:
- API test ingest
- Preview dữ liệu lấy mẫu
- UI hiển thị kết quả test
DoD:
- Admin test được trước khi activate nguồn

### E04. Ingestion Pipeline
**Feature E04-F01: Scheduler**
Tasks:
- Thiết lập scheduler framework
- Đọc schedule từ sources
- Trigger ingest jobs
- Ghi job logs
DoD:
- Job chạy theo lịch
- Có log trạng thái job

**Feature E04-F02: RSS Connector**
Tasks:
- Xây connector RSS
- Parse item feed
- Map item vào raw document schema
- Handle duplicate feed item cơ bản

**Feature E04-F03: Web Connector**
Tasks:
- Xây connector web scraping/parsing đơn giản
- Tải HTML
- Parse title/body/url/date cơ bản
- Xử lý lỗi kết nối

**Feature E04-F04: GitHub Release Connector**
Tasks:
- Kết nối GitHub releases/changelog
- Parse metadata release
- Lưu raw document

**Feature E04-F05: Legal/Gov Connector mẫu**
Tasks:
- Chọn 1-2 nguồn pháp lý/government mẫu
- Viết parser phù hợp
- Test ingest ổn định

**Feature E04-F06: Raw storage & job log**
Tasks:
- Tạo bảng raw_documents
- Tạo bảng job_logs
- Lưu raw content và metadata
- Ghi lỗi ingest
DoD cho Epic E04:
- Hệ thống ingest được từ ít nhất 3 loại nguồn
- Có job log
- Có raw document được lưu

### E05. Normalization & Deduplication
**Feature E05-F01: Content cleaning**
Tasks:
- Strip HTML
- Loại bỏ block nhiễu thường gặp
- Chuẩn hóa whitespace
- Chuẩn hóa encoding

**Feature E05-F02: Metadata extraction**
Tasks:
- Parse title
- Parse author
- Parse publish date
- Parse source domain
- Detect language

**Feature E05-F03: Deduplication v1**
Tasks:
- Tạo fingerprint
- So khớp duplicate exact match
- So khớp near-duplicate rule-based sơ bộ
- Đánh dấu duplicate group

**Feature E05-F04: Normalized storage**
Tasks:
- Tạo bảng normalized_documents
- Lưu tài liệu đã chuẩn hóa
- Gắn trạng thái normalized_status
DoD:
- Tài liệu ingest xong được chuẩn hóa
- Có dedup basic
- Dữ liệu sạch đủ cho analysis

### E06. AI Analysis & Insight Generation
**Feature E06-F01: Topic classification v1**
Tasks:
- Thiết kế taxonomy v1
- Viết classifier pipeline
- Mapping tài liệu -> topic
- Logging kết quả classify

**Feature E06-F02: Event type classification v1**
Tasks:
- Thiết kế event type set
- Classify release/policy/regulation/security/trend/deprecation

**Feature E06-F03: Summary generation v1**
Tasks:
- Sinh summary short
- Sinh summary medium
- Xác định prompt/logic an toàn bám nguồn
- Lưu summary vào insight

**Feature E06-F04: Insight creation**
Tasks:
- Thiết kế bảng insights
- Logic tạo insight từ normalized document
- Gắn link nguồn ban đầu
- Tránh tạo insight rác khi document không đạt tiêu chí

**Feature E06-F05: Role-based summary v2**
- Phase 2
Tasks:
- Summary cho manager/dev/legal
- Đánh giá chênh lệch tone và nội dung theo role

**Feature E06-F06: Event clustering v2**
- Phase 2
Tasks:
- Gộp nhiều normalized document vào event cluster
- Sinh canonical insight
DoD phase 1:
- Mỗi insight có topic, event type, summary, source link

### E07. Scoring & Business Rules
**Feature E07-F01: Trust score v1**
Tasks:
- Xác định công thức rule-based trust v1
- Tạo trust tier mapping
- Gắn trust label cho insight

**Feature E07-F02: Impact score v1**
Tasks:
- Xác định rule impact theo topic/event/department
- Mapping department ảnh hưởng
- Tạo impact label

**Feature E07-F03: Recommendation v1**
Tasks:
- Tạo rule action suggestion cơ bản
- Sinh recommendation text từ template/rule

**Feature E07-F04: Delivery rule engine v1**
Tasks:
- Match insight với delivery rules
- Quyết định digest/alert

**Feature E07-F05: Scoring v2 nâng cao**
- Phase 2+
Tasks:
- Kết hợp feedback, source corroboration, cluster confidence
DoD phase 1:
- Insight có trust_label, impact_label, department mapping, recommendation sơ bộ

### E08. Insight Repository & Search
**Feature E08-F01: Insight persistence**
Tasks:
- Tạo schema insights, insight_source_links, insight_departments
- API get insight list/detail

**Feature E08-F02: Filter & query support**
Tasks:
- Filter theo topic
- Filter theo impact
- Filter theo trust
- Filter theo department
- Filter theo thời gian
- Sort newest/impact/trust

**Feature E08-F03: Search v1**
Tasks:
- Search keyword theo title/summary
- Full-text search cơ bản

**Feature E08-F04: Search/Vector index v2**
- Phase 2
Tasks:
- Tạo vector index hoặc semantic search
- Đồng bộ insight/source vào search index
DoD:
- Dashboard và detail page đọc dữ liệu insight ổn định
- Search cơ bản dùng được ở phase 1

### E09. Dashboard & Insight UI
**Feature E09-F01: Layout & navigation**
Tasks:
- Xây app shell
- Sidebar
- Header filters
- User menu

**Feature E09-F02: Dashboard overview**
Tasks:
- KPI cards
- Top risks block
- Top opportunities block
- Compliance alerts block
- Insight feed block

**Feature E09-F03: Insight list page**
Tasks:
- Table/card list
- Filter panel
- Sort options
- Pagination

**Feature E09-F04: Insight detail page**
Tasks:
- Header badges
- Summary block
- Impact/recommendation block
- Source block
- Timeline block
- Feedback block

**Feature E09-F05: Executive dashboard**
- Phase 1 basic, phase 3 nâng cao
Tasks:
- Executive summary block
- Department heat summary
- Strategic risk block

**Feature E09-F06: Team dashboard**
Tasks:
- Team filter default
- High impact view for team
- What needs attention block

**Feature E09-F07: Chatbot UI**
- Phase 2
Tasks:
- Chat window
- History list
- Related sources panel
DoD phase 1:
- User đăng nhập xong xem được dashboard, insight list, insight detail, basic executive/team views

### E10. Delivery & Notification
**Feature E10-F01: Delivery rule CRUD**
Tasks:
- Schema delivery_rules
- API CRUD rules
- UI rule management cơ bản

**Feature E10-F02: Digest builder**
Tasks:
- Chọn insight theo rule và lịch
- Tạo nội dung digest
- Render template email/Teams

**Feature E10-F03: Email delivery**
Tasks:
- Tích hợp email service
- Gửi digest
- Lưu log gửi

**Feature E10-F04: Teams delivery**
Tasks:
- Tích hợp Teams webhook/bot
- Gửi digest/alert
- Lưu log gửi

**Feature E10-F05: Realtime alert logic**
Tasks:
- Trigger alert khi impact và rule phù hợp
- Chống spam bằng limit/rule
DoD phase 1:
- Gửi được email digest và Teams digest theo rule
- Có log gửi thành công/thất bại

### E11. Feedback & Quality Loop
**Feature E11-F01: Insight feedback**
Tasks:
- API gửi feedback
- UI nút Useful/Not useful
- UI chọn reason code
- Lưu feedback DB

**Feature E11-F02: Feedback summary**
Tasks:
- Tổng hợp feedback theo insight
- Tổng hợp feedback theo topic/department
- Báo cáo feedback cơ bản cho admin

**Feature E11-F03: Quality analytics v2**
- Phase 2
Tasks:
- Dashboard chất lượng insight
- Tỷ lệ useful theo nguồn/topic/rule
DoD phase 1:
- User phản hồi được
- Admin xem được số liệu phản hồi cơ bản

### E12. Chatbot & Retrieval
- Phase 2
**Feature E12-F01: Retrieval service**
Tasks:
- Truy xuất insight liên quan theo filter và semantic/keyword
- Gộp source context

**Feature E12-F02: Chat API**
Tasks:
- POST /chat/query
- Xác thực user
- Gọi retrieval
- Tạo grounded answer
- Trả cited insights/sources

**Feature E12-F03: Chat UI**
Tasks:
- Giao diện chat
- Suggested questions
- Nút feedback answer

**Feature E12-F04: Chat history**
Tasks:
- Lưu query log
- Hiển thị history cơ bản
DoD:
- User hỏi được câu hỏi theo topic/department/time
- Trả lời có cited sources

### E13. Admin Operations & Monitoring
**Feature E13-F01: Job monitoring**
Tasks:
- API jobs list
- UI health/jobs screen
- Thống kê success/failure

**Feature E13-F02: System health**
Tasks:
- Health endpoint
- Check DB/queue/service status
- UI hiển thị health summary

**Feature E13-F03: Audit log viewer**
Tasks:
- API lấy audit logs
- UI bảng audit logs cơ bản

**Feature E13-F04: Delivery monitoring**
Tasks:
- Tổng hợp log delivery
- Lọc failed deliveries
DoD:
- Admin nhìn được tình trạng ingest/process/delivery
- Có health summary cho vận hành

### E14. Action Workflow & External Integrations
- Phase 3
**Feature E14-F01: Create task from insight**
Tasks:
- Nút create task trên insight detail
- Mapping dữ liệu sang task payload
- Tích hợp Jira/Planner/Asana tùy chọn

**Feature E14-F02: Follow-up workflow**
Tasks:
- Trạng thái follow-up
- Assigned owner
- Due date

**Feature E14-F03: SOP impact suggestion**
Tasks:
- Mapping insight -> internal document/process
- Gợi ý review SOP/policy

### E15. Reporting & Executive Pack
- Phase 3
**Feature E15-F01: Executive weekly report**
Tasks:
- Tổng hợp top risks/opportunities
- Tạo executive summary
- Render PDF/slide output

**Feature E15-F02: Trend reporting**
Tasks:
- Báo cáo chủ đề tăng mạnh
- Báo cáo nguồn nổi bật
- Báo cáo department impact trend

### E16. QA, UAT, Release & Handover
**Feature E16-F01: Test planning**
Tasks:
- Viết test cases theo module
- Viết UAT scenarios
- Chuẩn bị dữ liệu test

**Feature E16-F02: Automated testing baseline**
Tasks:
- Unit test backend
- Component/UI test frontend cơ bản
- API test smoke

**Feature E16-F03: UAT execution**
Tasks:
- Chạy UAT với business owner
- Ghi nhận defects
- Chốt pass/fail

**Feature E16-F04: Release checklist**
Tasks:
- Checklist deploy
- Checklist rollback
- Checklist config production

**Feature E16-F05: Handover package**
Tasks:
- Repo handover
- Architecture doc handover
- Admin guide
- User guide
- Operations guide
DoD:
- Có test report
- Có UAT sign-off hoặc tương đương
- Có handover package đầy đủ

---

## 5. Ưu tiên triển khai theo MoSCoW

### Must Have (Phase 1)
- E01, E02 cơ bản
- E03 source CRUD
- E04 ingest RSS/Web/GitHub mẫu
- E05 normalize + dedup basic
- E06 classify + summary + insight creation
- E07 trust/impact/recommendation basic
- E08 insight query/list/detail
- E09 dashboard + detail + basic team view
- E10 email/Teams digest
- E11 feedback basic
- E13 jobs/health basic
- E16 test + handover cơ bản

### Should Have
- Executive dashboard nâng cao
- Search tốt hơn
- Feedback analytics
- Test ingest preview đẹp hơn

### Could Have
- Multi-language role summaries nâng cao
- Advanced source simulation
- Rich trend analytics

### Won’t Have in phase 1
- Task integration sâu
- SOP impact automation
- Full chatbot with memory and advanced retrieval
- PDF/slide executive auto pack hoàn chỉnh

---

## 6. Dependency map chính
- E01 là nền cho toàn bộ epic khác
- E02 cần trước E09, E10, E12, E13 admin
- E03 -> E04 -> E05 -> E06 -> E07 -> E08 -> E09/E10/E12
- E07 + E08 cần trước E10
- E08 search/index cần trước E12
- E06/E07 chất lượng đủ tốt trước E12
- E08 + E09 + E10 + E11 cần trưởng thành trước E14/E15

---

## 7. Sprint gợi ý cho Phase 1

### Sprint 0 - Setup
- E01 foundation
- E02 auth skeleton
- DB schema draft
- Architecture lock

### Sprint 1 - Source + Ingest
- E03 source management API/UI
- E04 scheduler + RSS connector + raw storage
- E13 job log basic

### Sprint 2 - Normalize + Insight
- E05 normalize/dedup basic
- E06 classify/summary/insight creation
- E07 trust/impact rule v1

### Sprint 3 - Dashboard + Detail
- E08 insights API
- E09 dashboard overview/list/detail
- E11 feedback basic

### Sprint 4 - Delivery + Admin Ops
- E10 email/Teams digest
- E13 health/jobs UI
- UAT round 1

### Sprint 5 - Stabilize & Go-live
- Fix bug
- Improve scoring/routing
- UAT round 2
- Release/handover

---

## 8. Backlog theo đội

### Backend
- Auth API
- Source CRUD API
- Ingest scheduler
- RSS/Web/GitHub connectors
- Raw storage
- Normalize pipeline
- Dedup rules
- Classify service
- Summary service
- Trust/impact scoring service
- Insight APIs
- Delivery rule API
- Email/Teams send service
- Feedback API
- Jobs/health API

### Frontend
- Login page
- App shell
- Dashboard overview
- Insight list page
- Insight detail page
- Source management page
- Delivery rules page cơ bản
- Jobs/health page
- Feedback UI

### Data/AI
- Taxonomy v1
- Prompt/pipeline cho classify
- Prompt/pipeline cho summary
- Rule impact mapping v1
- Trust scoring factors v1
- Quality evaluation sample set

### QA
- Test plan
- Test cases source/ingest/insight/dashboard/delivery
- Regression checklist
- UAT support

### DevOps
- Dev/test/prod env
- CI baseline
- Secret/env management
- Logging/health check setup
- Deploy script/checklist

---

## 9. Definition of Done tổng quát
Một feature được coi là hoàn thành khi:
1. Code đã được review và merge
2. Unit test hoặc test phù hợp đã chạy đạt
3. API hoặc UI đáp ứng acceptance criteria
4. Logging lỗi cơ bản đã có nếu là backend/process
5. Tài liệu cấu hình hoặc note kỹ thuật đã cập nhật
6. QA xác nhận pass ở môi trường test
7. Nếu là business-facing feature thì đã có UAT hoặc review tương đương

---

## 10. Rủi ro triển khai theo backlog
- Scope creep -> chốt Must Have phase 1
- Chất lượng source parser không ổn định -> ưu tiên RSS/API/official sources trước
- Output AI chưa đủ tốt -> dùng rule + AI kết hợp, làm bộ sample evaluation sớm
- Digest spam hoặc kém hữu ích -> rule chặt, feedback loop từ phase 1
- Admin UI quá tải -> phase 1 chỉ build source + rule + jobs cơ bản

---

## 11. Cách chuyển backlog sang công cụ quản lý công việc
### Epic
- E01 Foundation
- E02 Auth
- ...

### Story
- Theo từng feature hoặc user story

### Task/Sub-task
- API
- DB
- UI
- Test
- Docs

### Label
- backend
- frontend
- ai
- qa
- devops
- phase1
- phase2
- critical

### Priority
- P0
- P1
- P2
- P3

