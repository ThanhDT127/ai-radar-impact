"""Định nghĩa "text để embed" của một insight — MỘT chỗ duy nhất (design D2).

Vì sao phải một chỗ: text dùng lúc ingest và text dùng lúc backfill mà lệch nhau thì corpus
mang hai họ vector khác nhau, và **không có gì báo lỗi** — chỉ là cosine giữa hai nhóm tin
kém đi một chút, tức là xếp hạng tệ đi một cách im lặng. Cùng loại bẫy với `_relevance` và
`_question_terms` phải dùng chung một regex.

Đơn vị embed là **cả insight, không chunk** (D2): insight vốn ngắn, và mode B đã nhồi cả bài
gốc nên không cần truy hồi theo đoạn.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover — chỉ để gợi ý kiểu, tránh phụ thuộc vòng lúc chạy
    from app.models.insight import Insight


def build_embedding_text(insight: "Insight") -> str:
    """Chuỗi cô đọng đại diện cho insight: `title + signal + so_what + summary_short + topics`.

    Cùng bộ field mà `_relevance` soi, trừ `affected_roles` — vai trò là **trục xếp hạng**
    riêng (`score_for_role`, `_roles_in_question`), nhét vào vector chỉ làm mọi tin cùng vai
    trò trông giống nhau về ngữ nghĩa và làm loãng tín hiệu chủ đề.

    Ghép bằng xuống dòng chứ không bằng dấu cách: model embedding đọc đây như văn bản, và
    ranh giới dòng giúp nó không dính tiêu đề vào câu đầu của phần tóm tắt.
    """
    parts = [
        insight.title,
        insight.signal,
        insight.so_what,
        insight.summary_short,
        " · ".join(insight.topics or []),
    ]
    return "\n".join(p.strip() for p in parts if p and p.strip())
