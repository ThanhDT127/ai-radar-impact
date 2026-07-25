## ADDED Requirements

### Requirement: Auto‑fallback từ scope bài sang scope mở rộng

Ở chế độ per‑insight, khi câu hỏi rõ ràng **không thể trả lời từ nội dung bài đang xem**, service SHALL tự
mở rộng phạm vi sang toàn hệ thống thay vì trả lời cụt. Cơ chế: lượt gọi model ở chế độ per‑insight SHALL
được hướng dẫn phát một **sentinel văn bản thuần đã định nghĩa** khi (và chỉ khi) câu hỏi nằm ngoài phạm vi
bài; service phát hiện sentinel SHALL dựng **context mở rộng** gồm insight của bài đang xem **cộng** index
toàn cục đã xếp hạng (tái dùng đúng retrieval do server điều khiển của chế độ toàn cục), rồi gọi model **lần
thứ hai** để trả lời.

Câu trả lời mở rộng SHALL nêu rõ rằng đã tìm trên toàn hệ thống (không chỉ bài đang xem), citation SHALL lấy
từ bảng ánh xạ `[n]` của index toàn cục, và `mode` SHALL là `"expanded"`. Tổng số lượt gọi model cho một câu
hỏi SHALL KHÔNG vượt quá 2. Service SHALL KHÔNG dùng `response_schema` để phát/đọc sentinel. Sentinel SHALL
được phát **dè dặt**: câu hỏi còn trả lời được dù chỉ một phần từ nội dung bài SHALL KHÔNG kích hoạt mở rộng.

Service SHALL KHÔNG dùng một lượt gọi model riêng chỉ để phân loại phạm vi; tín hiệu ngoài‑phạm‑vi SHALL là
kết quả của chính lượt gọi trả lời per‑insight.

#### Scenario: Câu hỏi nằm trong phạm vi bài
- **WHEN** người dùng đang mở một insight và hỏi một câu trả lời được từ nội dung bài
- **THEN** service trả lời ở chế độ per‑insight với đúng 1 lượt gọi model, `mode="insight"`, không mở rộng

#### Scenario: Câu hỏi vượt phạm vi bài
- **WHEN** người dùng đang mở insight B và hỏi về một chủ đề chỉ có ở insight khác trong hệ thống
- **THEN** lượt gọi per‑insight phát sentinel, service dựng context mở rộng (insight B + index toàn cục) và gọi model lần hai
- **AND** câu trả lời nêu rõ đã tìm toàn hệ thống, `citations` lấy từ index toàn cục, `mode="expanded"`, tổng 2 lượt gọi

#### Scenario: Mở rộng nhưng toàn hệ thống cũng không có
- **WHEN** câu hỏi vượt phạm vi bài và index toàn cục cũng không có tin nào khớp
- **THEN** service trả lời trung thực rằng không tìm thấy trong toàn hệ thống, `citations` rỗng, không bịa từ bài đang xem

#### Scenario: Trần hai lượt gọi
- **WHEN** một câu hỏi kích hoạt mở rộng
- **THEN** service dùng đúng 2 lượt gọi (per‑insight + toàn cục) và SHALL KHÔNG thực hiện lượt thứ ba; `chat_logs` ghi `model_calls=2`

#### Scenario: Sentinel phát dè dặt
- **WHEN** câu hỏi trả lời được một phần từ nội dung bài
- **THEN** lượt gọi per‑insight SHALL trả lời trực tiếp và SHALL KHÔNG phát sentinel, không phát sinh lượt gọi mở rộng

## MODIFIED Requirements

### Requirement: Chế độ per-insight dùng bài gốc đầy đủ
Ở chế độ B, context gửi cho Gemini SHALL gồm các trường insight (`title`, `signal`, `so_what`, `why_it_matters`, `recommendations`, `risks`, `summary_medium`) và toàn bộ `raw_documents.normalized_content` của bài gốc (nội dung đã bị giới hạn 8000 ký tự từ lúc ingest nên không cần cắt thêm).

Khi câu hỏi không thể trả lời từ nội dung bài, service SHALL KHÔNG trả lời cụt mà SHALL mở rộng sang toàn hệ thống theo requirement "Auto‑fallback từ scope bài sang scope mở rộng". Chế độ B chỉ trả lời trong phạm vi bài khi câu hỏi thực sự nằm trong phạm vi đó.

#### Scenario: Hỏi chi tiết nằm ngoài summary
- **WHEN** người dùng hỏi một chi tiết có trong bài gốc nhưng không có trong summary/signal của insight
- **THEN** bot trả lời được dựa trên bài gốc, không mở rộng

#### Scenario: Bài gốc đã bị tombstone-purge
- **WHEN** insight còn tồn tại nhưng `normalized_content` của tài liệu gốc đã bị xoá theo retention
- **THEN** service trả lời bằng các trường insight và nói rõ rằng bài gốc đã hết hạn lưu trữ, không trả lời như thể vẫn còn bài

#### Scenario: Câu hỏi vượt phạm vi bài kích hoạt mở rộng
- **WHEN** người dùng đang mở một insight nhưng hỏi câu mà nội dung bài không đề cập
- **THEN** service mở rộng sang toàn hệ thống thay vì trả lời "bài này không đề cập" rồi dừng
