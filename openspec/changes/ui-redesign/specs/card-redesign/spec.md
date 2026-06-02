## ADDED Requirements

### Requirement: Left Border Color theo Intelligence Tier
Mỗi card phải có viền trái 4px với màu sắc tương ứng intelligence_tier: Tactical=red, Operational=orange, Strategic=purple, Informational=gray. Viền này giúp người dùng phân loại nhanh bằng mắt.

#### Scenario: Card hiển thị đúng màu viền theo tier
- **WHEN** card render với `intelligence_tier` là "Tactical"
- **THEN** viền trái card có màu red (`--color-danger`)
- **WHEN** card render với `intelligence_tier` là "Operational"
- **THEN** viền trái card có màu orange (`--color-warning`)
- **WHEN** card render với `intelligence_tier` là "Strategic"
- **THEN** viền trái card có màu purple (`--color-strategic`)
- **WHEN** card render với `intelligence_tier` là "Informational"
- **THEN** viền trái card có màu gray (`--color-neutral`)

#### Scenario: Card không có intelligence_tier
- **WHEN** card render mà `intelligence_tier` là null hoặc undefined
- **THEN** viền trái card có màu gray (`--color-neutral`) làm fallback mặc định

### Requirement: Urgency Strip
Card của insight có urgency là "critical" hoặc "high" phải hiển thị thanh gradient mỏng (3px) ở đầu card để thu hút sự chú ý.

#### Scenario: Thanh urgency hiển thị cho item cấp thiết
- **WHEN** card render với `urgency` là "critical" hoặc "high"
- **THEN** một thanh gradient mỏng (3px height) xuất hiện ở top edge của card, gradient từ màu urgency sang trong suốt

#### Scenario: Thanh urgency ẩn cho item thường
- **WHEN** card render với `urgency` là "medium", "low", hoặc "watch"
- **THEN** không hiển thị thanh gradient — card bắt đầu bình thường từ content

### Requirement: So What Snippet ưu tiên
Field `so_what` được hiển thị làm snippet chính trên card khi có giá trị. Nếu không có, fallback theo thứ tự: `signal` → `summary_short`.

#### Scenario: so_what làm snippet chính
- **WHEN** insight có `so_what` không rỗng
- **THEN** card hiển thị `so_what` làm đoạn mô tả chính, cắt ngắn ở 2 dòng với ellipsis

#### Scenario: Fallback khi so_what rỗng
- **WHEN** insight có `so_what` là null hoặc chuỗi rỗng
- **THEN** card hiển thị `signal` làm snippet; nếu `signal` cũng rỗng, hiển thị `summary_short`

#### Scenario: Tất cả field snippet đều rỗng
- **WHEN** `so_what`, `signal`, và `summary_short` đều null hoặc rỗng
- **THEN** card vẫn render bình thường, vùng snippet trống nhưng không bị vỡ layout

### Requirement: Compact Inline Badge Row
Badge row hiển thị compact inline (urgency + tier + momentum) thay thế footer cũ. Badge nằm ngang, kích thước nhỏ, không chiếm nhiều không gian.

#### Scenario: Badge row hiển thị đầy đủ
- **WHEN** card render với đủ dữ liệu urgency, intelligence_tier, momentum
- **THEN** một hàng badge inline hiển thị cả 3 giá trị, mỗi badge có icon + label, cách nhau 8px gap

#### Scenario: Badge row khi thiếu một số field
- **WHEN** card render mà `momentum` là null
- **THEN** badge row chỉ hiển thị urgency + tier, không có khoảng trống hoặc placeholder cho momentum

### Requirement: Vietnam Flag cho Vietnam Relevance High
Card có `vietnam_relevance` = "high" hiển thị icon cờ Việt Nam (🇻🇳) để nhấn mạnh mức độ liên quan.

#### Scenario: Cờ Việt Nam hiển thị khi relevance cao
- **WHEN** insight có `vietnam_relevance` là "high"
- **THEN** icon 🇻🇳 hiển thị trên card, đặt gần badge row hoặc title

#### Scenario: Không hiển thị cờ khi relevance thấp
- **WHEN** insight có `vietnam_relevance` là "medium", "low", hoặc null
- **THEN** không hiển thị icon cờ Việt Nam

### Requirement: Thumbnail với Error Fallback
Thumbnail 120x84px hiển thị ảnh `primary_image`. Khi ảnh lỗi hoặc không có, fallback sang placeholder. Behavior này đã tồn tại — giữ nguyên và đảm bảo tương thích với card layout mới.

#### Scenario: Thumbnail load thành công
- **WHEN** insight có `primary_image` URL hợp lệ và ảnh load được
- **THEN** thumbnail hiển thị ảnh 120x84px, `object-fit: cover`, bo góc 6px

#### Scenario: Thumbnail lỗi fallback
- **WHEN** `primary_image` URL trả về lỗi (404, CORS, timeout)
- **THEN** hiển thị placeholder gradient hoặc icon thay thế, giữ đúng kích thước 120x84px
