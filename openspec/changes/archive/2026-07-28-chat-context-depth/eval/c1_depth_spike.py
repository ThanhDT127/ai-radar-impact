"""SPIKE: câu so sánh TƯỜNG MINH (C1) — độ sâu index 115 token/tin có đủ không?

Hai nhánh, cùng câu hỏi, cùng model, cùng system prompt:

  A  HIỆN TRẠNG   `_answer_global` thật: index nén [1..60], 115 token/tin
  B  GHIM 2 BÀI   hai tin đích ở mức "7 field phân tích" (KHÔNG raw content) tại [1][2],
                  index toàn cục từ [3] (đã loại hai tin đó)

Chấm bằng LLM-judge một chỉ số DUY NHẤT: **Comparison Adequacy** — câu trả lời có thực
sự ĐỐI CHIẾU hai tin không, hay chỉ liệt kê song song. Đây là thứ `chat_answer_harness`
không đo (nó đo Faithfulness / AnsRel / CitPrec).

    docker compose exec -e PYTHONPATH=/app backend python /tmp/c1_depth_spike.py
"""

import asyncio
import json
import time
import uuid

from app.ai.gemini_client import GeminiClient
from app.ai.prompts import CHAT_SYSTEM_PROMPT, build_chat_expanded_prompt
from app.config import settings
from app.services import chat_service as cs
from app.services.chat_grounding import build_index_block, build_insight_block
from tests.eval.chat_fixture import load_corpus, load_embeddings, rehydrate_corpus

JUDGE_PROMPT = """\
Bạn chấm chất lượng một câu trả lời SO SÁNH. Người dùng hỏi so sánh hai tin tức.

CÂU HỎI: {question}

HAI TIN CẦN ĐƯỢC SO SÁNH:
- A: {title_a}
- B: {title_b}

CÂU TRẢ LỜI:
{answer}

Chấm theo thang:
2 = ĐỐI CHIẾU thật: nêu >=2 chiều so sánh cụ thể (mục đích/phạm vi/mức khẩn/đối tượng/
    con số) và nói rõ hai bên KHÁC nhau ra sao, hoặc kết luận chọn cái nào.
1 = MÔ TẢ SONG SONG: có nhắc cả hai tin nhưng chỉ tóm tắt từng cái rời nhau, người đọc
    phải tự rút ra khác biệt.
0 = THIẾU: bỏ sót một trong hai tin, hoặc trả lời lạc đề, hoặc từ chối.

In ĐÚNG một dòng JSON, không giải thích thêm:
{{"diem": 0|1|2, "ly_do": "<tối đa 20 từ>"}}"""


class _FixtureResult:
    def __init__(self, obj):
        self._obj = obj

    def scalar_one_or_none(self):
        return self._obj


class _FixtureSession:
    def __init__(self, by_id):
        self._by_id = by_id

    async def execute(self, stmt):
        wanted = [v for v in stmt.compile().params.values() if isinstance(v, uuid.UUID)]
        return _FixtureResult(self._by_id.get(str(wanted[0])) if wanted else None)


def make_service(corpus, by_id):
    service = cs.ChatService(session=_FixtureSession(by_id), gemini=GeminiClient())

    async def _list(*_a, **_k):
        return list(corpus)

    async def _sum():
        return 0

    async def _create(**_k):
        return None

    service.insight_repo.list_for_chat = _list
    service.chat_log_repo.sum_model_calls_today = _sum
    service.chat_log_repo.create = _create
    return service


def pinned_block(insights) -> str:
    """Hai bài ghim ở mức 7-field (không raw content), đánh số [1] [2].

    `build_insight_block` chốt cứng "[1]" ở đầu — spike thì thay số bằng tay; bản thật
    sẽ phải nhận `start` như `build_index_block`.
    """
    out = []
    for n, insight in enumerate(insights, start=1):
        block = build_insight_block(insight, None)
        out.append(block.replace("[1]", f"[{n}]", 1))
    return "\n\n".join(out)


async def arm_a(service, question):
    started = time.monotonic()
    result = await service.answer(question=question, history=[], insight_id=None)
    return result["answer"], result["citations"], int((time.monotonic() - started) * 1000)


async def arm_b(service, question, targets, corpus, qvec):
    """Ghim `targets` ở [1][2], index toàn cục từ [3]. Vẫn đúng MỘT bảng ánh xạ."""
    ids = {str(i.id) for i in targets}
    rest = service._rank([i for i in corpus if str(i.id) not in ids], question, qvec)
    top_k = settings.chat_index_top_k
    candidates = rest[: top_k - len(targets)] if top_k > 0 else rest
    index_block, mapping = build_index_block(candidates, start=len(targets) + 1)
    for n, insight in enumerate(targets, start=1):
        mapping[n] = insight

    prompt = build_chat_expanded_prompt(
        insight_block=pinned_block(targets),
        index_block=index_block,
        history_block="",
        question=question,
    )
    started = time.monotonic()
    text, _calls = await asyncio.to_thread(
        service.gemini.chat, CHAT_SYSTEM_PROMPT, prompt, cs.ChatStreamState()
    )
    latency = int((time.monotonic() - started) * 1000)
    answer, citations = cs.resolve_citations(text, mapping)
    answer, citations = cs.enforce_grounding(answer, citations)
    return answer, citations, latency


def judge(client, question, title_a, title_b, answer):
    out, _ = client.chat(
        "Bạn là giám khảo nghiêm khắc. Chỉ in JSON một dòng.",
        JUDGE_PROMPT.format(
            question=question, title_a=title_a, title_b=title_b, answer=answer
        ),
        cs.ChatStreamState(),
    )
    try:
        return json.loads(out[out.index("{") : out.rindex("}") + 1])
    except Exception:
        return {"diem": None, "ly_do": f"judge lỗi: {out[:40]}"}


async def main():
    scenarios = [
        s
        for s in json.load(open("/tmp/cmp_scenarios.json", encoding="utf-8"))
        if s["family"] == "C1-explicit"
    ]
    corpus = rehydrate_corpus(load_corpus(), embeddings=load_embeddings())
    by_id = {str(i.id): i for i in corpus}

    def expand(prefix):
        return next(k for k in by_id if k.startswith(prefix))

    client = GeminiClient()
    rows = []
    for n, s in enumerate(scenarios, start=1):
        targets = [by_id[expand(p)] for p in s["must_have"]]
        qvec = client.embed_one(s["question"], "RETRIEVAL_QUERY")

        a_ans, a_cit, a_ms = await arm_a(make_service(corpus, by_id), s["question"])
        b_ans, b_cit, b_ms = await arm_b(
            make_service(corpus, by_id), s["question"], targets, corpus, qvec
        )

        want = {str(t.id) for t in targets}
        row = {
            "id": s["id"],
            "question": s["question"],
            "titles": [t.title[:38] for t in targets],
            "A": {
                "answer": a_ans,
                "chars": len(a_ans),
                "ms": a_ms,
                "both_cited": want <= {str(c["insight_id"]) for c in a_cit},
                "n_cit": len(a_cit),
                "judge": judge(client, s["question"], targets[0].title, targets[1].title, a_ans),
            },
            "B": {
                "answer": b_ans,
                "chars": len(b_ans),
                "ms": b_ms,
                "both_cited": want <= {str(c["insight_id"]) for c in b_cit},
                "n_cit": len(b_cit),
                "judge": judge(client, s["question"], targets[0].title, targets[1].title, b_ans),
            },
        }
        rows.append(row)
        print(
            f"  [{n}/{len(scenarios)}] {s['id']:<24} "
            f"A: điểm={row['A']['judge']['diem']} cả2={row['A']['both_cited']} {row['A']['chars']}ký tự "
            f"| B: điểm={row['B']['judge']['diem']} cả2={row['B']['both_cited']} {row['B']['chars']}ký tự",
            flush=True,
        )

    print("\n" + "=" * 100)
    hdr = f"{'kịch bản':<24}{'A điểm':>7}{'A cả2':>7}{'A ký tự':>9}{'A ms':>7}   {'B điểm':>7}{'B cả2':>7}{'B ký tự':>9}{'B ms':>7}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(
            f"{r['id']:<24}{str(r['A']['judge']['diem']):>7}{'✔' if r['A']['both_cited'] else '✘':>7}"
            f"{r['A']['chars']:>9}{r['A']['ms']:>7}   "
            f"{str(r['B']['judge']['diem']):>7}{'✔' if r['B']['both_cited'] else '✘':>7}"
            f"{r['B']['chars']:>9}{r['B']['ms']:>7}"
        )

    def avg(arm, key):
        vals = [r[arm]["judge"]["diem"] for r in rows if r[arm]["judge"]["diem"] is not None] if key == "diem" else [r[arm][key] for r in rows]
        return sum(vals) / len(vals) if vals else 0

    print(
        f"\nTRUNG BÌNH  A: điểm={avg('A','diem'):.2f}  cả-hai-trích={sum(r['A']['both_cited'] for r in rows)}/{len(rows)}  "
        f"{avg('A','chars'):.0f} ký tự  {avg('A','ms'):.0f}ms"
    )
    print(
        f"            B: điểm={avg('B','diem'):.2f}  cả-hai-trích={sum(r['B']['both_cited'] for r in rows)}/{len(rows)}  "
        f"{avg('B','chars'):.0f} ký tự  {avg('B','ms'):.0f}ms"
    )
    json.dump(rows, open("/tmp/c1_result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nChi tiết câu trả lời ở /tmp/c1_result.json")


if __name__ == "__main__":
    asyncio.run(main())
