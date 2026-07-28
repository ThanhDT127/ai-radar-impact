"""Task 0.2 — đo `_rank` HIỆN TẠI trên bộ "khám phá bằng chi tiết".

Đây là **cổng chặn** của change: nếu tầng xếp hạng hôm nay đã đưa bài đúng lên top-5 thì
chunk retrieval không mua được gì, và change phải đóng (task 0.3).

Chạy đúng `ChatService._rank` thật (RRF lexical + vector mức insight) trên đúng corpus
fixture 179 tin mà mọi baseline đang dùng. Vector câu hỏi gọi Vertex **một lần** rồi đông
lạnh vào `detail_query_vectors.jsonl` — lần chạy sau miễn phí và tất định, cùng luật với
`chat_query_vectors.jsonl` của RS harness.

    docker compose exec -e PYTHONPATH=/app backend python /app/eval_chunk/measure_detail_rank.py

Đọc kết quả: cột `hạng` là vị trí của bài đúng trong danh sách đã xếp. Trần thật của câu
trả lời là **5 tin** (`CHAT_SYSTEM_PROMPT`: "TỐI ĐA 5 tin") — bài xếp hạng 30 tuy lọt index
top-60 nhưng model gần như chắc chắn không dùng tới.
"""

import json
from pathlib import Path

from app.ai.gemini_client import EMBED_TASK_QUERY, GeminiClient
from app.config import settings
from app.services.chat_service import ChatService, _question_terms
from tests.eval.chat_fixture import load_corpus, load_embeddings, rehydrate_corpus

EVAL_DIR = Path(__file__).parent
SCENARIOS_PATH = EVAL_DIR / "detail_scenarios.jsonl"
VECTORS_PATH = EVAL_DIR / "detail_query_vectors.jsonl"
RESULT_PATH = EVAL_DIR / "detail_rank_result.json"

ANSWER_BUDGET = 5
VECTOR_PRECISION = 6


class _NoModel:
    """Cùng vai trò với `_NoModel` của RS harness: `_rank` chạm model là sai."""

    def __getattr__(self, name):
        raise AssertionError(f"`_rank` vừa chạm tới model (`{name}`) — nó phải thuần.")


def load_scenarios() -> list[dict]:
    return [json.loads(l) for l in SCENARIOS_PATH.open(encoding="utf-8") if l.strip()]


def query_vectors(scenarios: list[dict]) -> dict[str, list[float]]:
    """Đông lạnh vector câu hỏi; chỉ gọi Vertex cho kịch bản chưa có."""
    cached = {}
    if VECTORS_PATH.exists():
        cached = {
            row["scenario_id"]: row["embedding"]
            for row in (json.loads(l) for l in VECTORS_PATH.open(encoding="utf-8") if l.strip())
        }
    missing = [s for s in scenarios if s["id"] not in cached]
    if missing:
        client = GeminiClient()
        for scenario in missing:
            vector = client.embed_one(scenario["question"], EMBED_TASK_QUERY)
            cached[scenario["id"]] = [round(float(v), VECTOR_PRECISION) for v in vector]
        with VECTORS_PATH.open("w", encoding="utf-8") as fh:
            for scenario in scenarios:
                fh.write(
                    json.dumps(
                        {"scenario_id": scenario["id"], "embedding": cached[scenario["id"]]},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        print(f"(đã embed {len(missing)} câu hỏi mới → {VECTORS_PATH.name})")
    return cached


def main() -> None:
    scenarios = load_scenarios()
    corpus = rehydrate_corpus(load_corpus(), embeddings=load_embeddings())
    vectors = query_vectors(scenarios)
    service = ChatService(session=None, gemini=_NoModel())
    top_k = settings.chat_index_top_k

    rows = []
    for scenario in scenarios:
        target = scenario["must_have"][0]
        ranked = service._rank(list(corpus), scenario["question"], vectors[scenario["id"]])
        position = next(
            (n for n, insight in enumerate(ranked, 1) if str(insight.id) == target), None
        )
        rows.append(
            {
                "id": scenario["id"],
                "question": scenario["question"],
                "probe": scenario["probe"],
                "rank": position,
                "in_top5": position is not None and position <= ANSWER_BUDGET,
                "in_index": position is not None and (top_k == 0 or position <= top_k),
                "title": next(
                    (i.title for i in corpus if str(i.id) == target), "?"
                ),
                "terms": _question_terms(scenario["question"]),
                "top5_titles": [i.title[:44] for i in ranked[:5]],
            }
        )

    print(f"\nCorpus {len(corpus)} tin · K = {top_k} · trần câu trả lời = {ANSWER_BUDGET}\n")
    header = f"{'kịch bản':<26}{'định danh':<26}{'hạng':>5}{'top-5':>7}{'index':>7}  bài đúng"
    print(header)
    print("-" * 118)
    for row in rows:
        print(
            f"{row['id']:<26}{row['probe'][:24]:<26}{str(row['rank']):>5}"
            f"{'✔' if row['in_top5'] else '✘':>7}{'✔' if row['in_index'] else '✘':>7}  "
            f"{row['title'][:46]}"
        )

    n = len(rows)
    outside_5 = sum(1 for r in rows if not r["in_top5"])
    outside_k = sum(1 for r in rows if not r["in_index"])
    recall5 = (n - outside_5) / n
    recallk = (n - outside_k) / n
    ranks = [r["rank"] for r in rows if r["rank"]]

    print(
        f"\n  recall@{ANSWER_BUDGET} = {recall5:.3f}   recall@{top_k} = {recallk:.3f}   "
        f"hạng xấu nhất = {max(ranks)}   trung vị = {sorted(ranks)[len(ranks)//2]}"
    )
    print(
        f"  ngoài top-{ANSWER_BUDGET}: {outside_5}/{n} = {outside_5 / n:.1%}   "
        f"(cổng của change: ≥ 30%)"
    )
    print(f"  ⇒ {'TIẾP TỤC' if outside_5 / n >= 0.30 else 'ĐÓNG CHANGE'}\n")

    RESULT_PATH.write_text(
        json.dumps(
            {
                "corpus_size": len(corpus),
                "top_k": top_k,
                "answer_budget": ANSWER_BUDGET,
                "recall_at_5": recall5,
                "recall_at_k": recallk,
                "outside_top5_ratio": outside_5 / n,
                "rows": rows,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"Đã ghi {RESULT_PATH}")


if __name__ == "__main__":
    main()
