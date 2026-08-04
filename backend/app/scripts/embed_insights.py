"""Backfill embedding cho insight chưa có (chat-hybrid-retrieval, design D4).

    docker compose exec backend python -m app.scripts.embed_insights
    docker compose exec backend python -m app.scripts.embed_insights --limit 50
    docker compose exec backend python -m app.scripts.embed_insights --all-statuses
    docker compose exec backend python -m app.scripts.embed_insights --redo   # embed LẠI tất cả

Vì sao là script chứ không phải migration: migration phải tất định và chạy được offline.
Một `alembic upgrade head` phụ thuộc credentials Vertex + mạng + hạn mức API là thứ sẽ hỏng
đúng lúc dựng lại môi trường (design D4).

**Idempotent**: mặc định chỉ đụng tới hàng `embedding IS NULL`, nên chạy lại chỉ vá phần
còn thiếu — chạy hai lần không tạo ra gì trùng lặp và không tốn thêm lượt embed nào.

**Giữ lại làm công cụ, đừng dọn.** Nó là đường vá cho mọi ca `embedding NULL`: embed lỗi
lúc publish (D6), corpus nhập từ nơi khác, hoặc đổi định nghĩa `build_embedding_text`.
Đổi MODEL hay đổi `build_embedding_text` thì phải chạy `--redo`: trộn hai họ vector trong
cùng một cột làm cosine giữa hai nhóm tin lệch đi mà không có gì báo lỗi.
"""

import argparse
import asyncio
import logging
import time

from sqlalchemy import select

from app.ai.embedding import build_embedding_text
from app.ai.gemini_client import EMBED_BATCH_SIZE, EMBED_TASK_DOCUMENT, GeminiClient
from app.database import async_session_maker
from app.models.insight import Insight

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Nghỉ giữa hai lô. Backfill là việc chạy nền, không ai đứng chờ — nhường hạn mức cho
# pipeline analysis và cho chat đang phục vụ người dùng thật.
BATCH_PAUSE_SECONDS = 1.0


async def main(limit: int | None, redo: bool, all_statuses: bool, dry_run: bool) -> None:
    gemini = GeminiClient()

    async with async_session_maker() as session:
        query = select(Insight)
        if not all_statuses:
            # Đúng tập mà chat dựng index (`list_for_chat`): tin không bao giờ được xếp
            # hạng thì embed chỉ tốn tiền.
            query = query.where(Insight.status == "published").where(
                Insight.is_primary == True  # noqa: E712
            )
        if not redo:
            query = query.where(Insight.embedding.is_(None))
        query = query.order_by(Insight.created_at.desc())
        if limit:
            query = query.limit(limit)

        insights = list((await session.execute(query)).scalars().all())
        if not insights:
            print("Không có insight nào cần embed — đã đủ.")
            return

        print(
            f"{len(insights)} insight cần embed "
            f"({'embed LẠI tất cả' if redo else 'chỉ hàng embedding NULL'})"
        )
        if dry_run:
            for insight in insights[:5]:
                print(f"  - {insight.title[:70]}")
            print("(dry-run — không gọi Vertex, không ghi DB)")
            return

        done = failed = empty = 0
        for start in range(0, len(insights), EMBED_BATCH_SIZE):
            batch = insights[start : start + EMBED_BATCH_SIZE]
            texts = [build_embedding_text(i) for i in batch]

            # Tin không có chữ nào để embed (title rỗng + mọi field tóm tắt NULL) sẽ làm
            # Vertex từ chối CẢ LÔ, kéo theo những tin lành ở cùng lô. Tách ra trước.
            usable = [(i, t) for i, t in zip(batch, texts) if t]
            empty += len(batch) - len(usable)
            if not usable:
                continue

            vectors = gemini.embed([t for _, t in usable], EMBED_TASK_DOCUMENT)
            for (insight, _), vector in zip(usable, vectors):
                if vector is None:
                    failed += 1
                    continue
                insight.embedding = vector
                done += 1

            # Commit theo lô: một lỗi ở lô 5 không nên vứt bỏ 4 lô đã embed thành công
            # (đã tốn tiền rồi). Chạy lại sẽ tiếp đúng chỗ dừng nhờ điều kiện IS NULL.
            await session.commit()
            print(f"  … {min(start + EMBED_BATCH_SIZE, len(insights))}/{len(insights)}")
            if start + EMBED_BATCH_SIZE < len(insights):
                time.sleep(BATCH_PAUSE_SECONDS)

        print(f"\nXong: {done} embed thành công, {failed} lỗi, {empty} không có text.")
        if failed:
            print("Chạy lại lệnh này để vá phần lỗi (idempotent).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="chỉ xử lý N tin đầu")
    parser.add_argument(
        "--redo",
        action="store_true",
        help="embed LẠI cả tin đã có vector — dùng khi đổi model hoặc đổi build_embedding_text",
    )
    parser.add_argument(
        "--all-statuses",
        action="store_true",
        help="kể cả insight không published/is_primary (mặc định bỏ qua — chat không dùng tới)",
    )
    parser.add_argument("--dry-run", action="store_true", help="chỉ đếm, không gọi Vertex")
    args = parser.parse_args()
    asyncio.run(main(args.limit, args.redo, args.all_statuses, args.dry_run))
