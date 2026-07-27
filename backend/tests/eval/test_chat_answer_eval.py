"""Bảo vệ chính bộ đo chất lượng câu trả lời chat.

Các test ở đây **KHÔNG gọi model** — chúng giữ cho fixture còn đủ, nhãn tay còn nhất quán,
phép chấm cấu trúc còn nhạy, và số đã chốt còn tái lập được từ snapshot. Phần sinh câu trả
lời + LLM-judge nằm sau cờ `CHAT_EVAL_LIVE=1` vì 114 lượt gọi (~$0,66) là quá đắt cho một
suite test chạy thường xuyên.

Đo lại thật:
    docker compose exec backend python -m tests.eval.chat_answer_harness --live
"""

import json
import os

import pytest

from tests.eval.chat_answer_harness import (
    CITATION_PRECISION_FLOOR,
    FAITHFULNESS_FLOOR,
    citation_precision,
    load_baseline,
    load_snapshot,
    score,
    verdict,
)
from tests.eval.chat_fixture import SCENARIO_MODES, load_anchors, load_corpus, load_scenarios

LIVE_ENABLED = os.getenv("CHAT_EVAL_LIVE") == "1"


def test_scenarios_cover_all_three_modes():
    scenarios = load_scenarios()
    assert len(scenarios) >= 50, "bộ kịch bản đóng băng là ~50 câu, đừng để teo lại"

    by_mode = {mode: [s for s in scenarios if s["mode"] == mode] for mode in SCENARIO_MODES}
    for mode, rows in by_mode.items():
        assert rows, f"mất sạch kịch bản mode {mode}"
    # `expanded` là đường sinh câu trả lời dễ sai grounding nhất (chat-scope-routing) —
    # bộ đo mất nhóm này thì mất đúng chỗ đáng đo nhất.
    assert len(by_mode["expanded"]) >= 10


def test_every_scenario_has_a_readable_label():
    for scenario in load_scenarios():
        assert scenario["label_reason"].strip(), scenario["id"]
        assert len(scenario["label_reason"]) > 20, (
            f"{scenario['id']}: lý do nhãn quá ngắn để kiểm lại được"
        )


def test_anchors_carry_real_article_content():
    """Mode B nạp toàn văn bài gốc — anchor rỗng nghĩa là đang đo trên context nghèo hơn thật."""
    anchors = load_anchors()
    assert anchors
    for insight_id, content in anchors.items():
        assert len(content) > 200, f"{insight_id}: nội dung bài gốc quá ngắn, purge rồi?"


def test_loader_rejects_label_pointing_outside_corpus(tmp_path):
    """Nhãn trỏ tin không có trong corpus phải chặn ngay, đừng chấm tiếp rồi báo số sai."""
    scenario = load_scenarios()[0] | {
        "must_have": ["00000000-0000-0000-0000-000000000000"],
    }
    bad = tmp_path / "bad.jsonl"
    bad.write_text(json.dumps(scenario, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="không có trong corpus"):
        load_scenarios(bad)


def test_corpus_loader_rejects_missing_field(tmp_path):
    """Fixture thiếu field mà pipeline thật đọc = đo trên đầu vào nghèo hơn production."""
    from tests.eval.chat_fixture import load_corpus as load

    row = dict(load_corpus()[0])
    row.pop("recommendations")
    stale = tmp_path / "stale.jsonl"
    stale.write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="thiếu field"):
        load(stale)


def test_citation_precision_catches_fabricated_marker():
    """Phép chấm citation phải nhạy với marker bịa — và không gọi model."""
    served = {"1": "aaaaaaaa-0000-0000-0000-000000000000"}

    clean, bogus = citation_precision({"raw_answer": "Tin A [1].", "served": served})
    assert (clean, bogus) == (1.0, [])

    dirty, bogus = citation_precision({"raw_answer": "Tin A [1] và tin B [7].", "served": served})
    assert dirty == 0.5
    assert bogus == [7], "phải nêu đích danh marker bịa, không chỉ hạ điểm"


def test_citation_precision_measured_before_grounding_strips_markers():
    """Marker bịa chỉ còn thấy được trên câu trả lời THÔ.

    `resolve_citations` xoá mọi marker ngoài bảng ánh xạ, nên nếu bộ đo lỡ chấm trên
    `answer` đã dọn thì điểm luôn 1,00 và bộ đo trở thành đồ trang trí. Test này khoá đúng
    thứ tự đó.
    """
    from app.services.chat_grounding import resolve_citations

    raw = "Tin A [1] và tin bịa [7]."
    cleaned, _ = resolve_citations(raw, {1: _FakeInsight()})
    assert "[7]" not in cleaned

    served = {"1": "aaaaaaaa-0000-0000-0000-000000000000"}
    assert citation_precision({"raw_answer": raw, "served": served})[0] == 0.5
    assert citation_precision({"raw_answer": cleaned, "served": served})[0] == 1.0


class _FakeInsight:
    id = "aaaaaaaa-0000-0000-0000-000000000000"
    title = "Tin A"
    source_url = "https://example.test/a"


def test_snapshot_covers_every_scenario():
    """Snapshot phải phủ ĐỦ bộ kịch bản.

    `chat_scenarios.jsonl` là nguồn nhãn tay dùng chung với benchmark xếp hạng, nên nó sẽ được
    thêm câu (ví dụ `chat-rank-stability` thêm nhóm probe 27/07). Thêm câu mà quên đo thì bộ đo
    này lặng lẽ báo cáo trên tập nhỏ hơn — đúng loại hỏng im lặng mà cả hai bộ đo sinh ra để
    chặn. Đo bù rẻ: `--live --only <id1>,<id2>`.
    """
    measured = {r["scenario_id"] for r in load_snapshot()}
    declared = {s["id"] for s in load_scenarios()}

    missing = sorted(declared - measured)
    assert not missing, (
        f"{len(missing)} kịch bản chưa có câu trả lời trong snapshot: {missing}. "
        f"Chạy `--live --only {','.join(missing[:3])}` rồi chốt lại baseline."
    )


def test_snapshot_reproduces_frozen_baseline():
    """Chấm lại snapshot phải ra đúng số đã chốt — công thức không được trôi âm thầm."""
    baseline = load_baseline()
    assert baseline, "chưa có baseline: chạy `--live --freeze-baseline` một lần"

    scored = score(load_snapshot())
    for metric, value in baseline["overall"].items():
        assert scored["overall"][metric] == pytest.approx(value, abs=1e-9), metric


def test_frozen_baseline_meets_hard_thresholds():
    """Baseline đã chốt phải tự nó đạt ngưỡng cứng — không chốt một baseline đang hỏng."""
    baseline = load_baseline()
    assert baseline["overall"]["faithfulness"] >= FAITHFULNESS_FLOOR
    assert baseline["overall"]["citation_precision"] >= CITATION_PRECISION_FLOOR


def test_gate_fails_when_a_citation_is_fabricated():
    """Một citation bịa là đủ để FAIL — ngưỡng citation tuyệt đối, không có dung sai."""
    records = load_snapshot()
    poisoned = [dict(r) for r in records]
    poisoned[0] = poisoned[0] | {
        "raw_answer": (poisoned[0].get("raw_answer") or "") + " thêm nguồn ma [999].",
    }

    passed, reasons = verdict(score(poisoned), load_baseline())
    assert not passed
    assert any("Citation Precision" in r for r in reasons)
    assert any(poisoned[0]["scenario_id"] in r for r in reasons), "phải gọi tên kịch bản hỏng"


def test_gate_fails_when_faithfulness_drops():
    """Faithfulness tụt dưới 0,95 phải FAIL và nêu tên kịch bản kéo điểm xuống."""
    records = [dict(r) for r in load_snapshot()]
    for record in records[:6]:
        record["faithfulness"] = {"score": 0.0, "claims": []}

    passed, reasons = verdict(score(records), load_baseline())
    assert not passed
    assert any("Faithfulness" in r for r in reasons)


@pytest.mark.skipif(not LIVE_ENABLED, reason="cần CHAT_EVAL_LIVE=1 — 114 lượt gọi, ~$0,66")
def test_live_pipeline_meets_gate():
    """Đo lại thật: pipeline chat hiện hành phải đạt ngưỡng gate."""
    import asyncio

    from tests.eval.chat_answer_harness import generate, judge_all

    records = asyncio.run(generate(load_scenarios()))
    judge_all(records)
    passed, reasons = verdict(score(records), load_baseline())
    assert passed, "; ".join(reasons)
