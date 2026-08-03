"""Đông lạnh kết quả tra cứu ngoài để bộ đo giữ tính TẤT ĐỊNH (task 9.1).

Vì sao phải đông lạnh: nội dung web đổi theo thời gian và theo vị trí địa lý. Gọi thật trong
harness thì (a) hai lần chạy cho hai kết quả khác nhau nên không so sánh được với baseline,
và (b) mỗi lần chạy tốn tiền grounding — mà harness là thứ cần chạy nhiều lần.

Đông lạnh **nội dung đã tải**, không phải chỉ uri: uri thì lần sau tải lại vẫn ra trang khác.
Cùng lý do với `chat_chunk_ranks.jsonl` — ở đó đông lạnh *thứ hạng* chứ không phải vector, để
harness không phải dựng lại một đường tính thứ hai.

    # sinh/cập nhật fixture (tốn tiền, chỉ chạy khi đổi kịch bản)
    docker compose exec backend python -m tests.eval.web_fixture --refresh
"""

import argparse
import asyncio
import json
import pathlib
from datetime import datetime, timezone

from app.ai.gemini_client import get_chat_client
from app.config import settings
from app.services.web_lookup import collect_web_sources

HERE = pathlib.Path(__file__).parent
FIXTURE = HERE / "chat_web_sources.jsonl"

# Truy vấn của các kịch bản `partial_ground` — vế mà corpus KHÔNG có.
QUERIES = [
    "Gemini Embedding 2 model dimensions and context length",
    "Cohere Embed model for RAG retrieval quality",
    "Pinecone vector database storage architecture",
    "Vietnam Decree 13 personal data protection requirements",
    "OpenAI text-embedding-3 API pricing",
]


def _fingerprint() -> dict:
    """Dấu vân tay: đổi hằng số nào thì fixture phải sinh lại.

    `load_web_sources` NỔ khi lệch. Không có nó thì đổi `chat_web_max_sources` hay
    `MAX_CONTENT_LENGTH` rồi chạy harness sẽ chấm trên dữ liệu mốc mà mọi con số vẫn trông
    bình thường — đúng chế độ hỏng mà fixture đông lạnh sinh ra để chặn.
    """
    from app.services.normalizer import MAX_CONTENT_LENGTH

    return {
        "_meta": True,
        "queries": len(QUERIES),
        "max_sources": settings.chat_web_max_sources,
        "max_content_length": MAX_CONTENT_LENGTH,
        "search_model": settings.chat_web_search_model_id,
    }


async def refresh() -> None:
    client = get_chat_client()
    lines = [json.dumps(_fingerprint(), ensure_ascii=False)]

    for query in QUERIES:
        print(f"tra cứu: {query!r}")
        result = await asyncio.to_thread(client.search_web, query)
        sources = await collect_web_sources(
            result.uris,
            limit=settings.chat_web_max_sources,
            timeout=settings.chat_web_fetch_timeout_seconds,
        )
        print(f"  → {len(sources)}/{len(result.uris)} nguồn tải được")
        lines.append(
            json.dumps(
                {
                    "query": query,
                    "captured_at": datetime.now(timezone.utc).isoformat(),
                    "search_entry_point": result.search_entry_point,
                    "sources": [
                        {"uri": s.uri, "title": s.title, "text": s.text, "verbatim": s.verbatim}
                        for s in sources
                    ],
                },
                ensure_ascii=False,
            )
        )

    FIXTURE.write_text("\n".join(lines) + "\n")
    print(f"\nĐã ghi {FIXTURE} ({FIXTURE.stat().st_size / 1024:.0f}KB)")


def load_web_sources() -> dict[str, dict]:
    """Đọc fixture, NỔ nếu dấu vân tay lệch cấu hình hiện tại."""
    if not FIXTURE.exists():
        raise FileNotFoundError(
            f"Thiếu {FIXTURE.name} — chạy `python -m tests.eval.web_fixture --refresh`"
        )
    lines = [json.loads(x) for x in FIXTURE.read_text().splitlines() if x.strip()]
    meta, rows = lines[0], lines[1:]
    now = _fingerprint()
    lệch = {k: (meta.get(k), now[k]) for k in now if k != "_meta" and meta.get(k) != now[k]}
    if lệch:
        raise RuntimeError(
            f"Fixture tra cứu đã MỐC — lệch {lệch}. "
            "Chạy `python -m tests.eval.web_fixture --refresh` để sinh lại."
        )
    return {r["query"]: r for r in rows}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="gọi Vertex thật, TỐN TIỀN")
    args = ap.parse_args()
    if not args.refresh:
        data = load_web_sources()
        print(f"{len(data)} truy vấn đã đông lạnh:")
        for q, row in data.items():
            print(f"  {len(row['sources'])} nguồn | {q}")
    else:
        asyncio.run(refresh())
