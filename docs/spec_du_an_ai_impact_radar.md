# ĐẶC TẢ DỰ ÁN: AI IMPACT RADAR CHO DOANH NGHIỆP

## 1. Thông tin chung
- **Tên dự án**: AI Impact Radar
- **Loại dự án**: Nền tảng AI thu thập, xác minh, tổng hợp và phân tích thông tin có ảnh hưởng đến doanh nghiệp
- **Mục tiêu chính**: Giúp doanh nghiệp theo dõi các thay đổi quan trọng từ bên ngoài và bên trong, sau đó phân tích tác động đến từng phòng ban, vai trò, quy trình và đề xuất hành động phù hợp.
- **Đối tượng sử dụng**: Ban lãnh đạo, quản lý phòng ban, Dev, Data/AI, Content/Marketing, Legal/Compliance, HR/L&D, Admin hệ thống.
- **Phạm vi triển khai khuyến nghị**: Triển khai theo nhiều phase, bắt đầu từ MVP tập trung vào Tech + AI + Pháp lý công nghệ + Quy trình phát triển phần mềm.

---

# 2. Bối cảnh và bài toán

## 2.1 Bối cảnh
Doanh nghiệp hiện phải đối mặt với lượng lớn thông tin thay đổi liên tục từ nhiều nguồn:
- Công nghệ, AI, dữ liệu, an ninh thông tin
- Quy trình phát triển phần mềm, DevOps, GitHub, framework, API, pricing, deprecation
- Chính sách nền tảng, luật và quy định liên quan đến dữ liệu, AI, quảng cáo, sở hữu trí tuệ
- Xu hướng content, marketing, SEO, social
- Thảo luận cộng đồng từ GitHub, Reddit, Hacker News, Facebook Group, forum chuyên ngành
- Tài liệu và quy trình nội bộ

## 2.2 Vấn đề hiện tại
- Thông tin phân tán ở nhiều nơi, khó theo dõi đồng bộ
- Các phòng ban không có thời gian tự theo dõi mọi thay đổi
- Khó xác định tin nào thực sự ảnh hưởng đến doanh nghiệp
- Khó đánh giá độ tin cậy của nguồn tin
- Tin cộng đồng hữu ích nhưng nhiều nhiễu
- Có thay đổi cần hành động nhưng bị phát hiện chậm
- Thiếu cơ chế map thông tin bên ngoài vào bối cảnh nội bộ

## 2.3 Bài toán cốt lõi
Xây dựng hệ thống AI có khả năng:
1. Thu thập dữ liệu từ nhiều nguồn đáng tin cậy và nguồn cộng đồng
2. Chuẩn hóa và phân loại nội dung
3. Đánh giá độ tin cậy
4. Phân tích tác động đến doanh nghiệp, phòng ban, vai trò
5. Sinh tóm tắt nhiều cấp độ
6. Đề xuất hành động phù hợp
7. Phân phối insight đến đúng người qua dashboard, email, Teams/chatbot

---

# 3. Mục tiêu dự án

## 3.1 Mục tiêu nghiệp vụ
- Giảm thời gian tìm kiếm và tổng hợp thông tin quan trọng
- Tăng tốc phản ứng của doanh nghiệp trước thay đổi công nghệ, AI, pháp luật, thị trường
- Giảm rủi ro bỏ sót thay đổi có ảnh hưởng lớn
- Hỗ trợ quản lý ra quyết định tốt hơn
- Chuẩn hóa tri thức cập nhật thành tài sản dùng lại trong công ty

## 3.2 Mục tiêu hệ thống
- Có pipeline thu thập thông tin đa nguồn
- Có cơ chế chấm điểm độ tin cậy và mức độ tác động
- Có dashboard tổng quan và chi tiết
- Có kênh phân phối chủ động qua email/Teams
- Có chatbot hỏi đáp trên dữ liệu đã được xử lý
- Có khả năng quản trị nguồn, phân quyền và truy vết

## 3.3 KPI đề xuất
- Giảm ít nhất 50% thời gian tổng hợp thông tin thủ công của người phụ trách
- Tỷ lệ insight được đánh giá hữu ích >= 70%
- Tỷ lệ insight có nguồn truy vết đầy đủ = 100%
- Tỷ lệ phân loại đúng chủ đề/phòng ban ảnh hưởng >= 80% trong phase 2
- Thời gian phát hiện sự kiện quan trọng sau khi nguồn công bố <= 24 giờ đối với nguồn chính thức

---

# 4. Phạm vi dự án

## 4.1 Trong phạm vi tổng thể
- Thu thập dữ liệu từ nguồn bên ngoài và nguồn nội bộ được cho phép
- Phân loại theo lĩnh vực, phòng ban, vai trò, mức độ ảnh hưởng
- Đánh giá độ tin cậy
- Tóm tắt insight
- Dashboard theo vai trò
- Email digest / Teams digest
- Chatbot hỏi đáp trên tập dữ liệu đã qua xử lý
- Quản trị nguồn và luật phân phối

## 4.2 Ngoài phạm vi giai đoạn đầu
- Dự báo định lượng phức tạp bằng mô hình riêng
- Tự động ra quyết định thay con người
- Full mobile app native
- Crawl toàn bộ mạng xã hội không kiểm soát
- Tự động cập nhật SOP hoặc policy vào production không qua phê duyệt

---

# 5. Stakeholder và người dùng

## 5.1 Stakeholder chính
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

## 5.2 Nhóm người dùng
### 1. Ban lãnh đạo
Nhu cầu:
- Xem top risk, top opportunity, thay đổi đáng chú ý
- Báo cáo tuần/tháng
- Hỗ trợ quyết định chiến lược

### 2. Quản lý phòng ban
Nhu cầu:
- Insight ảnh hưởng trực tiếp tới team
- Theo dõi task/khuyến nghị hành động
- Theo dõi độ ưu tiên

### 3. Dev / Tech Lead
Nhu cầu:
- Theo dõi thay đổi về framework, API, release, security, best practice, AI engineering

### 4. Data/AI Team
Nhu cầu:
- Theo dõi model mới, benchmark, eval, AI governance, data tooling

### 5. Content/Marketing
Nhu cầu:
- Theo dõi content trend, SEO, social, AI content policy

### 6. Legal/Compliance
Nhu cầu:
- Theo dõi luật, quy định, điều khoản nền tảng, sở hữu trí tuệ, dữ liệu

### 7. Admin hệ thống
Nhu cầu:
- Quản trị nguồn, vai trò, rule, lịch crawl, kênh phân phối

---

# 6. Định vị sản phẩm

AI Impact Radar là nền tảng giúp doanh nghiệp biến tín hiệu từ bên ngoài và nội bộ thành insight hành động được, bằng cách kết hợp:
- Thu thập đa nguồn
- AI phân tích
- Chấm điểm độ tin cậy
- Phân phối theo vai trò
- Truy vết nguồn và phản hồi người dùng

Sản phẩm không chỉ là news aggregator, mà là hệ thống intelligence và impact monitoring.

---

# 7. BFD - Business Flow Diagram ở mức nghiệp vụ

## 7.1 BFD tổng thể
1. Nguồn thông tin phát sinh thay đổi
2. Hệ thống thu thập dữ liệu từ nguồn
3. Hệ thống làm sạch, chuẩn hóa, nhóm trùng lặp
4. AI phân loại theo lĩnh vực, loại sự kiện, phòng ban ảnh hưởng
5. AI/Rule engine chấm điểm độ tin cậy và mức độ tác động
6. Hệ thống sinh insight và action recommendation
7. Hệ thống phân phối qua dashboard, email, Teams, chatbot
8. Người dùng đọc, phản hồi, đánh dấu hữu ích/không hữu ích
9. Hệ thống ghi nhận phản hồi để cải thiện rule/model/scoring

## 7.2 BFD theo vai trò người dùng
### Luồng cho lãnh đạo
- Nhận executive digest hàng tuần
- Mở dashboard executive
- Xem top 5 risk, top 5 opportunity, các thay đổi quan trọng
- Drill down vào chi tiết nguồn và tác động
- Giao đầu việc cho quản lý

### Luồng cho quản lý phòng ban
- Nhận digest theo team
- Mở dashboard team
- Xem insight ảnh hưởng đến team
- Xem hành động gợi ý
- Xác nhận nên theo dõi, cần xử lý, hoặc bỏ qua

### Luồng cho người dùng chuyên môn
- Hỏi chatbot theo ngữ cảnh công việc
- Tìm insight gần nhất theo công nghệ/chủ đề
- Xem chi tiết, nguồn, bình luận, đánh giá hữu ích

### Luồng cho admin
- Thêm nguồn
- Gán tier độ tin cậy mặc định
- Tạo rule phân phối
- Theo dõi lịch crawl, log lỗi, trạng thái pipeline

---

# 8. Use case tổng thể

## UC-01 Xem dashboard tổng quan
Actor: Lãnh đạo, Quản lý, Analyst
Kết quả: Thấy insight mới, mức ảnh hưởng, lĩnh vực, nguồn, department

## UC-02 Xem insight chi tiết
Actor: Mọi user có quyền
Kết quả: Thấy summary, nguồn gốc, nguồn xác minh chéo, mức độ tin cậy, phòng ban bị ảnh hưởng, hành động gợi ý

## UC-03 Nhận digest tự động
Actor: Mọi user được cấu hình nhận thông báo
Kết quả: Nhận email/Teams digest theo vai trò, team, chủ đề

## UC-04 Hỏi chatbot
Actor: User nghiệp vụ / chuyên môn
Kết quả: Nhận câu trả lời dựa trên insight đã xử lý và có trích nguồn

## UC-05 Quản trị nguồn dữ liệu
Actor: Admin
Kết quả: Thêm/sửa/tắt nguồn, cấu hình lịch lấy dữ liệu, gán mức độ ưu tiên

## UC-06 Phản hồi chất lượng insight
Actor: User cuối
Kết quả: Đánh giá insight hữu ích, sai đối tượng, sai mức độ, trùng lặp, không đáng quan tâm

## UC-07 Quản trị luật phân phối
Actor: Admin / Manager có quyền
Kết quả: Chỉ định insight nào gửi đến nhóm nào, qua kênh nào, tần suất nào

## UC-08 Theo dõi sức khỏe hệ thống
Actor: Admin / DevOps
Kết quả: Xem trạng thái pipeline, crawl, AI processing, queue, lỗi, tỉ lệ thành công

---

# 9. Phân kỳ triển khai theo phase

# PHASE 1 - MVP

## 9.1 Mục tiêu phase 1
Tạo phiên bản có thể dùng thực tế cho nhóm core users với chức năng:
- thu thập từ nguồn chọn lọc
- chuẩn hóa và phân loại cơ bản
- tóm tắt insight
- phân tích tác động theo phòng ban ở mức rule + AI
- dashboard cơ bản
- email/Teams digest

## 9.2 Nguồn dữ liệu phase 1
Ưu tiên nguồn chất lượng cao:
- Website chính thức của vendor công nghệ
- Blog kỹ thuật chính thức
- GitHub release/changelog của repo trọng yếu
- Website chính phủ / văn bản pháp lý / cơ quan quản lý
- Một số nguồn chuyên môn uy tín

## 9.3 Đối tượng sử dụng phase 1
- Lãnh đạo/Quản lý
- Dev/Tech Lead
- Data/AI
- Legal/Compliance

## 9.4 Chức năng phase 1
### F1. Quản lý danh mục nguồn
- Thêm/sửa/tắt nguồn
- Gắn loại nguồn
- Gắn tier độ tin cậy mặc định
- Gắn lịch crawl

### F2. Thu thập dữ liệu
- Kéo dữ liệu từ URL/RSS/API/GitHub release/nguồn pháp lý
- Lưu raw content và metadata
- Ghi log trạng thái từng lần thu thập

### F3. Chuẩn hóa dữ liệu
- Làm sạch HTML/text
- Tách tiêu đề, ngày, tác giả, nguồn, URL, ngôn ngữ
- Tạo fingerprint để chống trùng lặp

### F4. Phân loại chủ đề và loại sự kiện
- Chủ đề: AI, Tech, Data, Legal, Security, Content, Market, Process
- Loại sự kiện: update, release, regulation, security alert, trend, deprecation, discussion

### F5. Tóm tắt insight
- Tóm tắt ngắn (1-2 câu)
- Tóm tắt trung bình (5 bullet/ý)
- Summary theo vai trò (dev/legal/manager)

### F6. Phân tích tác động
- Gắn phòng ban bị ảnh hưởng
- Gắn mức ảnh hưởng: low / medium / high / critical
- Gắn tính chất: risk / opportunity / compliance / watchlist

### F7. Dashboard
- Dashboard tổng quan
- Bộ lọc theo chủ đề, phòng ban, thời gian, độ tin cậy, mức ảnh hưởng
- Trang chi tiết insight

### F8. Digest phân phối
- Email digest hàng ngày/tuần
- Teams digest theo team/role
- Rule gửi theo mức ảnh hưởng và chủ đề

### F9. Truy vết nguồn
- Mỗi insight phải xem được nguồn gốc
- Có mục nguồn xác minh chéo nếu có

### F10. Feedback cơ bản
- Hữu ích / Không hữu ích
- Sai đối tượng / Trùng / Không quan trọng

## 9.5 Yêu cầu phi chức năng phase 1
- Toàn bộ insight đều có source trace
- Có retry cho crawl thất bại
- Có log pipeline ingest/process/delivery
- Có phân quyền xem dashboard và admin chức năng
- Có audit với thay đổi cấu hình nguồn
- Dashboard tải trang chính dưới ngưỡng chấp nhận được
- Không để AI output chưa qua source trace xuất hiện như dữ liệu chính thức

## 9.6 Đầu ra phase 1
- Bản MVP vận hành được
- Dashboard web
- Digest email/Teams
- Bộ nguồn quản trị được
- Bộ taxonomy và scoring cơ bản

---

# PHASE 2 - ANALYTICS & COPILOT

## 10.1 Mục tiêu phase 2
Nâng từ hệ thống tổng hợp lên hệ thống hỏi đáp và intelligence tốt hơn.

## 10.2 Chức năng phase 2
### F11. Chatbot hỏi đáp theo dữ liệu đã xử lý
- Hỏi theo thời gian, theo team, theo chủ đề
- Trả lời có citation/source
- Có thể so sánh theo tuần/tháng

### F12. Chấm điểm độ tin cậy nâng cao
- Dựa trên source tier, loại nguồn, tính chính thức, đối chiếu chéo, độ mới, độ nhất quán
- Tách rõ official / expert / community / unverified

### F13. Dedup và event clustering nâng cao
- Gộp nhiều bài nói về cùng một sự kiện
- Sinh insight hợp nhất từ nhiều nguồn

### F14. Personalization theo vai trò
- Executive view
- Manager view
- Dev view
- Legal view
- Content view

### F15. Phản hồi học hỏi
- Ghi nhận feedback người dùng
- Điều chỉnh rule phân phối, scoring, relevance

### F16. Quản trị luật phân phối nâng cao
- Rule theo chủ đề + team + mức ảnh hưởng + thời gian
- Rule theo blacklist/whitelist nguồn

### F17. Theo dõi xu hướng ngắn hạn
- Chủ đề tăng nhanh trong 7 ngày / 30 ngày
- Top nguồn đóng góp insight

## 10.3 Phi chức năng phase 2
- Chatbot phải trả lời trên dữ liệu có truy vết
- Tách knowledge curated với raw content
- Có rate limit và cache cho hỏi đáp
- Có theo dõi chất lượng trả lời

---

# PHASE 3 - ACTION WORKFLOW & INTEGRATION

## 11.1 Mục tiêu phase 3
Biến insight thành workflow hành động và tích hợp sâu vào vận hành doanh nghiệp.

## 11.2 Chức năng phase 3
### F18. Action recommendation nâng cao
- Tạo khuyến nghị theo loại sự kiện
- Gắn suggested owner, deadline gợi ý

### F19. Task integration
- Tạo task sang Jira/Asana/Trello/Planner
- Theo dõi trạng thái action

### F20. SOP/Policy impact suggestion
- Gợi ý tài liệu nội bộ có thể bị ảnh hưởng
- Gợi ý cần review quy trình nào

### F21. Executive reporting tự động
- Report tuần/tháng dạng PDF/slide
- KPI trend, heatmap ảnh hưởng, major alerts

### F22. Internal knowledge mapping
- Map insight với tool đang dùng, hệ thống nội bộ, quy trình nội bộ, phòng ban liên quan

### F23. Multi-source governance
- Approval workflow cho insight critical
- Cơ chế phê duyệt trước khi broadcast rộng

## 11.3 Phi chức năng phase 3
- Có workflow trạng thái cho action
- Có audit trail cho quyết định broadcast/approve
- Tích hợp phân quyền với hệ thống nội bộ nếu cần

---

# 12. Danh mục chức năng đầy đủ (Functional Requirements)

## Nhóm A - Quản trị nguồn
**FR-01** Hệ thống cho phép quản trị danh sách nguồn dữ liệu.
**FR-02** Mỗi nguồn có các thuộc tính: tên, loại nguồn, URL/API, chủ đề, tier tin cậy mặc định, tần suất crawl, trạng thái.
**FR-03** Admin có thể bật/tắt nguồn.
**FR-04** Hệ thống ghi nhận lịch sử thay đổi cấu hình nguồn.

## Nhóm B - Thu thập dữ liệu
**FR-05** Hệ thống cho phép lấy dữ liệu từ web/RSS/API/GitHub releases/tài liệu pháp lý.
**FR-06** Hệ thống lưu raw content, metadata, thời điểm thu thập.
**FR-07** Hệ thống ghi log trạng thái ingest thành công/thất bại.
**FR-08** Hệ thống có cơ chế retry cho nguồn lỗi tạm thời.

## Nhóm C - Chuẩn hóa và phân tích
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

## Nhóm D - Insight
**FR-19** Hệ thống tạo insight từ một hoặc nhiều nguồn.
**FR-20** Insight phải có summary ngắn, summary chi tiết, nguồn gốc.
**FR-21** Insight có thể có nguồn xác minh chéo.
**FR-22** Insight có thể có recommended action.
**FR-23** Insight có thể có tag department, role, priority.

## Nhóm E - Dashboard & Search
**FR-24** Dashboard tổng quan hiển thị top insight theo thời gian.
**FR-25** Cho phép lọc theo thời gian, chủ đề, nguồn, độ tin cậy, team, impact.
**FR-26** Có trang chi tiết insight.
**FR-27** Có mục top risks, top opportunities, compliance alerts.
**FR-28** Có mục xu hướng theo thời gian ở phase 2 trở lên.

## Nhóm F - Delivery
**FR-29** Hệ thống gửi email digest theo lịch.
**FR-30** Hệ thống gửi Teams digest/alert theo rule.
**FR-31** Hệ thống hỗ trợ rule phân phối theo nhóm người dùng.
**FR-32** Chỉ gửi alert realtime cho insight có mức độ phù hợp theo cấu hình.

## Nhóm G - Chatbot
**FR-33** Người dùng có thể hỏi chatbot về insight đã xử lý.
**FR-34** Chatbot trả lời kèm trích nguồn.
**FR-35** Chatbot có thể lọc theo khoảng thời gian và phòng ban.
**FR-36** Chatbot không trả lời ngoài phạm vi dữ liệu được cấp quyền nếu cấu hình hạn chế.

## Nhóm H - Feedback & Learning
**FR-37** Người dùng có thể đánh giá insight.
**FR-38** Người dùng có thể báo insight sai đối tượng, sai mức độ, trùng, không hữu ích.
**FR-39** Hệ thống lưu feedback để cải thiện ranking/scoring/rule.

## Nhóm I - Quản trị & phân quyền
**FR-40** Hệ thống có phân quyền theo vai trò.
**FR-41** Chỉ admin mới được quản trị nguồn và rule.
**FR-42** Hệ thống log các thao tác quản trị chính.
**FR-43** Hệ thống cho phép cấu hình từ điển chủ đề, department mapping, trust tier.

---

# 13. Yêu cầu phi chức năng (Non-functional Requirements)

## 13.1 Bảo mật
**NFR-01** Hệ thống phải có cơ chế xác thực người dùng.
**NFR-02** Hệ thống phải phân quyền theo vai trò.
**NFR-03** Cấu hình nguồn, rule, admin action phải có audit log.
**NFR-04** Dữ liệu nội bộ và dữ liệu nhạy cảm phải được kiểm soát truy cập.

## 13.2 Truy vết và minh bạch
**NFR-05** Mọi insight phải có ít nhất một nguồn gốc truy vết được.
**NFR-06** Insight tổng hợp từ nhiều nguồn phải thể hiện danh sách nguồn liên quan.
**NFR-07** Hệ thống phải phân biệt rõ nội dung nguồn, nội dung AI summary và nhận định nội suy.

## 13.3 Hiệu năng
**NFR-08** Dashboard tổng quan phải phản hồi trong ngưỡng chấp nhận được với dữ liệu ở quy mô MVP.
**NFR-09** Pipeline ingest/process phải hỗ trợ chạy theo lịch định kỳ.
**NFR-10** Chatbot phải có cache hoặc chiến lược tối ưu truy vấn cho câu hỏi phổ biến.

## 13.4 Khả năng mở rộng
**NFR-11** Kiến trúc phải cho phép bổ sung nguồn mới mà không ảnh hưởng lớn đến module khác.
**NFR-12** Hệ thống phải cho phép thêm chủ đề, loại sự kiện, department mapping.
**NFR-13** Hệ thống phải hỗ trợ mở rộng kênh phân phối.

## 13.5 Vận hành
**NFR-14** Phải có logging cho ingest, processing, delivery, chatbot.
**NFR-15** Phải có monitoring trạng thái job và lỗi.
**NFR-16** Phải có backup dữ liệu cấu hình và dữ liệu đã xử lý theo chính sách triển khai.
**NFR-17** Phải có checklist deploy và rollback.

## 13.6 Chất lượng AI
**NFR-18** AI summary không được thay thế nguồn gốc.
**NFR-19** Các insight critical nên có rule xác minh chéo hoặc phê duyệt.
**NFR-20** Hệ thống phải cho phép đánh giá chất lượng output AI qua feedback người dùng.

---

# 14. Taxonomy và mô hình phân loại

## 14.1 Chủ đề
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

## 14.2 Loại sự kiện
- New release
- Policy change
- Regulation update
- Security alert
- Deprecation
- Trend signal
- Community discussion
- Research update
- Operational incident

## 14.3 Loại nguồn
- Official
- Professional/Expert
- Community
- Internal

## 14.4 Mức độ tin cậy
- Very High
- High
- Medium
- Low
- Unverified

## 14.5 Mức độ ảnh hưởng
- Critical
- High
- Medium
- Low
- Watch

## 14.6 Tính chất
- Risk
- Opportunity
- Compliance
- Informational
- Watchlist

## 14.7 Đối tượng ảnh hưởng
- Executive
- Engineering
- Data/AI
- Product
- Content/Marketing
- Legal/Compliance
- HR/L&D
- All company

---

# 15. Kiến trúc hệ thống tổng thể

## 15.1 Kiến trúc logic
Hệ thống gồm 7 lớp chính:
1. Source Connector Layer
2. Ingestion & Normalization Layer
3. Knowledge & Storage Layer
4. AI Analysis Layer
5. Business Rules & Scoring Layer
6. Delivery & Experience Layer
7. Governance & Operations Layer

## 15.2 Mô tả từng lớp
### 1. Source Connector Layer
Chức năng:
- Kết nối nguồn web, RSS, API, GitHub, nguồn pháp lý, nguồn nội bộ
- Quản lý lịch lấy dữ liệu
- Ghi log crawl

### 2. Ingestion & Normalization Layer
Chức năng:
- Clean text/HTML
- Chuẩn hóa metadata
- Language detection
- Dedup fingerprint
- Chunking nếu cần cho chatbot/search

### 3. Knowledge & Storage Layer
Chức năng:
- Lưu raw documents
- Lưu metadata
- Lưu curated insights
- Lưu taxonomy, rule, feedback
- Lưu vector index cho search/chatbot nếu áp dụng

### 4. AI Analysis Layer
Chức năng:
- Classifier
- Summarizer
- Impact analyzer
- Role-based summarizer
- Event clustering

### 5. Business Rules & Scoring Layer
Chức năng:
- Trust score
- Impact score
- Department mapping
- Priority/routing rule
- Approval rule

### 6. Delivery & Experience Layer
Chức năng:
- Web dashboard
- Insight detail page
- Teams/Email digest
- Chatbot
- Admin console

### 7. Governance & Operations Layer
Chức năng:
- Auth, RBAC
- Audit log
- Job monitoring
- Error handling
- Metrics and health check

---

# 16. Kiến trúc triển khai đề xuất

## 16.1 Thành phần vật lý chính
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

## 16.2 Gợi ý công nghệ
### Frontend
- React / Next.js
- UI library phù hợp doanh nghiệp

### Backend
- Python FastAPI hoặc Node.js NestJS
- REST API

### Processing
- Python workers
- n8n cho một số luồng tự động hóa đơn giản

### Database
- PostgreSQL cho dữ liệu nghiệp vụ và cấu hình
- Object storage cho raw content
- Redis/Queue cho job queue
- Vector DB hoặc pgvector/OpenSearch phase 2

### Integration
- Microsoft Teams webhook/bot
- SMTP/Email service
- GitHub API
- RSS/Web parser/API connectors

### Monitoring
- Logging tập trung
- Dashboard sức khỏe pipeline

---

# 17. Các module hệ thống

## M1. Source Management Module
Quản trị nguồn, lịch crawl, trust tier, tag chủ đề

## M2. Ingestion Module
Kéo dữ liệu, parse dữ liệu, lưu raw, ghi log

## M3. Normalization Module
Chuẩn hóa nội dung, metadata, dedup

## M4. Analysis Module
Classify, summarize, impact scoring, trust scoring, event clustering

## M5. Insight Repository Module
Lưu insight curated, mapping với source, tags, score

## M6. Dashboard Module
Danh sách insight, filter, detail, executive view

## M7. Delivery Module
Email digest, Teams alert, routing rules

## M8. Chatbot/Search Module
Semantic search, retrieval, grounded Q&A

## M9. Feedback Module
Lưu feedback, stats đánh giá, cải thiện relevance

## M10. Admin & Governance Module
RBAC, audit, taxonomy, settings, observability

---

# 18. Data Flow chính

## 18.1 Flow ingest đến insight
1. Scheduler kích hoạt job theo lịch
2. Connector lấy dữ liệu từ nguồn
3. Dữ liệu raw được lưu và ghi metadata ban đầu
4. Normalizer làm sạch, chuẩn hóa, chống trùng
5. Analysis module phân loại và tóm tắt
6. Rule engine chấm trust/impact/priority
7. Insight được lưu vào curated repository
8. Delivery engine xét rule để gửi digest/alert
9. Dashboard và chatbot truy cập insight repository

## 18.2 Flow chatbot
1. User nhập câu hỏi
2. Hệ thống kiểm tra quyền và bối cảnh
3. Search/retrieval lấy insight/source phù hợp
4. LLM tạo câu trả lời grounded
5. Trả lời kèm nguồn và mốc thời gian
6. Người dùng phản hồi chất lượng trả lời

## 18.3 Flow feedback learning
1. User đánh giá insight
2. Hệ thống lưu feedback
3. Module analytics tổng hợp feedback
4. Admin hoặc rule engine điều chỉnh trọng số/rule

---

# 19. Thiết kế dữ liệu mức khái niệm

## 19.1 Entity chính
### Source
- source_id
- name
- source_type
- domain
- access_method
- trust_tier_default
- category_tags
- crawl_schedule
- status

### RawDocument
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

### EventCluster
- event_id
- title
- canonical_topic
- first_seen_at
- last_seen_at
- confidence

### Insight
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

### InsightSourceLink
- insight_id
- document_id
- relation_type (primary/corroborating/reference)

### DeliveryRule
- rule_id
- audience_type
- audience_ref
- topics
- min_impact
- channels
- schedule
- status

### DeliveryLog
- delivery_id
- insight_id
- channel
- recipient_group
- sent_at
- status

### Feedback
- feedback_id
- insight_id
- user_id
- rating
- reason_code
- comment
- created_at

### UserRoleMapping
- user_id
- role
- department
- permission_set

### TaxonomyConfig
- taxonomy_id
- taxonomy_type
- code
- label
- parent_code
- active

---

# 20. API sơ bộ

## 20.1 API dashboard
- GET /insights
- GET /insights/{id}
- GET /dashboard/summary
- GET /dashboard/executive
- GET /topics
- GET /departments

## 20.2 API admin
- GET /sources
- POST /sources
- PUT /sources/{id}
- POST /sources/{id}/enable
- POST /sources/{id}/disable
- GET /delivery-rules
- POST /delivery-rules
- PUT /delivery-rules/{id}

## 20.3 API processing/ops
- POST /jobs/ingest/run
- GET /jobs/status
- GET /health
- GET /logs/summary

## 20.4 API feedback
- POST /insights/{id}/feedback
- GET /feedback/stats

## 20.5 API chatbot
- POST /chat/query
- GET /chat/history

---

# 21. UI/UX thiết kế chức năng

## 21.1 Dashboard tổng quan
Thành phần:
- Bộ lọc toàn cục
- Top insight mới
- Top risk
- Top opportunity
- Compliance alerts
- Chủ đề nổi bật
- Department impact heat summary

## 21.2 Dashboard executive
Thành phần:
- 5 thay đổi đáng chú ý nhất tuần
- Tác động theo phòng ban
- Rủi ro ưu tiên cao
- Cơ hội đầu tư/thử nghiệm
- Xu hướng và khuyến nghị tổng quát

## 21.3 Dashboard team view
Thành phần:
- Insight liên quan team
- Alert cần chú ý
- Các thay đổi theo chủ đề chuyên môn
- Gợi ý hành động

## 21.4 Insight detail page
Thành phần:
- Tiêu đề
- Summary ngắn và chi tiết
- Mức độ tin cậy
- Mức độ ảnh hưởng
- Đối tượng bị ảnh hưởng
- Hành động gợi ý
- Nguồn chính
- Nguồn xác minh chéo
- Lịch sử phát hiện
- Feedback

## 21.5 Admin nguồn dữ liệu
Thành phần:
- Danh sách nguồn
- Form thêm/sửa nguồn
- Trạng thái crawl
- Trust tier mặc định
- Lịch crawl

## 21.6 Admin luật phân phối
Thành phần:
- Danh sách rule
- Tạo rule gửi theo team/chủ đề/mức độ
- Lịch gửi digest

## 21.7 Chatbot panel
Thành phần:
- Hộp nhập câu hỏi
- Câu hỏi gợi ý
- Kết quả trả lời
- Danh sách nguồn liên quan
- Bộ lọc theo khoảng thời gian/chủ đề/team

---

# 22. Logic scoring đề xuất

## 22.1 Trust score sơ bộ
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

## 22.2 Impact score sơ bộ
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

# 23. Rule phân phối đề xuất

## 23.1 Nguyên tắc
- Không spam
- Đúng người, đúng lúc, đúng mức độ
- Digest cho tin thường, alert cho tin critical/high theo rule

## 23.2 Rule ví dụ
- Insight loại Security + Impact >= High => gửi Teams alert cho Engineering lead
- Insight loại Legal/Compliance + Impact >= Medium => gửi digest ngày cho Legal + Management
- Insight AI trend + Opportunity >= Medium => vào digest tuần cho Data/AI và Management
- Insight Content/SEO => gửi digest tuần cho Content/Marketing

---

# 24. Test strategy theo dự án

## 24.1 Test chức năng
- Test thêm/sửa/tắt nguồn
- Test crawl từng loại nguồn
- Test parse và metadata extraction
- Test dedup
- Test classify
- Test summary
- Test insight generation
- Test dashboard filter
- Test detail page
- Test email/Teams delivery
- Test chatbot grounded answer

## 24.2 Test dữ liệu
- Dữ liệu thiếu tiêu đề
- Dữ liệu trùng
- Dữ liệu sai ngày tháng
- Nguồn không phản hồi
- HTML nhiễu
- Ngôn ngữ pha trộn

## 24.3 Test AI quality
- Summary có bám nguồn không
- Role-based summary có đúng người dùng không
- Impact mapping có hợp lý không
- Chatbot có trích nguồn đúng không

## 24.4 Test phi chức năng
- Phân quyền
- Tải dashboard
- Retry ingest
- Audit log
- Độ ổn định queue
- Monitoring và health check

## 24.5 UAT scenario
- Manager xem insight của team mình
- Dev tìm thay đổi framework gần đây
- Legal xem thay đổi liên quan AI regulation
- Executive xem top risk tuần này
- User nhận digest đúng rule

---

# 25. Deploy và vận hành

## 25.1 Môi trường
- Dev
- Test/UAT
- Production

## 25.2 Yêu cầu vận hành
- Lịch ingest định kỳ
- Health check cho connector, worker, API, queue
- Log lỗi tập trung
- Dashboard giám sát số lượng insight/ngày, số job lỗi, số delivery lỗi

## 25.3 Handover bắt buộc
- Repo source code
- Tài liệu kiến trúc
- Tài liệu vận hành
- Tài liệu cấu hình môi trường
- Tài liệu người dùng
- Danh sách nguồn
- Danh sách rule
- Phiên bản triển khai hiện tại
- Đầu mối hỗ trợ

---

# 26. Rủi ro chính và biện pháp

## R1. Quá rộng phạm vi
Biện pháp: giới hạn nguồn và domain trong phase 1

## R2. Nhiễu từ nguồn cộng đồng
Biện pháp: tách tier, không broadcast rộng nếu chưa xác minh

## R3. AI summary sai ngữ cảnh
Biện pháp: luôn kèm source trace, feedback loop, approval rule cho critical insights

## R4. Khó map đúng phòng ban bị ảnh hưởng
Biện pháp: kết hợp taxonomy + rule + feedback người dùng

## R5. Spam alert
Biện pháp: delivery rule chặt, ưu tiên digest, rate limit alert

## R6. Thiếu owner sau bàn giao
Biện pháp: xác định rõ admin, ops, business owner từ đầu

---

# 27. Roadmap thực hiện đề xuất

## Sprint/Đợt 1
- Chốt taxonomy
- Chốt scope nguồn phase 1
- Thiết kế kiến trúc và data model
- Dựng module source management + ingest cơ bản

## Sprint/Đợt 2
- Chuẩn hóa + classify + summary
- Dựng insight repository
- Dựng dashboard cơ bản

## Sprint/Đợt 3
- Dựng digest email/Teams
- Dựng admin rule
- UAT phase 1

## Sprint/Đợt 4
- Chatbot grounded Q&A
- Trust scoring nâng cao
- Dedup/event clustering

## Sprint/Đợt 5+
- Workflow action
- Task integration
- Executive reporting

---

# 28. Kết luận thiết kế

AI Impact Radar nên được triển khai như một nền tảng đa lớp:
- **Thu thập nguồn**
- **Chuẩn hóa dữ liệu**
- **AI phân tích**
- **Scoring và rule nghiệp vụ**
- **Phân phối theo vai trò**
- **Truy vết, phản hồi và cải tiến**

Để đảm bảo khả thi, dự án nên triển khai theo phase với phase 1 tập trung vào giá trị thực dụng: nguồn chính thống, dashboard, digest, insight có truy vết và phân tích tác động cơ bản. Phase 2 và 3 sẽ mở rộng thành hệ thống intelligence và workflow mạnh hơn.

---

# 29. BRD - Business Requirements Document

## 29.1 Mục tiêu business
Doanh nghiệp cần một hệ thống giúp phát hiện sớm, tổng hợp nhanh và phân phối chính xác những thay đổi từ môi trường bên ngoài có thể ảnh hưởng đến hoạt động nội bộ. Hệ thống phải giảm phụ thuộc vào việc theo dõi thủ công và giúp các bộ phận phản ứng nhanh hơn với thay đổi.

## 29.2 Vấn đề business cần giải quyết
### Vấn đề 1: Thông tin phân tán
Thông tin nằm ở nhiều nguồn khác nhau: website chính thức, diễn đàn, GitHub, nguồn pháp lý, mạng xã hội, cộng đồng chuyên môn.

### Vấn đề 2: Thiếu cơ chế lọc tín hiệu quan trọng
Không phải tin nào cũng có giá trị như nhau. Thiếu hệ thống phân loại và đánh giá tác động theo bối cảnh doanh nghiệp.

### Vấn đề 3: Phản ứng chậm
Các thay đổi quan trọng như security alert, chính sách AI, thay đổi điều khoản dịch vụ, luật mới, deprecation… thường được phát hiện muộn.

### Vấn đề 4: Khó phối hợp liên phòng ban
Một thay đổi có thể liên quan đến nhiều phòng ban nhưng hiện không có cơ chế chỉ định rõ bộ phận nào cần biết và cần hành động.

### Vấn đề 5: Thiếu minh bạch nguồn
Thông tin tóm tắt thường không đi kèm nguồn gốc, làm giảm mức độ tin tưởng và khó kiểm chứng.

## 29.3 Giá trị business mong đợi
- Giảm thời gian tổng hợp thông tin thủ công
- Nâng cao tốc độ phản ứng trước thay đổi
- Giảm rủi ro bỏ sót cảnh báo quan trọng
- Tạo một trung tâm tri thức cập nhật cho doanh nghiệp
- Tăng khả năng phối hợp giữa các phòng ban

## 29.4 Business capability cần có
- Theo dõi đa nguồn
- Tóm tắt đa cấp độ
- Đánh giá mức độ ảnh hưởng
- Đánh giá độ tin cậy
- Phân phối theo vai trò
- Truy vết nguồn
- Phản hồi và học hỏi

## 29.5 Business KPI chi tiết
- 80% insight gửi cho đúng nhóm đối tượng theo đánh giá sau UAT
- 100% insight hiển thị nguồn gốc
- 70% trở lên insight trong digest được người dùng đánh giá hữu ích ở phase 1
- Giảm ít nhất 50% thời gian tạo báo cáo tổng hợp tuần so với thủ công
- Thời gian từ khi nguồn chính thức công bố tới khi hệ thống ingest xong dưới 24 giờ đối với nguồn đã đăng ký

## 29.6 Phạm vi business theo phase
### Phase 1
- Theo dõi nguồn chính thống và nguồn chuyên môn uy tín
- Hỗ trợ Tech, AI, Legal/Compliance
- Hiển thị dashboard và gửi digest

### Phase 2
- Thêm chatbot và cá nhân hóa theo vai trò
- Bổ sung chấm điểm độ tin cậy nâng cao và event clustering

### Phase 3
- Gắn workflow hành động, tích hợp task management, báo cáo lãnh đạo tự động

---

# 30. FRD - Functional Requirements Document chi tiết

## 30.1 Nguyên tắc viết FRD
Mỗi chức năng gồm:
- Mục tiêu
- Actor
- Tiền điều kiện
- Luồng chính
- Ngoại lệ
- Dữ liệu vào/ra
- Acceptance criteria

## 30.2 FR chi tiết theo module

### FR-01 Quản lý nguồn dữ liệu
**Mục tiêu**: Cho phép admin cấu hình và quản lý danh sách nguồn thu thập.

**Actor**: Admin

**Tiền điều kiện**:
- Người dùng đã đăng nhập với quyền admin

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

# 31. User stories và acceptance criteria theo phase

## 31.1 Phase 1
### US-01 Là quản lý, tôi muốn nhận digest hàng ngày để biết các thay đổi quan trọng liên quan team của mình.
**Acceptance**:
- Digest gửi đúng lịch
- Chỉ chứa insight thuộc rule áp dụng cho team
- Mỗi insight có summary ngắn và link xem chi tiết

### US-02 Là dev lead, tôi muốn xem các thay đổi liên quan AI/tech/security trên dashboard.
**Acceptance**:
- Có filter theo chủ đề
- Có filter theo mức độ ảnh hưởng
- Insight hiển thị nguồn và ngày công bố

### US-03 Là admin, tôi muốn thêm nguồn mới để mở rộng phạm vi theo dõi.
**Acceptance**:
- Form nguồn có validation
- Sau khi lưu có thể test ingest nguồn

## 31.2 Phase 2
### US-04 Là user, tôi muốn hỏi chatbot “Tuần này có gì ảnh hưởng team legal?”
**Acceptance**:
- Trả lời ngắn gọn
- Có nguồn trích dẫn
- Có nhắc mốc thời gian rõ ràng

### US-05 Là analyst, tôi muốn biết nhiều nguồn nào đang nói về cùng một sự kiện.
**Acceptance**:
- Hệ thống gộp event cluster
- Insight hiển thị nhiều nguồn liên kết

## 31.3 Phase 3
### US-06 Là manager, tôi muốn chuyển insight thành task để team xử lý.
**Acceptance**:
- Có nút tạo task từ insight
- Task chứa title, summary, impact, source

---

# 32. BFD chi tiết theo quy trình nghiệp vụ

## 32.1 BFD cấp doanh nghiệp
**Bước 1**: Nguồn bên ngoài/nội bộ phát sinh thay đổi
**Bước 2**: Hệ thống thu thập và lưu raw data
**Bước 3**: Hệ thống chuẩn hóa và gắn metadata
**Bước 4**: Hệ thống phân tích và sinh insight
**Bước 5**: Hệ thống đánh giá trust/impact/relevance
**Bước 6**: Hệ thống phân phối insight
**Bước 7**: Người dùng tiếp nhận, phản hồi, tạo hành động
**Bước 8**: Hệ thống học từ phản hồi và tối ưu rule

## 32.2 BFD xử lý insight critical
1. Hệ thống phát hiện sự kiện có impact cao hoặc critical
2. Rule engine đánh dấu cần alert
3. Nếu loại sự kiện thuộc security/compliance/critical policy change thì chuyển vào luồng review hoặc broadcast theo rule
4. Gửi alert Teams/email cho đúng nhóm
5. Ghi nhận ai đã nhận, ai đã xem, ai phản hồi

## 32.3 BFD luồng quản trị nguồn
1. Admin đăng nhập
2. Tạo nguồn
3. Test kết nối/ingest mẫu
4. Lưu nguồn
5. Nguồn tham gia lịch crawl định kỳ
6. Theo dõi log lỗi và tinh chỉnh nếu cần

---

# 33. Flow hệ thống chi tiết

## 33.1 Sequence flow ingest
1. Scheduler gửi yêu cầu tới Ingestion Service
2. Ingestion Service lấy danh sách nguồn active đến thời điểm chạy
3. Connector tương ứng được gọi
4. Kết quả trả về raw content
5. Raw content lưu vào RawDocument store
6. Ingestion log được ghi vào JobLog
7. Message được đẩy vào queue xử lý chuẩn hóa

## 33.2 Sequence flow analysis
1. Analysis Worker lấy normalized document từ queue
2. Chạy classifier
3. Chạy summarizer
4. Chạy trust scoring
5. Chạy impact scoring
6. Tạo insight record
7. Gắn link tới source documents
8. Đẩy sự kiện sang delivery queue

## 33.3 Sequence flow delivery
1. Delivery Worker lấy insight mới
2. Tải danh sách delivery rules đang active
3. So khớp audience theo topic/impact/team/schedule
4. Tạo digest hoặc alert item
5. Gửi qua channel
6. Lưu delivery log

## 33.4 Sequence flow chatbot
1. User gửi câu hỏi
2. API xác thực user và nạp context quyền
3. Search/Retrieval truy xuất insight và source phù hợp
4. LLM tạo câu trả lời grounded từ context đã truy xuất
5. Trả câu trả lời + nguồn liên quan + timestamp
6. User đánh giá câu trả lời nếu muốn

---

# 34. Kiến trúc hệ thống chi tiết hơn

## 34.1 Sơ đồ thành phần logic
### A. Presentation Layer
- Web Dashboard UI
- Admin UI
- Chatbot UI
- Teams/Email message views

### B. API Layer
- Auth API
- Insight API
- Admin API
- Chat API
- Feedback API
- Ops API

### C. Application Services
- Source Service
- Ingestion Service
- Normalization Service
- Analysis Service
- Scoring Service
- Delivery Service
- Feedback Service
- Search/Chat Service

### D. Data Layer
- PostgreSQL
- Object Storage
- Search/Vector Index
- Cache/Redis
- Job Queue

### E. Integration Layer
- RSS/Web/API connectors
- GitHub connector
- Government/legal data connector
- Email service
- Teams webhook/bot

### F. Observability Layer
- Log collector
- Metrics
- Health monitor
- Admin operations dashboard

## 34.2 Mối quan hệ các thành phần
- Frontend gọi Backend API
- Backend API gọi Application Services
- Application Services ghi/đọc dữ liệu từ DB, Queue, Storage
- Ingestion và Analysis chạy async qua Queue
- Delivery lấy dữ liệu từ Insight Repository và Rule Store
- Chatbot truy xuất từ Insight Repository và Search Index

---

# 35. Database schema sơ bộ chi tiết

## 35.1 Bảng sources
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

## 35.2 Bảng raw_documents
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

## 35.3 Bảng normalized_documents
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

## 35.4 Bảng event_clusters
- id
- canonical_title
- canonical_topic
- canonical_event_type
- first_seen_at
- last_seen_at
- cluster_confidence
- status

## 35.5 Bảng insights
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

## 35.6 Bảng insight_source_links
- id
- insight_id
- normalized_document_id
- relation_type
- weight

## 35.7 Bảng insight_departments
- id
- insight_id
- department_code
- role_code
- relevance_score

## 35.8 Bảng delivery_rules
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

## 35.9 Bảng deliveries
- id
- insight_id
- rule_id
- channel
- recipient_group
- payload_snapshot_json
- sent_at
- delivery_status
- error_message

## 35.10 Bảng feedbacks
- id
- insight_id
- user_id
- feedback_type
- rating
- comment
- created_at

## 35.11 Bảng users
- id
- username/email
- display_name
- department_code
- status

## 35.12 Bảng user_roles
- id
- user_id
- role_code
- assigned_at

## 35.13 Bảng taxonomies
- id
- taxonomy_type
- code
- label
- parent_code
- active_flag

## 35.14 Bảng job_logs
- id
- job_type
- source_id
- started_at
- finished_at
- job_status
- records_processed
- error_message

## 35.15 Bảng audit_logs
- id
- actor_id
- action_type
- entity_type
- entity_id
- before_json
- after_json
- created_at

---

# 36. API spec chi tiết hơn

## 36.1 API - Sources
### GET /api/v1/sources
Mục đích: lấy danh sách nguồn
Query params:
- status
- source_type
- keyword

Response fields:
- id, name, type, schedule, trust tier, status, last run status

### POST /api/v1/sources
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

### PUT /api/v1/sources/{id}
Cập nhật nguồn

### POST /api/v1/sources/{id}/test
Chạy test ingest cho nguồn

### POST /api/v1/sources/{id}/toggle
Bật/tắt nguồn

## 36.2 API - Insights
### GET /api/v1/insights
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

### GET /api/v1/insights/{id}
Trả chi tiết insight gồm:
- summary
- source links
- trust/impact
- department mapping
- recommendation
- timeline

## 36.3 API - Dashboard
### GET /api/v1/dashboard/overview
Trả về:
- total insights period
- top risks
- top opportunities
- top compliance alerts
- trend counts by topic

### GET /api/v1/dashboard/executive
Trả về summary đã tối ưu cho executive

## 36.4 API - Delivery rules
### GET /api/v1/delivery-rules
### POST /api/v1/delivery-rules
### PUT /api/v1/delivery-rules/{id}
### DELETE /api/v1/delivery-rules/{id}

## 36.5 API - Feedback
### POST /api/v1/insights/{id}/feedback
Request body:
- feedback_type
- rating
- comment

### GET /api/v1/feedback/summary

## 36.6 API - Chat
### POST /api/v1/chat/query
Request body:
- question
- filters(optional)

Response:
- answer
- cited_insight_ids
- cited_sources
- confidence_note

## 36.7 API - Ops
### GET /api/v1/ops/jobs
### GET /api/v1/ops/jobs/{id}
### GET /api/v1/health
### GET /api/v1/ops/metrics

---

# 37. Role & Permission Matrix

## 37.1 Admin
- Toàn quyền quản trị nguồn
- Toàn quyền quản trị taxonomy
- Toàn quyền rule phân phối
- Xem log và health system
- Xem tất cả insight

## 37.2 Executive
- Xem executive dashboard
- Xem insight và report được phân quyền
- Không quản trị nguồn

## 37.3 Manager
- Xem dashboard team
- Xem insight liên quan team
- Nhận digest
- Gửi feedback

## 37.4 Specialist User
- Xem insight trong phạm vi được cấp
- Dùng chatbot
- Gửi feedback

## 37.5 Analyst
- Xem dashboard chuyên sâu
- Xem cluster/source chi tiết
- Không sửa nguồn nếu không có quyền admin

## 37.6 Ops/DevOps
- Xem job logs, metrics, health
- Không sửa nội dung insight nếu không có quyền bổ sung

---

# 38. Use case chi tiết trọng điểm

## UC-01 Xem executive dashboard
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

## UC-02 Quản trị nguồn mới
**Actor**: Admin
**Luồng chính**:
1. Admin nhập cấu hình nguồn
2. Chạy test kết nối
3. Hệ thống trả sample ingest
4. Admin lưu nguồn
5. Nguồn được đưa vào lịch chạy

## UC-03 Hỏi chatbot
**Actor**: Manager/Analyst/User
**Ví dụ câu hỏi**: “Tuần này có thay đổi gì ảnh hưởng team engineering?”
**Kết quả**:
- Chatbot trả lời bằng tiếng người dùng
- Nêu mốc thời gian
- Liệt kê 3-5 insight liên quan
- Có nguồn đi kèm

---

# 39. Đề xuất backlog kỹ thuật theo phase

## 39.1 Phase 1 backlog
### Nhóm nền tảng
- Setup repo
- Setup auth cơ bản
- Setup database schema phase 1
- Setup queue/job runner
- Setup logging

### Nhóm nguồn
- Source management UI/API
- RSS/Web source connector base
- GitHub release connector
- Legal/gov source connector mẫu

### Nhóm xử lý
- Raw document storage
- Normalization pipeline
- Dedup pipeline cơ bản
- Topic classifier bản đầu
- Summary generator bản đầu
- Impact rule engine bản đầu
- Trust rule engine bản đầu

### Nhóm hiển thị
- Dashboard overview
- Insight list
- Insight detail page
- Admin source screen
- Delivery rule screen cơ bản

### Nhóm phân phối
- Email digest service
- Teams digest service
- Delivery log

### Nhóm feedback
- Insight feedback API/UI cơ bản

## 39.2 Phase 2 backlog
- Search index/vector store
- Retrieval service
- Chat API
- Chat UI
- Event clustering
- Advanced trust scoring
- Role-based personalization
- Feedback analytics dashboard

## 39.3 Phase 3 backlog
- Task integration service
- Executive report generator
- SOP mapping engine
- Approval workflow for critical alerts

---

# 40. Test cases mẫu theo module

## 40.1 Source Management
- Tạo nguồn hợp lệ
- Tạo nguồn thiếu URL
- Tạo nguồn trùng
- Toggle nguồn active/inactive
- Audit log sau cập nhật nguồn

## 40.2 Ingestion
- Crawl RSS thành công
- Crawl website thành công
- Crawl GitHub release thành công
- Timeout nguồn
- Retry sau lỗi tạm thời

## 40.3 Insight processing
- Tài liệu mới tạo insight thành công
- Hai tài liệu gần trùng không tạo 2 insight rác
- Summary có dữ liệu
- Impact label được gắn
- Trust label được gắn

## 40.4 Delivery
- Tạo digest ngày đúng rule
- Gửi Teams thành công
- Log lỗi gửi email
- Insight low impact không bị alert realtime nếu rule không cho phép

## 40.5 Chatbot
- Hỏi theo topic
- Hỏi theo department
- Hỏi theo khoảng thời gian
- Trả lời có nguồn
- Trả lời với câu hỏi ngoài scope phải xử lý an toàn

---

# 41. UAT checklist theo phase 1

## Với business owner
- Insight có đúng chủ đề không
- Impact có hợp lý không
- Digest có dễ đọc không
- Có insight nào thiếu nguồn không

## Với manager
- Dashboard có đủ filter không
- Insight có đúng team không
- Có thấy các thay đổi thật sự hữu ích không

## Với admin
- Có quản trị nguồn được không
- Có thấy log job không
- Có bật/tắt rule được không

---

# 42. Deliverable chính thức theo từng phase

## Phase 1
- BRD
- FRD
- Taxonomy v1
- Architecture v1
- Data model v1
- API spec v1
- Dashboard UI v1
- Delivery rule v1
- MVP running system
- Test report phase 1
- Handover doc phase 1

## Phase 2
- Chatbot spec
- Retrieval design
- Trust scoring v2
- Event clustering design
- Personalization spec
- Test report phase 2

## Phase 3
- Action workflow spec
- Integration spec
- Executive reporting pack
- Governance & approval flow doc

---

# 43. Quyết định thiết kế quan trọng

## DD-01 Dùng chiến lược phase-based, không làm full-scope ngay
Lý do: bài toán quá rộng, cần giảm rủi ro và tạo giá trị sớm.

## DD-02 Giai đoạn đầu ưu tiên nguồn chính thống và nguồn chuyên môn uy tín
Lý do: tăng trust, giảm nhiễu, dễ chứng minh giá trị.

## DD-03 Mọi insight phải truy vết được nguồn
Lý do: đây là điều kiện tối thiểu để hệ thống được tin dùng.

## DD-04 Dashboard + Digest là hai kênh hiển thị cốt lõi ở phase 1
Lý do: phù hợp cả nhu cầu pull và push.

## DD-05 Chatbot chỉ triển khai sau khi curated insight repository đủ tốt
Lý do: tránh chatbot trả lời trên dữ liệu lộn xộn.

## DD-06 Rule engine kết hợp AI scoring
Lý do: chỉ dùng AI dễ thiếu kiểm soát, chỉ dùng rule thì kém linh hoạt.

---

# 44. Khuyến nghị thực thi ngay sau tài liệu này

1. Chốt Phase 1 scope chính thức
2. Chốt taxonomy v1 với các phòng ban sử dụng đầu tiên
3. Chốt danh sách 20-30 nguồn ưu tiên
4. Chốt wireframe dashboard và detail page
5. Chốt database schema v1 để bắt đầu build backend
6. Chốt delivery rules v1 cho email và Teams
7. Chuẩn bị bộ dữ liệu mẫu để test chất lượng summary và impact mapping

---

# 45. Kết luận mở rộng

Bộ tài liệu này đã được thiết kế trực tiếp cho dự án AI Impact Radar, không phải mẫu chung. Tài liệu có thể dùng làm nền cho:
- review với business
- review kiến trúc với kỹ thuật
- tách backlog triển khai
- chuẩn bị proposal trình lãnh đạo
- làm đầu vào cho thiết kế UI và phân rã sprint

---

# 46. Wireframe, UI Flow và Information Architecture

## 46.1 Mục tiêu thiết kế UI/UX
UI/UX của AI Impact Radar phải phục vụ đồng thời 4 yêu cầu:
1. Xem nhanh tín hiệu quan trọng
2. Đào sâu insight khi cần
3. Hành động hoặc chia sẻ thông tin đúng người
4. Quản trị nguồn và quy tắc một cách minh bạch

Nguyên tắc thiết kế:
- Ưu tiên khả năng đọc nhanh
- Làm rõ trust, impact, source ngay trên màn hình
- Không để dashboard biến thành “danh sách tin tức” thuần túy
- Tách rõ màn hình cho user nghiệp vụ và admin
- Mỗi insight đều dẫn tới trang chi tiết có thể truy vết

## 46.2 Sitemap tổng thể
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

# 47. Wireframe chi tiết từng màn hình

## 47.1 Màn hình đăng nhập
### Mục tiêu
Cho phép người dùng truy cập hệ thống an toàn.

### Thành phần chính
- Logo hệ thống
- Tên hệ thống: AI Impact Radar
- Input email/username
- Input mật khẩu hoặc SSO button
- Nút đăng nhập
- Liên kết quên mật khẩu nếu áp dụng
- Thông báo lỗi khi sai thông tin

### Hành vi
- Nếu đăng nhập thành công, điều hướng theo role tới dashboard phù hợp
- Nếu user là executive, có thể mặc định vào executive dashboard
- Nếu user là admin, có quyền vào khu vực quản trị

---

## 47.2 Dashboard tổng quan
### Mục tiêu
Cung cấp bức tranh chung về insight mới, các thay đổi đáng chú ý, xu hướng theo thời gian.

### Bố cục đề xuất
#### Header
- Global search
- Bộ chọn thời gian (24h / 7 ngày / 30 ngày / custom)
- Bộ lọc department
- Bộ lọc topic
- Bộ lọc impact
- Nút mở chatbot
- User menu

#### Cột trái / menu trái
- Dashboard
- Insights
- Chatbot
- Digest history
- Admin (nếu có quyền)

#### Khu vực nội dung chính
**Khối 1: KPI cards**
- Tổng số insight trong kỳ
- Số insight impact cao/critical
- Số compliance alerts
- Số nguồn hoạt động

**Khối 2: Top risks**
- Danh sách 5 insight risk nổi bật
- Hiển thị title, impact badge, source count, updated time

**Khối 3: Top opportunities**
- Danh sách 5 insight opportunity nổi bật

**Khối 4: Chủ đề nổi bật**
- Biểu đồ hoặc danh sách chủ đề có nhiều biến động

**Khối 5: Feed insight mới nhất**
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

### Hành vi
- Click card insight -> mở insight detail
- Dùng filter -> toàn bộ dashboard cập nhật
- Search -> chuyển sang insight list với kết quả lọc

---

## 47.3 Dashboard executive
### Mục tiêu
Giúp lãnh đạo xem nhanh những thay đổi đáng chú ý nhất ở cấp chiến lược.

### Bố cục đề xuất
**Khối 1: Executive summary**
- Một đoạn AI summary 5-7 dòng về tuần/tháng hiện tại

**Khối 2: Top strategic risks**
- 5 item quan trọng nhất

**Khối 3: Top opportunities**
- 5 item nổi bật

**Khối 4: Department impact heat panel**
- Danh sách các phòng ban và số insight ảnh hưởng cao

**Khối 5: Compliance and policy watch**
- Các thay đổi pháp lý/chính sách cần theo dõi

**Khối 6: Suggested actions**
- Những hành động nên ưu tiên xem xét trong kỳ

### Hành vi
- Mỗi item mở detail page
- Có nút export report PDF/slide ở phase 3

---

## 47.4 Dashboard theo team
### Mục tiêu
Giúp trưởng nhóm hoặc nhân sự chuyên môn xem insight liên quan trực tiếp đội của mình.

### Thành phần chính
- Bộ lọc theo team mặc định sẵn
- Danh sách insight liên quan team
- Phân nhóm theo topic hoặc priority
- Khu vực “What needs attention today”
- Khu vực “Watchlist”
- Khu vực “Most discussed / most referenced sources” ở phase 2

### Hành vi
- Manager có thể đánh dấu insight là cần follow-up
- Có thể chia sẻ link insight cho team

---

## 47.5 Màn hình danh sách insight
### Mục tiêu
Cho phép tìm, lọc, phân loại và duyệt insight ở chế độ danh sách chi tiết hơn dashboard.

### Thành phần chính
- Search box
- Bộ lọc nâng cao:
  - topic
  - event type
  - impact
  - trust
  - department
  - source type
  - date range
  - nature
- Bảng hoặc card list

### Cấu trúc item trong list
- Tiêu đề
- Tóm tắt ngắn
- Topic
- Event type
- Trust label
- Impact label
- Departments affected
- Số nguồn
- Ngày công bố / ngày hệ thống phát hiện
- Trạng thái (new / reviewed / watch)

### Hành vi
- Sort theo impact, trust, newest
- Bulk actions ở phase cao hơn nếu cần

---

## 47.6 Trang chi tiết insight
### Mục tiêu
Là màn hình quan trọng nhất, nơi người dùng kiểm tra độ tin cậy và hiểu rõ tác động.

### Bố cục đề xuất
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
- Summary theo role (tab dev / manager / legal nếu có)

**Khối tác động**
- Departments affected
- Role affected
- Vì sao hệ thống cho rằng insight này quan trọng
- Gợi ý hành động

**Khối nguồn**
- Nguồn chính
- Nguồn xác minh chéo
- Link mở nguồn ngoài hệ thống
- Metadata nguồn: domain, publish date, source type

**Khối timeline**
- Lịch sử xuất hiện hoặc cập nhật sự kiện
- Danh sách nguồn mới thêm vào event cluster (phase 2)

**Khối phản hồi**
- Useful / Not useful
- Wrong target / Duplicate / Low relevance
- Comment box

**Khối thao tác**
- Share link
- Save / Follow
- Create task (phase 3)

### Hành vi
- Nếu insight là cluster, cho phép mở danh sách các tài liệu nguồn liên quan
- Nếu user không có quyền admin thì chỉ xem, không sửa scoring

---

## 47.7 Chatbot / Copilot panel
### Mục tiêu
Hỗ trợ hỏi đáp theo vai trò và ngữ cảnh.

### Bố cục đề xuất
**Khối trái**
- Danh sách hội thoại gần đây
- Mẫu câu hỏi gợi ý

**Khối phải**
- Ô nhập câu hỏi
- Bộ lọc nhanh theo team/topic/time
- Khu vực trả lời chính
- Danh sách sources/insights liên quan bên dưới
- Nút feedback câu trả lời

### Câu hỏi gợi ý
- Tuần này có gì ảnh hưởng đến team engineering?
- Có thay đổi pháp lý nào về AI trong 30 ngày qua?
- Những xu hướng AI nào đáng theo dõi cho công ty?

### Hành vi
- Trả lời có source list
- Cho phép click source/insight để xem detail
- Có cảnh báo nếu câu trả lời dựa trên nguồn chưa xác minh mạnh

---

## 47.8 Màn hình quản trị nguồn
### Mục tiêu
Giúp admin cấu hình nguồn dữ liệu.

### Bố cục đề xuất
- Danh sách nguồn dạng bảng
- Cột: tên nguồn, loại nguồn, trạng thái, trust tier mặc định, lịch crawl, lần chạy gần nhất, trạng thái lần chạy gần nhất
- Nút thêm nguồn
- Bộ lọc theo loại nguồn / trạng thái

### Drawer/Popup thêm nguồn
- Source name
- Source type
- Base URL/API endpoint
- Access method
- Topic mặc định
- Trust tier mặc định
- Crawl schedule
- Enable/Disable
- Test ingest button

### Hành vi
- Test ingest hiển thị bản preview dữ liệu lấy được
- Cấu hình thay đổi phải lưu audit log

---

## 47.9 Màn hình quản trị rule phân phối
### Mục tiêu
Giúp admin xác định insight nào gửi cho ai qua kênh nào.

### Thành phần chính
- Danh sách rule
- Điều kiện rule:
  - audience type
  - topic
  - min impact
  - trust threshold
  - channel
  - digest/alert
  - schedule
- Nút tạo/sửa/xóa rule
- Khu vực mô phỏng rule (nên có ở phase 2 nếu được)

---

## 47.10 Màn hình health và jobs
### Mục tiêu
Theo dõi vận hành hệ thống.

### Thành phần chính
- Số lượng job ingest/process/delivery hôm nay
- Số job lỗi
- Connector lỗi nhiều nhất
- Queue size
- Delivery failure summary
- API health status
- Bảng log job gần nhất

---

# 48. UI Flow chi tiết

## 48.1 Flow 1: User đọc insight từ dashboard
1. User mở dashboard
2. Xem top insight hoặc feed mới
3. Click một insight
4. Mở trang detail
5. Đọc summary, trust, impact, sources
6. Đánh dấu useful hoặc share link

## 48.2 Flow 2: Manager theo dõi team
1. Manager vào team dashboard
2. Lọc team engineering
3. Xem danh sách insight high impact
4. Mở chi tiết insight
5. Xem gợi ý hành động
6. Chia sẻ cho team hoặc follow-up

## 48.3 Flow 3: User hỏi chatbot
1. User mở chatbot
2. Nhập câu hỏi
3. Hệ thống trả câu trả lời grounded
4. User click nguồn để kiểm tra
5. User feedback câu trả lời

## 48.4 Flow 4: Admin thêm nguồn mới
1. Admin mở Source Management
2. Chọn Add source
3. Nhập cấu hình nguồn
4. Chạy test ingest
5. Xem preview
6. Lưu nguồn
7. Nguồn được active và tham gia lịch crawl

## 48.5 Flow 5: Admin tạo rule digest
1. Admin mở Delivery Rules
2. Tạo rule mới
3. Chọn audience/team/channel/topic/impact/schedule
4. Lưu rule
5. Rule được áp dụng vào lần gửi tiếp theo

---

# 49. Wireframe mô tả dạng text block

## 49.1 Wireframe dashboard tổng quan
[Header: Search | Time range | Topic filter | Department filter | Open chatbot | User menu]
[Sidebar: Dashboard | Insights | Chatbot | Digest history | Admin]
[Row 1: KPI cards x4]
[Row 2: Top Risks | Top Opportunities]
[Row 3: Trending Topics | Compliance Alerts]
[Row 4: Insight Feed full width]

## 49.2 Wireframe insight detail
[Title + badges]
[Summary short]
[Summary detailed]
[Impact & Recommendation panel]
[Sources panel]
[Timeline panel]
[Feedback panel]
[Action buttons: Share | Follow | Create task]

## 49.3 Wireframe chatbot
[Left: chat history + suggested questions]
[Right top: filters]
[Right center: answer area]
[Right bottom: related sources and insights]
[Bottom: input box]

## 49.4 Wireframe admin source management
[Toolbar: Add source | Filter source type | Filter status]
[Table sources]
[Right drawer: source form + test ingest preview]

---

# 50. UI States cần thiết

## 50.1 Empty state
- Chưa có insight
- Chưa có nguồn
- Chưa có rule phân phối
- Chưa có kết quả chatbot

## 50.2 Error state
- Lỗi tải dashboard
- Lỗi ingest nguồn
- Lỗi gửi digest
- Lỗi chatbot không truy xuất được nguồn phù hợp

## 50.3 Loading state
- Dashboard skeleton cards
- Insight detail loading block
- Chatbot typing/loading
- Admin test ingest progress

## 50.4 Permission state
- Người dùng không đủ quyền xem admin module
- Người dùng không đủ quyền xem insight nội bộ nhạy cảm

---

# 51. ERD chi tiết và quan hệ dữ liệu

## 51.1 Quan hệ chính
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

## 51.2 Ràng buộc logic
- Một insight bắt buộc phải có ít nhất một source link
- Một raw document có thể bị đánh dấu duplicate và không tạo normalized document mới nếu áp dụng cơ chế hợp nhất sớm
- Một delivery phải gắn với ít nhất một insight và một rule hoặc lý do gửi trực tiếp
- Feedback phải gắn user và insight

## 51.3 Chỉ mục nên có
- Index theo topic, impact_label, trust_label trên bảng insights
- Index theo source_id và fetched_at trên raw_documents
- Index theo published_at trên normalized_documents
- Index theo department_code trên insight_departments
- Full-text hoặc vector index cho summary/title/body_cleaned

---

# 52. DDL định hướng sơ bộ

## 52.1 sources
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

## 52.2 raw_documents
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

## 52.3 normalized_documents
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

## 52.4 event_clusters
- id UUID PK
- canonical_title TEXT NOT NULL
- canonical_topic VARCHAR NOT NULL
- canonical_event_type VARCHAR NOT NULL
- first_seen_at TIMESTAMP NOT NULL
- last_seen_at TIMESTAMP NOT NULL
- cluster_confidence NUMERIC(5,2) NULL
- status VARCHAR NOT NULL

## 52.5 insights
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

## 52.6 insight_source_links
- id UUID PK
- insight_id UUID FK -> insights.id
- normalized_document_id UUID FK -> normalized_documents.id
- relation_type VARCHAR NOT NULL
- weight NUMERIC(5,2) NULL

## 52.7 insight_departments
- id UUID PK
- insight_id UUID FK -> insights.id
- department_code VARCHAR NOT NULL
- role_code VARCHAR NULL
- relevance_score NUMERIC(5,2) NULL

## 52.8 delivery_rules
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

## 52.9 deliveries
- id UUID PK
- insight_id UUID FK -> insights.id
- rule_id UUID NULL FK -> delivery_rules.id
- channel VARCHAR NOT NULL
- recipient_group VARCHAR NOT NULL
- payload_snapshot_json JSONB NULL
- sent_at TIMESTAMP NULL
- delivery_status VARCHAR NOT NULL
- error_message TEXT NULL

## 52.10 feedbacks
- id UUID PK
- insight_id UUID FK -> insights.id
- user_id UUID FK -> users.id
- feedback_type VARCHAR NOT NULL
- rating INTEGER NULL
- comment TEXT NULL
- created_at TIMESTAMP NOT NULL

## 52.11 users
- id UUID PK
- account_key VARCHAR UNIQUE NOT NULL
- display_name VARCHAR NOT NULL
- department_code VARCHAR NULL
- status VARCHAR NOT NULL

## 52.12 user_roles
- id UUID PK
- user_id UUID FK -> users.id
- role_code VARCHAR NOT NULL
- assigned_at TIMESTAMP NOT NULL

## 52.13 taxonomies
- id UUID PK
- taxonomy_type VARCHAR NOT NULL
- code VARCHAR NOT NULL
- label VARCHAR NOT NULL
- parent_code VARCHAR NULL
- active_flag BOOLEAN NOT NULL

## 52.14 job_logs
- id UUID PK
- job_type VARCHAR NOT NULL
- source_id UUID NULL FK -> sources.id
- started_at TIMESTAMP NOT NULL
- finished_at TIMESTAMP NULL
- job_status VARCHAR NOT NULL
- records_processed INTEGER NULL
- error_message TEXT NULL

## 52.15 audit_logs
- id UUID PK
- actor_id UUID NULL FK -> users.id
- action_type VARCHAR NOT NULL
- entity_type VARCHAR NOT NULL
- entity_id UUID NULL
- before_json JSONB NULL
- after_json JSONB NULL
- created_at TIMESTAMP NOT NULL

---

# 53. API contract request/response chi tiết

## 53.1 GET /api/v1/insights
### Request query
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

### Response mẫu
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

## 53.2 GET /api/v1/insights/{id}
### Response mẫu
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

## 53.3 POST /api/v1/sources
### Request body mẫu
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

### Response mẫu
```json
{
  "id": "uuid",
  "message": "Source created successfully"
}
```

## 53.4 POST /api/v1/insights/{id}/feedback
### Request body mẫu
```json
{
  "feedback_type": "wrong_target",
  "rating": 2,
  "comment": "Nội dung này phù hợp legal hơn là engineering"
}
```

### Response mẫu
```json
{
  "message": "Feedback saved successfully"
}
```

## 53.5 POST /api/v1/chat/query
### Request body mẫu
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

### Response mẫu
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

# 54. Mapping UI với API

## 54.1 Dashboard overview
- GET /dashboard/overview
- GET /insights?filters...

## 54.2 Insight detail
- GET /insights/{id}
- POST /insights/{id}/feedback

## 54.3 Source management
- GET /sources
- POST /sources
- PUT /sources/{id}
- POST /sources/{id}/test
- POST /sources/{id}/toggle

## 54.4 Delivery rule screen
- GET /delivery-rules
- POST /delivery-rules
- PUT /delivery-rules/{id}

## 54.5 Chatbot
- POST /chat/query

---

# 55. Mô tả dashboard metrics chi tiết

## 55.1 Business dashboard metrics
- total_insights_current_period
- high_impact_insights_count
- critical_alerts_count
- compliance_alerts_count
- unique_active_sources_count
- average_user_feedback_rating

## 55.2 Operations dashboard metrics
- ingest_jobs_success_rate
- processing_jobs_success_rate
- delivery_success_rate
- failed_connectors_count
- queue_backlog_size
- average_chat_response_time

---

# 56. Định nghĩa trạng thái chính

## 56.1 Insight status
- new
- reviewed
- watch
- archived

## 56.2 Job status
- queued
- running
- success
- failed
- partial_success

## 56.3 Source status
- draft
- active
- inactive
- error

## 56.4 Delivery status
- pending
- sent
- failed
- skipped

---

# 57. Wireframe priority cho phase 1

## Bắt buộc phải thiết kế ngay
- Login
- Dashboard tổng quan
- Insight list
- Insight detail
- Source management
- Delivery rules cơ bản
- Health/jobs basic screen

## Có thể để phase 2
- Executive dashboard nâng cao
- Chatbot UI hoàn chỉnh
- Feedback analytics dashboard
- Simulation rule UI

---

# 58. Kết luận phần UI/ERD/API

Phần mở rộng này đã bổ sung:
- kiến trúc thông tin giao diện
- wireframe mức text rõ ràng
- luồng thao tác người dùng và admin
- ERD và quan hệ dữ liệu cụ thể hơn
- DDL định hướng
- contract API request/response mẫu
- mapping giữa UI và backend

Như vậy tài liệu hiện tại đã tiến gần tới mức có thể dùng cho 3 đội cùng lúc:
- **business** xem flow và màn hình
- **design** bám wireframe để vẽ Figma
- **backend/frontend** bám schema và API để triển khai

---

# 59. Backlog Implementation chi tiết theo Epic

## 59.1 Mục tiêu phần backlog
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

# 60. Danh sách Epic tổng thể

## E01. Foundation & Project Setup
## E02. Authentication, Authorization & User Management
## E03. Source Management
## E04. Ingestion Pipeline
## E05. Normalization & Deduplication
## E06. AI Analysis & Insight Generation
## E07. Scoring & Business Rules
## E08. Insight Repository & Search
## E09. Dashboard & Insight UI
## E10. Delivery & Notification
## E11. Feedback & Quality Loop
## E12. Chatbot & Retrieval
## E13. Admin Operations & Monitoring
## E14. Action Workflow & External Integrations
## E15. Reporting & Executive Pack
## E16. QA, UAT, Release & Handover

---

# 61. Phase mapping theo Epic

## Phase 1
- E01, E02, E03, E04, E05, E06, E07, E08, E09, E10, E11, E13, E16

## Phase 2
- E06 nâng cao, E07 nâng cao, E08 nâng cao, E09 mở rộng, E12, E13 nâng cao, E16

## Phase 3
- E14, E15, E07 mở rộng, E09 executive reporting nâng cao, E16

---

# 62. Epic E01 - Foundation & Project Setup

## Mục tiêu
Thiết lập nền tảng kỹ thuật, repo, chuẩn coding, CI cơ bản, môi trường phát triển.

## Feature E01-F01: Repository & Branch Strategy
### User Story
Là đội phát triển, chúng tôi cần một repo và branch strategy chuẩn để cùng làm việc ổn định.

### Tasks
- Tạo repository frontend
- Tạo repository backend hoặc monorepo theo quyết định kiến trúc
- Thiết lập branch strategy: main/develop/feature/hotfix
- Thiết lập PR template
- Thiết lập code review checklist
- Thiết lập README dự án
- Thiết lập convention commit message

### Dependency
- Không phụ thuộc

### Priority
- Critical

### Definition of Done
- Repo tạo xong
- Branch strategy được mô tả
- Team có thể clone và chạy skeleton app

## Feature E01-F02: Environment Setup
### Tasks
- Thiết lập dev environment template
- Thiết lập env config structure
- Thiết lập local DB
- Thiết lập queue/cache local
- Thiết lập docker-compose local nếu dùng

### DoD
- Chạy được app frontend/backend local
- DB và queue local hoạt động

## Feature E01-F03: CI baseline
### Tasks
- Thiết lập CI chạy lint
- Thiết lập CI chạy unit test cơ bản
- Thiết lập build check

### DoD
- PR chạy CI tự động
- Thất bại khi lint/test lỗi

---

# 63. Epic E02 - Authentication, Authorization & User Management

## Mục tiêu
Đảm bảo truy cập hệ thống có kiểm soát và đúng vai trò.

## Feature E02-F01: Authentication
### Stories
- Là user, tôi muốn đăng nhập hệ thống an toàn.
- Là admin, tôi muốn giới hạn người được truy cập.

### Tasks
- Chọn phương án auth: local auth hoặc SSO
- Thiết kế user session/token flow
- Xây API login/logout/refresh token
- Xây UI login
- Xử lý session timeout

### Priority
- High

### Dependency
- E01

### DoD
- User đăng nhập được
- API xác thực hoạt động
- Session được kiểm soát

## Feature E02-F02: RBAC
### Tasks
- Thiết kế role model
- Tạo bảng users, roles, user_roles
- Middleware kiểm tra quyền
- Phân quyền route frontend
- Phân quyền API admin/user

### DoD
- Admin vào được khu admin
- User thường không truy cập được admin API

---

# 64. Epic E03 - Source Management

## Mục tiêu
Cho phép cấu hình, bật/tắt và theo dõi nguồn dữ liệu.

## Feature E03-F01: Source CRUD API
### Stories
- Là admin, tôi muốn thêm/sửa/tắt nguồn.

### Tasks
- Thiết kế schema sources
- Xây GET /sources
- Xây POST /sources
- Xây PUT /sources/{id}
- Xây toggle source status
- Xây validation nguồn
- Xây audit log khi sửa nguồn

### DoD
- CRUD nguồn hoạt động
- Có validation và audit log

## Feature E03-F02: Source Management UI
### Tasks
- Xây danh sách nguồn
- Xây form thêm/sửa nguồn
- Hiển thị trạng thái nguồn
- Filter theo loại nguồn/trạng thái

### DoD
- Admin quản trị được nguồn từ UI

## Feature E03-F03: Test ingest preview
### Tasks
- API test ingest
- Preview dữ liệu lấy mẫu
- UI hiển thị kết quả test

### DoD
- Admin test được trước khi activate nguồn

---

# 65. Epic E04 - Ingestion Pipeline

## Mục tiêu
Thu thập dữ liệu tự động từ các nguồn đã cấu hình.

## Feature E04-F01: Scheduler
### Tasks
- Thiết lập scheduler framework
- Đọc schedule từ sources
- Trigger ingest jobs
- Ghi job logs

### DoD
- Job chạy theo lịch
- Có log trạng thái job

## Feature E04-F02: RSS Connector
### Tasks
- Xây connector RSS
- Parse item feed
- Map item vào raw document schema
- Handle duplicate feed item cơ bản

### Priority
- Critical

## Feature E04-F03: Web Connector
### Tasks
- Xây connector web scraping/parsing đơn giản
- Tải HTML
- Parse title/body/url/date cơ bản
- Xử lý lỗi kết nối

## Feature E04-F04: GitHub Release Connector
### Tasks
- Kết nối GitHub releases/changelog
- Parse metadata release
- Lưu raw document

## Feature E04-F05: Legal/Gov Connector mẫu
### Tasks
- Chọn 1-2 nguồn pháp lý/government mẫu
- Viết parser phù hợp
- Test ingest ổn định

## Feature E04-F06: Raw storage & job log
### Tasks
- Tạo bảng raw_documents
- Tạo bảng job_logs
- Lưu raw content và metadata
- Ghi lỗi ingest

### DoD cho Epic E04
- Hệ thống ingest được từ ít nhất 3 loại nguồn
- Có job log
- Có raw document được lưu

---

# 66. Epic E05 - Normalization & Deduplication

## Mục tiêu
Chuẩn hóa tài liệu và loại bỏ trùng lặp, giảm noise.

## Feature E05-F01: Content cleaning
### Tasks
- Strip HTML
- Loại bỏ block nhiễu thường gặp
- Chuẩn hóa whitespace
- Chuẩn hóa encoding

## Feature E05-F02: Metadata extraction
### Tasks
- Parse title
- Parse author
- Parse publish date
- Parse source domain
- Detect language

## Feature E05-F03: Deduplication v1
### Tasks
- Tạo fingerprint
- So khớp duplicate exact match
- So khớp near-duplicate rule-based sơ bộ
- Đánh dấu duplicate group

## Feature E05-F04: Normalized storage
### Tasks
- Tạo bảng normalized_documents
- Lưu tài liệu đã chuẩn hóa
- Gắn trạng thái normalized_status

### DoD cho Epic E05
- Tài liệu ingest xong được chuẩn hóa
- Có dedup basic
- Dữ liệu sạch đủ cho analysis

---

# 67. Epic E06 - AI Analysis & Insight Generation

## Mục tiêu
Sinh insight có summary và phân loại từ dữ liệu đã chuẩn hóa.

## Feature E06-F01: Topic classification v1
### Tasks
- Thiết kế taxonomy v1
- Viết classifier pipeline
- Mapping tài liệu -> topic
- Logging kết quả classify

## Feature E06-F02: Event type classification v1
### Tasks
- Thiết kế event type set
- Classify release/policy/regulation/security/trend/deprecation

## Feature E06-F03: Summary generation v1
### Tasks
- Sinh summary short
- Sinh summary medium
- Xác định prompt/logic an toàn bám nguồn
- Lưu summary vào insight

## Feature E06-F04: Insight creation
### Tasks
- Thiết kế bảng insights
- Logic tạo insight từ normalized document
- Gắn link nguồn ban đầu
- Tránh tạo insight rác khi document không đạt tiêu chí

## Feature E06-F05: Role-based summary v2
### Phase
- Phase 2
### Tasks
- Summary cho manager/dev/legal
- Đánh giá chênh lệch tone và nội dung theo role

## Feature E06-F06: Event clustering v2
### Phase
- Phase 2
### Tasks
- Gộp nhiều normalized document vào event cluster
- Sinh canonical insight

### DoD cho Epic E06 phase 1
- Mỗi insight có topic, event type, summary, source link

---

# 68. Epic E07 - Scoring & Business Rules

## Mục tiêu
Tính toán trust, impact, priority và routing theo rule nghiệp vụ.

## Feature E07-F01: Trust score v1
### Tasks
- Xác định công thức rule-based trust v1
- Tạo trust tier mapping
- Gắn trust label cho insight

## Feature E07-F02: Impact score v1
### Tasks
- Xác định rule impact theo topic/event/department
- Mapping department ảnh hưởng
- Tạo impact label

## Feature E07-F03: Recommendation v1
### Tasks
- Tạo rule action suggestion cơ bản
- Sinh recommendation text từ template/rule

## Feature E07-F04: Delivery rule engine v1
### Tasks
- Match insight với delivery rules
- Quyết định digest/alert

## Feature E07-F05: Scoring v2 nâng cao
### Phase
- Phase 2+
### Tasks
- Kết hợp feedback, source corroboration, cluster confidence

### DoD cho Epic E07 phase 1
- Insight có trust_label, impact_label, department mapping, recommendation sơ bộ

---

# 69. Epic E08 - Insight Repository & Search

## Mục tiêu
Lưu trữ và truy xuất insight hiệu quả cho dashboard và chatbot.

## Feature E08-F01: Insight persistence
### Tasks
- Tạo schema insights, insight_source_links, insight_departments
- API get insight list/detail

## Feature E08-F02: Filter & query support
### Tasks
- Filter theo topic
- Filter theo impact
- Filter theo trust
- Filter theo department
- Filter theo thời gian
- Sort newest/impact/trust

## Feature E08-F03: Search v1
### Tasks
- Search keyword theo title/summary
- Full-text search cơ bản

## Feature E08-F04: Search/Vector index v2
### Phase
- Phase 2
### Tasks
- Tạo vector index hoặc semantic search
- Đồng bộ insight/source vào search index

### DoD cho Epic E08
- Dashboard và detail page đọc dữ liệu insight ổn định
- Search cơ bản dùng được ở phase 1

---

# 70. Epic E09 - Dashboard & Insight UI

## Mục tiêu
Cung cấp trải nghiệm trực quan cho người dùng cuối.

## Feature E09-F01: Layout & navigation
### Tasks
- Xây app shell
- Sidebar
- Header filters
- User menu

## Feature E09-F02: Dashboard overview
### Tasks
- KPI cards
- Top risks block
- Top opportunities block
- Compliance alerts block
- Insight feed block

## Feature E09-F03: Insight list page
### Tasks
- Table/card list
- Filter panel
- Sort options
- Pagination

## Feature E09-F04: Insight detail page
### Tasks
- Header badges
- Summary block
- Impact/recommendation block
- Source block
- Timeline block
- Feedback block

## Feature E09-F05: Executive dashboard
### Phase
- Phase 1 basic, phase 3 nâng cao
### Tasks
- Executive summary block
- Department heat summary
- Strategic risk block

## Feature E09-F06: Team dashboard
### Tasks
- Team filter default
- High impact view for team
- What needs attention block

## Feature E09-F07: Chatbot UI
### Phase
- Phase 2
### Tasks
- Chat window
- History list
- Related sources panel

### DoD cho Epic E09 phase 1
- User đăng nhập xong xem được dashboard, insight list, insight detail, basic executive/team views

---

# 71. Epic E10 - Delivery & Notification

## Mục tiêu
Đưa insight tới đúng người qua email/Teams.

## Feature E10-F01: Delivery rule CRUD
### Tasks
- Schema delivery_rules
- API CRUD rules
- UI rule management cơ bản

## Feature E10-F02: Digest builder
### Tasks
- Chọn insight theo rule và lịch
- Tạo nội dung digest
- Render template email/Teams

## Feature E10-F03: Email delivery
### Tasks
- Tích hợp email service
- Gửi digest
- Lưu log gửi

## Feature E10-F04: Teams delivery
### Tasks
- Tích hợp Teams webhook/bot
- Gửi digest/alert
- Lưu log gửi

## Feature E10-F05: Realtime alert logic
### Tasks
- Trigger alert khi impact và rule phù hợp
- Chống spam bằng limit/rule

### DoD cho Epic E10 phase 1
- Gửi được email digest và Teams digest theo rule
- Có log gửi thành công/thất bại

---

# 72. Epic E11 - Feedback & Quality Loop

## Mục tiêu
Thu thập phản hồi để cải thiện chất lượng insight và routing.

## Feature E11-F01: Insight feedback
### Tasks
- API gửi feedback
- UI nút Useful/Not useful
- UI chọn reason code
- Lưu feedback DB

## Feature E11-F02: Feedback summary
### Tasks
- Tổng hợp feedback theo insight
- Tổng hợp feedback theo topic/department
- Báo cáo feedback cơ bản cho admin

## Feature E11-F03: Quality analytics v2
### Phase
- Phase 2
### Tasks
- Dashboard chất lượng insight
- Tỷ lệ useful theo nguồn/topic/rule

### DoD cho Epic E11 phase 1
- User phản hồi được
- Admin xem được số liệu phản hồi cơ bản

---

# 73. Epic E12 - Chatbot & Retrieval

## Mục tiêu
Cho phép user hỏi đáp trên insight đã xử lý.

## Feature E12-F01: Retrieval service
### Phase
- Phase 2
### Tasks
- Truy xuất insight liên quan theo filter và semantic/keyword
- Gộp source context

## Feature E12-F02: Chat API
### Tasks
- POST /chat/query
- Xác thực user
- Gọi retrieval
- Tạo grounded answer
- Trả cited insights/sources

## Feature E12-F03: Chat UI
### Tasks
- Giao diện chat
- Suggested questions
- Nút feedback answer

## Feature E12-F04: Chat history
### Tasks
- Lưu query log
- Hiển thị history cơ bản

### DoD cho Epic E12
- User hỏi được câu hỏi theo topic/department/time
- Trả lời có cited sources

---

# 74. Epic E13 - Admin Operations & Monitoring

## Mục tiêu
Theo dõi sức khỏe hệ thống và hỗ trợ vận hành.

## Feature E13-F01: Job monitoring
### Tasks
- API jobs list
- UI health/jobs screen
- Thống kê success/failure

## Feature E13-F02: System health
### Tasks
- Health endpoint
- Check DB/queue/service status
- UI hiển thị health summary

## Feature E13-F03: Audit log viewer
### Tasks
- API lấy audit logs
- UI bảng audit logs cơ bản

## Feature E13-F04: Delivery monitoring
### Tasks
- Tổng hợp log delivery
- Lọc failed deliveries

### DoD cho Epic E13
- Admin nhìn được tình trạng ingest/process/delivery
- Có health summary cho vận hành

---

# 75. Epic E14 - Action Workflow & External Integrations

## Mục tiêu
Biến insight thành hành động và tích hợp công cụ bên ngoài.

## Feature E14-F01: Create task from insight
### Phase
- Phase 3
### Tasks
- Nút create task trên insight detail
- Mapping dữ liệu sang task payload
- Tích hợp Jira/Planner/Asana tùy chọn

## Feature E14-F02: Follow-up workflow
### Tasks
- Trạng thái follow-up
- Assigned owner
- Due date

## Feature E14-F03: SOP impact suggestion
### Tasks
- Mapping insight -> internal document/process
- Gợi ý review SOP/policy

---

# 76. Epic E15 - Reporting & Executive Pack

## Mục tiêu
Tạo báo cáo định kỳ cho lãnh đạo và stakeholders.

## Feature E15-F01: Executive weekly report
### Phase
- Phase 3
### Tasks
- Tổng hợp top risks/opportunities
- Tạo executive summary
- Render PDF/slide output

## Feature E15-F02: Trend reporting
### Tasks
- Báo cáo chủ đề tăng mạnh
- Báo cáo nguồn nổi bật
- Báo cáo department impact trend

---

# 77. Epic E16 - QA, UAT, Release & Handover

## Mục tiêu
Đảm bảo chất lượng trước go-live và bàn giao đầy đủ.

## Feature E16-F01: Test planning
### Tasks
- Viết test cases theo module
- Viết UAT scenarios
- Chuẩn bị dữ liệu test

## Feature E16-F02: Automated testing baseline
### Tasks
- Unit test backend
- Component/UI test frontend cơ bản
- API test smoke

## Feature E16-F03: UAT execution
### Tasks
- Chạy UAT với business owner
- Ghi nhận defects
- Chốt pass/fail

## Feature E16-F04: Release checklist
### Tasks
- Checklist deploy
- Checklist rollback
- Checklist config production

## Feature E16-F05: Handover package
### Tasks
- Repo handover
- Architecture doc handover
- Admin guide
- User guide
- Operations guide

### DoD cho Epic E16
- Có test report
- Có UAT sign-off hoặc tương đương
- Có handover package đầy đủ

---

# 78. Ưu tiên triển khai theo MoSCoW

## Must Have (Phase 1)
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

## Should Have
- Executive dashboard nâng cao
- Search tốt hơn
- Feedback analytics
- Test ingest preview đẹp hơn

## Could Have
- Multi-language role summaries nâng cao
- Advanced source simulation
- Rich trend analytics

## Won’t Have in phase 1
- Task integration sâu
- SOP impact automation
- Full chatbot with memory and advanced retrieval
- PDF/slide executive auto pack hoàn chỉnh

---

# 79. Dependency map chính

## Nhóm phụ thuộc nền
- E01 là nền cho toàn bộ epic khác
- E02 cần trước E09, E10, E12, E13 admin

## Nhóm ingest đến insight
- E03 -> E04 -> E05 -> E06 -> E07 -> E08 -> E09/E10/E12

## Nhóm delivery
- E07 + E08 cần trước E10

## Nhóm chatbot
- E08 search/index cần trước E12
- E06/E07 chất lượng đủ tốt trước E12

## Nhóm báo cáo/action workflow
- E08 + E09 + E10 + E11 cần trưởng thành trước E14/E15

---

# 80. Sprint gợi ý cho Phase 1

## Sprint 0 - Setup
- E01 foundation
- E02 auth skeleton
- DB schema draft
- Architecture lock

## Sprint 1 - Source + Ingest
- E03 source management API/UI
- E04 scheduler + RSS connector + raw storage
- E13 job log basic

## Sprint 2 - Normalize + Insight
- E05 normalize/dedup basic
- E06 classify/summary/insight creation
- E07 trust/impact rule v1

## Sprint 3 - Dashboard + Detail
- E08 insights API
- E09 dashboard overview/list/detail
- E11 feedback basic

## Sprint 4 - Delivery + Admin Ops
- E10 email/Teams digest
- E13 health/jobs UI
- UAT round 1

## Sprint 5 - Stabilize & Go-live
- Fix bug
- Improve scoring/routing
- UAT round 2
- Release/handover

---

# 81. Backlog chi tiết cho Phase 1 theo đội

## 81.1 Backend
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

## 81.2 Frontend
- Login page
- App shell
- Dashboard overview
- Insight list page
- Insight detail page
- Source management page
- Delivery rules page cơ bản
- Jobs/health page
- Feedback UI

## 81.3 Data/AI
- Taxonomy v1
- Prompt/pipeline cho classify
- Prompt/pipeline cho summary
- Rule impact mapping v1
- Trust scoring factors v1
- Quality evaluation sample set

## 81.4 QA
- Test plan
- Test cases source/ingest/insight/dashboard/delivery
- Regression checklist
- UAT support

## 81.5 DevOps
- Dev/test/prod env
- CI baseline
- Secret/env management
- Logging/health check setup
- Deploy script/checklist

---

# 82. Definition of Done tổng quát

Một feature được coi là hoàn thành khi:
1. Code đã được review và merge
2. Unit test hoặc test phù hợp đã chạy đạt
3. API hoặc UI đáp ứng acceptance criteria
4. Logging lỗi cơ bản đã có nếu là backend/process
5. Tài liệu cấu hình hoặc note kỹ thuật đã cập nhật
6. QA xác nhận pass ở môi trường test
7. Nếu là business-facing feature thì đã có UAT hoặc review tương đương

---

# 83. Rủi ro triển khai theo backlog

## R1. Scope creep
Biện pháp:
- Chốt Must Have phase 1
- Không thêm chatbot đầy đủ vào phase 1

## R2. Chất lượng source parser không ổn định
Biện pháp:
- Ưu tiên RSS/API/official sources trước
- Có test ingest preview

## R3. Output AI chưa đủ tốt
Biện pháp:
- Dùng rule + AI kết hợp
- Làm bộ sample evaluation ngay từ sprint 2

## R4. Digest spam hoặc kém hữu ích
Biện pháp:
- Chỉ digest theo nhóm đối tượng rõ
- Gắn feedback loop từ phase 1

## R5. Admin UI quá tải chức năng
Biện pháp:
- Phase 1 chỉ build source + rule + jobs cơ bản

---

# 84. Cách chuyển backlog này sang công cụ quản lý công việc

## Gợi ý cấu trúc Jira/Trello/Planner
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

---

# 85. Kết luận phần backlog implementation

Phần này đã biến bộ tài liệu từ mức **thiết kế giải pháp** sang mức **chuẩn bị triển khai thực tế**. Sau bước này, dự án đã có đủ nền để:
- chốt scope phase 1
- chia sprint
- giao việc theo đội
- estimate nguồn lực
- chuẩn bị UAT/go-live

Bộ tài liệu hiện tại đã bao gồm:
- BRD
- FRD
- BFD/flow
- kiến trúc hệ thống
- module và thành phần
- UI flow / wireframe
- ERD / schema định hướng
- API contract sơ bộ
- backlog implementation chi tiết

---

# 86. Source Strategy và Source Catalog v1

## 86.1 Mục tiêu của source strategy
Xây dựng danh mục nguồn đủ rộng để phát hiện tín hiệu quan trọng nhưng đủ chặt để đảm bảo:
- độ tin cậy
- khả năng truy vết
- khả năng tích hợp kỹ thuật
- khả năng vận hành ổn định
- tính phù hợp với doanh nghiệp

## 86.2 Nguyên tắc chọn nguồn
1. Ưu tiên nguồn chính thức hoặc có thẩm quyền cao
2. Ưu tiên nguồn có cấu trúc tốt: RSS, API, changelog, release notes, docs hub
3. Tách rõ nguồn “fact source” và nguồn “signal source”
4. Không để nguồn cộng đồng đi thẳng thành alert critical nếu chưa được corroborate
5. Phase 1 chỉ chọn nguồn có giá trị cao, ít nhiễu, dễ vận hành

## 86.3 Phân tầng nguồn
### Tier A - Official / Regulatory / Primary Source
- Website chính thức của vendor/platform
- Docs/changelog/release note chính thức
- Cổng thông tin chính phủ, cơ quan quản lý, cơ sở dữ liệu pháp luật chính thức
- Cơ sở dữ liệu học thuật hoặc metadata chính thống

### Tier B - Professional / Curated Technical Source
- Nguồn kỹ thuật uy tín, chuyên ngành, cộng đồng nghề nghiệp chính thống
- Tạp chí/kênh kỹ thuật thuộc tổ chức chuyên môn lớn

### Tier C - Community Signal Source
- Hacker News, Stack Exchange, Reddit, cộng đồng kỹ thuật mở
- Dùng để bắt tín hiệu sớm, pain point, phản ứng cộng đồng

### Tier D - Internal Source
- SOP nội bộ
- Danh sách tool đang dùng
- Repo nội bộ
- Tài liệu quy trình nội bộ
- mapping team/system/process

---

# 87. Danh mục nguồn chi tiết theo nhóm

## 87.1 Nhóm Official AI / Model Vendor / Platform

### S01. OpenAI News
- **Loại**: Official vendor
- **Mục đích**: Theo dõi thông báo công ty, sản phẩm, an toàn, bảo mật, enterprise, agents SDK, model update
- **Loại dữ liệu nên lấy**: title, category, publish date, URL, summary sơ bộ
- **Tích hợp khuyến nghị**: parser web/RSS nếu có feed phù hợp
- **Trust tier mặc định**: Very High
- **Broadcast policy**: Có thể broadcast rộng nếu impact phù hợp
- **Ưu tiên Phase 1**: Rất cao

### S02. OpenAI Homepage / Product pages / Docs hub
- **Loại**: Official vendor
- **Mục đích**: Theo dõi product launch, docs changes, platform capability change
- **Trust tier**: Very High
- **Ưu tiên**: Cao

### S03. Anthropic Newsroom
- **Loại**: Official vendor
- **Mục đích**: Theo dõi model launch, policy, enterprise/security initiative, Claude ecosystem
- **Trust tier**: Very High
- **Ưu tiên**: Cao

### S04. Google AI / Google Blog - AI
- **Loại**: Official vendor
- **Mục đích**: Theo dõi AI announcements, AI Studio, Gemini, research applications
- **Trust tier**: Very High
- **Ưu tiên**: Cao

### S05. Google DeepMind Blog
- **Loại**: Official research/vendor
- **Mục đích**: Theo dõi breakthrough, model, safety, science collaboration
- **Trust tier**: Very High
- **Ưu tiên**: Cao

### S06. Google Developers Blog
- **Loại**: Official developer platform
- **Mục đích**: Theo dõi API/tooling/platform updates tác động dev
- **Trust tier**: Very High
- **Ưu tiên**: Cao

### S07. Google Search Central News
- **Loại**: Official SEO/Search source
- **Mục đích**: Theo dõi thay đổi Search/SEO/documentation/chính sách hiển thị nội dung
- **Trust tier**: Very High
- **Ưu tiên**: Rất cao nếu có content/SEO team

### S08. Google Search Central Documentation Updates
- **Loại**: Official changelog
- **Mục đích**: Theo dõi thay đổi docs SEO/Search có thể tác động content/marketing/web team
- **Trust tier**: Very High
- **Ưu tiên**: Cao

### S09. Microsoft Learn
- **Loại**: Official docs
- **Mục đích**: Theo dõi Microsoft AI, Azure, Teams, security, admin guidance
- **Trust tier**: Very High
- **Ưu tiên**: Rất cao nếu doanh nghiệp dùng Microsoft ecosystem

### S10. Microsoft Tech Community
- **Loại**: Official community/professional
- **Mục đích**: Theo dõi cập nhật chuyên sâu, thông báo kỹ thuật, community guidance của Microsoft
- **Trust tier**: High
- **Ưu tiên**: Cao

### S11. Meta Newsroom
- **Loại**: Official vendor
- **Mục đích**: Theo dõi AI product, platform, policy, enterprise announcements từ Meta
- **Trust tier**: Very High
- **Ưu tiên**: Trung bình-Cao

### S12. Meta AI
- **Loại**: Official AI product presence
- **Mục đích**: Theo dõi khả năng, positioning và thay đổi sản phẩm AI của Meta
- **Trust tier**: High
- **Ưu tiên**: Trung bình

### S13. AWS Machine Learning Blog
- **Loại**: Official cloud/vendor
- **Mục đích**: Theo dõi AI/ML platform, infrastructure, production guidance
- **Trust tier**: Very High
- **Ưu tiên**: Cao

### S14. AWS What's New
- **Loại**: Official product update source
- **Mục đích**: Theo dõi dịch vụ mới, thay đổi pricing/capability/availability
- **Trust tier**: Very High
- **Ưu tiên**: Cao

### S15. Google Cloud Blog
- **Loại**: Official cloud/vendor
- **Mục đích**: Theo dõi AI infrastructure, Vertex AI, cloud platform changes
- **Trust tier**: Very High
- **Ưu tiên**: Cao

### S16. NVIDIA Blog
- **Loại**: Official vendor
- **Mục đích**: Theo dõi GPU/AI infra/model ecosystem announcements
- **Trust tier**: Very High
- **Ưu tiên**: Cao với team AI/hạ tầng

### S17. Cloudflare Blog
- **Loại**: Official vendor
- **Mục đích**: Theo dõi network, security, edge, AI gateway, web platform changes
- **Trust tier**: Very High
- **Ưu tiên**: Trung bình-Cao

### S18. GitHub Changelog
- **Loại**: Official platform changelog
- **Mục đích**: Theo dõi thay đổi API, repo, actions, developer workflow
- **Trust tier**: Very High
- **Ưu tiên**: Rất cao

### S19. GitHub REST API Docs
- **Loại**: Official docs/API
- **Mục đích**: Connector chuẩn để lấy release/repo metadata/issues/discussions nếu được dùng
- **Trust tier**: Very High
- **Ưu tiên**: Rất cao

### S20. GitHub Repository Releases (theo repo chọn lọc)
- **Loại**: Official repo source
- **Mục đích**: Theo dõi release note của framework/tool mà công ty đang dùng
- **Trust tier**: Very High
- **Ưu tiên**: Rất cao

---

## 87.2 Nhóm pháp lý, quy định, chính sách

### S21. Hệ thống văn bản Chính phủ Việt Nam (vanban.chinhphu.vn)
- **Loại**: Official government source
- **Mục đích**: Theo dõi nghị định, quyết định, chỉ thị, văn bản quy phạm pháp luật và văn bản điều hành
- **Trust tier**: Very High
- **Broadcast policy**: Có thể dùng làm nguồn gốc pháp lý chính
- **Ưu tiên**: Rất cao

### S22. Cổng Pháp luật Quốc gia / Bộ Tư pháp
- **Loại**: Official legal portal
- **Mục đích**: Theo dõi tra cứu văn bản, hiệu lực, văn bản liên quan
- **Trust tier**: Very High
- **Ưu tiên**: Rất cao

### S23. Cơ sở dữ liệu Luật Việt Nam của Quốc hội (vietlaw.quochoi.vn)
- **Loại**: Official legislative source
- **Mục đích**: Theo dõi luật, nghị quyết, tình trạng văn bản, dữ liệu pháp lý chính thống
- **Trust tier**: Very High
- **Ưu tiên**: Rất cao

### S24. Thư Viện Pháp Luật
- **Loại**: Curated legal reference
- **Mục đích**: Tra cứu nhanh, hệ thống hóa, theo dõi cách diễn giải/tổng hợp văn bản
- **Trust tier**: High
- **Lưu ý**: Không thay thế nguồn chính thức cho insight critical
- **Ưu tiên**: Cao

### S25. CISA Cybersecurity Advisories
- **Loại**: Official government security advisories
- **Mục đích**: Theo dõi cảnh báo an ninh mạng, zero-day, exploited vulnerabilities, threat campaigns
- **Trust tier**: Very High
- **Ưu tiên**: Cao nếu công ty có nhu cầu security/compliance

### S26. NIST NVD
- **Loại**: Official vulnerability database
- **Mục đích**: Theo dõi CVE, severity, impact metrics, vulnerability metadata
- **Trust tier**: Very High
- **Ưu tiên**: Cao nếu liên quan devops/security

### S27. OWASP
- **Loại**: Professional security source
- **Mục đích**: Best practices, top risks, application security guidance
- **Trust tier**: High
- **Ưu tiên**: Trung bình-Cao

---

## 87.3 Nhóm học thuật và nghiên cứu

### S28. arXiv
- **Loại**: Scholarly preprint archive
- **Mục đích**: Theo dõi paper mới về AI/ML/data/science/engineering
- **Tích hợp khuyến nghị**: arXiv API
- **Trust tier**: High cho research signal, không mặc định là production fact
- **Ưu tiên**: Cao

### S29. Crossref REST API
- **Loại**: Scholarly metadata source
- **Mục đích**: DOI, metadata, abstract, update, retraction/correction link, publication metadata
- **Trust tier**: Very High cho metadata
- **Ưu tiên**: Cao

### S30. Nature
- **Loại**: Peer-reviewed research publisher
- **Mục đích**: Theo dõi paper, commentary, science breakthrough ảnh hưởng công nghệ/AI
- **Trust tier**: Very High
- **Ưu tiên**: Trung bình-Cao

### S31. Science / ScienceDirect / AI Journal (AIJ)
- **Loại**: Scholarly journal ecosystem
- **Mục đích**: Theo dõi kết quả nghiên cứu, bài review, xu hướng AI chính thống
- **Trust tier**: Very High
- **Ưu tiên**: Trung bình

### S32. ACM TechNews
- **Loại**: Professional curated tech digest
- **Mục đích**: Theo dõi tin công nghệ dành cho chuyên gia máy tính, được ACM tổng hợp định kỳ
- **Trust tier**: High
- **Ưu tiên**: Trung bình-Cao

### S33. IEEE Spectrum
- **Loại**: Professional engineering publication
- **Mục đích**: Theo dõi công nghệ, AI, hạ tầng, engineering trends, deep analysis
- **Trust tier**: High
- **Ưu tiên**: Cao

---

## 87.4 Nhóm tech press / business-tech press uy tín

### S34. Reuters Technology / Reuters business-tech reporting
- **Loại**: Global newswire / business-tech press
- **Mục đích**: Theo dõi tin công nghệ, chính sách, doanh nghiệp, M&A, regulation, sự kiện lớn
- **Trust tier**: High
- **Ưu tiên**: Cao

### S35. Associated Press (AP)
- **Loại**: News wire
- **Mục đích**: Theo dõi tin tức chính thống tốc độ cao, đặc biệt các sự kiện công nghệ/policy lớn
- **Trust tier**: High
- **Ưu tiên**: Trung bình

### S36. Ars Technica
- **Loại**: Tech journalism
- **Mục đích**: Tin công nghệ, AI, policy, security, systems, explainers kỹ thuật
- **Trust tier**: High
- **Ưu tiên**: Cao

### S37. The Verge
- **Loại**: Mainstream tech media
- **Mục đích**: Theo dõi tech news, AI, product moves, platform changes, policy narratives
- **Trust tier**: Medium-High
- **Ưu tiên**: Trung bình-Cao

### S38. WIRED
- **Loại**: Tech/science/business media
- **Mục đích**: Theo dõi xu hướng, điều tra, phân tích, long-form về AI và công nghệ
- **Trust tier**: Medium-High
- **Ưu tiên**: Trung bình

### S39. TechCrunch
- **Loại**: Startup/tech media
- **Mục đích**: Theo dõi startup, AI companies, funding, product launches, ecosystem moves
- **Trust tier**: Medium-High
- **Ưu tiên**: Trung bình

---

## 87.5 Nhóm cộng đồng kỹ thuật, diễn đàn, group mở

### S40. Hacker News
- **Loại**: Community signal
- **Mục đích**: Bắt tín hiệu sớm về tooling, AI, infra, startup tech, phản ứng cộng đồng kỹ thuật
- **Tích hợp**: HN API chính thức
- **Trust tier**: Medium
- **Broadcast policy**: Không dùng làm sole source cho critical alerts
- **Ưu tiên**: Cao

### S41. Stack Exchange / Stack Overflow
- **Loại**: Professional community Q&A
- **Mục đích**: Theo dõi pain points thực tế, lỗi phổ biến, xu hướng adoption, câu hỏi nhiều quan tâm
- **Tích hợp**: Stack Exchange API
- **Trust tier**: Medium-High cho vấn đề kỹ thuật thực hành
- **Ưu tiên**: Cao

### S42. Reddit (theo subreddit whitelist)
- **Loại**: Community signal
- **Mục đích**: Theo dõi phản ứng cộng đồng, use case thực tế, phàn nàn/pain point, trend
- **Tích hợp**: Reddit Data API theo terms
- **Trust tier**: Medium-Low
- **Lưu ý**: Chỉ dùng theo whitelist subreddit; cần tuân thủ terms
- **Ưu tiên**: Trung bình

### S43. GitHub Discussions / Issues (theo repo chọn lọc)
- **Loại**: Community + repo-operational signal
- **Mục đích**: Theo dõi bug nóng, regression, community pain point, feature requests
- **Trust tier**: Medium-High nếu thuộc repo chính thức
- **Ưu tiên**: Trung bình-Cao

### S44. Microsoft Tech Community forums/blog hubs
- **Loại**: Official-professional community
- **Mục đích**: Theo dõi vấn đề vận hành thật, triển khai enterprise, guidance từ cộng đồng chuyên môn
- **Trust tier**: High
- **Ưu tiên**: Cao với hệ sinh thái Microsoft

### S45. Dev.to / Hashnode / Medium (whitelist tác giả)
- **Loại**: Community publishing
- **Mục đích**: Theo dõi best practice thực chiến, giải pháp triển khai, tutorial adoption
- **Trust tier**: Medium
- **Lưu ý**: Chỉ nên whitelist tác giả/domain có chất lượng
- **Ưu tiên**: Thấp-Trung bình cho phase 1

---

## 87.6 Nhóm nguồn nội bộ cần có để impact analysis chính xác

### S46. Danh mục công cụ và nền tảng công ty đang sử dụng
- **Loại**: Internal source
- **Mục đích**: Map thay đổi từ ngoài vào đúng hệ thống nội bộ
- **Trust tier**: Very High
- **Ưu tiên**: Rất cao

### S47. Danh mục repo, framework, dependency chiến lược nội bộ
- **Loại**: Internal source
- **Mục đích**: Xác định repo/ứng dụng nào chịu tác động từ release, CVE, deprecation
- **Ưu tiên**: Rất cao

### S48. SOP / Quy trình vận hành / Quy trình phát triển phần mềm
- **Loại**: Internal source
- **Mục đích**: Gợi ý SOP nào cần review khi insight xuất hiện
- **Ưu tiên**: Cao

### S49. Danh mục phòng ban, vai trò, owner hệ thống
- **Loại**: Internal source
- **Mục đích**: Routing digest và impact mapping
- **Ưu tiên**: Rất cao

### S50. Policy nội bộ về AI, dữ liệu, bảo mật, truyền thông
- **Loại**: Internal source
- **Mục đích**: So khớp thay đổi bên ngoài với quy định nội bộ hiện tại
- **Ưu tiên**: Cao

---

# 88. Community groups và kênh mở nên whitelist theo chủ đề

## 88.1 Nhóm community nên dùng ở Phase 2 hoặc làm watchlist
### AI/ML
- Hacker News các thread AI/LLM/tooling
- Reddit: r/MachineLearning, r/LocalLLaMA, r/artificial, r/LanguageTechnology (nếu còn hoạt động phù hợp)
- GitHub Discussions của các repo AI lớn mà công ty đang dùng

### Dev / Software Engineering
- Stack Overflow tags theo framework/tool đang dùng
- Hacker News thread về platform release, infra, dev tools
- GitHub Issues/Discussions của framework quan trọng

### SEO / Content / Search
- Google Search Central news là nguồn chính
- Có thể theo dõi thêm community thảo luận mở sau phase 1, nhưng không nên đưa Facebook group vào connector chính ngay

### Security
- CISA/NVD là nguồn chính
- Cộng đồng chuyên môn chỉ dùng như watchlist hoặc enrichment

## 88.2 Nhóm community chưa khuyến nghị làm connector Phase 1
- Facebook Groups (do khó tích hợp ổn định, khó chuẩn hóa, khó governance)
- Community đóng hoặc private forum không có access policy rõ ràng
- Nguồn chỉ có giá trị cảm tính/viral nhưng ít metadata

---

# 89. Source Catalog v1 đề xuất chính thức

## 89.1 Danh sách ưu tiên Phase 1 (khuyến nghị 25 nguồn đầu tiên)
### Nhóm bắt buộc
1. OpenAI News
2. OpenAI docs/product pages
3. Anthropic Newsroom
4. Google AI Blog
5. Google DeepMind Blog
6. Google Developers Blog
7. Google Search Central News
8. Google Search Central Documentation Updates
9. Microsoft Learn
10. Microsoft Tech Community
11. GitHub Changelog
12. GitHub Releases của repo trọng yếu
13. GitHub REST API Docs
14. AWS What's New
15. AWS ML Blog
16. Google Cloud Blog
17. Cloudflare Blog
18. NVIDIA Blog
19. vanban.chinhphu.vn
20. Cổng Pháp luật/Bộ Tư pháp
21. vietlaw.quochoi.vn
22. Thư Viện Pháp Luật
23. arXiv API
24. Crossref REST API
25. Hacker News API

### Nhóm nên có nếu đủ nguồn lực Phase 1
26. Stack Exchange API
27. CISA Advisories
28. NIST NVD
29. IEEE Spectrum
30. ACM TechNews

## 89.2 Danh sách Phase 2
31. Reddit whitelist subreddits
32. GitHub Discussions/Issues theo repo
33. Meta Newsroom
34. Meta AI
35. Ars Technica
36. Reuters Technology
37. AP
38. WIRED
39. The Verge
40. TechCrunch

---

# 90. Source metadata schema khuyến nghị cho catalog

Mỗi nguồn trong catalog nên có các trường:
- source_code
- source_name
- source_group
- source_type
- authority_level
- trust_tier_default
- target_departments
- target_topics
- purpose
- access_method
- ingest_method
- crawl_frequency
- verification_policy
- broadcast_policy
- geo_scope
- language
- phase_priority
- owner_internal
- notes

Ví dụ:
- source_code: S07
- source_name: Google Search Central News
- source_group: Official Tech/SEO
- source_type: official
- authority_level: primary
- trust_tier_default: Very High
- target_departments: Content, Marketing, Web, Product
- target_topics: SEO, Search, Policy
- purpose: Theo dõi thay đổi Search và SEO
- access_method: web/docs/news page
- ingest_method: parser/changelog capture
- crawl_frequency: daily
- verification_policy: not required for official source
- broadcast_policy: digest + alert theo impact
- phase_priority: P1

---

# 91. Chính sách sử dụng nguồn theo governance

## 91.1 Chính sách broadcast
- Tier A có thể sinh insight production trực tiếp
- Tier B có thể sinh insight production nếu nội dung rõ và có relevance cao
- Tier C chỉ sinh watchlist hoặc digest nội bộ nếu chưa có nguồn corroborate
- Tier D dùng để map impact, không phải nguồn broadcast ra bên ngoài tổ chức

## 91.2 Chính sách xác minh chéo
- Pháp lý/compliance critical: luôn ưu tiên nguồn chính thức và giữ link nguồn gốc
- Community signal high impact: cần ít nhất một nguồn chính thức hoặc nguồn chuyên môn mạnh corroborate trước khi alert rộng
- Research signal: không tự suy diễn thành “nên áp dụng ngay”; cần đi qua logic impact riêng

## 91.3 Chính sách phase
- Phase 1: chỉ dùng catalog v1 đã whitelist
- Phase 2: thêm community có kiểm soát và media chất lượng cao
- Phase 3: thêm internal mapping sâu và workflow hành động

---

# 92. Kết luận phần source catalog

Source Catalog v1 của AI Impact Radar nên bắt đầu bằng một tập nguồn nhỏ nhưng chất lượng cao, chia rõ vai trò của từng nguồn:
- nguồn gốc chính thức để xác thực và broadcast
- nguồn kỹ thuật/chuyên môn để bổ sung bối cảnh
- nguồn cộng đồng để phát hiện tín hiệu sớm
- nguồn nội bộ để map tác động vào doanh nghiệp

Nếu triển khai đúng theo catalog này, hệ thống sẽ tránh được 3 rủi ro lớn nhất:
1. ngập nhiễu
2. thiếu truy vết
3. gửi sai người/sai mức độ

Phần tiếp theo có thể làm là chuẩn hóa danh mục này thành bảng vận hành thực tế dạng spreadsheet với các cột metadata, crawl policy, trust tier và phase priority để import vào hệ thống quản trị nguồn.

