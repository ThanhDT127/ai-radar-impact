"""SPIKE (không phải code sản phẩm): đo recall của `_rank` trên câu hỏi SO SÁNH hai insight.

Chạy trong container backend, đọc fixture read-only ở tests/eval/. Không ghi gì vào repo.

    docker compose cp <file> backend:/tmp/ && docker compose exec backend python /tmp/cmp_rank_spike.py

Câu hỏi cần trả lời:
  - Câu so sánh TƯỜNG MINH (gọi tên cả hai) có kéo được ĐỒNG THỜI hai tin vào top-5 không?
  - Câu so sánh HỒI CHỈ ("hai bài vừa rồi") thì recall bằng bao nhiêu? (giả thuyết: ~0 theo cấu trúc)
  - Chế độ expanded (bài đang xem miễn phí ở [1]) có cứu được không?
"""

import json
import sys

from app.config import settings
from app.ai.gemini_client import EMBED_TASK_QUERY, GeminiClient
from app.services.chat_service import ChatService, _question_terms
from tests.eval.chat_fixture import load_corpus, load_embeddings, rehydrate_corpus

ANSWER_BUDGET = 5


class _NoModel:
    def __getattr__(self, name):
        raise AssertionError(f"chạm model: {name}")


def rank(candidates, question, qvec):
    return ChatService(session=None, gemini=_NoModel())._rank(candidates, question, qvec)


def main():
    scenarios = json.load(open("/tmp/cmp_scenarios.json", encoding="utf-8"))
    corpus_rows = load_corpus()
    corpus = rehydrate_corpus(corpus_rows, embeddings=load_embeddings())
    by_id = {str(i.id): i for i in corpus}

    # Kịch bản viết bằng prefix 8 ký tự cho dễ đọc — nở ra id đầy đủ, nổ nếu mơ hồ.
    def expand(prefix):
        hits = [k for k in by_id if k.startswith(prefix)]
        if len(hits) != 1:
            raise SystemExit(f"prefix {prefix!r} khớp {len(hits)} tin")
        return hits[0]

    for s in scenarios:
        s["must_have"] = [expand(p) for p in s["must_have"]]
        if s.get("anchor"):
            s["anchor"] = expand(s["anchor"])

    client = GeminiClient()
    vectors = {}
    for s in scenarios:
        if not _question_terms(s["question"]):
            vectors[s["id"]] = None  # `_rank` sẽ tự tắt tầng vector; khỏi tốn lượt embed
            continue
        vectors[s["id"]] = client.embed_one(s["question"], EMBED_TASK_QUERY)

    top_k = settings.chat_index_top_k
    rows = []
    for s in scenarios:
        candidates = [i for i in corpus if str(i.id) != s.get("anchor")]
        ranked = rank(candidates, s["question"], vectors[s["id"]])
        pos = {str(i.id): n for n, i in enumerate(ranked, start=1)}
        ranks = [pos.get(i) for i in s["must_have"]]
        rows.append(
            {
                "id": s["id"],
                "family": s["family"],
                "mode": s["mode"],
                "question": s["question"],
                "terms": _question_terms(s["question"]),
                "vector": vectors[s["id"]] is not None,
                "ranks": ranks,
                "titles": [by_id[i].title[:40] for i in s["must_have"]],
                "r_at_k": sum(1 for r in ranks if r and r <= top_k) / len(ranks),
                "r_at_5": sum(1 for r in ranks if r and r <= ANSWER_BUDGET) / len(ranks),
                # "cả hai cùng lọt" — đại lượng thật sự quan trọng cho câu SO SÁNH:
                # trả lời được đòi CẢ HAI tin, không phải trung bình của hai.
                "both_at_k": all(r and r <= top_k for r in ranks),
                "both_at_5": all(r and r <= ANSWER_BUDGET for r in ranks),
            }
        )

    print(f"Corpus {len(corpus)} tin · K={top_k} · budget câu trả lời={ANSWER_BUDGET}\n")
    hdr = f"{'kịch bản':<22}{'họ':<14}{'hạng must_have':<20}{'r@60':>6}{'r@5':>6}{'cả2@60':>8}{'cả2@5':>7}  vector"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        rk = ", ".join(str(x) if x else "—" for x in r["ranks"])
        print(
            f"{r['id']:<22}{r['family']:<14}{rk:<20}{r['r_at_k']:>6.2f}{r['r_at_5']:>6.2f}"
            f"{'✔' if r['both_at_k'] else '✘':>8}{'✔' if r['both_at_5'] else '✘':>7}  "
            f"{'có' if r['vector'] else 'TẮT (rỗng từ khoá)'}"
        )

    print("\nTheo họ kịch bản:")
    fams = {}
    for r in rows:
        fams.setdefault(r["family"], []).append(r)
    for fam, rs in sorted(fams.items()):
        n = len(rs)
        print(
            f"  {fam:<14} n={n}  r@60={sum(x['r_at_k'] for x in rs)/n:.2f}  "
            f"r@5={sum(x['r_at_5'] for x in rs)/n:.2f}  "
            f"cả-hai@60={sum(x['both_at_k'] for x in rs)}/{n}  "
            f"cả-hai@5={sum(x['both_at_5'] for x in rs)}/{n}"
        )

    print("\nChi tiết câu trượt top-5:")
    for r in rows:
        for title, rank_ in zip(r["titles"], r["ranks"]):
            if not rank_ or rank_ > ANSWER_BUDGET:
                print(f"  {r['id']:<22} «{title}» hạng {rank_}")

    json.dump(rows, open("/tmp/cmp_result.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    sys.exit(main())
