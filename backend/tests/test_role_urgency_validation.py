"""Validate bộ vai trò đóng + `urgency` theo vai trò trong recommendations.

Hai bất biến được canh ở đây:
1. `affected_roles` chỉ chứa giá trị thuộc `ALLOWED_ROLES` (9 chức danh) — chặn
   giá trị của taxonomy `Source.target_roles` (DevOps, Data/AI…) lọt vào insight.
2. `recommendations[role].urgency` luôn tồn tại và thuộc tập đóng; thiếu/sai thì
   hạ về "medium" (không alert) chứ KHÔNG drop cả entry.
"""

from app.ai.prompts import ALLOWED_ROLE_URGENCY, ALLOWED_ROLES
from app.services.analyzer import (
    _validate_affected_roles,
    _validate_recommendations,
)


def _rec(action_type="read", note="Đọc tài liệu.", **extra):
    return {"action_type": action_type, "note": note, **extra}


# --- affected_roles ---------------------------------------------------------


def test_affected_roles_keeps_allowed():
    assert _validate_affected_roles(["Security", "Tech Lead"]) == [
        "Security",
        "Tech Lead",
    ]


def test_affected_roles_drops_target_role_taxonomy_values():
    """DevOps/Data/AI/Infrastructure thuộc target_roles, không thuộc ALLOWED_ROLES."""
    assert _validate_affected_roles(
        ["DevOps", "Security", "Data/AI", "Infrastructure"]
    ) == ["Security"]


def test_affected_roles_empty_and_none():
    assert _validate_affected_roles([]) == []
    assert _validate_affected_roles(None) == []


def test_allowed_roles_is_the_nine_job_titles():
    """Chốt bộ 9 — đổi bộ này phải sửa RoleBadge.tsx + TooltipContent.ts."""
    assert len(ALLOWED_ROLES) == 9
    assert "DevOps" not in ALLOWED_ROLES
    assert "Data/AI" not in ALLOWED_ROLES


# --- recommendations[role].urgency ------------------------------------------


def test_urgency_valid_is_preserved():
    recs = {"Security": _rec(urgency="high")}
    out = _validate_recommendations(recs, ["Security"])
    assert out["Security"]["urgency"] == "high"


def test_urgency_invalid_value_falls_back_to_medium():
    recs = {"Security": _rec(urgency="critical")}  # 'critical' ∉ tập đóng
    out = _validate_recommendations(recs, ["Security"])
    assert out["Security"]["urgency"] == "medium"
    assert out["Security"]["action_type"] == "read"  # entry KHÔNG bị drop


def test_urgency_missing_key_falls_back_to_medium():
    """Insight cũ không có khoá urgency → medium → không alert hồi tố."""
    recs = {"Security": _rec()}
    out = _validate_recommendations(recs, ["Security"])
    assert out["Security"]["urgency"] == "medium"


def test_urgency_values_are_closed_set():
    assert ALLOWED_ROLE_URGENCY == ["high", "medium", "low"]
    assert "critical" not in ALLOWED_ROLE_URGENCY


def test_role_outside_affected_roles_still_dropped():
    """Hành vi cũ không đổi."""
    recs = {"Dev": _rec(urgency="high")}
    assert _validate_recommendations(recs, ["Security"]) is None
