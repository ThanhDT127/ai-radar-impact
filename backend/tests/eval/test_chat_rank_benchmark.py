"""Benchmark xếp hạng chạy TRONG `pytest` mặc định — không skip, không gọi model.

Khác `test_gate_benchmark.py` và `test_chat_answer_eval.py` ở đúng một điểm: thứ đo ở đây là
hàm thuần của chúng ta, nên nó miễn phí và tất định ⇒ chạy được mọi lần, không cần cờ.

Đo lại thủ công (có bảng đầy đủ + chi tiết từng miss):
    docker compose exec backend python -m tests.eval.chat_rank_harness
"""

import pytest

from app.config import settings
from tests.eval.chat_rank_harness import (
    ANSWER_BUDGET,
    _NoModel,
    load_baseline,
    measure,
    verdict,
)
from tests.eval.chat_fixture import load_scenarios


def test_benchmark_does_not_regress_against_baseline():
    """Lưới chính: recall@K hoặc recall@5 tụt so với baseline ⇒ đỏ, nêu đích danh câu nào."""
    baseline = load_baseline()
    assert baseline, "chưa có baseline: chạy `chat_rank_harness --freeze-baseline` một lần"

    passed, reasons = verdict(measure(), baseline)
    assert passed, "\n".join(reasons)


def test_a_single_question_dropping_fails_and_is_named():
    """Hồi quy tập trung ở MỘT câu phải đỏ, kể cả khi trung bình tổng gần như không đổi.

    Đây là ca 4b.2: recall tổng 42% mà riêng một chủ đề còn 11% — "tổng 88%" không nói được
    câu nào vỡ. Giả lập bằng cách hạ recall của đúng một kịch bản rồi so với baseline thật.
    """
    baseline = load_baseline()
    result = measure()

    victim = next(r for r in result["rows"] if r["recall_at_answer"] not in (None, 0.0))
    victim["recall_at_answer"] = 0.0

    passed, reasons = verdict(result, baseline)
    assert not passed
    assert any(victim["scenario_id"] in reason for reason in reasons), (
        f"harness fail nhưng không gọi tên {victim['scenario_id']}: {reasons}"
    )


def test_benchmark_is_deterministic():
    """Chạy hai lần trên cùng fixture và cùng code phải cho kết quả giống hệt."""
    first, second = measure(), measure()
    assert first["overall"] == second["overall"]
    assert first["overall_at_answer"] == second["overall_at_answer"]
    assert [r["worst_rank"] for r in first["rows"]] == [r["worst_rank"] for r in second["rows"]]


def test_benchmark_reads_k_from_settings_not_a_hardcoded_number():
    """Đổi `chat_index_top_k` phải đổi phép đo — hằng số chép cứng là đo sai một cách im lặng."""
    assert measure()["top_k"] == settings.chat_index_top_k


def test_benchmark_cannot_call_a_model():
    """Bất biến 'miễn phí' được bảo đảm bằng cấu trúc: client model nổ khi bị chạm tới."""
    with pytest.raises(AssertionError, match="phải thuần và miễn phí"):
        _NoModel().chat


def test_question_set_covers_every_known_failure_mode():
    """Bộ câu phải phủ đủ 6 nhóm của design D4 — thiếu nhóm nào là mù đúng chỗ đó."""
    groups = {s["group"] for s in load_scenarios()}
    required = {
        "open_model": "(a) chủ đề ngách, urgency thấp — ca 4b.2",
        "ascii_short": "(b) từ khoá ASCII hai ký tự",
        "role": "(c) câu nêu tên vai trò",
        "role_trap": "(d) từ chứa tên vai trò làm chuỗi con (device/DevOps)",
        "generic": "(e) câu chung chung, không từ khoá đặc trưng",
        "role_empty": "(f) vai trò không có tin nào ảnh hưởng",
    }
    missing = {g: why for g, why in required.items() if g not in groups}
    assert not missing, f"bộ câu hỏi thiếu nhóm: {missing}"


def test_answer_budget_matches_the_prompt_it_models():
    """recall@5 chỉ có nghĩa khi 5 đúng là trần tin mà `CHAT_SYSTEM_PROMPT` cho phép."""
    from app.ai.prompts import CHAT_SYSTEM_PROMPT

    assert f"TỐI ĐA {ANSWER_BUDGET} tin" in CHAT_SYSTEM_PROMPT, (
        "trần tin trong prompt đã đổi — sửa ANSWER_BUDGET và chốt lại baseline, "
        "đừng để bộ đo mô hình hoá một luật không còn tồn tại"
    )


def test_expanded_scenarios_exclude_their_anchor_from_the_index():
    """Mode mở rộng loại bài đang xem khỏi index toàn cục — bộ đo phải loại y hệt."""
    from tests.eval.chat_rank_harness import _candidates
    from tests.eval.chat_fixture import load_corpus, rehydrate_corpus

    corpus = rehydrate_corpus(load_corpus())
    expanded = next(s for s in load_scenarios() if s["mode"] == "expanded")

    ids = {str(i.id) for i in _candidates(expanded, corpus)}
    assert expanded["anchor_insight_id"] not in ids
    assert len(ids) == len(corpus) - 1
