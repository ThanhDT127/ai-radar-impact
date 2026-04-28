# 02. FRD & REQUIREMENTS — AI IMPACT RADAR

## 1. Phân kỳ triển khai theo phase

### Phase 1 - MVP
Mục tiêu:
- thu thập từ nguồn chọn lọc
- chuẩn hóa và phân loại cơ bản
- tóm tắt insight
- phân tích tác động theo phòng ban ở mức rule + AI
- dashboard cơ bản
- email/Teams digest

Nguồn dữ liệu phase 1:
- Website chính thức của vendor công nghệ
- Blog kỹ thuật chính thức
- GitHub release/changelog của repo trọng yếu
- Website chính phủ / văn bản pháp lý / cơ quan quản lý
- Một số nguồn chuyên môn uy tín

Đối tượng sử dụng phase 1:
- Lãnh đạo/Quản lý
- Dev/Tech Lead
- Data/AI
- Legal/Compliance

### Phase 2 - Analytics & Copilot
- chatbot hỏi đáp theo dữ liệu đã xử lý
- chấm điểm độ tin cậy nâng cao
- dedup và event clustering nâng cao
- personalization theo vai trò
- theo dõi xu hướng ngắn hạn

### Phase 3 - Action Workflow & Integration
- action recommendation nâng cao
- task integration
- SOP/policy impact suggestion
- executive reporting tự động
- internal knowledge mapping
- approval workflow cho insight critical

---

## 2. Functional Requirements (FR)

### Nhóm A - Quản trị nguồn
**FR-01** Hệ thống cho phép quản trị danh sách nguồn dữ liệu.
**FR-02** Mỗi nguồn có các thuộc tính: tên, loại nguồn, URL/API, chủ đề, tier tin cậy mặc định, tần suất crawl, trạng thái.
**FR-03** Admin có thể bật/tắt nguồn.
**FR-04** Hệ thống ghi nhận lịch sử thay đổi cấu hình nguồn.

### Nhóm B - Thu thập dữ liệu
**FR-05** Hệ thống cho phép lấy dữ liệu từ web/RSS/API/GitHub releases/tài liệu pháp lý.
**FR-06** Hệ thống lưu raw content, metadata, thời điểm thu thập.
**FR-07** Hệ thống ghi log trạng thái ingest thành công/thất bại.
**FR-08** Hệ thống có cơ chế retry cho nguồn lỗi tạm thời.

### Nhóm C - Chuẩn hóa và phân tích
**FR-09** Hệ thống chuẩn hóa text, loại bỏ nhiễu.
**FR-10** Hệ thống nhận diện ngôn ngữ.
**FR-11** Hệ thống trích xuất metadata cơ bản.
**FR-12** Hệ thống phát hiện trùng lặp.
**FR-13** Hệ thống phân loại theo chủ đề.
**FR-14** Hệ thống phân loại theo loại sự kiện.
**FR-15** Hệ thống gắn mức độ tin cậy.
**FR-16** Hệ thống gắn phòng ban/role bị ảnh hưởng.
**FR-17** Hệ thống gắn mức độ ảnh hưởng.
**FR-18** Hệ thống gắn tính chất: risk/opportunity/compliance/watchlist.

### Nhóm D - Insight
**FR-19** Hệ thống tạo insight từ một hoặc nhiều nguồn.
**FR-20** Insight phải có summary ngắn, summary chi tiết, nguồn gốc.
**FR-21** Insight có thể có nguồn xác minh chéo.
**FR-22** Insight có thể có recommended action.
**FR-23** Insight có thể có tag department, role, priority.

### Nhóm E - Dashboard & Search
**FR-24** Dashboard tổng quan hiển thị top insight theo thời gian.
**FR-25** Cho phép lọc theo thời gian, chủ đề, nguồn, độ tin cậy, team, impact.
**FR-26** Có trang chi tiết insight.
**FR-27** Có mục top risks, top opportunities, compliance alerts.
**FR-28** Có mục xu hướng theo thời gian ở phase 2 trở lên.

### Nhóm F - Delivery
**FR-29** Hệ thống gửi email digest theo lịch.
**FR-30** Hệ thống gửi Teams digest/alert theo rule.
**FR-31** Hệ thống hỗ trợ rule phân phối theo nhóm người dùng.
**FR-32** Chỉ gửi alert realtime cho insight có mức độ phù hợp theo cấu hình.

### Nhóm G - Chatbot
**FR-33** Người dùng có thể hỏi chatbot về insight đã xử lý.
**FR-34** Chatbot trả lời kèm trích nguồn.
**FR-35** Chatbot có thể lọc theo khoảng thời gian và phòng ban.
**FR-36** Chatbot không trả lời ngoài phạm vi dữ liệu được cấp quyền nếu cấu hình hạn chế.

### Nhóm H - Feedback & Learning
**FR-37** Người dùng có thể đánh giá insight.
**FR-38** Người dùng có thể báo insight sai đối tượng, sai mức độ, trùng, không hữu ích.
**FR-39** Hệ thống lưu feedback để cải thiện ranking/scoring/rule.

### Nhóm I - Quản trị & phân quyền
**FR-40** Hệ thống có phân quyền theo vai trò.
**FR-41** Chỉ admin mới được quản trị nguồn và rule.
**FR-42** Hệ thống log các thao tác quản trị chính.
**FR-43** Hệ thống cho phép cấu hình từ điển chủ đề, department mapping, trust tier.

---

## 3. Non-functional Requirements (NFR)

### 3.1 Bảo mật
**NFR-01** Hệ thống phải có cơ chế xác thực người dùng.
**NFR-02** Hệ thống phải phân quyền theo vai trò.
**NFR-03** Cấu hình nguồn, rule, admin action phải có audit log.
**NFR-04** Dữ liệu nội bộ và dữ liệu nhạy cảm phải được kiểm soát truy cập.

### 3.2 Truy vết và minh bạch
**NFR-05** Mọi insight phải có ít nhất một nguồn gốc truy vết được.
**NFR-06** Insight tổng hợp từ nhiều nguồn phải thể hiện danh sách nguồn liên quan.
**NFR-07** Hệ thống phải phân biệt rõ nội dung nguồn, nội dung AI summary và nhận định nội suy.

### 3.3 Hiệu năng
**NFR-08** Dashboard tổng quan phải phản hồi trong ngưỡng chấp nhận được với dữ liệu ở quy mô MVP.
**NFR-09** Pipeline ingest/process phải hỗ trợ chạy theo lịch định kỳ.
**NFR-10** Chatbot phải có cache hoặc chiến lược tối ưu truy vấn cho câu hỏi phổ biến.

### 3.4 Khả năng mở rộng
**NFR-11** Kiến trúc phải cho phép bổ sung nguồn mới mà không ảnh hưởng lớn đến module khác.
**NFR-12** Hệ thống phải cho phép thêm chủ đề, loại sự kiện, department mapping.
**NFR-13** Hệ thống phải hỗ trợ mở rộng kênh phân phối.

### 3.5 Vận hành
**NFR-14** Phải có logging cho ingest, processing, delivery, chatbot.
**NFR-15** Phải có monitoring trạng thái job và lỗi.
**NFR-16** Phải có backup dữ liệu cấu hình và dữ liệu đã xử lý theo chính sách triển khai.
**NFR-17** Phải có checklist deploy và rollback.

### 3.6 Chất lượng AI
**NFR-18** AI summary không được thay thế nguồn gốc.
**NFR-19** Các insight critical nên có rule xác minh chéo hoặc phê duyệt.
**NFR-20** Hệ thống phải cho phép đánh giá chất lượng output AI qua feedback người dùng.

---

## 4. FRD chi tiết theo module

### FR-01 Quản lý nguồn dữ liệu
**Mục tiêu**: Cho phép admin cấu hình và quản lý danh sách nguồn thu thập.
**Actor**: Admin
**Tiền điều kiện**: Người dùng đã đăng nhập với quyền admin
**Luồng chính**:
1. Admin mở màn hình Source Management
2. Admin tạo nguồn mới với các thông tin bắt buộc
3. Hệ thống kiểm tra tính hợp lệ của cấu hình
4. Hệ thống lưu nguồn
5. Hệ thống hiển thị nguồn ở trạng thái hoạt động hoặc nháp tùy cấu hình
**Dữ liệu bắt buộc**:
- Tên nguồn
- Loại nguồn
- URL/API endpoint
- Chủ đề chính
- Trust tier mặc định
- Tần suất crawl
- Trạng thái
**Ngoại lệ**:
- URL không hợp lệ
- Trùng nguồn
- Thiếu trường bắt buộc
**Acceptance criteria**:
- Admin tạo được nguồn mới
- Hệ thống lưu đầy đủ cấu hình
- Mỗi thay đổi nguồn có audit log
- Có thể bật/tắt nguồn mà không xóa lịch sử

### FR-02 Thu thập dữ liệu theo lịch
**Mục tiêu**: Hệ thống tự động lấy dữ liệu từ các nguồn đã cấu hình.
**Actor**: Scheduler / System
**Tiền điều kiện**:
- Nguồn ở trạng thái active
- Có lịch crawl hợp lệ
**Luồng chính**:
1. Scheduler kích hoạt job ingest
2. Connector gọi nguồn tương ứng
3. Hệ thống nhận dữ liệu và lưu raw document
4. Hệ thống ghi trạng thái job
**Ngoại lệ**:
- Timeout
- Nguồn từ chối truy cập
- Parse lỗi
**Acceptance criteria**:
- Job ingest tạo được raw document khi thành công
- Job lỗi phải có log và trạng thái lỗi
- Có retry cho lỗi tạm thời

### FR-03 Chuẩn hóa và chống trùng lặp
**Mục tiêu**: Làm sạch dữ liệu và loại bỏ tài liệu trùng hoặc gần trùng.
**Actor**: Processing Worker
**Luồng chính**:
1. Nhận raw document mới
2. Làm sạch nội dung
3. Chuẩn hóa metadata
4. Sinh fingerprint
5. Kiểm tra trùng lặp
6. Nếu trùng, đánh dấu liên kết; nếu không trùng, tạo normalized document
**Acceptance criteria**:
- Tài liệu sau xử lý có title, body, source, date nếu trích xuất được
- Tài liệu trùng không tạo insight rác lặp lại không cần thiết

### FR-04 Phân loại chủ đề và loại sự kiện
**Mục tiêu**: Gán taxonomy cho tài liệu/insight.
**Actor**: Analysis Engine
**Acceptance criteria**:
- Mỗi insight có ít nhất 1 chủ đề chính
- Mỗi insight có 1 loại sự kiện chính
- Hệ thống cho phép manual override về sau

### FR-05 Sinh insight và summary
**Mục tiêu**: Tạo insight dễ đọc từ một hoặc nhiều nguồn.
**Actor**: Analysis Engine
**Luồng chính**:
1. Nhận normalized document hoặc event cluster
2. Sinh summary ngắn
3. Sinh summary trung bình
4. Sinh summary theo role nếu có cấu hình
5. Lưu insight
**Acceptance criteria**:
- Insight có summary ngắn
- Insight có summary chi tiết
- Insight liên kết ít nhất một nguồn
- Summary không được mất ý nghĩa chính của nguồn

### FR-06 Chấm điểm độ tin cậy
**Mục tiêu**: Gắn trust score cho insight.
**Acceptance criteria**:
- Insight có trust score và trust label
- Trust score phải truy ngược được các yếu tố thành phần ở mức hệ thống nội bộ

### FR-07 Chấm điểm tác động
**Mục tiêu**: Xác định mức độ ảnh hưởng và nhóm bị ảnh hưởng.
**Acceptance criteria**:
- Mỗi insight có impact label
- Mỗi insight có danh sách department/role bị ảnh hưởng
- Có thể override bằng rule hoặc admin

### FR-08 Dashboard tổng quan
**Mục tiêu**: Hiển thị insight tổng quan cho người dùng.
**Actor**: User
**Acceptance criteria**:
- Người dùng xem được danh sách insight mới
- Có filter theo thời gian, chủ đề, impact, trust, team
- Click vào insight mở được trang chi tiết

### FR-09 Trang insight chi tiết
**Acceptance criteria**:
- Hiển thị được title, summary, source, trust, impact, department, action suggestion
- Nếu có nhiều nguồn thì hiển thị danh sách nguồn
- Hiển thị feedback form

### FR-10 Gửi digest qua Email/Teams
**Acceptance criteria**:
- Hệ thống gửi đúng nhóm theo rule
- Có log gửi thành công/thất bại
- Digest chứa title, summary ngắn, impact, source link

### FR-11 Chatbot grounded Q&A
**Acceptance criteria**:
- Câu trả lời có nguồn liên quan
- Có lọc theo thời gian/chủ đề nếu người dùng hỏi
- Không trả lời ngoài quyền truy cập của user nếu có RBAC cho dữ liệu

### FR-12 Feedback insight
**Acceptance criteria**:
- User gửi được phản hồi
- Hệ thống lưu loại phản hồi và timestamp
- Feedback được đưa vào báo cáo chất lượng

### FR-13 Quản trị taxonomy và mapping
**Acceptance criteria**:
- Admin có thể thêm/sửa topic, event type, department mapping
- Thay đổi taxonomy không làm hỏng dữ liệu cũ

### FR-14 Theo dõi sức khỏe hệ thống
**Acceptance criteria**:
- Admin xem được trạng thái job ingest/process/delivery
- Xem được số lỗi theo ngày
- Có health endpoint cho backend

---

## 5. User Stories và Acceptance theo phase

### Phase 1
**US-01** Là quản lý, tôi muốn nhận digest hàng ngày để biết các thay đổi quan trọng liên quan team của mình.
Acceptance:
- Digest gửi đúng lịch
- Chỉ chứa insight thuộc rule áp dụng cho team
- Mỗi insight có summary ngắn và link xem chi tiết

**US-02** Là dev lead, tôi muốn xem các thay đổi liên quan AI/tech/security trên dashboard.
Acceptance:
- Có filter theo chủ đề
- Có filter theo mức độ ảnh hưởng
- Insight hiển thị nguồn và ngày công bố

**US-03** Là admin, tôi muốn thêm nguồn mới để mở rộng phạm vi theo dõi.
Acceptance:
- Form nguồn có validation
- Sau khi lưu có thể test ingest nguồn

### Phase 2
**US-04** Là user, tôi muốn hỏi chatbot “Tuần này có gì ảnh hưởng team legal?”
Acceptance:
- Trả lời ngắn gọn
- Có nguồn trích dẫn
- Có nhắc mốc thời gian rõ ràng

**US-05** Là analyst, tôi muốn biết nhiều nguồn nào đang nói về cùng một sự kiện.
Acceptance:
- Hệ thống gộp event cluster
- Insight hiển thị nhiều nguồn liên kết

### Phase 3
**US-06** Là manager, tôi muốn chuyển insight thành task để team xử lý.
Acceptance:
- Có nút tạo task từ insight
- Task chứa title, summary, impact, source

---

## 6. Taxonomy và mô hình phân loại

### 6.1 Chủ đề
- AI
- Technology
- Data
- Software Process
- Security
- Legal/Compliance
- Content/Marketing
- Service/Platform
- Market/Competitor
- Internal Governance

### 6.2 Loại sự kiện
- New release
- Policy change
- Regulation update
- Security alert
- Deprecation
- Trend signal
- Community discussion
- Research update
- Operational incident

### 6.3 Loại nguồn
- Official
- Professional/Expert
- Community
- Internal

### 6.4 Mức độ tin cậy
- Very High
- High
- Medium
- Low
- Unverified

### 6.5 Mức độ ảnh hưởng
- Critical
- High
- Medium
- Low
- Watch

### 6.6 Tính chất
- Risk
- Opportunity
- Compliance
- Informational
- Watchlist

### 6.7 Đối tượng ảnh hưởng
- Executive
- Engineering
- Data/AI
- Product
- Content/Marketing
- Legal/Compliance
- HR/L&D
- All company

