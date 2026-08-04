"""Backfill đoạn thân bài + embedding cho tín hiệu xếp hạng thứ ba (chat-chunk-retrieval).

    docker compose exec backend python -m app.scripts.chunk_documents
    docker compose exec backend python -m app.scripts.chunk_documents --limit 50
    docker compose exec backend python -m app.scripts.chunk_documents --dry-run
    docker compose exec backend python -m app.scripts.chunk_documents --redo   # chunk LẠI tất cả

Vì sao là script chứ không phải migration: cùng lý do với `embed_insights` — migration phải
tất định và chạy được offline, một `alembic upgrade head` phụ thuộc credentials Vertex + mạng
+ hạn mức API là thứ sẽ hỏng đúng lúc dựng lại môi trường.

**Idempotent**: mặc định chỉ đụng bài **chưa có đoạn nào**, nên chạy lại chỉ vá phần còn
thiếu. Chạy hai lần liên tiếp thì lần hai không đổi gì và không tốn lượt embed nào.

⚠️ **`--redo` là BẮT BUỘC khi đổi hằng số chunk** (`app/ai/chunking.py`) **hoặc đổi model
embedding**. Hai họ vector trộn trong một cột làm cosine lệch mà **không có gì báo lỗi** —
cùng cái bẫy của `build_embedding_text`. Sau `--redo` phải sinh lại fixture xếp hạng của RS
harness, không thì bộ đo chấm một corpus khác corpus đang phục vụ.

Lượt embed ở đây **KHÔNG** tính vào `max_daily_chat_calls` / `max_daily_analysis`: hai bộ
đếm đó canh budget lượt sinh văn bản (~19k token), còn đây là vài trăm token trên model
embedding, rẻ hơn vài bậc.
"""

import argparse
import asyncio
import logging
import time

from sqlalchemy import select

from app.ai.chunking import split_content
from app.ai.gemini_client import EMBED_BATCH_SIZE, EMBED_TASK_DOCUMENT, GeminiClient
from app.database import async_session_maker
from app.models.insight import Insight
from app.models.raw_document import RawDocument
from app.repositories.document_chunk_repo import DocumentChunkRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

BATCH_PAUSE_SECONDS = 1.0


async def main(limit: int | None, redo: bool, all_statuses: bool, dry_run: bool) -> None:
    gemini = GeminiClient()

    async with async_session_maker() as session:
        repo = DocumentChunkRepository(session)

        # Chỉ chunk bài CÓ insight: đoạn phục vụ xếp hạng insight, nên bài chưa phân tích
        # (hoặc bị gate loại) chunk ra cũng không ai xếp hạng tới — chỉ tốn tiền embed.
        query = select(Insight.id, RawDocument.id, RawDocument.normalized_content).join(
            RawDocument, Insight.raw_document_id == RawDocument.id
        )
        if not all_statuses:
            # Đúng tập mà chat dựng index (`list_for_chat`).
            query = query.where(Insight.status == "published").where(
                Insight.is_primary == True  # noqa: E712
            )
        query = query.where(RawDocument.normalized_content.isnot(None))
        query = query.order_by(Insight.created_at.desc())

        rows = list((await session.execute(query)).all())

        if not redo:
            existing = await repo.document_ids_with_chunks()
            rows = [r for r in rows if r[1] not in existing]
        if limit:
            rows = rows[:limit]

        if not rows:
            print("Không có bài nào cần chunk — đã đủ.")
            return

        # Chunk trước, embed sau: `split_content` là hàm thuần và miễn phí, nên biết chính
        # xác số đoạn TRƯỚC khi tiêu một đồng nào. Đó cũng là thứ `--dry-run` in ra.
        planned = [
            (insight_id, doc_id, split_content(content))
            for insight_id, doc_id, content in rows
        ]
        planned = [p for p in planned if p[2]]
        total_chunks = sum(len(p[2]) for p in planned)

        print(
            f"{len(planned)} bài → {total_chunks} đoạn "
            f"({'chunk LẠI tất cả' if redo else 'chỉ bài chưa có đoạn'})"
        )
        if dry_run:
            for insight_id, _, chunks in planned[:5]:
                print(f"  - {str(insight_id)[:8]}: {len(chunks)} đoạn, "
                      f"{[len(c) for c in chunks]} ký tự")
            print("(dry-run — không gọi Vertex, không ghi DB)")
            return

        done = failed = 0
        for start in range(0, len(planned), EMBED_BATCH_SIZE):
            batch = planned[start : start + EMBED_BATCH_SIZE]
            for insight_id, doc_id, chunks in batch:
                vectors = gemini.embed(chunks, EMBED_TASK_DOCUMENT)
                # Đoạn embed lỗi vẫn được LƯU với `embedding NULL`: truy vấn xếp hạng lọc
                # `IS NOT NULL` nên nó không nhiễu, còn giữ lại thì `--redo` vá được và ta
                # không mất dấu vết bài nào đã chunk.
                await repo.replace_for_document(
                    raw_document_id=doc_id,
                    insight_id=insight_id,
                    chunks=chunks,
                    embeddings=vectors,
                )
                failed += sum(1 for v in vectors if v is None)
                done += len(chunks)

            print(f"  … {min(start + EMBED_BATCH_SIZE, len(planned))}/{len(planned)} bài")
            if start + EMBED_BATCH_SIZE < len(planned):
                time.sleep(BATCH_PAUSE_SECONDS)

        print(f"\nXong: {done} đoạn đã ghi, {failed} đoạn embed lỗi (embedding NULL).")
        if failed:
            print("Chạy `--redo` cho phần lỗi, hoặc chạy lại sau khi Vertex ổn định.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="chỉ xử lý N bài đầu")
    parser.add_argument(
        "--redo",
        action="store_true",
        help="chunk LẠI cả bài đã có đoạn — BẮT BUỘC khi đổi hằng số chunk hoặc đổi model",
    )
    parser.add_argument(
        "--all-statuses",
        action="store_true",
        help="kể cả insight không published/is_primary (mặc định bỏ qua — chat không dùng tới)",
    )
    parser.add_argument("--dry-run", action="store_true", help="chỉ đếm, không gọi Vertex")
    args = parser.parse_args()
    asyncio.run(main(args.limit, args.redo, args.all_statuses, args.dry_run))
