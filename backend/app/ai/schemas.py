"""`response_schema` cho lần gọi gate — ràng buộc cấu trúc ở tầng API.

Trước change này chỉ có `response_mime_type="application/json"`, vốn chỉ *gợi ý*
định dạng chứ không ép cấu trúc. Hậu quả đo được (438 doc, 20/07/2026): 3→9 lỗi
parse JSON mỗi 50 doc ở gate. Mỗi lỗi làm doc fail-open đi thẳng vào deep
analysis, tốn oan một lượt gọi đắt tiền. Sau khi bật schema: 0 lỗi / 50 doc.

Enum sinh TỪ hằng số trong `prompts.py` (design D2) — thêm một giá trị vào hằng
số thì schema đổi theo, không có bước chép tay nào để quên.

CHỈ áp cho gate. Deep analysis (`analyze`) đã thử và bỏ: `response_schema` khiến
model sinh `why_it_matters` lặp vô nghĩa tới ~6500 ký tự (giới hạn 300) cho tới
khi chạm `max_output_tokens` → 16/16 doc lỗi `Unterminated string`, 0 insight.
`max_length` không cứu được vì Vertex không thực thi nó. Chi tiết và hướng đi
tiếp: `openspec/changes/gemini-structured-output/measurement.md`.
"""

from google.genai import types

from app.ai.prompts import ALLOWED_CONTENT_TYPES

_NULLABLE_STR = types.Schema(type=types.Type.STRING, nullable=True)
_BOOL = types.Schema(type=types.Type.BOOLEAN)

# Giới hạn độ dài khai báo trong schema, lấy đúng từ phần QUY TẮC của `prompts.py`.
# Lưu ý: Vertex KHÔNG thực thi `max_length` (đã kiểm chứng) — để đây làm tài liệu
# và phòng khi API hỗ trợ về sau; ràng buộc thật vẫn nằm ở prompt.
_LEN_GATE_REASON = 200
_LEN_NOISE_SIGNAL = 200


def _capped_str(limit: int) -> types.Schema:
    return types.Schema(type=types.Type.STRING, max_length=limit)


def _enum(values: list[str]) -> types.Schema:
    return types.Schema(type=types.Type.STRING, enum=list(values))


def build_gate_schema() -> types.Schema:
    """Schema cho `gate_analyze`.

    `evidence` để nullable từng trường vì prompt yêu cầu ghi null khi không tìm
    thấy bằng chứng — đó là tín hiệu có ý nghĩa, không phải thiếu dữ liệu.
    """
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
            "evidence": types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "code_or_api": _NULLABLE_STR,
                    "cve_or_regulation": _NULLABLE_STR,
                    "benchmark_data": _NULLABLE_STR,
                },
                required=["code_or_api", "cve_or_regulation", "benchmark_data"],
            ),
            "noise_signals": types.Schema(
                type=types.Type.ARRAY, items=_capped_str(_LEN_NOISE_SIGNAL)
            ),
            "actionability_score": types.Schema(
                type=types.Type.NUMBER, minimum=0.0, maximum=1.0
            ),
            "content_type": _enum(ALLOWED_CONTENT_TYPES),
            "gate_reason": _capped_str(_LEN_GATE_REASON),
            "pass_gate": _BOOL,
        },
        required=[
            "evidence",
            "noise_signals",
            "actionability_score",
            "content_type",
            "gate_reason",
            "pass_gate",
        ],
    )
