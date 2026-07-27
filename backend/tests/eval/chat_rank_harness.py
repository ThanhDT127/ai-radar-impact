"""Benchmark recall của TẦNG XẾP HẠNG chat (`_rank`) — thuần, miễn phí, tất định.

Vì sao tồn tại: `_rank()` quyết định tin nào lọt vào index gửi cho model. Cắt sai ở đây thì
model **không bao giờ nhìn thấy** tin đúng — và vẫn trả lời trôi chảy từ phần còn lại. Đó là
chế độ hỏng `chatbot-qa` 4b.2 đã đo: recall tổng 42%, riêng câu "mô hình mã nguồn mở" còn
2/18 tin (11%). Bản sửa đưa lên ~91%, nhưng con số đó **chưa từng được commit** — bốn file
test chat hiện có đều bảo vệ *cơ chế* (grounding, quota, mode routing), không file nào bảo vệ
*chất lượng xếp hạng*. Đây là thứ duy nhất bắt được hồi quy đó.

CHẠY
    docker compose exec backend python -m tests.eval.chat_rank_harness      # báo cáo đầy đủ
    docker compose exec backend python -m tests.eval.chat_rank_harness --freeze-baseline
    docker compose exec backend python -m pytest tests/eval/ -q             # chạy luôn trong suite

**KHÔNG có `--live`, không tốn đồng nào, không đụng model.** Khác `tests.eval.harness` (gate) và
`tests.eval.chat_answer_harness` (chất lượng câu trả lời) ở đúng điểm đó: thứ đo ở đây là **code
của chúng ta**, không phải phán đoán của model. Nên nó chạy được trong `pytest` mặc định.

KHI NÀO **BẮT BUỘC** CHẠY LẠI
    Sửa bất kỳ thứ nào sau đây: `_rank`, `_relevance`, `_question_terms`, `_roles_in_question`,
    `STOPWORDS` (`chat_service_terms.py`), `score_for_role` / `role_urgency` /
    `has_practical_indicator` (`delivery_engine.py`), hoặc `settings.chat_index_top_k`.
    Harness đọc K từ `settings.chat_index_top_k` chứ không chép cứng — đổi K là đổi phép đo.

LUẬT BASELINE
    Baseline đầu tiên chốt trên code **chưa sửa gì**. Mỗi lần một thay đổi **có chủ đích** làm
    recall tăng, phải **chốt lại baseline ở mức mới** kèm lý do. Không chốt lại thì guard vẫn nằm
    ở mức cũ thấp hơn, và một lần revert sẽ tụt về đúng baseline cũ ⇒ **harness pass, lỗi quay lại
    im lặng**. Đó chính là ca harness sinh ra để chặn. Chốt lại để test chuyển xanh là tự tháo lưới.

ĐỌC KẾT QUẢ
    recall@K  = |must_have ∩ top-K| / |must_have|. `must_have` là nhãn tay: tin mà **bỏ sót là
                hỏng rõ ràng** (design D3). Câu không có `must_have` in `—` và không vào trung bình.
    KHÔNG có precision — cố ý (D3). Tin lạc đề lọt vào index chỉ tốn ~108 token và model đã bị dặn
    "tối đa 5 tin"; tin đúng bị cắt thì mất hẳn. Bất đối xứng này giống FN-tệ-hơn-FP của gate.
    Mỗi miss in kèm **thứ hạng thật** của tin bị cắt — số đó cho biết trượt sát nút hay trượt xa.

GIỚI HẠN DIỄN GIẢI
    - Fixture là ảnh chụp corpus 27/07/2026 (179 tin). Đo **hồi quy so với chính nó**; recall@60
      trên 179 tin KHÔNG suy ra recall@60 trên 1000 tin. Corpus lớn lên đáng kể thì sinh lại
      fixture và chốt lại baseline, đừng suy diễn.
    - Nhóm nào chỉ có 1 câu thì đọc như **tín hiệu**, không phải bằng chứng (cùng cảnh báo n<5 của
      gate harness).
    - Nhãn tay chủ quan → mỗi `must_have` có `label_reason` đọc được trong `chat_scenarios.jsonl`.
"""

import argparse
import json
from pathlib import Path

from app.config import settings
from app.services.chat_service import ChatService, _question_terms, _roles_in_question
from tests.eval.chat_fixture import (
    FIXTURE_DIR,
    load_corpus,
    load_scenarios,
    rehydrate_corpus,
)

BASELINE_PATH = FIXTURE_DIR / "chat_rank_baseline.json"

BASELINE_META = {
    "measured_at": "2026-07-27",
    "commit": "a00fe2e",
    "corpus": "chat_corpus.jsonl @ 27/07/2026 — 179 insight published+is_primary",
    "note": "chốt trên code CHƯA sửa (`_roles_in_question` còn khớp chuỗi con)",
    "revisions": [
        {
            "date": "2026-07-27",
            "recall_at_k": "1,000 → 0,988",
            "recall_at_answer": "0,812 → 0,812",
            "reason": (
                "`chat-citation-integrity` 4.1: `_relevance` đổi sang khớp theo BIÊN TỪ. "
                "recall@60 giảm vì `exp-gemma-to-eol` mất một khớp NHẦM (`kế` khớp chuỗi con "
                "trong `kết`) — tin Cypress trước nay lọt top-60 nhờ tai nạn. recall@5 net "
                "không đổi: `glo-open-model-analysis` +0,50, `exp-nettacker-to-vnpost` −0,50 "
                "(`sql` không còn khớp `MySQL`). Chi tiết + ba kết luận ở "
                "openspec/changes/chat-citation-integrity/measurement.md."
            ),
        }
    ],
}

# Dung sai: recall là tỉ lệ trên tập must_have nhỏ, một tin trượt đã đổi 0,33 ở câu 3 tin.
# So bằng tuyệt đối sẽ fail giả khi thêm/bớt kịch bản; dung sai này là "tụt thật sự".
TOLERANCE = 0.01

# Trần số tin model được phép dùng trong MỘT câu trả lời (`CHAT_SYSTEM_PROMPT`: "TỐI ĐA 5 tin").
# recall@60 đo "tin có lọt index không"; recall@5 đo "tin có thực sự tới tay người đọc không".
# Đo 27/07/2026: recall@60 bão hoà 1,000 trên cả 47 câu ⇒ tự nó không bắt được hồi quy nào
# nhỏ hơn "văng khỏi top-60". recall@5 và `worst_rank` mới là phần nhạy.
ANSWER_BUDGET = 5


class _NoModel:
    """Client model NỔ khi bị chạm tới.

    `_rank` là method của `ChatService` nên phải gọi qua một instance. Thay vì tạo
    `GeminiClient` thật (cần credentials, và mở đường cho một lượt gọi lọt vào bộ đo lẽ ra
    miễn phí), tiêm cái này: mọi truy cập thuộc tính đều ném lỗi. Bộ đo **không thể** gọi
    model — đó là bất biến được bảo đảm bằng cấu trúc, không phải bằng lời hứa.
    """

    def __getattr__(self, name):
        raise AssertionError(
            f"Benchmark xếp hạng vừa chạm tới model (`{name}`) — nó phải thuần và miễn phí. "
            "Xem lại thay đổi vừa rồi ở `_rank`."
        )


def _rank(candidates: list, question: str) -> list:
    """`ChatService._rank` thật, gắn vào một service không có DB và không có model."""
    service = ChatService(session=None, gemini=_NoModel())
    return service._rank(candidates, question)


def _candidates(scenario: dict, corpus: list) -> list:
    """Tập ứng viên ĐÚNG như `_answer_global` dựng ra cho kịch bản đó.

    Chế độ mở rộng loại bài đang xem khỏi index toàn cục (nó đã đi kèm ở `[1]`), nên harness
    phải loại y hệt — không thì đo trên tập ứng viên khác production.
    """
    anchor = scenario.get("anchor_insight_id")
    if scenario["mode"] == "expanded" and anchor:
        return [i for i in corpus if str(i.id) != anchor]
    return list(corpus)


def measure(scenarios: list[dict] | None = None) -> dict:
    """Chạy `_rank()` thật trên fixture. Không gọi model, tất định."""
    scenarios = scenarios if scenarios is not None else load_scenarios()
    # Mode B không đi qua `_rank` (context là đúng 1 bài) — đo nó ở đây là đo cái không tồn tại.
    scenarios = [s for s in scenarios if s["mode"] != "insight"]

    corpus = rehydrate_corpus(load_corpus())
    top_k = settings.chat_index_top_k
    rows = []

    for scenario in scenarios:
        candidates = _candidates(scenario, corpus)
        ranked = _rank(candidates, scenario["question"])
        position = {str(insight.id): n for n, insight in enumerate(ranked, start=1)}
        selected = {str(i.id) for i in (ranked[:top_k] if top_k > 0 else ranked)}

        must = scenario.get("must_have") or []
        # Thứ hạng thật của từng tin bắt buộc. Đây là đại lượng NHẠY: recall@60 trên corpus
        # 179 tin bão hoà ở 1,00 (đo 27/07) nên tự nó không phân biệt được gì — xem
        # `recall_at_answer` và `worst_rank` bên dưới.
        ranks = [position.get(i) for i in must]
        misses = [
            {
                "insight_id": insight_id,
                "title": next(
                    (i.title for i in corpus if str(i.id) == insight_id), "?"
                ),
                "rank": position.get(insight_id),
            }
            for insight_id in must
            if insight_id not in selected
        ]
        rows.append(
            {
                "scenario_id": scenario["id"],
                "group": scenario["group"],
                "mode": scenario["mode"],
                "question": scenario["question"],
                "recall": (len(must) - len(misses)) / len(must) if must else None,
                # Trần thật của câu trả lời là 5 tin (`CHAT_SYSTEM_PROMPT`), không phải 60.
                # Tin xếp hạng 40 tuy lọt index nhưng model gần như chắc chắn không dùng tới —
                # đúng cảnh 4b.2: "model vẫn trả lời trôi chảy từ 2 tin sót lại".
                "recall_at_answer": (
                    sum(1 for r in ranks if r is not None and r <= ANSWER_BUDGET) / len(must)
                    if must
                    else None
                ),
                "worst_rank": max((r for r in ranks if r is not None), default=None),
                "must_total": len(must),
                "misses": misses,
                "terms": _question_terms(scenario["question"]),
                "roles": _roles_in_question(scenario["question"]),
            }
        )

    scored = [r["recall"] for r in rows if r["recall"] is not None]
    at_answer = [r["recall_at_answer"] for r in rows if r["recall_at_answer"] is not None]
    return {
        "top_k": top_k,
        "answer_budget": ANSWER_BUDGET,
        "corpus_size": len(corpus),
        "rows": rows,
        "overall": sum(scored) / len(scored) if scored else None,
        "overall_at_answer": sum(at_answer) / len(at_answer) if at_answer else None,
        "questions_scored": len(scored),
    }


def verdict(result: dict, baseline: dict | None) -> tuple[bool, list[str]]:
    """FAIL khi recall tổng tụt, HOẶC bất kỳ câu nào tụt so với baseline của chính nó."""
    if not baseline:
        return True, []

    reasons = []
    for key, label in (("overall", f"recall@{result['top_k']}"),
                       ("overall_at_answer", f"recall@{result['answer_budget']}")):
        now, before = result[key], baseline.get(key)
        if now is not None and before is not None and now < before - TOLERANCE:
            reasons.append(
                f"{label} tổng {now:.3f} tụt dưới baseline {before:.3f} (dung sai {TOLERANCE})"
            )

    base_rows = {r["scenario_id"]: r for r in baseline["rows"]}
    for row in result["rows"]:
        base = base_rows.get(row["scenario_id"], {})
        for key, label in (("recall", f"recall@{result['top_k']}"),
                           ("recall_at_answer", f"recall@{result['answer_budget']}")):
            before, now = base.get(key), row[key]
            if before is None or now is None or now >= before - TOLERANCE:
                continue
            detail = "; ".join(
                f"cắt mất «{m['title'][:44]}» (hạng thật {m['rank']})" for m in row["misses"]
            ) or f"tin bắt buộc tụt xuống hạng {row['worst_rank']}"
            reasons.append(
                f"{row['scenario_id']} ({row['group']}): {label} {now:.2f} tụt từ {before:.2f} — {detail}"
            )

    # Kịch bản mới chưa có trong baseline: không fail, nhưng phải nói ra — im lặng thì
    # người đọc tưởng baseline đang phủ hết.
    new = [r["scenario_id"] for r in result["rows"] if r["scenario_id"] not in base_rows]
    if new:
        reasons.append(
            f"CHÚ Ý (không phải fail): {len(new)} kịch bản chưa có trong baseline "
            f"({', '.join(new[:6])}) — chốt lại baseline kèm lý do."
        )
        return not [r for r in reasons if not r.startswith("CHÚ Ý")], reasons

    return not reasons, reasons


def format_report(result: dict, baseline: dict | None) -> str:
    base_rows = {r["scenario_id"]: r for r in (baseline or {}).get("rows", [])}
    lines = [
        f"Corpus {result['corpus_size']} tin · K = {result['top_k']} "
        f"(settings.chat_index_top_k) · {result['questions_scored']} câu có nhãn must_have",
        "",
    ]
    header = (f"{'kịch bản':<28}{'nhóm':<14}{'r@' + str(result['top_k']):>6}{'':<6}"
              f"{'r@' + str(result['answer_budget']):>5}{'':<6}{'hạng xấu nhất':>13}  "
              f"{'trục vai trò':<18}từ khoá")
    lines.append(header)
    lines.append("-" * 118)

    for row in sorted(result["rows"], key=lambda r: (r["group"], r["scenario_id"])):
        base = base_rows.get(row["scenario_id"], {})

        def cell(key):
            value = row[key]
            text = "   — " if value is None else f"{value:>5.2f}"
            before = base.get(key)
            delta = "     "
            if value is not None and before is not None:
                diff = value - before
                delta = "    =" if abs(diff) < 1e-9 else f" {'▲' if diff > 0 else '▼'}{abs(diff):.2f}"
            return text, delta

        recall, d_recall = cell("recall")
        answer, d_answer = cell("recall_at_answer")
        worst = "  —" if row["worst_rank"] is None else str(row["worst_rank"])
        roles = ", ".join(row["roles"]) or "(không có)"
        terms = ", ".join(row["terms"][:4]) or "(rỗng — mọi từ là stopword)"
        lines.append(
            f"{row['scenario_id']:<28}{row['group']:<14}{recall}{d_recall:<6}"
            f"{answer}{d_answer:<6}{worst:>13}  {roles:<18}{terms}"
        )
        for miss in row["misses"]:
            lines.append(
                f"    ❌ cắt mất «{miss['title'][:56]}» — hạng thật {miss['rank']}/{result['corpus_size']}"
            )

    lines.append("")
    lines.append("Theo nhóm:")
    groups: dict[str, list] = {}
    for row in result["rows"]:
        groups.setdefault(row["group"], []).append(row)
    for group, rows in sorted(groups.items()):
        def mean(key):
            values = [r[key] for r in rows if r[key] is not None]
            return f"{sum(values) / len(values):.2f}" if values else "  — "

        flag = "   (n=1, chỉ là tín hiệu)" if len(rows) == 1 else ""
        lines.append(
            f"  {group:<14} n={len(rows):<3} r@{result['top_k']}={mean('recall')} "
            f"r@{result['answer_budget']}={mean('recall_at_answer')}{flag}"
        )

    lines.append("")
    for key, label in (("overall", f"recall@{result['top_k']:<3}"),
                       ("overall_at_answer", f"recall@{result['answer_budget']:<3}")):
        value = result[key]
        base = f"   (baseline {baseline[key]:.3f})" if baseline and baseline.get(key) is not None else "   (chưa có baseline)"
        lines.append(f"TỔNG {label} = " + ("  —  " if value is None else f"{value:.3f}") + base)
    lines.append(
        f"      recall@{result['top_k']} bão hoà là BÌNH THƯỜNG trên corpus {result['corpus_size']} tin — "
        f"phần nhạy là recall@{result['answer_budget']} và cột hạng xấu nhất."
    )
    return "\n".join(lines)


def load_baseline(path: Path = BASELINE_PATH) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark recall xếp hạng chat (0 lượt gọi model)")
    parser.add_argument("--freeze-baseline", action="store_true",
                        help="ghi kết quả hiện tại thành baseline — CÓ CHỦ ĐÍCH, kèm lý do")
    args = parser.parse_args()

    result = measure()
    baseline = load_baseline()
    print(format_report(result, baseline))

    passed, reasons = verdict(result, baseline)
    print()
    print(f"VERDICT: {'PASS ✅' if passed else 'FAIL ❌'}")
    for reason in reasons:
        print(f"  - {reason}")

    if args.freeze_baseline:
        BASELINE_PATH.write_text(
            json.dumps({"meta": BASELINE_META, **result}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"\nĐã chốt baseline vào {BASELINE_PATH} — nhớ ghi LÝ DO vào commit.")

    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
