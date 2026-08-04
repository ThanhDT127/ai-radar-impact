"""Bảo vệ tính toàn vẹn của benchmark gate.

Các test ở đây KHÔNG gọi model — chúng bảo vệ *chính bộ đo*: fixture còn đủ, còn khớp cửa
sổ gate thật, và công thức matrix còn tái lập được số đã chốt. Phần đo lại bằng Vertex nằm
sau cờ `GATE_EVAL_LIVE=1` vì 54 lượt gọi mỗi lần chạy là quá đắt cho một suite test.

Đo lại thật:
    docker compose exec backend python -m tests.eval.harness --live
"""

import os

import pytest

from app.ai.prompts import GATE_CONTENT_LIMIT
from tests.eval.harness import (
    BASELINE_2026_07_21,
    build_matrix,
    load_fixture,
    predict_new,
    predict_old,
    run_live,
)

LIVE_ENABLED = os.getenv("GATE_EVAL_LIVE") == "1"


def test_fixture_loads_and_is_complete():
    samples = load_fixture()
    assert len(samples) == 54, "mẫu đóng băng của w4-gate-accuracy là 54 doc"
    assert sum(1 for s in samples if s["human_label"] == "SIGNAL") == 34
    assert sum(1 for s in samples if s["human_label"] == "NOISE") == 20


def test_fixture_content_window_matches_real_gate():
    """Fixture phải cắt đúng bằng cửa sổ `build_gate_prompt` đọc.

    Đây là chốt chặn cho ca hỏng im lặng: đổi `GATE_CONTENT_LIMIT` mà quên sinh lại fixture
    thì benchmark vẫn chạy, vẫn ra số, nhưng đo trên đầu vào khác production.
    """
    for sample in load_fixture():
        assert sample["content_truncated_at"] == GATE_CONTENT_LIMIT
        assert len(sample["content"]) <= GATE_CONTENT_LIMIT
        assert sample["content"].strip(), f"{sample['doc_id']}: content rỗng"


def test_fixture_rejects_stale_content_window(tmp_path, monkeypatch):
    """Loader phải TỪ CHỐI fixture lệch cửa sổ, không đo tiếp rồi báo số sai."""
    import json

    stale = tmp_path / "stale.jsonl"
    sample = load_fixture()[0] | {"content_truncated_at": GATE_CONTENT_LIMIT + 1}
    stale.write_text(json.dumps(sample, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Sinh lại fixture"):
        load_fixture(stale)


def test_baseline_matrix_reproduces_measurement():
    """Công thức matrix phải cho đúng bảng đã chốt 21/07/2026 (acc 94% / rec 100% / prec 92%)."""
    matrix = build_matrix(load_fixture(), predict_new)

    assert matrix.as_dict() == BASELINE_2026_07_21
    assert round(matrix.accuracy, 2) == 0.94
    assert round(matrix.recall, 2) == 1.00
    assert round(matrix.precision, 2) == 0.92


def test_old_gate_matrix_reproduces_measurement():
    """Matrix "trước" — recall 53%, 16 tin tốt bị giết nhầm."""
    matrix = build_matrix(load_fixture(), predict_old)

    assert matrix.as_dict() == {"tp": 18, "fp": 0, "fn": 16, "tn": 20}
    assert round(matrix.accuracy, 2) == 0.70
    assert round(matrix.recall, 2) == 0.53


@pytest.mark.skipif(not LIVE_ENABLED, reason="cần GATE_EVAL_LIVE=1 — 54 lượt gọi Vertex")
def test_live_gate_matches_baseline():
    """Đo lại thật: `GATE_PROMPT` hiện hành không được hồi quy so với baseline 21/07."""
    samples = load_fixture()
    live = run_live(samples)
    matrix = build_matrix(samples, lambda s: live[s["doc_id"]])

    assert matrix.fn == 0, "gate đang giết nhầm tin SIGNAL — hồi quy nghiêm trọng"
    assert matrix.as_dict() == BASELINE_2026_07_21
