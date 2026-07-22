"""Sinh fixture benchmark gate từ DB + nhãn tay của `w4-gate-accuracy`.

CHẠY MỘT LẦN (22/07/2026) để đóng băng 54 mẫu vào `gate_benchmark.jsonl`. Giữ lại file
này làm bằng chứng xuất xứ — change `gate-benchmark-durability` sinh ra chính vì lần
trước công cụ đo bị xoá và không ai dựng lại được.

Cần DB còn `normalized_content` của 54 doc. Sau `retention_months` (6 tháng) thì
`purge_expired` xoá nội dung và script này không chạy lại được nữa — đó là lý do fixture
phải tự chứa thay vì trỏ doc_id vào DB.

Usage (từ /app trong container backend):
    python -m tests.eval.build_fixture --labels <csv> --out tests/eval/gate_benchmark.jsonl
"""

import argparse
import asyncio
import csv
import json
from pathlib import Path

from sqlalchemy import select

from app.ai.prompts import GATE_CONTENT_LIMIT
from app.database import async_session_maker
from app.models.raw_document import RawDocument


def _norm_label(raw: str) -> str:
    """Nhãn tay trong CSV có ca `'NOISE '` thừa khoảng trắng — chuẩn hoá ngay từ nguồn."""
    return (raw or "").strip().upper()


def _norm_bool(raw: str) -> bool:
    return (raw or "").strip().upper() == "TRUE"


async def build(labels_path: Path, out_path: Path) -> None:
    rows = list(csv.DictReader(labels_path.open(encoding="utf-8")))
    by_id = {r["doc_id"]: r for r in rows}

    async with async_session_maker() as session:
        result = await session.execute(
            select(RawDocument).where(RawDocument.id.in_(list(by_id)))
        )
        docs = {str(d.id): d for d in result.scalars().all()}

    missing = sorted(set(by_id) - set(docs))
    if missing:
        raise SystemExit(
            f"{len(missing)} doc không còn trong DB — fixture sẽ không đầy đủ:\n"
            + "\n".join(missing)
        )

    written = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for doc_id, row in by_id.items():
            doc = docs[doc_id]
            content = (doc.normalized_content or "")[:GATE_CONTENT_LIMIT]
            if not content.strip():
                raise SystemExit(f"{doc_id}: normalized_content rỗng — đã bị purge?")

            label = _norm_label(row.get("human_label", ""))
            if label not in ("SIGNAL", "NOISE"):
                raise SystemExit(f"{doc_id}: human_label không hợp lệ: {label!r}")

            fh.write(
                json.dumps(
                    {
                        "doc_id": doc_id,
                        "source": row.get("source", ""),
                        "source_type": row.get("source_type", ""),
                        "title": doc.title or row.get("title", ""),
                        "source_url": row.get("source_url", ""),
                        # Cắt đúng bằng cửa sổ gate thật — KHÔNG hardcode lại con số.
                        "content": content,
                        "content_truncated_at": GATE_CONTENT_LIMIT,
                        "human_label": label,
                        "human_reason": (row.get("human_reason") or "").strip(),
                        # Verdict gate MỚI đo ngày 21/07/2026 — baseline chống hồi quy.
                        "verdict_2026_07_21": _norm_bool(row.get("gate_pass_new", "")),
                        "actionability_score": row.get("gate_score", ""),
                        "content_type": row.get("content_type", ""),
                        "gate_reason": (row.get("gate_reason") or "").strip(),
                        # Trạng thái gate CŨ (IoT-only) — dùng dựng matrix "trước".
                        "old_status": row.get("old_status", ""),
                        "gate_skipped": _norm_bool(row.get("gate_skipped", "")),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            written += 1

    print(f"Đã ghi {written} mẫu vào {out_path} (cắt {GATE_CONTENT_LIMIT} ký tự)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", required=True, type=Path, help="gate_eval.csv có human_label")
    parser.add_argument("--out", required=True, type=Path, help="đường dẫn JSONL đầu ra")
    args = parser.parse_args()
    asyncio.run(build(args.labels, args.out))


if __name__ == "__main__":
    main()
