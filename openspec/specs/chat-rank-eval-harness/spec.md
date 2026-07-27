# chat-rank-eval-harness Specification

## Purpose
TBD - created by archiving change chat-rank-stability. Update Purpose after archive.
## Requirements
### Requirement: Benchmark xếp hạng tự chứa, không phụ thuộc dữ liệu sống

Bộ đo chất lượng xếp hạng chat SHALL lưu đủ đầu vào để tái lập trong repo: mỗi mẫu insight gồm định danh
và toàn bộ field mà `_rank()` đọc — `title`, `signal`, `so_what`, `summary_short`, `topics`,
`affected_roles` (tầng độ liên quan) và `recommendations`, `impact_label`, `practical_indicators`,
`actionability_score`, `intelligence_tier`, `trust_score`, `published_at`, `created_at` (tầng độ quan
trọng). Bộ đo SHALL chạy được khi database không tồn tại, rỗng, hoặc các insight tương ứng đã bị xoá.

Bộ đo SHALL dựng lại mẫu thành thực thể `Insight` thật ở trạng thái tách rời session, SHALL KHÔNG dùng
đối tượng giả chấp nhận thuộc tính tuỳ ý.

#### Scenario: Chạy khi không có database
- **WHEN** người dùng chạy benchmark trong môi trường không kết nối được PostgreSQL
- **THEN** benchmark vẫn chạy trọn vẹn và in báo cáo recall từ fixture trong repo

#### Scenario: Field mà thuật toán xếp hạng đọc bị đổi tên
- **WHEN** một cột được đổi tên hoặc `score_for_role()` bắt đầu đọc field mới chưa có trong fixture
- **THEN** benchmark dừng với thông báo rõ ràng về field thiếu
- **AND** benchmark SHALL KHÔNG âm thầm đo tiếp trên dữ liệu khuyết

### Requirement: Đo recall@K trên nhãn must-have gán tay

Bộ đo SHALL đo **recall@K** — tỉ lệ insight thuộc tập `must_have` của một câu hỏi lọt vào `K` phần tử đầu
sau khi `_rank()` xếp, với `K` lấy đúng từ `settings.chat_index_top_k`. Mỗi câu hỏi SHALL kèm tập
`must_have` gán tay cùng lý do chấm cho từng phần tử.

Bộ đo SHALL KHÔNG yêu cầu gán nhãn nhị phân relevant/irrelevant cho toàn bộ corpus, và SHALL KHÔNG báo
cáo precision — chế độ hỏng cần bắt là tin hiển nhiên liên quan bị cắt khỏi index.

#### Scenario: Tin bắt buộc bị cắt khỏi index
- **WHEN** một insight thuộc `must_have` của câu hỏi bị xếp ngoài top-K
- **THEN** benchmark tính nó là miss và hạ recall của câu hỏi đó
- **AND** báo cáo nêu đích danh insight bị cắt cùng thứ hạng thực tế của nó

#### Scenario: K lấy từ cấu hình thật
- **WHEN** `settings.chat_index_top_k` được đổi
- **THEN** benchmark đo theo giá trị mới, không theo hằng số chép cứng trong bộ đo

### Requirement: Bộ đo không gọi model, chạy miễn phí và tất định

Bộ đo SHALL đo hàm xếp hạng thuần, SHALL KHÔNG gọi Vertex AI hay bất kỳ model nào, và SHALL KHÔNG tiêu
tốn quota `MAX_DAILY_CHAT_CALLS` hay `MAX_DAILY_ANALYSIS`. Chạy hai lần trên cùng fixture và cùng code
SHALL cho kết quả giống hệt nhau.

#### Scenario: Chạy trong bộ test mặc định
- **WHEN** chạy `pytest` không kèm biến môi trường đặc biệt
- **THEN** benchmark chạy đầy đủ, không bị skip, và không phát sinh lần gọi model nào

#### Scenario: Chạy lặp lại
- **WHEN** benchmark chạy hai lần liên tiếp trên fixture và code không đổi
- **THEN** hai báo cáo trùng khớp hoàn toàn

### Requirement: Bộ câu hỏi phủ các chế độ hỏng đã biết

Bộ câu hỏi SHALL phủ tối thiểu các nhóm: (a) chủ đề ngách mà tin liên quan có `recommendations[role].urgency`
thấp, (b) từ khoá ASCII ngắn hai ký tự, (c) câu hỏi nêu tên vai trò, (d) câu hỏi chứa từ mà một tên vai
trò là chuỗi con của nó, (e) câu hỏi chung chung không có từ khoá đặc trưng, (f) vai trò không có insight
nào ảnh hưởng tới.

Bộ đo SHALL ghi rõ mỗi câu hỏi thuộc nhóm nào, để khi một nhóm hồi quy thì đọc được ngay từ báo cáo.

#### Scenario: Chủ đề ngách, độ khẩn thấp
- **WHEN** benchmark chạy câu hỏi về một chủ đề mà mọi tin liên quan đều có urgency thấp
- **THEN** recall của câu đó được báo cáo riêng, không bị hoà vào recall tổng

#### Scenario: Từ khoá ASCII hai ký tự
- **WHEN** benchmark chạy câu hỏi chứa từ khoá `AI`
- **THEN** báo cáo cho biết recall của câu đó, đủ để phát hiện việc so khớp chuỗi con làm tầng độ liên
  quan mất khả năng phân biệt

### Requirement: Baseline đóng băng, báo cáo theo từng câu hỏi

Bộ đo SHALL lưu baseline recall kèm ngày chốt, SHALL in recall của **từng câu hỏi** bên cạnh recall tổng,
và SHALL báo lỗi khi recall tổng tụt dưới baseline hoặc khi bất kỳ câu hỏi nào tụt so với baseline của
chính nó, theo dung sai khai báo tường minh.

Việc cập nhật baseline SHALL là hành động có chủ đích kèm lý do ghi lại, SHALL KHÔNG được làm để test
chuyển xanh.

#### Scenario: Hồi quy tập trung ở một loại câu hỏi
- **WHEN** một thay đổi làm recall tổng chỉ giảm nhẹ nhưng một câu hỏi tụt mạnh
- **THEN** benchmark báo lỗi và nêu đích danh câu hỏi tụt cùng mức chênh so với baseline

#### Scenario: Thay đổi không ảnh hưởng xếp hạng
- **WHEN** code đổi nhưng thứ hạng không đổi
- **THEN** benchmark báo đạt và in recall khớp baseline

### Requirement: Hướng dẫn chạy và giới hạn diễn giải nằm cùng chỗ với code

Bộ đo SHALL đi kèm hướng dẫn chạy chính xác đặt cùng chỗ với code, nêu rõ khi nào bắt buộc chạy lại
(sửa `_rank`, `_relevance`, `_question_terms`, `_roles_in_question`, `_STOPWORDS`, `score_for_role`,
`chat_index_top_k`) và giới hạn diễn giải của mẫu. Script sinh fixture SHALL được giữ lại trong repo làm
bằng chứng xuất xứ.

#### Scenario: Người đọc muốn biết khi nào phải chạy lại
- **WHEN** một lập trình viên chuẩn bị sửa hàm thuộc tầng xếp hạng
- **THEN** tài liệu đi kèm nêu rõ benchmark này là thứ duy nhất bắt được hồi quy đó và phải chạy lại

#### Scenario: Corpus lớn hơn nhiều so với lúc chụp fixture
- **WHEN** người đọc muốn suy kết quả recall sang corpus lớn hơn đáng kể
- **THEN** tài liệu nêu rõ fixture là ảnh chụp tại thời điểm cụ thể, đo hồi quy so với chính nó, và
  không suy ra được chất lượng trên corpus khác quy mô

