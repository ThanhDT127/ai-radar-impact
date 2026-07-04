## Why

Thẻ thông tin `InsightCard` trên Dashboard hiện tại đang bị quá tải thông tin dạng chữ (text-heavy), làm giảm khả năng "scan nhanh" của các kỹ sư khi lướt qua danh sách tin tức. Người dùng gặp khó khăn trong việc phát hiện nhanh các thuộc tính kỹ thuật thực tế quan trọng như bài viết có code mẫu hay không, có benchmark đo lường hiệu năng hay không, hay có thay đổi API quan trọng nào không.

Cần cấu trúc lại thẻ thành hai vùng thông tin tách biệt và trực quan hơn:
1. **Vùng Tín hiệu Kỹ thuật (Technical Signals):** Hiển thị nổi bật các chỉ số thực hành dạng icon/badge như `💻 Có code mẫu`, `📊 Có benchmark`, `🔗 Thay đổi API`, `🛡️ Bảo mật` để kỹ sư nhận diện giá trị thực hành của tin tức ngay lập tức.
2. **Vùng Phân tích Nhanh (Quick Analysis):** Chứa Tiêu đề hiển thị cùng ý nghĩa cốt lõi của bản tin và tối đa 2-3 dòng tóm tắt tinh gọn.

## What Changes

1. **Frontend Component (`InsightCard.tsx`):**
   - Tái cấu trúc CSS Grid/Flexbox của thẻ để phân chia thành Vùng Tín hiệu Kỹ thuật ở trên và Vùng Phân tích Nhanh ở dưới.
   - Thêm phần hiển thị biểu tượng trực quan dựa trên các thuộc tính boolean có sẵn từ API:
     * `insight.has_code_example` ➔ `💻 Có code mẫu`
     * `insight.has_benchmark` ➔ `📊 Có benchmark`
     * `insight.has_api_change` ➔ `🔗 Thay đổi API`
     * `insight.has_security_patch` ➔ `🛡️ Bảo mật`
   - Chỉ render phần gạch đầu dòng tóm tắt tinh gọn (tối đa 2-3 bullets thay vì 5 bullets) để nhường không gian hiển thị cho các tín hiệu kỹ thuật.
   - Giữ nguyên các badge về Urgency, Tier, và Momentum ở chân trang (footer).

## Capabilities

### New Capabilities
- Không có.

### Modified Capabilities
- `insight-dashboard`: Thay đổi giao diện hiển thị của thẻ `InsightCard` để cấu trúc lại thông tin thành 2 vùng chuyên biệt.

## Impact

- **Frontend:**
  - File [InsightCard.tsx](file:///d:/Works/AI%20Radar%20Impact/frontend/src/components/InsightCard.tsx) — Sửa đổi cấu trúc HTML rendering.
  - File [card.module.css](file:///d:/Works/AI%20Radar%20Impact/frontend/src/styles/card.module.css) — Thêm các CSS rules cho vùng tín hiệu kỹ thuật và layout mới.

- **Backend:** Không thay đổi.

- **Non-goals:**
  - Không thay đổi API payload hay cấu trúc Database.
  - Không sửa đổi prompt hay dữ liệu trả về của Gemini.
