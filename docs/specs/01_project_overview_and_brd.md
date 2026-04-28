# 01. PROJECT OVERVIEW & BRD — AI IMPACT RADAR

## 1. Thông tin chung
- **Tên dự án**: AI Impact Radar
- **Loại dự án**: Nền tảng AI thu thập, xác minh, tổng hợp và phân tích thông tin có ảnh hưởng đến doanh nghiệp
- **Mục tiêu chính**: Giúp doanh nghiệp theo dõi các thay đổi quan trọng từ bên ngoài và bên trong, sau đó phân tích tác động đến từng phòng ban, vai trò, quy trình và đề xuất hành động phù hợp.
- **Đối tượng sử dụng**: Ban lãnh đạo, quản lý phòng ban, Dev, Data/AI, Content/Marketing, Legal/Compliance, HR/L&D, Admin hệ thống.
- **Phạm vi triển khai khuyến nghị**: Triển khai theo nhiều phase, bắt đầu từ MVP tập trung vào Tech + AI + Pháp lý công nghệ + Quy trình phát triển phần mềm.

---

## 2. Bối cảnh và bài toán

### 2.1 Bối cảnh
Doanh nghiệp hiện phải đối mặt với lượng lớn thông tin thay đổi liên tục từ nhiều nguồn:
- Công nghệ, AI, dữ liệu, an ninh thông tin
- Quy trình phát triển phần mềm, DevOps, GitHub, framework, API, pricing, deprecation
- Chính sách nền tảng, luật và quy định liên quan đến dữ liệu, AI, quảng cáo, sở hữu trí tuệ
- Xu hướng content, marketing, SEO, social
- Thảo luận cộng đồng từ GitHub, Reddit, Hacker News, Facebook Group, forum chuyên ngành
- Tài liệu và quy trình nội bộ

### 2.2 Vấn đề hiện tại
- Thông tin phân tán ở nhiều nơi, khó theo dõi đồng bộ
- Các phòng ban không có thời gian tự theo dõi mọi thay đổi
- Khó xác định tin nào thực sự ảnh hưởng đến doanh nghiệp
- Khó đánh giá độ tin cậy của nguồn tin
- Tin cộng đồng hữu ích nhưng nhiều nhiễu
- Có thay đổi cần hành động nhưng bị phát hiện chậm
- Thiếu cơ chế map thông tin bên ngoài vào bối cảnh nội bộ

### 2.3 Bài toán cốt lõi
Xây dựng hệ thống AI có khả năng:
1. Thu thập dữ liệu từ nhiều nguồn đáng tin cậy và nguồn cộng đồng
2. Chuẩn hóa và phân loại nội dung
3. Đánh giá độ tin cậy
4. Phân tích tác động đến doanh nghiệp, phòng ban, vai trò
5. Sinh tóm tắt nhiều cấp độ
6. Đề xuất hành động phù hợp
7. Phân phối insight đến đúng người qua dashboard, email, Teams, chatbot

---

## 3. Mục tiêu dự án

### 3.1 Mục tiêu nghiệp vụ
- Giảm thời gian tìm kiếm và tổng hợp thông tin quan trọng
- Tăng tốc phản ứng của doanh nghiệp trước thay đổi công nghệ, AI, pháp luật, thị trường
- Giảm rủi ro bỏ sót thay đổi có ảnh hưởng lớn
- Hỗ trợ quản lý ra quyết định tốt hơn
- Chuẩn hóa tri thức cập nhật thành tài sản dùng lại trong công ty

### 3.2 Mục tiêu hệ thống
- Có pipeline thu thập thông tin đa nguồn
- Có cơ chế chấm điểm độ tin cậy và mức độ tác động
- Có dashboard tổng quan và chi tiết
- Có kênh phân phối chủ động qua email/Teams
- Có chatbot hỏi đáp trên dữ liệu đã được xử lý
- Có khả năng quản trị nguồn, phân quyền và truy vết

### 3.3 KPI đề xuất
- Giảm ít nhất 50% thời gian tổng hợp thông tin thủ công của người phụ trách
- Tỷ lệ insight được đánh giá hữu ích >= 70%
- Tỷ lệ insight có nguồn truy vết đầy đủ = 100%
- Tỷ lệ phân loại đúng chủ đề/phòng ban ảnh hưởng >= 80% trong phase 2
- Thời gian phát hiện sự kiện quan trọng sau khi nguồn công bố <= 24 giờ đối với nguồn chính thức

---

## 4. Phạm vi dự án

### 4.1 Trong phạm vi tổng thể
- Thu thập dữ liệu từ nguồn bên ngoài và nguồn nội bộ được cho phép
- Phân loại theo lĩnh vực, phòng ban, vai trò, mức độ ảnh hưởng
- Đánh giá độ tin cậy
- Tóm tắt insight
- Dashboard theo vai trò
- Email digest / Teams digest
- Chatbot hỏi đáp trên tập dữ liệu đã qua xử lý
- Quản trị nguồn và luật phân phối

### 4.2 Ngoài phạm vi giai đoạn đầu
- Dự báo định lượng phức tạp bằng mô hình riêng
- Tự động ra quyết định thay con người
- Full mobile app native
- Crawl toàn bộ mạng xã hội không kiểm soát
- Tự động cập nhật SOP hoặc policy vào production không qua phê duyệt

---

## 5. Stakeholder và người dùng

### 5.1 Stakeholder chính
- Sponsor / Ban giám đốc
- Business Owner
- PM/BA
- Solution Architect
- Dev Frontend
- Dev Backend
- Data/AI Engineer
- QA/Tester
- DevOps
- Đại diện các phòng ban

### 5.2 Nhóm người dùng
#### 1. Ban lãnh đạo
Nhu cầu:
- Xem top risk, top opportunity, thay đổi đáng chú ý
- Báo cáo tuần/tháng
- Hỗ trợ quyết định chiến lược

#### 2. Quản lý phòng ban
Nhu cầu:
- Insight ảnh hưởng trực tiếp tới team
- Theo dõi task/khuyến nghị hành động
- Theo dõi độ ưu tiên

#### 3. Dev / Tech Lead
Nhu cầu:
- Theo dõi thay đổi về framework, API, release, security, best practice, AI engineering

#### 4. Data/AI Team
Nhu cầu:
- Theo dõi model mới, benchmark, eval, AI governance, data tooling

#### 5. Content/Marketing
Nhu cầu:
- Theo dõi content trend, SEO, social, AI content policy

#### 6. Legal/Compliance
Nhu cầu:
- Theo dõi luật, quy định, điều khoản nền tảng, sở hữu trí tuệ, dữ liệu

#### 7. Admin hệ thống
Nhu cầu:
- Quản trị nguồn, vai trò, rule, lịch crawl, kênh phân phối

---

## 6. Định vị sản phẩm
AI Impact Radar là nền tảng giúp doanh nghiệp biến tín hiệu từ bên ngoài và nội bộ thành insight hành động được, bằng cách kết hợp:
- Thu thập đa nguồn
- AI phân tích
- Chấm điểm độ tin cậy
- Phân phối theo vai trò
- Truy vết nguồn và phản hồi người dùng

Sản phẩm không chỉ là news aggregator, mà là hệ thống intelligence và impact monitoring.

---

## 7. BRD - Business Requirements Document

### 7.1 Mục tiêu business
Doanh nghiệp cần một hệ thống giúp phát hiện sớm, tổng hợp nhanh và phân phối chính xác những thay đổi từ môi trường bên ngoài có thể ảnh hưởng đến hoạt động nội bộ. Hệ thống phải giảm phụ thuộc vào việc theo dõi thủ công và giúp các bộ phận phản ứng nhanh hơn với thay đổi.

### 7.2 Vấn đề business cần giải quyết
#### Vấn đề 1: Thông tin phân tán
Thông tin nằm ở nhiều nguồn khác nhau: website chính thức, diễn đàn, GitHub, nguồn pháp lý, mạng xã hội, cộng đồng chuyên môn.

#### Vấn đề 2: Thiếu cơ chế lọc tín hiệu quan trọng
Không phải tin nào cũng có giá trị như nhau. Thiếu hệ thống phân loại và đánh giá tác động theo bối cảnh doanh nghiệp.

#### Vấn đề 3: Phản ứng chậm
Các thay đổi quan trọng như security alert, chính sách AI, thay đổi điều khoản dịch vụ, luật mới, deprecation… thường được phát hiện muộn.

#### Vấn đề 4: Khó phối hợp liên phòng ban
Một thay đổi có thể liên quan đến nhiều phòng ban nhưng hiện không có cơ chế chỉ định rõ bộ phận nào cần biết và cần hành động.

#### Vấn đề 5: Thiếu minh bạch nguồn
Thông tin tóm tắt thường không đi kèm nguồn gốc, làm giảm mức độ tin tưởng và khó kiểm chứng.

### 7.3 Giá trị business mong đợi
- Giảm thời gian tổng hợp thông tin thủ công
- Nâng cao tốc độ phản ứng trước thay đổi
- Giảm rủi ro bỏ sót cảnh báo quan trọng
- Tạo một trung tâm tri thức cập nhật cho doanh nghiệp
- Tăng khả năng phối hợp giữa các phòng ban

### 7.4 Business capability cần có
- Theo dõi đa nguồn
- Tóm tắt đa cấp độ
- Đánh giá mức độ ảnh hưởng
- Đánh giá độ tin cậy
- Phân phối theo vai trò
- Truy vết nguồn
- Phản hồi và học hỏi

### 7.5 Business KPI chi tiết
- 80% insight gửi cho đúng nhóm đối tượng theo đánh giá sau UAT
- 100% insight hiển thị nguồn gốc
- 70% trở lên insight trong digest được người dùng đánh giá hữu ích ở phase 1
- Giảm ít nhất 50% thời gian tạo báo cáo tổng hợp tuần so với thủ công
- Thời gian từ khi nguồn chính thức công bố tới khi hệ thống ingest xong dưới 24 giờ đối với nguồn đã đăng ký

### 7.6 Phạm vi business theo phase
#### Phase 1
- Theo dõi nguồn chính thống và nguồn chuyên môn uy tín
- Hỗ trợ Tech, AI, Legal/Compliance
- Hiển thị dashboard và gửi digest

#### Phase 2
- Thêm chatbot và cá nhân hóa theo vai trò
- Bổ sung chấm điểm độ tin cậy nâng cao và event clustering

#### Phase 3
- Gắn workflow hành động, tích hợp task management, báo cáo lãnh đạo tự động

---

## 8. Quyết định thiết kế quan trọng ở góc business
- Dùng chiến lược phase-based, không làm full-scope ngay
- Giai đoạn đầu ưu tiên nguồn chính thống và nguồn chuyên môn uy tín
- Mọi insight phải truy vết được nguồn
- Dashboard + Digest là hai kênh hiển thị cốt lõi ở phase 1
- Chatbot chỉ triển khai sau khi curated insight repository đủ tốt
- Rule engine kết hợp AI scoring

---

## 9. Khuyến nghị thực thi ngay
1. Chốt Phase 1 scope chính thức
2. Chốt taxonomy v1 với các phòng ban sử dụng đầu tiên
3. Chốt danh sách 20-30 nguồn ưu tiên
4. Chốt wireframe dashboard và detail page
5. Chốt database schema v1 để bắt đầu build backend
6. Chốt delivery rules v1 cho email và Teams
7. Chuẩn bị bộ dữ liệu mẫu để test chất lượng summary và impact mapping

