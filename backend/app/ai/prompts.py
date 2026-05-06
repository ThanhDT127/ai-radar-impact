"""Gemini analysis prompts and response schema."""

ALLOWED_TOPICS = [
    "Trí tuệ nhân tạo",
    "Công nghệ",
    "Dữ liệu",
    "Quy trình phần mềm",
    "An ninh mạng",
    "Pháp lý/Tuân thủ",
    "Nội dung/Marketing",
    "Dịch vụ/Nền tảng",
    "Thị trường/Đối thủ",
    "Quản trị nội bộ",
]

ALLOWED_EVENT_TYPES = [
    "Phát hành mới",
    "Thay đổi chính sách",
    "Cập nhật quy định",
    "Cảnh báo bảo mật",
    "Ngừng hỗ trợ",
    "Tín hiệu xu hướng",
    "Thảo luận cộng đồng",
    "Cập nhật nghiên cứu",
    "Sự cố vận hành",
]

ALLOWED_NATURES = ["Rủi ro", "Cơ hội", "Tuân thủ", "Thông tin chung", "Theo dõi"]

ALLOWED_ROLES = [
    "Executive",
    "Engineering",
    "Data/AI",
    "Product",
    "Content/Marketing",
    "Legal/Compliance",
    "HR/L&D",
    "Toàn công ty",
]

ANALYSIS_PROMPT = """\
Bạn là chuyên gia phân tích AI. Phân tích bài viết sau và trả về JSON.

QUY TẮC:
- Chỉ sử dụng thông tin có trong bài viết
- KHÔNG suy đoán hoặc thêm kiến thức bên ngoài
- summary_short tối đa 200 ký tự, 1-2 câu, bằng tiếng Việt, súc tích và rõ ràng
- summary_medium tối đa 500 ký tự, 1 đoạn, bằng tiếng Việt, mô tả đầy đủ hơn
- topics chỉ chứa giá trị từ danh sách CHỦ ĐỀ CHO PHÉP
- event_type chỉ chọn 1 giá trị từ danh sách LOẠI SỰ KIỆN CHO PHÉP
- nature chỉ chọn 1 giá trị từ danh sách TÍNH CHẤT CHO PHÉP
- affected_roles: chọn 1 hoặc nhiều vai trò từ danh sách VAI TRÒ CHO PHÉP bị ảnh hưởng bởi sự kiện này
- Nếu không chắc chắn về phân loại, đặt confidence dưới 0.5

CHỦ ĐỀ CHO PHÉP: {topics}
LOẠI SỰ KIỆN CHO PHÉP: {event_types}
TÍNH CHẤT CHO PHÉP: {natures}
VAI TRÒ CHO PHÉP: {roles}

Trả về ONLY valid JSON (không markdown, không code block):
{{
  "topics": ["<chủ đề>"],
  "event_type": "<loại sự kiện>",
  "nature": "<tính chất>",
  "summary_short": "<1-2 câu tối đa 200 ký tự bằng tiếng Việt>",
  "summary_medium": "<1 đoạn tối đa 500 ký tự bằng tiếng Việt>",
  "affected_roles": ["<vai trò>"],
  "confidence": <0.0 đến 1.0>
}}

TIÊU ĐỀ BÀI VIẾT: {title}

NỘI DUNG BÀI VIẾT:
{content}
"""


def build_prompt(title: str, content: str) -> str:
    """Build the analysis prompt with title and content substituted."""
    return ANALYSIS_PROMPT.format(
        topics=", ".join(ALLOWED_TOPICS),
        event_types=", ".join(ALLOWED_EVENT_TYPES),
        natures=", ".join(ALLOWED_NATURES),
        roles=", ".join(ALLOWED_ROLES),
        title=title,
        content=content[:6000],  # Limit content to avoid token overflow
    )
