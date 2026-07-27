"""Fixture tự chứa cho bộ đo chất lượng câu trả lời chat (`chat-eval-quality-gate`).

Năm mảnh, năm file — đọc được độc lập, sinh lại được bằng một lệnh:

    chat_corpus.jsonl        toàn bộ insight `published` + `is_primary` (ảnh chụp corpus)
    chat_anchors.jsonl       `normalized_content` của riêng những bài mà kịch bản mode B neo vào
    chat_scenarios.jsonl     ~50 kịch bản gán nhãn tay (mode, câu hỏi, must_have, lý do)
    chat_embeddings.jsonl    vector 768 chiều của từng insight (chat-hybrid-retrieval)
    chat_query_vectors.jsonl vector 768 chiều của từng CÂU HỎI trong bộ kịch bản

Hai file vector sinh ra cùng `chat-hybrid-retrieval` (27/07/2026) và tồn tại vì đúng một lý
do: giữ bộ đo xếp hạng **miễn phí và tất định** sau khi `_rank` có tầng vector. Không có
chúng, hoặc harness phải gọi Vertex mỗi lần chạy (mất "0 đồng, chạy trong pytest mặc định"),
hoặc nó đo một `_rank` KHÔNG có tầng vector — tức là đo một pipeline không tồn tại trong
production, và im lặng về việc đó.

Vì sao corpus phải tự chứa (giống `gate_benchmark.jsonl`): bộ đo phải chạy được khi DB
tắt, và phải đo trên **cùng một corpus** qua thời gian. Đo trên DB sống thì mỗi lần ingest
lại đổi tập ứng viên, và điểm tụt vì corpus đổi sẽ bị đọc nhầm thành hồi quy prompt.

Vì sao `normalized_content` tách riêng: chỉ mode B nạp bài gốc, mà mode B chỉ neo vào vài
bài. Nhét content của cả 179 tin vào corpus là ~840KB thừa trong repo.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

from app.models.insight import Insight
from app.models.raw_document import RawDocument

FIXTURE_DIR = Path(__file__).parent
CORPUS_PATH = FIXTURE_DIR / "chat_corpus.jsonl"
ANCHORS_PATH = FIXTURE_DIR / "chat_anchors.jsonl"
SCENARIOS_PATH = FIXTURE_DIR / "chat_scenarios.jsonl"
EMBEDDINGS_PATH = FIXTURE_DIR / "chat_embeddings.jsonl"
QUERY_VECTORS_PATH = FIXTURE_DIR / "chat_query_vectors.jsonl"

# Mọi field mà pipeline chat thật ĐỌC. Danh sách này là hợp đồng giữa fixture và code
# sản phẩm — thiếu một field thì bộ đo vẫn chạy nhưng đo trên đầu vào nghèo hơn
# production, tức là cho số sai một cách im lặng. Nguồn của từng field:
#
#   _relevance()          title, signal, so_what, summary_short, topics, affected_roles
#   score_for_role()      recommendations, impact_label, practical_indicators,
#                         actionability_score, intelligence_tier, trust_score,
#                         published_at, created_at
#   build_index_block()   title, signal, summary_short, affected_roles, topics, ngày
#   build_insight_block() + why_it_matters, summary_medium, risks, recommendations
#   resolve_citations()   id, source_url
CORPUS_FIELDS = (
    "id",
    "title",
    "source_url",
    "summary_short",
    "summary_medium",
    "signal",
    "why_it_matters",
    "so_what",
    "topics",
    "affected_roles",
    "recommendations",
    "risks",
    "impact_label",
    "trust_score",
    "actionability_score",
    "intelligence_tier",
    "practical_indicators",
    "published_at",
    "created_at",
)

_DATETIME_FIELDS = ("published_at", "created_at")

# Mode của kịch bản = mode mà pipeline ĐÁNG LẼ trả về.
#   insight   hỏi trong phạm vi bài đang xem  → 1 bước, citation [1]
#   global    hỏi toàn hệ thống, không mở bài  → 1 bước
#   expanded  đang mở bài nhưng hỏi ra ngoài  → sentinel → bước 2 (chat-scope-routing)
SCENARIO_MODES = ("insight", "global", "expanded")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Không thấy {path.name}. Sinh lại bằng "
            "`python -m tests.eval.build_fixture_chat` (cần DB đang chạy)."
        )
    rows = [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]
    if not rows:
        raise ValueError(f"{path.name} rỗng")
    return rows


def load_corpus(path: Path = CORPUS_PATH) -> list[dict]:
    """Đọc corpus và khẳng định nó vẫn mang đủ field mà pipeline thật đọc."""
    rows = _load_jsonl(path)
    for row in rows:
        missing = [f for f in CORPUS_FIELDS if f not in row]
        if missing:
            raise ValueError(
                f"{row.get('id', '?')}: fixture thiếu field {missing}. "
                "Pipeline thật đọc những field này (xem CORPUS_FIELDS) — sinh lại fixture "
                "trước khi đo, đo tiếp sẽ cho số thấp giả."
            )
    return rows


def load_anchors(path: Path = ANCHORS_PATH) -> dict[str, str]:
    """`insight_id → normalized_content` cho các bài mà mode B/expanded neo vào."""
    return {row["insight_id"]: row["normalized_content"] for row in _load_jsonl(path)}


def load_embeddings(path: Path = EMBEDDINGS_PATH) -> dict[str, list[float]]:
    """`insight_id → vector` cho tầng vector của `_rank` (chat-hybrid-retrieval).

    **Ném lỗi khi thiếu file, không trả rỗng.** Thiếu embedding không làm bộ đo gãy — nó
    làm `_rank` lặng lẽ rơi về lexical (đường suy giảm êm của D6) và cho ra một con số
    trông hoàn toàn bình thường nhưng đo sai pipeline. Đúng loại lỗi mà harness sinh ra để
    chặn, nên nó phải nổ.
    """
    return {row["insight_id"]: row["embedding"] for row in _load_jsonl(path)}


def load_query_vectors(path: Path = QUERY_VECTORS_PATH) -> dict[str, list[float]]:
    """`scenario_id → vector câu hỏi`. Đông lạnh để bộ đo không phải gọi Vertex."""
    return {row["scenario_id"]: row["embedding"] for row in _load_jsonl(path)}


def load_scenarios(path: Path = SCENARIOS_PATH) -> list[dict]:
    """Đọc bộ kịch bản + kiểm tính nhất quán của nhãn tay.

    Nhãn sai hình dạng (mode lạ, must_have trỏ insight không có trong corpus, mode B
    không có anchor) làm điểm sai mà không báo lỗi — nên chặn ngay ở đây.
    """
    rows = _load_jsonl(path)
    corpus_ids = {row["id"] for row in load_corpus()}
    anchors = load_anchors()
    seen: set[str] = set()

    for row in rows:
        sid = row.get("id", "?")
        if sid in seen:
            raise ValueError(f"Trùng id kịch bản: {sid}")
        seen.add(sid)

        if row["mode"] not in SCENARIO_MODES:
            raise ValueError(f"{sid}: mode lạ {row['mode']!r}, phải thuộc {SCENARIO_MODES}")
        if not row.get("question", "").strip():
            raise ValueError(f"{sid}: thiếu câu hỏi")
        if not row.get("label_reason", "").strip():
            raise ValueError(f"{sid}: thiếu label_reason — nhãn không có lý do là nhãn không kiểm được")

        unknown = [i for i in row.get("must_have", []) if i not in corpus_ids]
        if unknown:
            raise ValueError(f"{sid}: must_have trỏ insight không có trong corpus: {unknown}")

        anchor = row.get("anchor_insight_id")
        if row["mode"] in ("insight", "expanded"):
            if not anchor:
                raise ValueError(f"{sid}: mode {row['mode']} phải có anchor_insight_id")
            if anchor not in corpus_ids:
                raise ValueError(f"{sid}: anchor_insight_id không có trong corpus")
            if anchor not in anchors:
                raise ValueError(
                    f"{sid}: chưa có nội dung bài gốc cho anchor {anchor}. "
                    "Chạy lại `python -m tests.eval.build_fixture_chat` để lấy content."
                )
        elif anchor:
            raise ValueError(f"{sid}: mode global không được có anchor_insight_id")

    return rows


def _parse_dt(value) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def rehydrate(
    row: dict, content: str | None = None, embedding: list[float] | None = None
) -> Insight:
    """JSONL → `Insight` ORM **transient** (không session, không DB).

    Transient chứ không detached-persistent: object chưa từng có identity nên SQLAlchemy
    không thử lazy-load quan hệ nào, kể cả `raw_document` — đó là lý do bộ đo chạy được
    khi `docker compose stop db`. Bài gốc (nếu có) gắn tay thành `RawDocument` transient.
    """
    fields = {f: row[f] for f in CORPUS_FIELDS}
    fields["id"] = uuid.UUID(fields["id"])
    for f in _DATETIME_FIELDS:
        fields[f] = _parse_dt(fields[f])

    insight = Insight(**fields)
    # `None` là trạng thái HỢP LỆ ở production (tin chưa backfill) — giữ nguyên chứ không
    # thay bằng vector 0, vì vector 0 là "chắc chắn không liên quan" chứ không phải "chưa biết".
    insight.embedding = embedding
    if content is not None:
        insight.raw_document = RawDocument(normalized_content=content)
    return insight


def rehydrate_corpus(
    rows: list[dict],
    anchors: dict[str, str] | None = None,
    embeddings: dict[str, list[float]] | None = None,
) -> list[Insight]:
    """Cả corpus dạng ORM; bài nào là anchor thì kèm luôn `normalized_content`.

    `embeddings=None` → tự nạp từ fixture. Mặc định phải là "giống production", vì lối rơi
    về lexical là một suy giảm ÊM: quên truyền embedding vào thì bộ đo vẫn chạy, vẫn ra số,
    chỉ là số của một `_rank` khác. Truyền `{}` tường minh khi cố ý muốn đo lối lexical.
    """
    anchors = anchors or {}
    if embeddings is None:
        embeddings = load_embeddings()
    return [
        rehydrate(row, anchors.get(row["id"]), embeddings.get(row["id"])) for row in rows
    ]
