"""`response_schema` của gate phải sinh TỪ hằng số trong prompts.py (design D2).

Test cốt lõi: thêm một giá trị vào hằng số → schema đổi theo. Nếu ai đó hardcode
enum vào schema, test này đỏ.

Deep analysis KHÔNG dùng response_schema (đã thử và bỏ — xem docstring của
`app/ai/schemas.py`), nên ở đây chỉ có gate.
"""

import importlib

from app.ai import prompts, schemas
from app.ai.prompts import ALLOWED_CONTENT_TYPES


def test_gate_schema_has_all_required_fields():
    s = schemas.build_gate_schema()
    assert set(s.properties) == {
        "evidence",
        "noise_signals",
        "actionability_score",
        "content_type",
        "gate_reason",
        "pass_gate",
    }
    assert set(s.required) == set(s.properties)


def test_gate_content_type_enum_comes_from_constant():
    s = schemas.build_gate_schema()
    assert s.properties["content_type"].enum == ALLOWED_CONTENT_TYPES


def test_gate_evidence_fields_are_nullable():
    """Prompt yêu cầu ghi null khi không có bằng chứng — schema phải cho phép."""
    ev = schemas.build_gate_schema().properties["evidence"]
    for field in ("code_or_api", "cve_or_regulation", "benchmark_data"):
        assert ev.properties[field].nullable is True


def test_gate_score_is_bounded():
    score = schemas.build_gate_schema().properties["actionability_score"]
    assert score.minimum == 0.0 and score.maximum == 1.0


def test_gate_text_fields_have_length_caps():
    s = schemas.build_gate_schema()
    assert s.properties["gate_reason"].max_length
    assert s.properties["noise_signals"].items.max_length


def test_schema_follows_constant_when_value_added(monkeypatch):
    """Thêm giá trị vào hằng số ⇒ schema đổi theo, không cần sửa schemas.py."""
    monkeypatch.setattr(
        prompts, "ALLOWED_CONTENT_TYPES", [*ALLOWED_CONTENT_TYPES, "tutorial"]
    )
    importlib.reload(schemas)
    try:
        assert "tutorial" in schemas.build_gate_schema().properties["content_type"].enum
    finally:
        monkeypatch.undo()
        importlib.reload(schemas)


def test_schema_reverts_after_reload():
    """Chốt: reload lại thì enum trở về tập gốc (bảo vệ test trên khỏi rò rỉ)."""
    assert (
        schemas.build_gate_schema().properties["content_type"].enum
        == ALLOWED_CONTENT_TYPES
    )
