"""Gemini analysis prompts and response schema."""

ALLOWED_TOPICS = [
    "AI/ML Ứng dụng",
    "AI/ML Nghiên cứu",
    "DevTools & Frameworks",
    "Cloud & Infrastructure",
    "Data Engineering",
    "Security & Compliance",
    "Software Architecture",
    "Developer Experience",
    "Platform & API",
    "Market & Competition",
    "Legal & Regulation",
    "Team & Process",
]

ALLOWED_EVENT_TYPES = [
    "Phát hành mới",
    "Thay đổi chính sách",
    "Cập nhật quy định",
    "Cảnh báo bảo mật",
    "Ngừng hỗ trợ/Deprecation",
    "Tín hiệu xu hướng",
    "Thảo luận cộng đồng",
    "Nghiên cứu/Paper",
    "Sự cố vận hành",
    "Breaking Change",
    "Benchmark/So sánh",
    "Hướng dẫn/Best Practice",
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

ALLOWED_ADOPTION_RINGS = ["Adopt", "Trial", "Assess", "Hold"]

# ---------------------------------------------------------------------------
# Gate Prompt — lightweight pre-screening (~200 tokens output)
# ---------------------------------------------------------------------------

GATE_PROMPT = """\
Bạn là AI triage agent. Đánh giá nhanh bài viết: đây là tin MỚI CÓ ÍCH cho team phần mềm hay chỉ là noise?

TIÊU CHÍ:
- practical (score ≥ 0.7): phát hành tool/SDK, breaking change, security patch, benchmark có số liệu, hướng dẫn có code
- strategic (score 0.4-0.7): xu hướng dài hạn, policy change, regulation, M&A ảnh hưởng trực tiếp tech stack
- theoretical (score 0.2-0.4): paper nghiên cứu chưa có sản phẩm, opinion piece, thought leadership
- noise (score < 0.2): PR/marketing fluff, M&A không liên quan tech, tin cũ rehash, vague listicle

Trả về ONLY valid JSON (không markdown, không code block):
{{"actionability_score": <0.0-1.0>, "content_type": "<practical|strategic|theoretical|noise>", "gate_reason": "<1 câu ≤100 ký tự>", "pass_gate": <true|false>}}

TIÊU ĐỀ: {title}

NỘI DUNG (trích):
{content}
"""

# ---------------------------------------------------------------------------
# Deep Analysis Prompt — full classification + actionable fields
# ---------------------------------------------------------------------------

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

QUY TẮC CHO CÁC TRƯỜNG ACTIONABLE:
- signal: 1 câu CÔ ĐỌNG (≤200 ký tự) nêu cốt lõi tín hiệu/implication. PHẢI KHÁC title — title là sự kiện, signal là implication.
- why_it_matters: 1-2 câu (≤300 ký tự) giải thích tại sao tin này QUAN TRỌNG VỚI TEAM PHẦN MỀM VIỆT NAM. Không lặp lại tóm tắt.
- recommendations: dict, KEYS PHẢI ⊆ affected_roles (KHÔNG được thêm role ngoài affected_roles). Mỗi value là object {{"action_type": <enum>, "note": <1 câu tiếng Việt cụ thể>}}. action_type ∈ {action_types}.
- risks: list[str] các rủi ro nếu adopt (license, security, privacy, vendor-lock, cost, maturity). Mỗi rủi ro 1 câu ngắn. Trả [] nếu không có rủi ro đáng kể.
- so_what: 1 câu (≤200 ký tự) trả lời "bài này thay đổi gì cho team?" — PHẢI KHÁC signal và summary_short.
- adoption_ring: chọn 1 giá trị duy nhất từ {adoption_rings}. Adopt = nên dùng ngay. Trial = thử nghiệm. Assess = đánh giá thêm. Hold = chưa nên dùng.
- practical_indicators: object JSON với 5 boolean flags: has_code_example, has_benchmark, has_api_change, has_migration_guide, has_security_patch.

CHỦ ĐỀ CHO PHÉP: {topics}
LOẠI SỰ KIỆN CHO PHÉP: {event_types}
TÍNH CHẤT CHO PHÉP: {natures}
VAI TRÒ CHO PHÉP: {roles}
ACTION_TYPE CHO PHÉP: {action_types}
ADOPTION_RING CHO PHÉP: {adoption_rings}

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
  "risks": ["<rủi ro 1>", "<rủi ro 2>"],
  "so_what": "<1 câu trả lời bài này thay đổi gì cho team>",
  "adoption_ring": "<Adopt|Trial|Assess|Hold>",
  "practical_indicators": {{
    "has_code_example": <true|false>,
    "has_benchmark": <true|false>,
    "has_api_change": <true|false>,
    "has_migration_guide": <true|false>,
    "has_security_patch": <true|false>
  }}
}}

TIÊU ĐỀ BÀI VIẾT: {title}

NỘI DUNG BÀI VIẾT:
{content}
"""


def build_gate_prompt(title: str, content: str) -> str:
    """Build the lightweight gate prompt for pre-screening."""
    return GATE_PROMPT.format(
        title=title,
        content=content[:2000],
    )


def build_prompt(title: str, content: str) -> str:
    """Build the deep analysis prompt with title and content substituted."""
    return ANALYSIS_PROMPT.format(
        topics=", ".join(ALLOWED_TOPICS),
        event_types=", ".join(ALLOWED_EVENT_TYPES),
        natures=", ".join(ALLOWED_NATURES),
        roles=", ".join(ALLOWED_ROLES),
        action_types=", ".join(ALLOWED_ACTION_TYPES),
        adoption_rings=", ".join(ALLOWED_ADOPTION_RINGS),
        title=title,
        content=content[:6000],
    )
