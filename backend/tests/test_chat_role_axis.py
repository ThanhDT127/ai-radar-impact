"""Nhận diện vai trò trong câu hỏi phải khớp theo BIÊN TỪ, không phải chuỗi con.

Vì sao đáng một file riêng: nhận nhầm vai trò **đổi cả trục xếp hạng** của toàn bộ danh sách
(`importance()` chuyển từ `max` trên `affected_roles` sang `score_for_role(insight, role)`), và
kéo theo cả tuyên bố "hệ thống không có tin nào cho vai trò X". Hỏng lặng lẽ, không log, không
dấu hiệu — đúng loại lỗi không ai phát hiện bằng mắt.

Quay `_roles_in_question` về `role.lower() in question.lower()` thì ít nhất 3 test ở đây đỏ.
"""

import pytest

from app.ai.prompts import ALLOWED_ROLES
from app.services.chat_service import _roles_in_question


@pytest.mark.parametrize(
    "question",
    [
        "tin về device IoT mới",
        "thiết bị device nào bị lỗi",
        "device management có gì mới",
    ],
)
def test_device_does_not_yield_dev(question):
    """`device` chứa `dev` — công ty có trụ cột IoT/Smart Home nên từ này xuất hiện dày đặc."""
    assert "Dev" not in _roles_in_question(question)


def test_devops_does_not_yield_dev():
    """`DevOps` thuộc taxonomy `Source.target_roles`, KHÔNG thuộc `ALLOWED_ROLES` — sai hai lần."""
    assert _roles_in_question("DevOps cần chú ý gì") == []


def test_single_word_role_still_matches():
    assert _roles_in_question("Dev cần làm gì tuần này") == ["Dev"]


@pytest.mark.parametrize(
    "question,expected",
    [
        ("Data Analyst có tin nào không", "Data Analyst"),
        ("tin cho Người dùng phổ thông", "Người dùng phổ thông"),
        ("bên Data Engineer nên đọc gì", "Data Engineer"),
    ],
)
def test_multi_word_roles_match_whole_phrase(question, expected):
    """Vai trò nhiều token phải khớp TRỌN CỤM và LIÊN TIẾP — không so tập hợp token."""
    assert expected in _roles_in_question(question)


def test_multi_word_role_not_matched_when_tokens_are_scattered():
    """Đủ token nhưng không liên tiếp thì KHÔNG phải nhắc tên vai trò.

    Đây là lý do phải so dãy con liên tiếp thay vì so tập hợp: "phổ thông" và "người dùng"
    đứng rời nhau là câu tiếng Việt bình thường, không phải đang gọi tên vai trò.
    """
    assert "Người dùng phổ thông" not in _roles_in_question(
        "phổ thông hoá tài liệu cho người dùng cuối"
    )


def test_question_without_role_selects_no_axis():
    assert _roles_in_question("có gì mới không") == []


def test_case_and_diacritics_insensitive_within_word_boundary():
    assert "Security" in _roles_in_question("bên SECURITY cần chú ý gì")
    assert "Tech Lead" in _roles_in_question("tech lead nên biết gì")


def test_every_allowed_role_is_detectable_when_named():
    """Không vai trò nào bị luật biên từ làm cho không thể nhận ra."""
    for role in ALLOWED_ROLES:
        assert role in _roles_in_question(f"tin cho {role} tuần này"), role


def test_substring_roles_do_not_leak_into_other_role_names():
    """`Dev` là chuỗi con của `Data Engineer`? không — nhưng `Dev` vs `DevOps` thì có.

    Khẳng định cụ thể: hỏi đúng `Data Engineer` thì KHÔNG kéo theo vai trò nào khác.
    """
    assert _roles_in_question("Data Engineer nên đọc tin nào") == ["Data Engineer"]
