"""Đo tỉ lệ SENTINEL GIẢ của tra cứu ngoài (task 9.2) — cổng bật mặc định.

Sentinel giả = model xin tra cứu ngoài cho một câu vốn **trả lời được hoàn toàn từ corpus**.
Nó tốn tiền search (~6× cả câu trả lời), tốn độ trễ tải trang, và mở nội dung web lạ vào
prompt — nên bias thiết kế là DÈ DẶT, và con số này là cách duy nhất biết bias đó có thật hay
chỉ là câu chữ trong prompt.

Khuôn theo phép đo sentinel giả của `chat-scope-routing` (đo được 0/6).

    docker compose exec backend python -m tests.eval.web_sentinel_rate

Chỉ chạy BƯỚC 1 (lượt trả lời có mang luật xin tra cứu) rồi dò sentinel trên văn bản thô —
**không** chạy tra cứu thật, nên chi phí là N lượt chat thường, không có lượt grounding nào.
"""

import argparse
import asyncio
import json
import pathlib

from app.ai.prompts import extract_web_lookup_query
from app.config import settings
from app.database import async_session_maker
from app.services.chat_service import ChatService

HERE = pathlib.Path(__file__).parent


def load_answerable(limit: int) -> list[dict]:
    """Kịch bản toàn cục vốn TRẢ LỜI ĐƯỢC từ corpus — tập âm của phép đo.

    Loại `absent`/`role_empty` (đúng là phải từ chối) và `partial_ground` (đúng là NÊN xin tra
    cứu). Còn lại là những câu mà bất kỳ lượt xin tra cứu nào cũng là dương tính giả.
    """
    rows = [
        json.loads(line)
        for line in (HERE / "chat_scenarios.jsonl").read_text().splitlines()
        if line.strip()
    ]
    keep = [
        r
        for r in rows
        if r["mode"] == "global"
        and not r.get("expects_refusal")
        and r["group"] not in ("absent", "role_empty", "partial_ground")
    ]
    return keep[:limit]


async def main(limit: int) -> None:
    # Bật cờ để prompt MANG luật xin tra cứu — đó chính là thứ đang được đo.
    settings.chat_web_fallback_enabled = True

    scenarios = load_answerable(limit)
    false_positives: list[tuple[str, str]] = []

    print(f"Đo trên {len(scenarios)} câu hỏi TRẢ LỜI ĐƯỢC từ corpus\n")
    for i, sc in enumerate(scenarios, 1):
        async with async_session_maker() as session:
            service = ChatService(session)
            # Bọc `_call_model` để bắt văn bản THÔ: `_web_lookup_turn` sẽ nuốt sentinel và
            # chạy tra cứu thật (tốn tiền) nếu ta để pipeline chạy tiếp.
            raw_seen: list[str] = []
            original = service._call_model

            async def spy(prompt, hold_sentinel=False, status=None, _o=original, _r=raw_seen):
                text = await _o(prompt, hold_sentinel=hold_sentinel, status=status)
                _r.append(text)
                # Cắt sentinel đi trước khi trả về ⇒ pipeline không bao giờ chạy bước tra cứu.
                return text.split("[[TRA_CỨU_NGOÀI:")[0].strip()

            service._call_model = spy
            await service.answer(sc["question"], [], None)

        asked = next((extract_web_lookup_query(t) for t in raw_seen if extract_web_lookup_query(t)), None)
        mark = "❌ SENTINEL GIẢ" if asked else "ok"
        print(f"  [{i:>2}/{len(scenarios)}] {mark:<15} {sc['id']}")
        if asked:
            print(f"           câu hỏi : {sc['question']}")
            print(f"           xin tra : {asked}")
            false_positives.append((sc["id"], asked))

    n = len(scenarios)
    bad = len(false_positives)
    print(f"\n{'='*70}")
    print(f"SENTINEL GIẢ: {bad}/{n} = {bad / n * 100:.1f}%")
    print("Ngưỡng khuyến nghị để bật mặc định: ≤ 5%. Cao hơn ⇒ siết luật ở `_WEB_LOOKUP_RULE`,")
    print("ĐỪNG bù bằng cách hạ trần quota — quota chặn chi phí, không chặn việc gạt nhầm.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=20)
    asyncio.run(main(ap.parse_args().limit))
