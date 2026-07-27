"""Sinh phần corpus của fixture chat từ DB — bằng chứng xuất xứ, giữ lại đừng dọn.

    docker compose exec backend python -m tests.eval.build_fixture_chat

Ghi hai file (xem `chat_fixture.py` để biết vì sao tách):

    tests/eval/chat_corpus.jsonl    mọi insight `published` + `is_primary`
    tests/eval/chat_anchors.jsonl   `normalized_content` của các bài mà kịch bản neo vào

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

from app.database import async_session_maker
from app.models.insight import Insight
from tests.eval.chat_fixture import (
    ANCHORS_PATH,
    CORPUS_FIELDS,
    CORPUS_PATH,
    SCENARIOS_PATH,
)


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
