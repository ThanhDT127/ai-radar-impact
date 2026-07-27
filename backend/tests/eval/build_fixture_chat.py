"""Sinh phần corpus của fixture chat từ DB — bằng chứng xuất xứ, giữ lại đừng dọn.

    docker compose exec backend python -m tests.eval.build_fixture_chat

Ghi bốn file (xem `chat_fixture.py` để biết vì sao tách):

    tests/eval/chat_corpus.jsonl        mọi insight `published` + `is_primary`
    tests/eval/chat_anchors.jsonl       `normalized_content` của các bài mà kịch bản neo vào
    tests/eval/chat_embeddings.jsonl    vector của từng insight (đọc thẳng từ cột DB)
    tests/eval/chat_query_vectors.jsonl vector của từng câu hỏi trong bộ kịch bản

⚠️ Chỉ phần **query vector** gọi Vertex (~50 lượt embed, vài xu) — corpus lấy vector có sẵn
trong DB nên không tốn gì. Tin nào `embedding IS NULL` thì chạy
`python -m app.scripts.embed_insights` TRƯỚC, không thì fixture thiếu vector và bộ đo xếp
hạng sẽ đo một `_rank` rơi về lexical mà không báo gì.

Anchor lấy từ `chat_scenarios.jsonl` (nếu đã có): script đọc `anchor_insight_id` của các
kịch bản mode `insight`/`expanded` rồi chỉ xuất content của đúng những bài đó. Lần chạy
đầu tiên — lúc chưa soạn kịch bản — file kịch bản chưa tồn tại là chuyện bình thường,
script bỏ qua phần anchor và báo rõ. Soạn kịch bản xong thì chạy lại để lấy content.

⚠️ `normalized_content` bị `purge_expired` xoá sau `retention_months`. Sau mốc đó script
này không dựng lại được anchor cũ nữa — đúng lý do fixture phải tự chứa thay vì trỏ id
vào DB (bài học `gate-benchmark-durability`).

Change change fixture (thêm kịch bản, mở rộng corpus) thì baseline trong
`chat_answer_harness.py` KHÔNG còn so sánh được — chốt lại baseline kèm lý do.
"""

import argparse
import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.ai.gemini_client import EMBED_TASK_QUERY, GeminiClient
from app.database import async_session_maker
from app.models.insight import Insight
from tests.eval.chat_fixture import (
    ANCHORS_PATH,
    CORPUS_FIELDS,
    CORPUS_PATH,
    EMBEDDINGS_PATH,
    QUERY_VECTORS_PATH,
    SCENARIOS_PATH,
)

# Số chữ số thập phân giữ lại của mỗi thành phần vector. Nguyên bản ~17 chữ số làm file
# phình gấp đôi mà không đổi được thứ hạng nào: thành phần embedding cỡ 1e-2 nên 6 chữ số
# đã dư bốn chữ số có nghĩa, và cosine là tổng của 768 tích — sai số làm tròn triệt tiêu
# lẫn nhau chứ không cộng dồn.
VECTOR_PRECISION = 6


def _serialize(insight: Insight) -> dict:
    row = {}
    for field in CORPUS_FIELDS:
        value = getattr(insight, field)
        if field in ("id",):
            value = str(value)
        elif hasattr(value, "isoformat"):
            value = value.isoformat()
        row[field] = value
    return row


def _wanted_anchor_ids(scenarios_path: Path) -> set[str]:
    if not scenarios_path.exists():
        print(f"(chưa có {scenarios_path.name} — bỏ qua phần anchor, chạy lại sau khi soạn kịch bản)")
        return set()
    ids = set()
    for line in scenarios_path.open(encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("anchor_insight_id"):
            ids.add(row["anchor_insight_id"])
    return ids


def _round(vector) -> list[float]:
    return [round(float(v), VECTOR_PRECISION) for v in vector]


def _write_embeddings(insights: list[Insight], path: Path) -> None:
    """Vector của corpus — đọc thẳng từ cột DB, KHÔNG gọi Vertex lại.

    Embed lại ở đây sẽ tạo ra một tập vector thứ hai khác tập đang phục vụ production, và
    bộ đo sẽ đo một corpus mà chat thật không bao giờ thấy.
    """
    missing = [str(i.id) for i in insights if i.embedding is None]
    if missing:
        raise SystemExit(
            f"{len(missing)} insight chưa có embedding — chạy "
            "`python -m app.scripts.embed_insights` trước, không thì bộ đo xếp hạng sẽ "
            f"lặng lẽ đo lối lexical.\nVí dụ: {missing[:3]}"
        )
    with path.open("w", encoding="utf-8") as fh:
        for insight in insights:
            fh.write(
                json.dumps(
                    {"insight_id": str(insight.id), "embedding": _round(insight.embedding)},
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"Đã ghi {len(insights)} vector insight vào {path}")


def _write_query_vectors(scenarios_path: Path, path: Path) -> None:
    """Vector của từng CÂU HỎI — chỗ duy nhất trong script này gọi Vertex.

    `RETRIEVAL_QUERY` chứ không `RETRIEVAL_DOCUMENT`: phải khớp đúng task_type mà
    `ChatService._embed_question` dùng, không thì fixture đo một cặp query↔doc lệch với
    production.
    """
    if not scenarios_path.exists():
        print(f"(chưa có {scenarios_path.name} — bỏ qua query vector)")
        return

    rows = [json.loads(line) for line in scenarios_path.open(encoding="utf-8") if line.strip()]
    questions = [(row["id"], row["question"]) for row in rows]
    vectors = GeminiClient().embed([q for _, q in questions], EMBED_TASK_QUERY)

    failed = [sid for (sid, _), v in zip(questions, vectors) if v is None]
    if failed:
        raise SystemExit(f"Embed câu hỏi lỗi cho {len(failed)} kịch bản: {failed[:5]}")

    with path.open("w", encoding="utf-8") as fh:
        for (scenario_id, _), vector in zip(questions, vectors):
            fh.write(
                json.dumps(
                    {"scenario_id": scenario_id, "embedding": _round(vector)},
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"Đã ghi {len(questions)} vector câu hỏi vào {path}")


async def build(corpus_path: Path, anchors_path: Path, scenarios_path: Path) -> None:
    async with async_session_maker() as session:
        result = await session.execute(
            select(Insight)
            .where(Insight.status == "published")
            .where(Insight.is_primary == True)  # noqa: E712
            .options(selectinload(Insight.raw_document))
            .order_by(Insight.published_at.desc().nullslast(), Insight.created_at.desc())
        )
        insights = list(result.scalars().all())

        with corpus_path.open("w", encoding="utf-8") as fh:
            for insight in insights:
                fh.write(json.dumps(_serialize(insight), ensure_ascii=False) + "\n")
        print(f"Đã ghi {len(insights)} insight vào {corpus_path}")

        _write_embeddings(insights, EMBEDDINGS_PATH)
        _write_query_vectors(scenarios_path, QUERY_VECTORS_PATH)

        wanted = _wanted_anchor_ids(scenarios_path)
        if not wanted:
            return

        by_id = {str(i.id): i for i in insights}
        missing = sorted(wanted - set(by_id))
        if missing:
            raise SystemExit(
                f"{len(missing)} anchor không còn là insight published+is_primary:\n"
                + "\n".join(missing)
            )

        written = 0
        with anchors_path.open("w", encoding="utf-8") as fh:
            for insight_id in sorted(wanted):
                doc = by_id[insight_id].raw_document
                content = (doc.normalized_content or "").strip() if doc else ""
                if not content:
                    raise SystemExit(
                        f"{insight_id}: normalized_content rỗng (đã purge?) — "
                        "chọn anchor khác cho kịch bản mode B."
                    )
                fh.write(
                    json.dumps(
                        {
                            "insight_id": insight_id,
                            "title": by_id[insight_id].title,
                            "normalized_content": content,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                written += 1
        print(f"Đã ghi nội dung bài gốc của {written} anchor vào {anchors_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=CORPUS_PATH)
    parser.add_argument("--anchors", type=Path, default=ANCHORS_PATH)
    parser.add_argument("--scenarios", type=Path, default=SCENARIOS_PATH)
    args = parser.parse_args()
    asyncio.run(build(args.corpus, args.anchors, args.scenarios))


if __name__ == "__main__":
    main()
