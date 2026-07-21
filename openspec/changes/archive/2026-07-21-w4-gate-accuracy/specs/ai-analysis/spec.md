## ADDED Requirements

### Requirement: Gate đánh giá theo phạm vi công ty 4 trụ cột

Gate pre-screening MUST phán pass/fail theo phạm vi công ty gồm **4 trụ cột**: (①) IoT, (②) Agent / AI /
Data Science, (③) Smart Home, (④) Bảo mật hệ thống/dữ liệu. Một document chỉ được xét pass khi chạm **ít
nhất một trụ cột**; document không chạm trụ nào MUST bị loại (`pass_gate = false`), bất kể nó có tính học
thuật hay nhắc tên công nghệ.

Nội dung Agent / LLM / AI / Data Science / ML tooling tổng quát MUST KHÔNG bị coi là NOISE mặc định (nó
thuộc trụ ②). Danh sách NOISE mặc định (tiền ảo, game, Web3, điện thoại/tai nghe tiêu dùng) được giữ.

Tin bảo mật hệ thống/dữ liệu (trụ ④) MUST được **duyệt mạnh**: hạ burden of proof, ưu tiên pass; không
bắt buộc phải có CVE ID cứng mới qua.

#### Scenario: Nội dung AI/Agent tổng quát không còn là noise mặc định
- **WHEN** gate nhận một bài về framework xây dựng LLM agent, không nhắc IoT/Smart Home
- **THEN** gate xét nó theo trụ ② (Agent/AI/DS), KHÔNG loại nó chỉ vì "không phục vụ IoT"

#### Scenario: Document không chạm trụ cột nào bị loại
- **WHEN** gate nhận một bài không liên quan bất kỳ trụ cột nào (vd: tin tài chính tiền ảo, drama ngành game)
- **THEN** `pass_gate = false`

#### Scenario: Tin bảo mật được duyệt mạnh
- **WHEN** gate nhận một cảnh báo bảo mật có action rõ cho Security/Dev nhưng không kèm CVE ID cứng
- **THEN** gate ưu tiên `pass_gate = true` theo cơ chế duyệt mạnh của trụ ④

### Requirement: Paper học thuật xét theo relevance, không theo thể loại

Gate MUST KHÔNG cho một document qua chỉ vì nó là paper nghiên cứu / arXiv / whitepaper (xét theo **thể
loại**). Paper học thuật MUST được xét theo **relevance** — có chạm trụ cột công ty hay không — và theo
**tính chuyển-giao**: paper đưa ra kỹ thuật/kiến trúc/kết quả một kỹ sư có thể dùng hoặc phải theo dõi thì
pass; paper chỉ là incrementalism trên leaderboard (SOTA +0.x%, biến thể nhỏ) hoặc lý thuyết thuần miền
xa thì fail.

Quyết định pass/fail của nhóm học thuật MUST nằm trong **điểm số** theo thang thường, KHÔNG dùng cờ
override lật kết quả — để không còn tình trạng cùng một dải điểm mang hai nghĩa pass và fail.

#### Scenario: Paper arXiv liên quan + chuyển-giao-được → pass
- **WHEN** gate nhận một paper arXiv về quantization giảm nửa VRAM cho inference trên edge
- **THEN** paper earn điểm ≥ ngưỡng pass theo thang thường (chạm trụ ② + chuyển-giao-được) và `pass_gate = true`

#### Scenario: Paper arXiv off-pillar / thuần lý thuyết → fail
- **WHEN** gate nhận một paper arXiv về chặn hội tụ của một optimizer dưới giả định non-convex, không góc triển khai và không chạm trụ cột nào
- **THEN** `pass_gate = false`, KHÔNG được cứu bởi bất kỳ ngoại lệ "vì là arXiv" nào

#### Scenario: Không có cờ override ở dải Theoretical
- **WHEN** một document được chấm trong dải điểm 0.2–0.4
- **THEN** kết quả pass/fail suy trực tiếp từ điểm số, không có mệnh đề "nếu là học thuật thì lật thành pass"

### Requirement: `gate_reason` phải khai trụ cột và lý do phán quyết

Khi gate phán một document, `gate_reason` MUST nêu được **trụ cột nào** đã áp dụng (hoặc "off-pillar")
và **lý do** pass/fail, trong giới hạn độ dài sẵn có (≤100 ký tự). Mục tiêu là để việc chấm tay/kiểm toán
đối chiếu được phán quyết của gate với nhãn của người, mà không cần lưu thêm dữ liệu xuống DB.

#### Scenario: Reason cho ca pass nêu trụ cột
- **WHEN** gate cho một bài qua vì nó là model nhỏ chạy được trên edge
- **THEN** `gate_reason` nêu trụ cột liên quan và lý do chuyển-giao (vd: "Trụ ②: model nhỏ chạy edge, chuyển-giao được")

#### Scenario: Reason cho ca loại nêu off-pillar
- **WHEN** gate loại một bài vì không chạm trụ cột nào
- **THEN** `gate_reason` nêu rõ off-pillar và lý do (vd: "Off-pillar: lý thuyết tối ưu thuần, không chuyển-giao")
