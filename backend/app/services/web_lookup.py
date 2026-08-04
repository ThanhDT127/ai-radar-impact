"""Biến uri thô của grounding thành `WebSource` dùng được (`chat-web-fallback` §5).

Đây là nửa sau của Fork B2: grounding chỉ cho **định danh nguồn**, nội dung thì ta tự tải.
Lý do không dùng bản tóm tắt model tự viết ở bước tra cứu — nếu văn bản do model viết mà
citation lại trỏ về trang gốc, thì một lần diễn giải sai thành **lời bịa có kèm nguồn hợp
lệ**, đúng chế độ hỏng mà mô hình trích dẫn của hệ thống sinh ra để chặn.
"""

import asyncio
import logging

import httpx

from app.connectors.web_article_connector import WebArticleConnector
from app.services.chat_grounding import WebSource
from app.services.normalizer import MAX_CONTENT_LENGTH

logger = logging.getLogger(__name__)

# Trang tin/tài liệu thường chặn client không có UA trình duyệt. Không phải để né chống-bot —
# chỉ để không bị từ chối ở bước giải chuyển hướng vì thiếu một header tầm thường.
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def _resolve(uri: str, timeout: float) -> str | None:
    """Giải link chuyển hướng của Vertex → URL THẬT.

    Vì sao cần, và vì sao KHÔNG phải vì nội dung (design D10, đo 03/08/2026): trafilatura tự
    theo redirect nên tỉ lệ lấy được nội dung y hệt nhau (8/9 cả hai cách). Bước này tồn tại
    cho **trích dẫn** — chỉ sau khi giải mới có URL người dùng bấm được và tiêu đề thật.
    `grounding_chunks[].web.title` chỉ chứa TÊN MIỀN (`'google.com'`), không dùng làm nhãn được.

    `HEAD` trước cho rẻ; trang nào chặn HEAD thì thử `GET`.
    """
    for method in ("HEAD", "GET"):
        try:
            with httpx.Client(
                follow_redirects=True, timeout=timeout, headers={"User-Agent": _UA}
            ) as client:
                response = client.request(method, uri)
                return str(response.url)
        except Exception:
            continue
    logger.info("Không giải được link chuyển hướng: %s", uri[:80])
    return None


def _fetch_one(uri: str, timeout: float) -> WebSource | None:
    """Một nguồn: giải chuyển hướng → tải → trích xuất. `None` = bỏ nguồn này.

    Nguồn không giải được thì **bỏ hẳn**, không rơi về link chuyển hướng: một nguồn mà người
    dùng không mở ra kiểm chứng được thì không phải là nguồn, chỉ là một chuỗi mờ đục có thể
    hết hạn.
    """
    real_url = _resolve(uri, timeout)
    if not real_url:
        return None

    article = WebArticleConnector().extract(real_url, timeout=int(timeout))
    if article is None or not article.content.strip():
        return None

    # CÙNG trần với ô sâu corpus — dùng lại hằng số chứ không chép số, để hai loại nguồn
    # không lặng lẽ có hai ngân sách token khác nhau.
    return WebSource(
        uri=real_url,
        title=(article.title or real_url)[:300],
        text=article.content.strip()[:MAX_CONTENT_LENGTH],
    )


async def collect_web_sources(
    uris: list[str], limit: int, timeout: float
) -> list[WebSource]:
    """Tải song song tối đa `limit` nguồn, bỏ nguồn nào hỏng.

    Song song vì độ trễ ở đây cộng thẳng vào TTFT: đo 03/08, mỗi nguồn tốn 0,7–3,7s (giải
    chuyển hướng + tải). Nối tiếp 3 nguồn là ~9s, song song là ~4s.

    Suy giảm êm (design D5): một phần hỏng → dùng phần còn lại. Hỏng hết → trả danh sách
    rỗng, và tầng service quyết định rơi về bản tóm tắt. **Không ca nào được ném ra ngoài.**
    """
    wanted = [u for u in uris if u][:limit]
    if not wanted:
        return []

    results = await asyncio.gather(
        *(asyncio.to_thread(_fetch_one, u, timeout) for u in wanted),
        return_exceptions=True,
    )

    sources: list[WebSource] = []
    for uri, result in zip(wanted, results):
        if isinstance(result, Exception):
            logger.warning("Tải nguồn %s lỗi: %s", uri[:60], result)
            continue
        if result is not None:
            sources.append(result)

    logger.info("Tra cứu ngoài: %d/%d nguồn lấy được nội dung", len(sources), len(wanted))
    return sources
