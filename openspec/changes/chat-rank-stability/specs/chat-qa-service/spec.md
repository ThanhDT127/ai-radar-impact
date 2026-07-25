## ADDED Requirements

### Requirement: Trục xếp hạng theo vai trò nhận diện vai trò theo biên từ

Khi câu hỏi nêu tên một vai trò trong `ALLOWED_ROLES`, tầng độ quan trọng SHALL xếp hạng theo trục vai trò
đó thay vì theo `affected_roles` của từng tin. Việc nhận diện tên vai trò trong câu hỏi SHALL khớp **theo
biên từ**: tên vai trò được tách thành dãy token bằng cùng quy tắc tách token dùng cho từ khoá, và SHALL
chỉ tính là khớp khi dãy token đó xuất hiện **liên tiếp và trọn vẹn** trong dãy token của câu hỏi.

Service SHALL KHÔNG suy ra vai trò từ chuỗi con nằm bên trong một từ khác. Service SHALL ghi log mức DEBUG
trục xếp hạng đã chọn cho mỗi câu hỏi ở chế độ toàn cục.

*Ghi chú:* yêu cầu này chi phối cả việc tính danh sách vai trò không có tin nào ảnh hưởng tới — nhận diện
sai vai trò dẫn tới tuyên bố sai về khoảng trống dữ liệu.

#### Scenario: Tên vai trò là chuỗi con của một từ khác
- **WHEN** người dùng hỏi "tin về device IoT mới"
- **THEN** service SHALL KHÔNG nhận diện vai trò `Dev`
- **AND** thứ tự xếp hạng rơi về mức quan trọng cao nhất trên `affected_roles` của từng tin

#### Scenario: Từ thuộc taxonomy khác chứa tên vai trò
- **WHEN** người dùng hỏi "DevOps cần chú ý gì"
- **THEN** service SHALL KHÔNG nhận diện vai trò `Dev` (`DevOps` thuộc taxonomy `Source.target_roles`,
  không thuộc `ALLOWED_ROLES`)

#### Scenario: Tên vai trò một từ đứng riêng
- **WHEN** người dùng hỏi "Dev cần làm gì tuần này"
- **THEN** service SHALL nhận diện vai trò `Dev` và xếp hạng theo trục đó

#### Scenario: Tên vai trò gồm nhiều từ
- **WHEN** người dùng hỏi câu chứa "Data Analyst" hoặc "Người dùng phổ thông"
- **THEN** service SHALL nhận diện đúng vai trò đó, khớp trọn cụm nhiều từ

#### Scenario: Câu hỏi không nêu vai trò nào
- **WHEN** người dùng hỏi "có gì mới không"
- **THEN** service SHALL KHÔNG chọn trục vai trò nào
- **AND** xếp hạng theo mức quan trọng cao nhất trên `affected_roles` của từng tin, mặc định `Toàn công ty`
  khi tin không có vai trò nào

#### Scenario: Ghi lại trục đã chọn
- **WHEN** service xử lý một câu hỏi ở chế độ toàn cục
- **THEN** service ghi log mức DEBUG nêu vai trò được nhận diện (hoặc việc không nhận diện được vai trò nào)
