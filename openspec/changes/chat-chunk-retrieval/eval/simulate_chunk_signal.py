"""Task 0.3 — bằng chứng TRIỂN VỌNG: tín hiệu đoạn có thực sự chữa 5 ca hỏng không?

Task 0.2 trả lời "chế độ hỏng có thật không" (33,3% ngoài top-5, vừa qua cổng 30%). Nó
KHÔNG trả lời "change này chữa được không" — và đó mới là câu quyết định có nên trả cái giá
kiến trúc (bảng mới, +5–6× dung lượng vector, phá tính thuần của `_rank`). Rủi ro cuối cùng
trong `design.md` ghi đúng chuyện đó: *"làm xong mà không ai được lợi"*.

Script này chunk + embed toàn bộ thân bài của corpus fixture MỘT LẦN (~$0,05, đông lạnh vào
`chunk_embeddings.jsonl`), rồi chạy **chính `ChatService._rank` thật** với `chunk_ranks` để
so hai cột trước/sau. Không có bản sao logic xếp hạng nào ở đây — đo một bản sao là đo một
pipeline không tồn tại.

Đo trên HAI bộ, và bộ thứ hai quan trọng ngang bộ thứ nhất:
  · 15 kịch bản `detail_discovery` (cái change nhắm tới)   — kỳ vọng TĂNG
  · 61 kịch bản RS hiện có (mọi câu hỏi khác)              — kỳ vọng KHÔNG TỤT

    docker compose exec -e PYTHONPATH=/app backend python /app/eval_chunk/simulate_chunk_signal.py
"""

import asyncio
import json
import time
import uuid
from pathlib import Path

from sqlalchemy import select

from app.ai.chunking import split_content
from app.ai.gemini_client import EMBED_TASK_DOCUMENT, EMBED_TASK_QUERY, GeminiClient
from app.config import settings
from app.database import async_session_maker
from app.models.insight import Insight
from app.models.raw_document import RawDocument
from app.services.chat_service import ChatService, _cosine, _competition_ranks, _question_terms
from tests.eval.chat_fixture import (
    load_corpus,
    load_embeddings,
    load_query_vectors,
    load_scenarios,
    rehydrate_corpus,
)

EVAL_DIR = Path(__file__).parent
CHUNKS_PATH = EVAL_DIR / "chunk_embeddings.jsonl"
DETAIL_SCENARIOS = EVAL_DIR / "detail_scenarios.jsonl"
DETAIL_VECTORS = EVAL_DIR / "detail_query_vectors.jsonl"
RESULT_PATH = EVAL_DIR / "simulate_chunk_result.json"

ANSWER_BUDGET = 5
VECTOR_PRECISION = 6


class _NoModel:
    def __getattr__(self, name):
        raise AssertionError(f"`_rank` vừa chạm tới model (`{name}`) — nó phải thuần.")


async def _bodies(ids: list[str]) -> dict[str, str]:
    async with async_session_maker() as session:
        rows = (
            await session.execute(
                select(Insight.id, RawDocument.normalized_content).join(
                    RawDocument, Insight.raw_document_id == RawDocument.id
                ).where(Insight.id.in_([uuid.UUID(i) for i in ids]))
            )
        ).all()
    return {str(i): c for i, c in rows if c}


def build_chunk_index() -> list[dict]:
    """`[{insight_id, ordinal, embedding}]` — đông lạnh, chỉ sinh một lần."""
    if CHUNKS_PATH.exists():
        return [json.loads(l) for l in CHUNKS_PATH.open(encoding="utf-8") if l.strip()]

    corpus = load_corpus()
    bodies = asyncio.run(_bodies([r["id"] for r in corpus]))
    pieces = [
        (row["id"], ordinal, chunk)
        for row in corpus
        for ordinal, chunk in enumerate(split_content(bodies.get(row["id"])))
    ]
    print(f"{len(pieces)} đoạn từ {len(bodies)}/{len(corpus)} bài có thân bài — đang embed…")

    client = GeminiClient()
    started = time.time()
    vectors = client.embed([p[2] for p in pieces], EMBED_TASK_DOCUMENT)
    elapsed = time.time() - started
    rows = [
        {"insight_id": iid, "ordinal": ordinal, "chars": len(text),
         "embedding": [round(float(v), VECTOR_PRECISION) for v in vector]}
        for (iid, ordinal, text), vector in zip(pieces, vectors)
        if vector is not None
    ]
    with CHUNKS_PATH.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Đã embed {len(rows)}/{len(pieces)} đoạn trong {elapsed:.1f}s → {CHUNKS_PATH.name}")
    return rows


def chunk_ranks_for(query_vector, chunks: list[dict]) -> dict[uuid.UUID, int]:
    """Thứ hạng của ĐOẠN KHỚP TỐT NHẤT, gộp về insight (design D1).

    Gộp bằng `min` chứ không trung bình: trung bình phạt bài dài vì những đoạn lạc đề mà
    chính nó không chọn có.
    """
    if query_vector is None:
        return {}
    sims = [_cosine(query_vector, c["embedding"]) for c in chunks]
    ranks = _competition_ranks(sims)
    best: dict[uuid.UUID, int] = {}
    for chunk, rank in zip(chunks, ranks):
        key = uuid.UUID(chunk["insight_id"])
        if rank < best.get(key, 10**9):
            best[key] = rank
    return best


def _rank_position(service, corpus, question, qvec, chunks, target, use_chunks):
    ranks = chunk_ranks_for(qvec, chunks) if use_chunks else None
    # Cổng "câu rỗng từ khoá" của `_rank` cũng phải áp cho tầng đoạn: một câu không có chủ
    # đề thì đoạn nào cũng "hơi giống", và cái hơi giống đó là nhiễu.
    if not _question_terms(question):
        ranks = None
    ordered = service._rank(list(corpus), question, qvec, ranks)
    return next((n for n, i in enumerate(ordered, 1) if str(i.id) == target), None)


def main() -> None:
    chunks = build_chunk_index()
    corpus = rehydrate_corpus(load_corpus(), embeddings=load_embeddings())
    service = ChatService(session=None, gemini=_NoModel())

    detail = [json.loads(l) for l in DETAIL_SCENARIOS.open(encoding="utf-8") if l.strip()]
    detail_vectors = {
        r["scenario_id"]: r["embedding"]
        for r in (json.loads(l) for l in DETAIL_VECTORS.open(encoding="utf-8") if l.strip())
    }

    print(f"\n① {len(detail)} kịch bản detail_discovery — cái change nhắm tới\n")
    print(f"{'kịch bản':<28}{'định danh':<24}{'trước':>7}{'sau':>7}   đổi")
    print("-" * 88)
    rows = []
    for scenario in detail:
        target = scenario["must_have"][0]
        qvec = detail_vectors[scenario["id"]]
        before = _rank_position(service, corpus, scenario["question"], qvec, chunks, target, False)
        after = _rank_position(service, corpus, scenario["question"], qvec, chunks, target, True)
        arrow = "=" if before == after else ("▲" if after < before else "▼")
        rows.append({"id": scenario["id"], "probe": scenario["probe"],
                     "before": before, "after": after})
        print(f"{scenario['id']:<28}{scenario['probe'][:22]:<24}{before:>7}{after:>7}   {arrow}")

    def recall5(key):
        return sum(1 for r in rows if r[key] <= ANSWER_BUDGET) / len(rows)

    print(f"\n  recall@5: {recall5('before'):.3f} → {recall5('after'):.3f}   "
          f"hạng xấu nhất: {max(r['before'] for r in rows)} → {max(r['after'] for r in rows)}")

    # ② Không hồi quy trên bộ câu hỏi thường — điều kiện bắt buộc, không phải phần thưởng.
    scenarios = [s for s in load_scenarios() if s["mode"] != "insight"]
    qvecs = load_query_vectors()
    print(f"\n② {len(scenarios)} kịch bản RS hiện có — điều kiện KHÔNG TỤT\n")
    reg = []
    for scenario in scenarios:
        must = [m for m in (scenario.get("must_have") or [])
                if m not in set(scenario.get("referenced_insight_ids") or [])]
        if not must:
            continue
        anchor = scenario.get("anchor_insight_id")
        refs = set(scenario.get("referenced_insight_ids") or [])
        pool = [i for i in corpus
                if str(i.id) != (anchor if scenario["mode"] == "expanded" else None)
                and str(i.id) not in refs]
        qvec = qvecs.get(scenario["id"])
        for use in (False, True):
            ranks = chunk_ranks_for(qvec, chunks) if use else None
            if not _question_terms(scenario["question"]):
                ranks = None
            ordered = service._rank(list(pool), scenario["question"], qvec, ranks)
            position = {str(i.id): n for n, i in enumerate(ordered, 1)}
            hit = sum(1 for m in must if position.get(m, 10**9) <= ANSWER_BUDGET) / len(must)
            if use:
                after = hit
            else:
                before = hit
        reg.append({"id": scenario["id"], "group": scenario["group"],
                    "before": before, "after": after})

    worse = [r for r in reg if r["after"] < r["before"] - 1e-9]
    better = [r for r in reg if r["after"] > r["before"] + 1e-9]
    mean_before = sum(r["before"] for r in reg) / len(reg)
    mean_after = sum(r["after"] for r in reg) / len(reg)
    print(f"  recall@5 trung bình: {mean_before:.3f} → {mean_after:.3f}   "
          f"tốt lên {len(better)} câu · TỤT {len(worse)} câu")
    for row in worse:
        print(f"    ▼ {row['id']} ({row['group']}): {row['before']:.2f} → {row['after']:.2f}")
    for row in better:
        print(f"    ▲ {row['id']} ({row['group']}): {row['before']:.2f} → {row['after']:.2f}")

    RESULT_PATH.write_text(
        json.dumps(
            {"chunks": len(chunks), "detail": rows, "regression": reg,
             "detail_recall5_before": recall5("before"), "detail_recall5_after": recall5("after"),
             "rs_recall5_before": mean_before, "rs_recall5_after": mean_after},
            ensure_ascii=False, indent=1),
        encoding="utf-8")
    print(f"\nĐã ghi {RESULT_PATH}")


if __name__ == "__main__":
    main()
