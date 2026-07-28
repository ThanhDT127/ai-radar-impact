"""Task 0.1 — đào định danh CHỈ tồn tại trong thân bài, không có trong biểu diễn truy hồi.

Vì sao phải đào bằng máy chứ không tự nghĩ ra câu hỏi: spike của `chat-context-depth` soạn
6 câu chi tiết bằng tay và **cả 6 đều truy hồi đúng ở hạng 1** — vì người soạn vô thức
chọn chủ đề mình nhớ được, mà thứ nhớ được là thứ có trong tiêu đề. Muốn đo đúng chế độ
hỏng "khám phá bằng chi tiết" thì phải chọn định danh theo **tiêu chí kiểm được**, không
theo trực giác.

Tiêu chí một định danh là ứng viên tốt:
  1. xuất hiện ≥ 2 lần trong `normalized_content` của đúng một bài (đủ thật, không phải lỗi OCR)
  2. VẮNG trong biểu diễn truy hồi của CHÍNH bài đó (title/signal/so_what/summary_short/topics
     — đúng bộ field mà `_relevance` soi và `build_embedding_text` embed)
  3. VẮNG trong biểu diễn truy hồi của MỌI bài khác — nếu nó có ở bài khác thì câu hỏi chứa
     nó sẽ kéo nhầm bài kia lên, và ca đo trở thành đo chuyện khác
  4. chỉ nằm trong thân bài của đúng MỘT insight ⇒ `must_have` có đúng một phần tử (DoD 0.1)
  5. "trông như định danh": có chữ số, hoặc CamelCase, hoặc ACRONYM, hoặc có `-`/`.`/`@`/`_`

    docker compose exec backend python /app/eval_chunk/mine_detail_terms.py

Corpus lấy từ `tests/eval/chat_corpus.jsonl` (ảnh chụp 27/07, cùng corpus mọi baseline đang
dùng); thân bài lấy từ DB theo `raw_document_id`. Bài nào đã bị `purge_expired` xoá content
thì bỏ qua và báo số.
"""

import asyncio
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from sqlalchemy import select

from app.database import async_session_maker
from app.models.insight import Insight
from tests.eval.chat_fixture import load_corpus

OUT_PATH = Path("/tmp/detail_terms.json")

# Cùng regex tách token mà `_question_terms` / `_relevance` dùng — hai bên phải nhìn thế
# giới bằng một luật, không thì "vắng trong biểu diễn" là một kết luận sai.
TOKEN_RE = re.compile(r"[0-9a-zA-ZÀ-ỹ]+")

# Định danh phải khác biệt về HÌNH DẠNG, không chỉ hiếm về tần suất: từ tiếng Anh thường
# hiếm trong corpus tiếng Việt cũng lọt hết nếu chỉ lọc theo tần suất.
IDENTIFIER_RE = re.compile(
    r"^(?=.*[0-9A-Z])"          # phải có chữ số hoặc chữ hoa ở đâu đó
    r"[0-9A-Za-z][0-9A-Za-z._\-@]*$"
)

MIN_BODY_HITS = 2
MIN_LEN = 3


def representation(row: dict) -> set[str]:
    """Tập token của BIỂU DIỄN TRUY HỒI — đúng bộ field `_relevance` soi.

    `affected_roles` cố ý KHÔNG có mặt: nó là trục xếp hạng riêng, và một định danh trùng
    tên vai trò không phải là thứ ta đang đi tìm.
    """
    text = " ".join(
        filter(
            None,
            [
                row.get("title"),
                row.get("signal"),
                row.get("so_what"),
                row.get("summary_short"),
                " ".join(row.get("topics") or []),
            ],
        )
    )
    return {t.lower() for t in TOKEN_RE.findall(text)}


def body_terms(content: str) -> Counter:
    """Đếm token thân bài, giữ NGUYÊN chữ hoa để lọc hình dạng, khoá theo bản lowercase."""
    counts: Counter = Counter()
    surface: dict[str, str] = {}
    for raw in re.findall(r"[0-9A-Za-zÀ-ỹ][0-9A-Za-zÀ-ỹ._\-@]*", content):
        token = raw.strip("._-@")
        if len(token) < MIN_LEN or not IDENTIFIER_RE.match(token):
            continue
        key = token.lower()
        counts[key] += 1
        surface.setdefault(key, token)
    counts.surface = surface  # type: ignore[attr-defined]
    return counts


async def load_bodies(ids: list[str]) -> dict[str, str]:
    async with async_session_maker() as session:
        rows = (
            await session.execute(
                select(Insight).where(Insight.id.in_(ids))
            )
        ).scalars().all()
        bodies = {}
        for insight in rows:
            doc = await session.get(type(insight).raw_document.property.mapper.class_,
                                    insight.raw_document_id)
            if doc is not None and doc.normalized_content:
                bodies[str(insight.id)] = doc.normalized_content
        return bodies


async def main() -> None:
    corpus = load_corpus()
    by_id = {row["id"]: row for row in corpus}
    bodies = await load_bodies(list(by_id))
    print(f"corpus {len(corpus)} tin · có thân bài {len(bodies)} · "
          f"thiếu {len(corpus) - len(bodies)} (purge hoặc content rỗng)")

    # Biểu diễn truy hồi của TOÀN corpus: một định danh có mặt ở bất kỳ biểu diễn nào cũng
    # bị loại (tiêu chí 3) — nếu không, câu hỏi sẽ kéo nhầm bài khác lên và ca đo hỏng.
    everywhere: set[str] = set()
    for row in corpus:
        everywhere |= representation(row)

    per_insight: dict[str, Counter] = {}
    doc_freq: Counter = Counter()
    surfaces: dict[str, str] = {}
    for insight_id, content in bodies.items():
        counts = body_terms(content)
        surfaces.update(counts.surface)  # type: ignore[attr-defined]
        kept = Counter(
            {
                term: n
                for term, n in counts.items()
                if n >= MIN_BODY_HITS and term not in everywhere
            }
        )
        per_insight[insight_id] = kept
        for term in kept:
            doc_freq[term] += 1

    # Tiêu chí 4: chỉ nằm trong thân bài của đúng một insight.
    unique_terms = {t for t, n in doc_freq.items() if n == 1}

    # ⚠️ Cổng chống DƯƠNG TÍNH GIẢ, học được lúc đọc kết quả lần chạy đầu: bộ đếm thân bài
    # giữ `.`/`-`/`@` bên trong token, còn `_question_terms` CẮT ở đó. Nên `v3.7.0` trông như
    # "vắng khắp nơi" trong khi câu hỏi chứa nó thực ra đi vào `_relevance` thành `v3`,`7`,`0`
    # — và bài `Announcing etcd v3.7.0` khớp ngay ở tiêu đề. Ứng viên chỉ hợp lệ khi MỌI
    # mảnh của nó (theo regex câu hỏi) đều vắng trong biểu diễn của toàn corpus; không thì
    # ca đo sẽ đo tầng lexical đang hoạt động bình thường và kết luận gate sẽ sai.
    def lexically_invisible(term: str) -> bool:
        pieces = [p for p in TOKEN_RE.findall(term.lower()) if len(p) >= 2]
        return bool(pieces) and all(p not in everywhere for p in pieces)

    unique_terms = {t for t in unique_terms if lexically_invisible(surfaces[t])}

    results = []
    for insight_id, counts in per_insight.items():
        picks = sorted(
            ((surfaces[t], n) for t, n in counts.items() if t in unique_terms),
            key=lambda p: -p[1],
        )[:12]
        if picks:
            results.append(
                {
                    "insight_id": insight_id,
                    "title": by_id[insight_id]["title"],
                    "topics": by_id[insight_id].get("topics"),
                    "terms": picks,
                }
            )

    results.sort(key=lambda r: -sum(n for _, n in r["terms"]))
    print(f"\n{len(results)} bài có ít nhất một định danh độc quyền thân bài\n")
    for row in results[:45]:
        terms = ", ".join(f"{t}×{n}" for t, n in row["terms"][:8])
        print(f"  {row['insight_id'][:8]}  {row['title'][:58]:<60} {terms}")

    OUT_PATH.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nĐã ghi {OUT_PATH}")


if __name__ == "__main__":
    sys.exit(asyncio.run(main()) or 0)
