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
    "DevOps",
    "Infrastructure",
    "Security",
    "BA/QA",
    "Designer/UX",
    "Toàn công ty",
]

ALLOWED_ACTION_TYPES = ["watch", "read", "test", "PoC", "roadmap"]

ANALYSIS_PROMPT = """\
Bạn là chuyên gia phân tích AI cho team phần mềm Việt Nam. Phân tích bài viết sau và trả về JSON.

QUY TẮC:
- Chỉ sử dụng thông tin có trong bài viết
- KHÔNG suy đoán hoặc thêm kiến thức bên ngoài
- summary_short tối đa 200 ký tự, 1-2 câu, bằng tiếng Việt, súc tích và rõ ràng
- summary_medium tối đa 500 ký tự, 1 đoạn, bằng tiếng Việt, mô tả đầy đủ hơn
- topics chỉ chứa giá trị từ danh sách CHỦ ĐỀ CHO PHÉP
- event_type chỉ chọn 1 giá trị từ danh sách LOẠI SỰ KIỆN CHO PHÉP
- nature chỉ chọn 1 giá trị từ danh sách TÍNH CHẤT CHO PHÉP
- affected_roles: chọn 1 hoặc nhiều vai trò từ danh sách VAI TRÒ CHO PHÉP bị ảnh hưởng bởi sự kiện này. Chọn role SPECIFIC nhất:
  * DevOps: CI/CD, observability, deployment automation, container orchestration
  * Infrastructure: cloud architecture, network, hardware, capacity planning
  * Security: AppSec, container security, CVE, compliance kỹ thuật
  * BA/QA: requirements analysis, test automation, quality processes
  * Designer/UX: UI/UX design, design system, design tools
  * Engineering: dùng làm fallback khi không khớp role specific nào ở trên
- Nếu không chắc chắn về phân loại, đặt confidence dưới 0.5

QUY TẮC CHO 4 TRƯỜNG ACTIONABLE MỚI:
- signal: 1 câu CÔ ĐỌNG (≤200 ký tự) nêu cốt lõi tín hiệu/implication. PHẢI KHÁC title — title là sự kiện ("Anthropic ra Claude 4.7"), signal là implication ("Mô hình mới rút ngắn khoảng cách với GPT-5 ở chi phí thấp hơn").
- why_it_matters: 1-2 câu (≤300 ký tự) giải thích tại sao tin này QUAN TRỌNG VỚI TEAM PHẦN MỀM VIỆT NAM. Không lặp lại tóm tắt.
- recommendations: dict, KEYS PHẢI ⊆ affected_roles (KHÔNG được thêm role ngoài affected_roles). Mỗi value là object {{"action_type": <enum>, "note": <1 câu tiếng Việt cụ thể>}}. action_type ∈ {action_types}.
- risks: list[str] các rủi ro nếu adopt (license, security, privacy, vendor-lock, cost, maturity). Mỗi rủi ro 1 câu ngắn. Trả [] nếu không có rủi ro đáng kể.

CHỦ ĐỀ CHO PHÉP: {topics}
LOẠI SỰ KIỆN CHO PHÉP: {event_types}
TÍNH CHẤT CHO PHÉP: {natures}
VAI TRÒ CHO PHÉP: {roles}
ACTION_TYPE CHO PHÉP: {action_types}

Trả về ONLY valid JSON (không markdown, không code block):
{{
  "topics": ["<chủ đề>"],
  "event_type": "<loại sự kiện>",
  "nature": "<tính chất>",
  "summary_short": "<1-2 câu tối đa 200 ký tự bằng tiếng Việt>",
  "summary_medium": "<1 đoạn tối đa 500 ký tự bằng tiếng Việt>",
  "affected_roles": ["<vai trò>"],
  "confidence": <0.0 đến 1.0>,
  "signal": "<1 câu cô đọng implication, khác title>",
  "why_it_matters": "<1-2 câu vì sao quan trọng với team VN>",
  "recommendations": {{
    "<role trong affected_roles>": {{"action_type": "<watch|read|test|PoC|roadmap>", "note": "<1 câu khuyến nghị>"}}
  }},
  "risks": ["<rủi ro 1>", "<rủi ro 2>"]
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
        action_types=", ".join(ALLOWED_ACTION_TYPES),
        title=title,
        content=content[:6000],  # Limit content to avoid token overflow
    )
