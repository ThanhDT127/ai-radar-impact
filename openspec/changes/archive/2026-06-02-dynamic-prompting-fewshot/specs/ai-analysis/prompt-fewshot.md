## MODIFIED Requirements

### Requirement: Nâng cấp chất lượng dịch và tóm tắt của AI qua Prompting nâng cao

Hệ thống phân tích AI (Module M4 - AI Analysis) MUST sử dụng prompt hệ thống đã nâng cấp, áp dụng Negative Constraints và Few-shot Prompting để loại bỏ văn phong dịch máy rập khuôn và tạo ra các bản tóm tắt tiếng Việt tự nhiên, chuyên nghiệp.

#### Scenario: Thực thi ràng buộc tiêu cực (Negative Constraints)
- **WHEN** mô hình Gemini tiến hành phân tích văn bản và sinh các trường nội dung tiếng Việt (`summary_short`, `signal`, `why_it_matters`, `so_what`, `recommendations`)
- **THEN** output của mô hình MUST không chứa bất kỳ cụm từ mở đầu sáo rỗng nào trong danh sách cấm (ví dụ: "Đối với các team...", "Điều này quan trọng vì...", "Bài viết này nói về...")
- **AND** câu văn SHALL đi thẳng trực tiếp vào nội dung kỹ thuật hoặc hành động cụ thể

#### Scenario: Sử dụng thuật ngữ chuyên ngành tự nhiên
- **WHEN** AI dịch và phân tích các bài viết kỹ thuật chứa thuật ngữ công nghệ phổ biến
- **THEN** mô hình SHALL giữ nguyên các thuật ngữ tiếng Anh thông dụng (như pipeline, CI/CD, API, container, cloud, framework) thay vì dịch sang tiếng Việt gượng ép hoặc tối nghĩa

#### Scenario: Bảo toàn định dạng JSON schema đầu ra
- **WHEN** mô hình Gemini trả về kết quả phân tích dưới dạng JSON string
- **THEN** kết quả trả về MUST tuân thủ chính xác 100% cấu trúc schema định sẵn (bao gồm các trường: title, summary_short, summary_medium, signal, why_it_matters, so_what, urgency, momentum, intelligence_tier, adoption_ring, affected_roles, recommendations...)
- **AND** hệ thống SHALL phân tích và lưu trữ thành công vào Database mà không gặp bất kỳ lỗi parse JSON hay ValidationError nào
