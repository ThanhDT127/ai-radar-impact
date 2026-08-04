"""SPIKE: câu hỏi CHI TIẾT — sự thật chỉ nằm trong thân bài, không có trong phân tích.

Đo hai điểm hỏng TÁCH BIỆT:
  (a) TRUY HỒI  — `_rank` có đưa đúng bài lên top-5 không? (miễn phí)
  (b) TRẢ LỜI   — chế độ toàn cục thật có nói đúng chi tiết không, hay từ chối, hay BỊA?
                  và mode B (có raw content) trên chính bài đó thì sao? (đối chứng)

Đối chứng mode B là phần quan trọng nhất: nó chứng minh dữ liệu CÓ trong hệ thống, chỉ là
tầng truy hồi toàn cục không với tới.
"""

import asyncio
import json
import uuid

from app.ai.gemini_client import GeminiClient
from app.services import chat_service as cs
from tests.eval.chat_fixture import (
    load_anchors, load_corpus, load_embeddings, rehydrate_corpus,
)

# (id bài, câu hỏi toàn cục, sự thật chỉ có trong thân bài, chuỗi cần thấy trong câu trả lời)
CASES = [
    ("41d16762", "Chunk size và overlap bao nhiêu thì tối ưu cho hệ thống RAG?",
     "bài đo được chunk 512 token, overlap 50", ["512"]),
    ("0882d18a", "EU AI Act liệt kê hệ thống AI rủi ro cao ở phụ lục nào?",
     "Annex III", ["annex", "phụ lục"]),
    ("104ba8cc", "Windows Server 2022 hết hỗ trợ mở rộng vào tháng nào?",
     "tháng 10 (October) — mốc extended support", ["october", "tháng 10"]),
    ("afe77d13", "Camera Kasa rò rỉ dữ liệu qua cổng UDP số bao nhiêu?",
     "cổng 9770", ["9770"]),
    ("15d83425", "Entra ID khuyến nghị phương thức xác thực chống phishing nào?",
     "passkeys / FIDO2, loại bỏ telecom-based MFA", ["passkey", "fido"]),
    ("9e815aec", "Gói npm nào bị chèn mã độc trong vụ AsyncAPI?",
     "@asyncapi/generator", ["generator"]),
]


class _R:
    def __init__(self, o): self._o = o
    def scalar_one_or_none(self): return self._o


class _S:
    def __init__(self, by): self._by = by
    async def execute(self, stmt):
        w = [v for v in stmt.compile().params.values() if isinstance(v, uuid.UUID)]
        return _R(self._by.get(str(w[0])) if w else None)


def service(corpus, by_id):
    s = cs.ChatService(session=_S(by_id), gemini=GeminiClient())
    async def _l(*a, **k): return list(corpus)
    async def _z(): return 0
    async def _c(**k): return None
    s.insight_repo.list_for_chat = _l
    s.chat_log_repo.sum_model_calls_today = _z
    s.chat_log_repo.create = _c
    return s


def hit(answer, needles):
    low = answer.lower()
    return any(n.lower() in low for n in needles)


REFUSAL = ("không tìm thấy", "không có thông tin", "không đủ căn cứ", "chưa có tin nào",
           "không đủ dữ liệu", "không nêu", "không nói rõ", "không đề cập", "không cung cấp")


def classify(answer, needles):
    if hit(answer, needles):
        return "ĐÚNG"
    if any(r in answer.lower() for r in REFUSAL):
        return "từ chối"
    return "⚠ NÓI KHÁC"   # trả lời trôi chảy nhưng không mang sự thật cần có


async def main():
    corpus = rehydrate_corpus(load_corpus(), anchors=load_anchors(),
                              embeddings=load_embeddings())
    by_id = {str(i.id): i for i in corpus}
    client = GeminiClient()

    def expand(p): return next(k for k in by_id if k.startswith(p))

    rows = []
    for n, (prefix, q, truth, needles) in enumerate(CASES, 1):
        tid = expand(prefix)
        target = by_id[tid]

        # (a) truy hồi — miễn phí
        qvec = client.embed_one(q, "RETRIEVAL_QUERY")
        ranked = cs.ChatService(session=None, gemini=client)._rank(list(corpus), q, qvec)
        rank = next(i for i, x in enumerate(ranked, 1) if str(x.id) == tid)

        # (b) trả lời — toàn cục (index 115 tok/tin)
        g = await service(corpus, by_id).answer(question=q, history=[], insight_id=None)
        # đối chứng — mode B trên chính bài đó (có raw content)
        b = await service(corpus, by_id).answer(question=q, history=[],
                                                insight_id=uuid.UUID(tid))

        row = {
            "q": q, "truth": truth, "title": target.title[:40], "rank": rank,
            "global": {"verdict": classify(g["answer"], needles), "answer": g["answer"],
                       "mode": g["mode"], "cited_target": any(
                           str(c["insight_id"]) == tid for c in g["citations"])},
            "modeB": {"verdict": classify(b["answer"], needles), "answer": b["answer"],
                      "mode": b["mode"]},
        }
        rows.append(row)
        print(f"  [{n}/{len(CASES)}] hạng {rank:>3} | toàn cục: {row['global']['verdict']:<11}"
              f"(mode={g['mode']}, trích đúng bài={row['global']['cited_target']}) "
              f"| mode B: {row['modeB']['verdict']}", flush=True)

    print("\n" + "=" * 104)
    h = f"{'câu hỏi':<52}{'hạng':>5}{'trích':>7}{'TOÀN CỤC':>13}{'MODE B':>12}"
    print(h); print("-" * len(h))
    for r in rows:
        print(f"{r['q'][:50]:<52}{r['rank']:>5}{'✔' if r['global']['cited_target'] else '✘':>7}"
              f"{r['global']['verdict']:>13}{r['modeB']['verdict']:>12}")
    print()
    for key in ("global", "modeB"):
        from collections import Counter
        c = Counter(r[key]["verdict"] for r in rows)
        print(f"  {key:<8} " + "  ".join(f"{k}={v}" for k, v in c.most_common()))
    print(f"\n  truy hồi: {sum(1 for r in rows if r['rank']<=5)}/{len(rows)} bài đúng nằm trong top-5")
    json.dump(rows, open("/tmp/detail_result.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


if __name__ == "__main__":
    asyncio.run(main())
