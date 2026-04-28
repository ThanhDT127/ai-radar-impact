# 03. FLOWS, USE CASES & UI/UX — AI IMPACT RADAR

## 1. BFD - Business Flow Diagram ở mức nghiệp vụ

### 1.1 BFD tổng thể
1. Nguồn thông tin phát sinh thay đổi
2. Hệ thống thu thập dữ liệu từ nguồn
3. Hệ thống làm sạch, chuẩn hóa, nhóm trùng lặp
4. AI phân loại theo lĩnh vực, loại sự kiện, phòng ban ảnh hưởng
5. AI/Rule engine chấm điểm độ tin cậy và mức độ tác động
6. Hệ thống sinh insight và action recommendation
7. Hệ thống phân phối qua dashboard, email, Teams, chatbot
8. Người dùng đọc, phản hồi, đánh dấu hữu ích/không hữu ích
9. Hệ thống ghi nhận phản hồi để cải thiện rule/model/scoring

### 1.2 BFD theo vai trò người dùng
#### Luồng cho lãnh đạo
- Nhận executive digest hàng tuần
- Mở dashboard executive
- Xem top 5 risk, top 5 opportunity, các thay đổi quan trọng
- Drill down vào chi tiết nguồn và tác động
- Giao đầu việc cho quản lý

#### Luồng cho quản lý phòng ban
- Nhận digest theo team
- Mở dashboard team
- Xem insight ảnh hưởng đến team
- Xem hành động gợi ý
- Xác nhận nên theo dõi, cần xử lý, hoặc bỏ qua

#### Luồng cho người dùng chuyên môn
- Hỏi chatbot theo ngữ cảnh công việc
- Tìm insight gần nhất theo công nghệ/chủ đề
- Xem chi tiết, nguồn, bình luận, đánh giá hữu ích

#### Luồng cho admin
- Thêm nguồn
- Gán tier độ tin cậy mặc định
- Tạo rule phân phối
- Theo dõi lịch crawl, log lỗi, trạng thái pipeline

---

## 2. Use case tổng thể

### UC-01 Xem dashboard tổng quan
Actor: Lãnh đạo, Quản lý, Analyst
Kết quả: Thấy insight mới, mức ảnh hưởng, lĩnh vực, nguồn, department

### UC-02 Xem insight chi tiết
Actor: Mọi user có quyền
Kết quả: Thấy summary, nguồn gốc, nguồn xác minh chéo, mức độ tin cậy, phòng ban bị ảnh hưởng, hành động gợi ý

### UC-03 Nhận digest tự động
Actor: Mọi user được cấu hình nhận thông báo
Kết quả: Nhận email/Teams digest theo vai trò, team, chủ đề

### UC-04 Hỏi chatbot
Actor: User nghiệp vụ / chuyên môn
Kết quả: Nhận câu trả lời dựa trên insight đã xử lý và có trích nguồn

### UC-05 Quản trị nguồn dữ liệu
Actor: Admin
Kết quả: Thêm/sửa/tắt nguồn, cấu hình lịch lấy dữ liệu, gán mức độ ưu tiên

### UC-06 Phản hồi chất lượng insight
Actor: User cuối
Kết quả: Đánh giá insight hữu ích, sai đối tượng, trùng lặp, không đáng quan tâm

### UC-07 Quản trị luật phân phối
Actor: Admin / Manager có quyền
Kết quả: Chỉ định insight nào gửi đến nhóm nào, qua kênh nào, tần suất nào

### UC-08 Theo dõi sức khỏe hệ thống
Actor: Admin / DevOps
Kết quả: Xem trạng thái pipeline, crawl, AI processing, queue, lỗi, tỉ lệ thành công

---

## 3. Use case chi tiết trọng điểm

### UC-01 Xem executive dashboard
**Actor**: Executive
**Tiền điều kiện**: đã đăng nhập
**Luồng chính**:
1. Người dùng mở executive dashboard
2. Hệ thống hiển thị khoảng thời gian mặc định 7 ngày gần nhất
3. Hệ thống trả top risks, opportunities, compliance alerts
4. Người dùng mở chi tiết một insight
5. Hệ thống hiển thị nguồn và khuyến nghị
**Kết quả mong đợi**:
- Executive nắm nhanh các thay đổi đáng chú ý nhất trong một màn hình

### UC-02 Quản trị nguồn mới
**Actor**: Admin
**Luồng chính**:
1. Admin nhập cấu hình nguồn
2. Chạy test kết nối
3. Hệ thống trả sample ingest
4. Admin lưu nguồn
5. Nguồn được đưa vào lịch chạy

### UC-03 Hỏi chatbot
**Actor**: Manager/Analyst/User
**Ví dụ câu hỏi**: “Tuần này có thay đổi gì ảnh hưởng team engineering?”
**Kết quả**:
- Chatbot trả lời bằng tiếng người dùng
- Nêu mốc thời gian
- Liệt kê 3-5 insight liên quan
- Có nguồn đi kèm

---

## 4. BFD chi tiết theo quy trình nghiệp vụ

### 4.1 BFD cấp doanh nghiệp
**Bước 1**: Nguồn bên ngoài/nội bộ phát sinh thay đổi
**Bước 2**: Hệ thống thu thập và lưu raw data
**Bước 3**: Hệ thống chuẩn hóa và gắn metadata
**Bước 4**: Hệ thống phân tích và sinh insight
**Bước 5**: Hệ thống đánh giá trust/impact/relevance
**Bước 6**: Hệ thống phân phối insight
**Bước 7**: Người dùng tiếp nhận, phản hồi, tạo hành động
**Bước 8**: Hệ thống học từ phản hồi và tối ưu rule

### 4.2 BFD xử lý insight critical
1. Hệ thống phát hiện sự kiện có impact cao hoặc critical
2. Rule engine đánh dấu cần alert
3. Nếu loại sự kiện thuộc security/compliance/critical policy change thì chuyển vào luồng review hoặc broadcast theo rule
4. Gửi alert Teams/email cho đúng nhóm
5. Ghi nhận ai đã nhận, ai đã xem, ai phản hồi

### 4.3 BFD luồng quản trị nguồn
1. Admin đăng nhập
2. Tạo nguồn
3. Test kết nối/ingest mẫu
4. Lưu nguồn
5. Nguồn tham gia lịch crawl định kỳ
6. Theo dõi log lỗi và tinh chỉnh nếu cần

---

## 5. Flow hệ thống chi tiết

### 5.1 Sequence flow ingest
1. Scheduler gửi yêu cầu tới Ingestion Service
2. Ingestion Service lấy danh sách nguồn active đến thời điểm chạy
3. Connector tương ứng được gọi
4. Kết quả trả về raw content
5. Raw content lưu vào RawDocument store
6. Ingestion log được ghi vào JobLog
7. Message được đẩy vào queue xử lý chuẩn hóa

### 5.2 Sequence flow analysis
1. Analysis Worker lấy normalized document từ queue
2. Chạy classifier
3. Chạy summarizer
4. Chạy trust scoring
5. Chạy impact scoring
6. Tạo insight record
7. Gắn link tới source documents
8. Đẩy sự kiện sang delivery queue

### 5.3 Sequence flow delivery
1. Delivery Worker lấy insight mới
2. Tải danh sách delivery rules đang active
3. So khớp audience theo topic/impact/team/schedule
4. Tạo digest hoặc alert item
5. Gửi qua channel
6. Lưu delivery log

### 5.4 Sequence flow chatbot
1. User gửi câu hỏi
2. API xác thực user và nạp context quyền
3. Search/Retrieval truy xuất insight và source phù hợp
4. LLM tạo câu trả lời grounded từ context đã truy xuất
5. Trả câu trả lời + nguồn liên quan + timestamp
6. User đánh giá câu trả lời nếu muốn

---

## 6. Information Architecture và Sitemap

### Khu vực người dùng cuối
- Trang đăng nhập
- Dashboard tổng quan
- Dashboard executive
- Dashboard theo team
- Danh sách insight
- Chi tiết insight
- Chatbot/Copilot
- Lịch sử digest hoặc thông báo đã gửi
- Hồ sơ cá nhân / cài đặt nhận thông báo

### Khu vực admin
- Quản trị nguồn dữ liệu
- Quản trị rule phân phối
- Quản trị taxonomy
- Quản trị người dùng / role
- Theo dõi job ingest/process/delivery
- Màn hình log và health system
- Báo cáo chất lượng insight / feedback

---

## 7. Wireframe và mô tả màn hình

### 7.1 Màn hình đăng nhập
- Logo hệ thống
- Tên hệ thống: AI Impact Radar
- Input email/username
- Input mật khẩu hoặc SSO button
- Nút đăng nhập
- Liên kết quên mật khẩu nếu áp dụng
- Thông báo lỗi khi sai thông tin

### 7.2 Dashboard tổng quan
#### Header
- Global search
- Bộ chọn thời gian (24h / 7 ngày / 30 ngày / custom)
- Bộ lọc department
- Bộ lọc topic
- Bộ lọc impact
- Nút mở chatbot
- User menu

#### Menu trái
- Dashboard
- Insights
- Chatbot
- Digest history
- Admin (nếu có quyền)

#### Nội dung chính
**KPI cards**
- Tổng số insight trong kỳ
- Số insight impact cao/critical
- Số compliance alerts
- Số nguồn hoạt động

**Top risks**
- Danh sách 5 insight risk nổi bật

**Top opportunities**
- Danh sách 5 insight opportunity nổi bật

**Chủ đề nổi bật**
- Biểu đồ hoặc danh sách chủ đề có nhiều biến động

**Feed insight mới nhất**
Mỗi card insight gồm:
- Tiêu đề
- Tóm tắt 2 dòng
- Topic badge
- Impact badge
- Trust badge
- Department tags
- Source count
- Published date / first seen
- Nút xem chi tiết

### 7.3 Dashboard executive
- Executive summary 5-7 dòng
- Top strategic risks
- Top opportunities
- Department impact heat panel
- Compliance and policy watch
- Suggested actions

### 7.4 Dashboard theo team
- Bộ lọc theo team mặc định sẵn
- Danh sách insight liên quan team
- Phân nhóm theo topic hoặc priority
- Khu vực “What needs attention today”
- Khu vực “Watchlist”

### 7.5 Màn hình danh sách insight
- Search box
- Bộ lọc nâng cao: topic, event type, impact, trust, department, source type, date range, nature
- Bảng hoặc card list
- Sort theo impact, trust, newest

### 7.6 Trang chi tiết insight
**Khối đầu trang**
- Title
- Topic / Event type badges
- Impact badge
- Trust badge
- Nature badge
- Priority badge
- First seen / last updated

**Khối summary**
- Summary ngắn
- Summary chi tiết
- Summary theo role

**Khối tác động**
- Departments affected
- Role affected
- Vì sao insight quan trọng
- Gợi ý hành động

**Khối nguồn**
- Nguồn chính
- Nguồn xác minh chéo
- Link mở nguồn ngoài hệ thống
- Metadata nguồn

**Khối timeline**
- Lịch sử xuất hiện hoặc cập nhật sự kiện

**Khối phản hồi**
- Useful / Not useful
- Wrong target / Duplicate / Low relevance
- Comment box

**Khối thao tác**
- Share link
- Save / Follow
- Create task (phase 3)

### 7.7 Chatbot / Copilot panel
- Danh sách hội thoại gần đây
- Mẫu câu hỏi gợi ý
- Ô nhập câu hỏi
- Bộ lọc nhanh theo team/topic/time
- Khu vực trả lời chính
- Danh sách sources/insights liên quan
- Nút feedback câu trả lời

### 7.8 Màn hình quản trị nguồn
- Danh sách nguồn dạng bảng
- Cột: tên nguồn, loại nguồn, trạng thái, trust tier mặc định, lịch crawl, lần chạy gần nhất, trạng thái lần chạy gần nhất
- Nút thêm nguồn
- Bộ lọc theo loại nguồn / trạng thái
- Drawer/Popup thêm nguồn
- Test ingest preview

### 7.9 Màn hình quản trị rule phân phối
- Danh sách rule
- Điều kiện rule: audience type, topic, min impact, trust threshold, channel, digest/alert, schedule
- Nút tạo/sửa/xóa rule

### 7.10 Màn hình health và jobs
- Số lượng job ingest/process/delivery hôm nay
- Số job lỗi
- Connector lỗi nhiều nhất
- Queue size
- Delivery failure summary
- API health status
- Bảng log job gần nhất

---

## 8. UI Flow chi tiết

### 8.1 Flow 1: User đọc insight từ dashboard
1. User mở dashboard
2. Xem top insight hoặc feed mới
3. Click một insight
4. Mở trang detail
5. Đọc summary, trust, impact, sources
6. Đánh dấu useful hoặc share link

### 8.2 Flow 2: Manager theo dõi team
1. Manager vào team dashboard
2. Lọc team engineering
3. Xem danh sách insight high impact
4. Mở chi tiết insight
5. Xem gợi ý hành động
6. Chia sẻ cho team hoặc follow-up

### 8.3 Flow 3: User hỏi chatbot
1. User mở chatbot
2. Nhập câu hỏi
3. Hệ thống trả câu trả lời grounded
4. User click nguồn để kiểm tra
5. User feedback câu trả lời

### 8.4 Flow 4: Admin thêm nguồn mới
1. Admin mở Source Management
2. Chọn Add source
3. Nhập cấu hình nguồn
4. Chạy test ingest
5. Xem preview
6. Lưu nguồn
7. Nguồn được active và tham gia lịch crawl

### 8.5 Flow 5: Admin tạo rule digest
1. Admin mở Delivery Rules
2. Tạo rule mới
3. Chọn audience/team/channel/topic/impact/schedule
4. Lưu rule
5. Rule được áp dụng vào lần gửi tiếp theo

---

## 9. Wireframe text block

### 9.1 Dashboard tổng quan
[Header: Search | Time range | Topic filter | Department filter | Open chatbot | User menu]
[Sidebar: Dashboard | Insights | Chatbot | Digest history | Admin]
[Row 1: KPI cards x4]
[Row 2: Top Risks | Top Opportunities]
[Row 3: Trending Topics | Compliance Alerts]
[Row 4: Insight Feed full width]

### 9.2 Insight detail
[Title + badges]
[Summary short]
[Summary detailed]
[Impact & Recommendation panel]
[Sources panel]
[Timeline panel]
[Feedback panel]
[Action buttons: Share | Follow | Create task]

### 9.3 Chatbot
[Left: chat history + suggested questions]
[Right top: filters]
[Right center: answer area]
[Right bottom: related sources and insights]
[Bottom: input box]

### 9.4 Admin source management
[Toolbar: Add source | Filter source type | Filter status]
[Table sources]
[Right drawer: source form + test ingest preview]

---

## 10. UI States cần thiết
- Empty state: chưa có insight/nguồn/rule/kết quả chatbot
- Error state: lỗi tải dashboard, ingest nguồn, gửi digest, chatbot retrieval
- Loading state: skeleton cards, detail loading, chatbot loading, test ingest progress
- Permission state: không đủ quyền xem admin module hoặc insight nhạy cảm

---

## 11. Wireframe priority cho phase 1
### Bắt buộc phải thiết kế ngay
- Login
- Dashboard tổng quan
- Insight list
- Insight detail
- Source management
- Delivery rules cơ bản
- Health/jobs basic screen

### Có thể để phase 2
- Executive dashboard nâng cao
- Chatbot UI hoàn chỉnh
- Feedback analytics dashboard
- Simulation rule UI

