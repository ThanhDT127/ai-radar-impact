## ADDED Requirements

### Requirement: Xếp hạng lai vector + lexical qua RRF, không ngưỡng

Ở chế độ toàn cục (và ở phần mở rộng của chế độ per‑insight), tầng độ‑liên‑quan của xếp hạng SHALL trộn hai
tín hiệu: **tương đồng ngữ nghĩa** (cosine giữa embedding câu hỏi và embedding insight) và **so khớp từ khoá**
(độ liên quan lexical theo biên từ), bằng **Reciprocal Rank Fusion** dạng `1/(60 + rank)`. Điểm RRF SHALL là
khoá xếp hạng chính; `delivery_engine.score_for_role()` SHALL giữ vai trò khoá phụ; và service SHALL cắt
`chat_index_top_k` **sau** khi xếp hạng.

Service SHALL KHÔNG áp ngưỡng similarity cứng để loại tin: vector chỉ dùng để **xếp hạng tốt hơn**, không để
lọc, nên tập candidate SHALL KHÔNG bao giờ rỗng vì lý do độ tương đồng thấp.

#### Scenario: Câu hỏi ngữ nghĩa lệch từ khoá
- **WHEN** người dùng hỏi bằng từ ngữ khác với chữ trong tin (ví dụ "cắt giảm nhân sự" trong khi tin ghi *layoff*)
- **THEN** tin liên quan về ngữ nghĩa vẫn được xếp đủ cao để nằm trong index top‑K, không bị cắt vì không trùng từ khoá

#### Scenario: Không có ngưỡng loại tin
- **WHEN** không tin nào đạt độ tương đồng vector cao
- **THEN** service vẫn xếp hạng và trả về top‑K tin tốt nhất theo RRF, không trả về danh sách rỗng vì ngưỡng

#### Scenario: Khớp chính xác vẫn được giữ nhờ tầng lexical
- **WHEN** câu hỏi chứa một định danh chính xác (tên model, số phiên bản, mã lỗi)
- **THEN** tín hiệu lexical trong RRF vẫn đẩy tin chứa đúng chuỗi đó lên, không bị vector làm loãng

### Requirement: Duy trì embedding cho insight và suy giảm êm khi embedding vắng

Hệ thống SHALL sinh và lưu một vector embedding cho mỗi insight khi insight được publish, và SHALL cho phép
backfill embedding cho insight đã có. Việc sinh embedding SHALL dùng cùng nhà cung cấp Vertex với chiều cố
định, và SHALL KHÔNG dùng ngân sách quota của generation.

Khi embedding của câu hỏi không tạo được (lỗi/timeout) hoặc khi một insight chưa có embedding, service SHALL
suy giảm êm: xếp hạng bằng tầng lexical mà KHÔNG làm hỏng câu trả lời. Lỗi sinh embedding của một insight
SHALL KHÔNG chặn việc tạo insight đó.

#### Scenario: Embedding câu hỏi lỗi
- **WHEN** lời gọi sinh embedding cho câu hỏi thất bại
- **THEN** service xếp hạng bằng tầng lexical và vẫn trả lời được; không trả lỗi cho người dùng

#### Scenario: Insight chưa có embedding
- **WHEN** một insight `published` chưa được backfill embedding (embedding NULL)
- **THEN** insight đó vẫn tham gia xếp hạng qua tầng lexical và không bị loại khỏi tập candidate

#### Scenario: Lỗi embedding khi publish insight
- **WHEN** sinh embedding thất bại lúc publish một insight
- **THEN** insight vẫn được tạo với embedding NULL và hệ thống ghi cảnh báo, không làm hỏng pipeline analysis
