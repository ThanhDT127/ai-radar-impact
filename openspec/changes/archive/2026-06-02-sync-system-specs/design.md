## Context

Tài liệu đặc tả hệ thống của AI Radar Impact gồm 2 file chính:
- `openspec/specs/insight-dashboard/spec.md`: Quản lý giao diện, bộ lọc, KPI, chi tiết bản tin và toolbar 3 chế độ đọc.
- `openspec/specs/ai-analysis/spec.md`: Quản lý logic AI Analysis, phân loại, tóm tắt và tìm kiếm dữ liệu.

Các thay đổi gần đây đã được hoàn thiện trong mã nguồn nhưng chưa được tích hợp đầy đủ vào hai file đặc tả chính này. Chúng ta cần cập nhật 2 file đặc tả trên để đồng bộ hóa với thực tế của hệ thống.

## Goals / Non-Goals

**Goals:**
- Tích hợp tất cả các spec delta từ các thay đổi cũ và mới vào file đặc tả chính.
- Đảm bảo các scenarios tuân thủ cấu trúc BDD (Given/When/Then hoặc When/Then/And) và sử dụng tiếng Việt tự nhiên với technical terms tiếng Anh.
- Sử dụng các từ khóa bắt buộc `MUST` và `SHALL` theo tiêu chuẩn OpenSpec.

**Non-Goals:**
- Không thay đổi mã nguồn, database schema hoặc logic API.
- Không thay đổi model AI (giữ nguyên Gemini 2.5 Flash).

## Decisions

### 1. Đồng bộ hóa Đặc tả Dashboard (M6: Dashboard)
Chúng ta sẽ gộp tất cả các yêu cầu frontend từ các change:
- **Chế độ đọc linh hoạt**: Tích hợp các scenarios chuyển đổi giữa Split View, Focus AI, và Focus Original. Nút "Phân tích chi tiết" và "Bài viết gốc" được Việt hóa và xử lý scroll jump bằng `window.scrollY`.
- **Tín hiệu kỹ thuật**: Thẻ `InsightCard` hiển thị badges `💻 Có code mẫu`, `📊 Có benchmark`, `🔗 Thay đổi API`, `🛡️ Bảo mật` dựa trên các trường boolean tương ứng, và giới hạn tối đa 3 bullets.
- **Tối ưu hiển thị**: `InsightCard` nhận `displayTitle` và loại bỏ các phần tử trùng lặp với `summary_short`.
- **KPI Upgrade**: Mỗi thẻ KPI hiển thị label mới, ⓘ tooltip giải thích và màu sắc cảnh báo theo ngữ cảnh.
- **Unified Filter Panel**: Bộ lọc hợp nhất thay cho tab bar cũ, hỗ trợ lọc đa tiêu chí, tìm kiếm debounced 300ms và nút "Xóa tất cả".
- **Cải tiến Badge & Tooltip**: Glassmorphism cho tất cả badges, prefix rõ ràng cho Urgency và Impact level, shimmer skeleton loading.
- **Chi tiết card**: Viền trái theo intelligence tier, cờ Việt Nam cho relevance high, và thumbnail 120x84px với error fallback.

Bảng DB bị ảnh hưởng: Không có.
API endpoints bị ảnh hưởng: `GET /api/v1/insights` (hỗ trợ query param `search`, pagination, and filters).

### 2. Đồng bộ hóa Đặc tả AI Analysis (M4: AI Analysis)
Chúng ta sẽ gộp các yêu cầu backend từ các change:
- **Tìm kiếm backend**: API `GET /api/v1/insights?search=keyword` tìm kiếm keyword trong `title`, `summary_short`, `summary_medium`, `signal`, `so_what`.
- **Few-shot Prompting và Ràng buộc**: Prompt hệ thống của Gemini Flash 2.0 (Vertex AI) tích hợp Negative Constraints để loại bỏ văn phong sáo rỗng tiếng Việt và 2 ví dụ few-shot JSON chất lượng cao. Bảo toàn định dạng JSON schema đầu ra.

Bảng DB bị ảnh hưởng: `insights`, `raw_documents` (status counts, processing_status).
Grounding strategy: Bám sát nguồn dữ liệu đầu vào, không suy diễn, confidence >= 0.5 mới tự động xuất bản (hoặc 0.3 theo mã nguồn thực tế).

## Risks / Trade-offs

- **Tài liệu dài hơn**: Việc gộp tất cả các yêu cầu cũ và mới sẽ làm tăng dung lượng file đặc tả chính. Tuy nhiên, điều này giúp tài liệu có cái nhìn tổng quan toàn diện và dễ dàng chạy kiểm thử hồi quy (regression testing) sau này.
- **Không ảnh hưởng đến n8n hay delivery**: Vì đây thuần túy là việc đồng bộ hóa đặc tả tài liệu (specs), không có thay đổi nào ảnh hưởng đến tích hợp n8n hay delivery pipeline.
