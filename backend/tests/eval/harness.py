"""Benchmark độ chính xác tiêu chí gate — 54 mẫu gán nhãn tay, tự chứa.

Vì sao tồn tại: không có unit test nào bảo vệ *tiêu chí* gate (khác với `test_gate_skipped.py`
bảo vệ *cơ chế*). Đây là thứ duy nhất phát hiện được hồi quy khi sửa `GATE_PROMPT`, và hồi quy
đó vô hình trong production — gate loại thì doc thành `low_signal` và không bao giờ lên UI để
ai đó nhận ra.

CHẠY
    docker compose exec backend python -m tests.eval.harness          # offline, 0 đồng, tức thì
    docker compose exec backend python -m tests.eval.harness --live    # đo lại thật bằng Vertex
    docker compose exec backend python -m pytest tests/eval/ -q        # live bị skip mặc định
    docker compose exec -e GATE_EVAL_LIVE=1 backend python -m pytest tests/eval/ -q

CHI PHÍ `--live`
    54 lượt gọi, prompt ngắn → dưới ~$0,10 một lần chạy, mất vài phút vì gọi tuần tự.
    ⚠️ Gọi thẳng `GeminiClient.gate_analyze()`, KHÔNG qua `AnalyzerService`, nên KHÔNG bị
    `MAX_DAILY_ANALYSIS` tính hay chặn. Tiền vẫn mất thật — đừng chạy trong vòng lặp.

ĐỌC KẾT QUẢ — quy ước giữ nguyên từ `w4-gate-accuracy`
    SIGNAL = positive, gate PASS = predicted positive.
    TP = pass & SIGNAL · FP = pass & NOISE · FN = fail & SIGNAL (giết nhầm) · TN = fail & NOISE
    Với sản phẩm radar, FN tệ hơn FP: bỏ sót tín hiệu là mất hẳn, lọt nhiễu thì người đọc lọc được.
    Baseline chốt 21/07/2026: TP=34 FP=3 FN=0 TN=17 → acc 94%, prec 92%, recall 100%, F1 96%.
    Đo lại 22/07/2026 sau khi dựng harness: khớp tuyệt đối, 0/54 mẫu đổi verdict (không có drift).

GIỚI HẠN DIỄN GIẢI
    - Mẫu là ảnh chụp tháng 7/2026. Đo *hồi quy so với chính nó*, KHÔNG đo chất lượng tuyệt đối
      của gate trên tin mới.
    - n < 5 chỉ là tín hiệu: huggingface/web_index/hackernews/reddit đều dưới 5 mẫu — đừng rút
      kết luận giữ/cắt nguồn từ mấy dòng đó.
    - 3 FP còn lại phần lớn là chuẩn khắt khe của người chấm; siết prompt theo chúng trên mẫu 54
      doc có rủi ro overfit. Quyết định 21/07 là KHÔNG tune.
    - Matrix "gate CŨ" suy từ `old_status` lịch sử, không phải re-run prompt cũ.

SINH LẠI FIXTURE (chỉ khi đổi `GATE_CONTENT_LIMIT` hoặc mở rộng mẫu)
    Cần DB còn `normalized_content` của 54 doc — sau `retention_months` thì `purge_expired` đã xoá
    và bước này không chạy lại được. Xem `build_fixture.py`; giữ file đó, đừng dọn.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from app.ai.prompts import GATE_CONTENT_LIMIT

FIXTURE_PATH = Path(__file__).parent / "gate_benchmark.jsonl"

# Baseline đã chốt ngày 21/07/2026 (xem measurement.md của w4-gate-accuracy).
BASELINE_2026_07_21 = {"tp": 34, "fp": 3, "fn": 0, "tn": 17}


@dataclass(frozen=True)
class Matrix:
    tp: int
    fp: int
    fn: int
    tn: int

    @property
    def total(self) -> int:
        return self.tp + self.fp + self.fn + self.tn

    @property
    def accuracy(self) -> float:
        return (self.tp + self.tn) / self.total if self.total else 0.0

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    def as_dict(self) -> dict:
        return {"tp": self.tp, "fp": self.fp, "fn": self.fn, "tn": self.tn}


def load_fixture(path: Path = FIXTURE_PATH) -> list[dict]:
    """Đọc fixture và khẳng định nó vẫn đo đúng thứ gate thật đọc.

    Nếu `GATE_CONTENT_LIMIT` đổi mà fixture không sinh lại, benchmark sẽ đo trên đầu vào
    khác với production — sai lệch im lặng, đúng loại lỗi change này sinh ra để chặn.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Không thấy fixture {path}. Sinh lại bằng `tests.eval.build_fixture` "
            "(cần DB còn normalized_content của 54 doc)."
        )

    samples = [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]
    if not samples:
        raise ValueError(f"Fixture {path} rỗng")

    for s in samples:
        if s["content_truncated_at"] != GATE_CONTENT_LIMIT:
            raise ValueError(
                f"Fixture cắt ở {s['content_truncated_at']} ký tự nhưng gate thật đọc "
                f"{GATE_CONTENT_LIMIT} (`GATE_CONTENT_LIMIT`). Sinh lại fixture trước khi đo — "
                "đo tiếp sẽ cho số sai một cách im lặng."
            )
        if s["human_label"] not in ("SIGNAL", "NOISE"):
            raise ValueError(f"{s['doc_id']}: human_label không hợp lệ {s['human_label']!r}")

    return samples


def build_matrix(samples: Iterable[dict], predict: Callable[[dict], bool]) -> Matrix:
    """Dựng confusion matrix từ hàm dự đoán `predict(sample) -> có pass gate không`."""
    tp = fp = fn = tn = 0
    for s in samples:
        passed = predict(s)
        signal = s["human_label"] == "SIGNAL"
        if passed and signal:
            tp += 1
        elif passed and not signal:
            fp += 1
        elif not passed and signal:
            fn += 1
        else:
            tn += 1
    return Matrix(tp=tp, fp=fp, fn=fn, tn=tn)


def predict_new(sample: dict) -> bool:
    """Verdict gate MỚI đo ngày 21/07/2026 (đã lưu trong fixture)."""
    return bool(sample["verdict_2026_07_21"])


def predict_old(sample: dict) -> bool:
    """Verdict gate CŨ (IoT-only), suy từ `old_status` lịch sử — xem giới hạn ở measurement.md."""
    return sample["old_status"] != "low_signal"


def format_matrix(name: str, m: Matrix) -> str:
    return (
        f"{name:<28} TP={m.tp:<3} FP={m.fp:<3} FN={m.fn:<3} TN={m.tn:<3} "
        f"acc={m.accuracy:.0%}  prec={m.precision:.0%}  rec={m.recall:.0%}  F1={m.f1:.0%}"
    )


def format_by_source(samples: list[dict], predict: Callable[[dict], bool]) -> str:
    """Bảng độ chính xác theo `source_type` — n<5 chỉ đọc như tín hiệu, không kết luận."""
    groups: dict[str, list[dict]] = {}
    for s in samples:
        groups.setdefault(s["source_type"], []).append(s)

    lines = [f"{'source_type':<18}{'n':>4}{'SIGNAL':>8}{'đúng':>8}"]
    for source_type, rows in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        signal = sum(1 for r in rows if r["human_label"] == "SIGNAL")
        correct = sum(
            1 for r in rows if predict(r) == (r["human_label"] == "SIGNAL")
        )
        flag = "  (n<5, chỉ là tín hiệu)" if len(rows) < 5 else ""
        lines.append(
            f"{source_type:<18}{len(rows):>4}{signal:>8}{correct:>5}/{len(rows):<3}{flag}"
        )
    return "\n".join(lines)


def run_live(samples: list[dict]) -> dict[str, bool]:
    """Chạy `GATE_PROMPT` hiện hành trên từng mẫu. Trả `doc_id -> pass_gate`.

    Import GeminiClient trong hàm: module này phải import được ở CI không có credentials.
    """
    from app.ai.gemini_client import GeminiClient

    client = GeminiClient()
    verdicts: dict[str, bool] = {}
    for i, s in enumerate(samples, start=1):
        result = client.gate_analyze(title=s["title"], content=s["content"])
        verdicts[s["doc_id"]] = bool(result.pass_gate)
        flag = "  ⚠️ lỗi parse (fail-open)" if getattr(result, "error", None) else ""
        print(f"  [{i:>2}/{len(samples)}] {s['title'][:52]:<52} "
              f"{'PASS' if result.pass_gate else 'FAIL'}{flag}")
    return verdicts


def diff_against_baseline(samples: list[dict], live: dict[str, bool]) -> list[str]:
    """Mẫu đổi verdict so với baseline 21/07, kèm chiều đổi (thứ cần đọc khi hồi quy)."""
    changed = []
    for s in samples:
        before, after = predict_new(s), live[s["doc_id"]]
        if before == after:
            continue
        signal = s["human_label"] == "SIGNAL"
        if before and not after:
            direction = "SIGNAL bị loại thêm ❌" if signal else "NOISE bị loại thêm ✅"
        else:
            direction = "SIGNAL lọt thêm ✅" if signal else "NOISE lọt thêm ❌"
        changed.append(f"  {direction}  [{s['source']}] {s['title'][:60]}")
    return changed


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark tiêu chí gate (54 mẫu nhãn tay)")
    parser.add_argument(
        "--live",
        action="store_true",
        help="gọi Vertex thật trên GATE_PROMPT hiện hành (54 lượt gọi, ăn quota analysis)",
    )
    args = parser.parse_args()

    samples = load_fixture()
    print(f"Fixture: {len(samples)} mẫu, cắt {GATE_CONTENT_LIMIT} ký tự "
          f"({sum(1 for s in samples if s['human_label'] == 'SIGNAL')} SIGNAL / "
          f"{sum(1 for s in samples if s['human_label'] == 'NOISE')} NOISE)\n")

    print(format_matrix("Gate CŨ (IoT-only)", build_matrix(samples, predict_old)))
    print(format_matrix("Gate 21/07 (4 trụ cột)", build_matrix(samples, predict_new)))

    if not args.live:
        print("\n" + format_by_source(samples, predict_new))
        print("\n(offline — dùng verdict đã lưu. Thêm --live để đo lại bằng Vertex.)")
        return

    print(f"\nĐo lại bằng Vertex trên GATE_PROMPT hiện hành ({len(samples)} lượt gọi)...")
    live = run_live(samples)
    live_matrix = build_matrix(samples, lambda s: live[s["doc_id"]])

    print()
    print(format_matrix("Gate HIỆN TẠI (đo lại)", live_matrix))
    print("\n" + format_by_source(samples, lambda s: live[s["doc_id"]]))

    changed = diff_against_baseline(samples, live)
    print(f"\nSo với baseline 21/07: {len(changed)} mẫu đổi verdict")
    for line in changed:
        print(line)
    if not changed:
        print("  (khớp hoàn toàn — GATE_PROMPT không hồi quy)")


if __name__ == "__main__":
    main()
