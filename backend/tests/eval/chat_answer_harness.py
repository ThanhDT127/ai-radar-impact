"""Bộ đo chất lượng câu trả lời chat — Faithfulness · Answer Relevance · Citation Precision.

Vì sao tồn tại: `chat_rank_benchmark` (RS) đo cạnh Context Relevance của RAG Triad — hàm
xếp hạng, thuần, miễn phí. Hai cạnh còn lại đo **câu trả lời model đẻ ra**, thứ chỉ tồn
tại sau khi chạy pipeline thật. Không có bộ đo này thì mọi lần sửa `CHAT_SYSTEM_PROMPT`,
prompt mode B / sentinel, hay đổi model/SDK đều **không có lưới** bắt hồi quy chất lượng
trả lời — và hồi quy đó vô hình trong production vì câu trả lời sai vẫn đọc rất trôi chảy.

CHẠY
    # chấm lại trên snapshot đã lưu — 0 lượt gọi model, tức thì, dùng để đọc lại/gate
    docker compose exec backend python -m tests.eval.chat_answer_harness

    # đo thật: sinh câu trả lời qua pipeline chat + chấm bằng LLM-judge, ghi đè snapshot
    docker compose exec backend python -m tests.eval.chat_answer_harness --live

    # chỉ chấm lại bằng judge trên câu trả lời đã lưu (không sinh mới)
    docker compose exec backend python -m tests.eval.chat_answer_harness --rejudge

    # lọc theo mode/nhóm khi soi một loại câu
    docker compose exec backend python -m tests.eval.chat_answer_harness --mode expanded

KHI NÀO **BẮT BUỘC** CHẠY LẠI `--live` (không phải "nên", là bắt buộc trước khi merge)
    - sửa `CHAT_SYSTEM_PROMPT`, `build_chat_insight_prompt`, `build_chat_global_prompt`,
      `build_chat_expanded_prompt`, `_SCOPE_RULE` hoặc `OUT_OF_SCOPE_SENTINEL`;
    - đổi `gemini_model_id`, `CHAT_MAX_OUTPUT_TOKENS`, temperature, hay nâng `google-genai`;
    - sửa `enforce_grounding` / `resolve_citations` / `build_index_block`;
    - sửa `_rank`, `_relevance`, `chat_index_top_k` (đổi context ⇒ đổi câu trả lời).
    Sinh lại fixture corpus KHÔNG được coi là "chạy lại" — corpus đổi thì baseline cũ hết
    so sánh được, phải chốt lại baseline kèm lý do.

CHI PHÍ MỘT LẦN `--live` (đếm thật 27/07/2026, 56 kịch bản)
    69 lượt sinh (380.537 token vào) + 102 lượt judge (74.158 token vào) = **171 lượt gọi**
    `gemini-2.5-flash`, 454.695 token vào + 6.353 token ra nhìn thấy được.
    Tiền: input $0,136 + output nhìn thấy $0,016 ⇒ **$0,15 cộng phần thinking**. Thinking
    KHÔNG đo lại được sau khi chạy nhưng **bị tính tiền như output** ($2,50/1M) và trên chat
    đo được 121–3.791 token/câu, nên thực tế rơi vào khoảng **$0,3–0,5 một lần chạy**.
    Thời gian: ~6,5 phút riêng phần sinh (median: insight 4,6s · global 5,7s · expanded 8,1s),
    tổng cả judge ~15 phút vì chạy tuần tự.
    ⚠️ Gọi thẳng `ChatService`/`genai`, KHÔNG qua route, nên KHÔNG bị `MAX_DAILY_CHAT_CALLS`
    tính hay chặn. Tiền vẫn mất thật — đừng chạy trong vòng lặp. Đo lại một nhóm hoặc một
    ca lẻ bằng `--mode` / `--only` rẻ hơn nhiều so với cả bộ, và snapshot được **gộp**
    chứ không bị ghi đè.

ĐỌC KẾT QUẢ
    Faithfulness      LLM-judge tách câu trả lời thành khẳng định rồi chấm từng khẳng định
                      có được **tin đã trích dẫn** bảo chứng không. S=1 · P=0,5 · N=0.
                      Ngưỡng cứng ≥ 0,95 (báo cáo To-Be).
    Citation Precision **cấu trúc, 0 lượt gọi model**: mọi marker `[n]` model in ra phải trỏ
                      một tin có thật trong index đã phục vụ. Đo trên câu trả lời **THÔ**,
                      trước `resolve_citations` — vì hàm đó âm thầm xoá marker lạc, nên đo
                      sau thì điểm luôn bằng 1,00 và bộ đo mất sạch tác dụng. Ngưỡng = 1,00.
    Answer Relevance  LLM-judge: câu trả lời có giải quyết đúng câu hỏi không. Baseline +
                      dung sai, KHÔNG ngưỡng tuyệt đối (báo cáo chỉ chốt số cho hai cạnh trên).
    must_have         **phụ trợ, không gate** — nhãn tay "tin nào bỏ sót là hỏng rõ ràng".
                      Cạnh recall/Context-Relevance là việc của RS, ở đây chỉ để đọc.

GIỚI HẠN DIỄN GIẢI
    - Judge cũng là model, cũng có sai số. Vì thế: verdict đóng khung ngắn, nhiệt độ 0,
      baseline có dung sai, và **báo cáo per-kịch-bản** — một loại câu vỡ không được chìm
      trong trung bình.
    - Snapshot là câu trả lời ĐÔNG LẠNH. Chạy offline chỉ chấm lại chỗ cũ; nó KHÔNG bắt
      được hồi quy prompt/model. Chỉ `--live` mới đo pipeline hiện tại.
    - Corpus là ảnh chụp 27/07/2026 (179 tin). Đo *hồi quy so với chính nó*, không phải
      chất lượng tuyệt đối trên corpus khác quy mô.
    - Nhóm `absent`/`role_empty` cố ý có Answer Relevance **thấp**: câu trả lời đúng ở đó là
      từ chối, mà từ chối thì theo định nghĩa không "giải quyết" câu hỏi. Nên các kịch bản
      `expects_refusal` bị **loại khỏi trung bình AnsRel** và đo bằng cột `từ chối đúng`.
      Đừng "chữa" điểm nhóm đó — chữa nghĩa là dạy bot bịa.
"""

import argparse
import asyncio
import json
import re
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from app.schemas.chat import ChatTurn, TurnCitation
from tests.eval.chat_fixture import (
    SCENARIO_MODES,
    FIXTURE_DIR,
    load_anchors,
    load_chunk_ranks,
    load_corpus,
    load_scenarios,
    rehydrate,
    rehydrate_corpus,
)

SNAPSHOT_PATH = FIXTURE_DIR / "chat_answer_snapshot.json"
BASELINE_PATH = FIXTURE_DIR / "chat_answer_baseline.json"

# Baseline đóng băng — xem BASELINE_PATH cho số per-kịch-bản.
#
# LUẬT BASELINE: chốt lại là hành động CÓ CHỦ ĐÍCH, kèm lý do ghi vào change/commit. Chốt
# lại để test chuyển xanh là tự tháo lưới: lần hồi quy sau sẽ nằm dưới mức mới mà vẫn "pass".
BASELINE_META = {
    "measured_at": "2026-07-29",
    "commit": "(chat-history-pinning, chưa commit)",
    "model": "gemini-2.5-flash",
    "corpus": "chat_corpus.jsonl @ 27/07/2026 — 179 insight published+is_primary",
    "note": (
        "Baseline ĐẦU TIÊN của bộ đo, chốt trên pipeline CHƯA sửa gì. "
        "Faithfulness 0,991 · Answer Relevance 0,922 · Citation Precision 1,000; "
        "từ chối đúng 5/5, lệch mode 0/56, judge lỗi 0. "
        "Một nhãn đã sửa TRƯỚC khi chốt: kịch bản blockchain cũ bị bỏ vì bài AsyncAPI thật "
        "sự có nhắc Ethereum/IPFS — model trả lời đúng, nhãn mới là cái sai."
    ),
    "revisions": [
        {
            "date": "2026-07-31",
            "reason": (
                "`chat-followup-rewrite` thêm 14 kịch bản nhóm `followup_new_topic` — "
                "**lần đầu bộ đo này chạy với `history` thật**. Trước đó `_run_one` truyền "
                "`history=[]` cho MỌI kịch bản, nên khoảng trống '0/98 kịch bản mang history' "
                "ghi ở revision 29/07 vừa là hạn chế của bộ kịch bản VỪA là hạn chế của chính "
                "runner. Nay `_history_for()` dựng lượt hỏi–đáp trước từ `turn1_question` + "
                "`turn1_cited`, kèm `citations` đủ `n`/`title`/`insight_id` để đường ghim của "
                "`chat-history-pinning` thật sự chạy. "
                "\n\n"
                "Nhóm mới: Faith **0,99** · AnsRel **0,89** · CitPrec **1,00** · must_have "
                "14/15. Hai ngưỡng cứng giữ nguyên. "
                "\n\n"
                "⚠️ AnsRel 0,89 của nhóm này THẤP hơn tổng thể và đó là **đúng như thiết kế**: "
                "nhóm đo câu nối tiếp cần tin CHƯA từng bàn, tức là chế độ hỏng mà "
                "`chat-followup-rewrite` nhắm tới và **đã dừng vì kết quả âm** (xem "
                "`measurement.md` §11). Hai ca kéo điểm xuống — `fub-supply-prevent` (AnsRel "
                "0,00) và `fub-cypress-agent` (0,50) — là MỐC ĐO, không phải hồi quy. Đừng "
                "'chữa' bằng cách sửa câu hỏi cho gần chữ trong tin."
            ),
        },
        {
            "date": "2026-07-29",
            "reason": (
                "`chat-history-pinning` — ghim **3 tin được trích gần nhất** trong history "
                "vào CUỐI index, nằm TRONG `chat_index_top_k` (đẩy đuôi bảng xếp hạng ra). "
                "TỔNG: Faith **0,99 → 0,98** (≥0,95 ✅) · AnsRel **0,94 → 0,96** · CitPrec "
                "**1,00** (=1,00 ✅) · từ chối đúng 5/5 · lệch mode 0/98 · `must_have` "
                "112 → 115/123. Cả hai ngưỡng cứng giữ nguyên. "
                "\n\n"
                "⚠️ LƯU Ý QUAN TRỌNG VỀ PHẠM VI CỦA CHÍNH BỘ ĐO NÀY: "
                "`chat_scenarios.jsonl` có **0/98 kịch bản mang `history`**, nên lượt "
                "`--live` **không bao giờ đi qua đường ghim**. Con số ở trên chứng minh "
                "*không hồi quy trên các đường cũ* (cần thiết — change sửa `build_context` "
                "và `_load_refs`), nó **KHÔNG** chứng minh *ghim vô hại*. "
                "Rủi ro thật (3 dòng tin cũ kéo model lạc đề khi hỏi chủ đề mới) phải đo "
                "bằng hội thoại HAI LƯỢT qua endpoint thật: đo 29/07 được **0/4** lạc đề và "
                "**2/2** câu quay lại tin đã bàn trả lời được (trước change: không với tới). "
                "Bộ đo đó hiện là script rời, CHƯA thường trực — xem "
                "`openspec/changes/chat-history-pinning/design.md` Open Question #4. "
                "\n\n"
                "Chênh lệch Faith 0,99 → 0,98 nằm trong nhiễu của LLM-judge: đo 29/07 trên "
                "pipeline CHƯA sửa gì cũng cho 0,99 với hai kịch bản lệch tới ±0,25 ở mức "
                "từng ca. Chỉ số TỔNG mới có nghĩa; đừng truy một kịch bản lẻ tụt điểm."
            ),
        },
        {
            "date": "2026-07-28",
            "reason": (
                "`chat-chunk-retrieval` — tín hiệu xếp hạng THỨ BA ở mức ĐOẠN thân bài, "
                "cộng một suất ô sâu dành cho tin có đoạn khớp nhất toàn corpus. "
                "Bộ kịch bản 83 → 98 (thêm 15 câu nhóm `detail_discovery`). "
                "TỔNG: Faith **0,99** (≥0,95 ✅) · AnsRel **0,92 → 0,95** · CitPrec **1,00** "
                "(=1,00 ✅) · từ chối đúng 5/5 · lệch mode 0/98. "
                "Nhóm `detail_discovery`: AnsRel 0,57 → 0,73 → **0,93**, và **15/15 câu trả "
                "lời được**. "
                "\n\n"
                "BA LẦN 'BỘ ĐO NÓI DỐI' đã phải sửa — cả ba đều im lặng, ghi lại để không "
                "tái sinh: "
                "(a) `_FixtureSession` chỉ phục vụ `select(Insight)` nên truy vấn đoạn ném "
                "lỗi, `_chunk_ranks` **nuốt lỗi rồi rơi về hai tín hiệu** — đúng thiết kế "
                "suy giảm êm, nhưng nghĩa là lượt `--live` đầu tiên chấm một pipeline KHÁC "
                "production mà không báo gì. Nay tiêm thứ hạng đoạn đông lạnh vào "
                "`_make_service`. "
                "(b) `_wanted_anchor_ids` chỉ lấy thân bài cho `anchor_insight_id`, trong "
                "khi từ `chat-context-depth` thì ô sâu rót `normalized_content` cho tin xếp "
                "hạng cao của BẤT KỲ câu toàn cục nào ⇒ ba kịch bản xếp **hạng 1** bị chấm "
                "'từ chối' chỉ vì fixture không có gì để rót. "
                "(c) Hai lần chốt baseline TRƯỚC ĐÓ ghi đè file mà **không** kèm lý do vào "
                "`BASELINE_META` (edit script trượt, không ai kiểm) — chính là cái 'chốt lại "
                "để test chuyển xanh' mà luật baseline cấm. Mục này là bản ghi bù. "
                "\n\n"
                "⚠️ MỘT NHÃN SAI ĐÃ SỬA TRƯỚC KHI CHỐT: `det-gpai-annex` hỏi 'nghĩa vụ nhà "
                "cung cấp GPAI nằm ở Annex mấy' — **tiền đề sai**: bài ghi nghĩa vụ GPAI ở "
                "*Chapter V*, còn Annex I/III là hai đường phân loại rủi ro cao. Model từ "
                "chối VÀ nêu đúng Chapter V, tức là trả lời đúng; nhãn mới là cái sai. Đổi "
                "câu hỏi sang 'Hệ thống AI rủi ro cao được liệt kê ở phụ lục nào?' "
                "(AnsRel 0,00 → 1,00). Tiền lệ 'sửa nhãn, đừng sửa ngưỡng' của ca "
                "blockchain — **KHÁC** `rank-eol-khai-tu`, ở đó sửa câu hỏi là xoá phép đo."
            ),
        },
        {
            "date": "2026-07-28",
            "reason": (
                "SỬA PHÉP ĐO (không đổi code sản phẩm): 4 kịch bản `comparison_expanded` "
                "chuyển sang đường THẬT. Người dùng đang xem một bài rồi hỏi so sánh thì "
                "widget đã đưa bài đó vào working set ⇒ payload là "
                "`referenced_insight_ids`, KHÔNG phải `insight_id`+sentinel. Nhóm đổi tên "
                "→ `comparison_in_article`, `mode` expanded → focused. "
                "Kết quả: nhóm đó **AnsRel 0,62 → 1,00**, riêng `cmp-gemma-expanded` "
                "0,00 → 1,00 (ca từng bị từ chối vì vế thứ hai hoàn toàn hồi chỉ — đúng "
                "cái mà working set sinh ra để chữa). "
                "TỔNG: Faith 0,99 → **1,00** · AnsRel 0,93 → **0,96** · CitPrec giữ 1,00. "
                "\n\n"
                "⚠️ Con số 0,62 cũ KHÔNG phải chất lượng kém — nó là lời dẫn 'Bài bạn đang "
                "xem không nhắc tới điều này' của prompt mở rộng, sai ngữ cảnh cho câu SO "
                "SÁNH (bài đang xem chính là một vế). Đường legacy `insight_id`+sentinel "
                "vẫn còn trong code (design D5) và vẫn có 13 kịch bản `expanded` canh nó; "
                "cái bỏ đi chỉ là việc dùng nó để mô tả một luồng người dùng không còn đi."
            ),
        },
        {
            "date": "2026-07-28",
            "reason": (
                "`chat-context-depth`: ô sâu (7 field + bài gốc) cho tới 3 tin, "
                "`referenced_insight_ids`, prompt `_COMPARISON_RULE`, marker history giải "
                "thành tiêu đề. Bộ kịch bản 56 → 83 (thêm 19 câu so sánh + 8 câu đã có). "
                "Faith 0,991 → **0,99** · AnsRel 0,922 → **0,93** · CitPrec giữ **1,00** · "
                "từ chối đúng 5/5 · lệch mode 0/83. PASS cả hai ngưỡng cứng. "
                "3 kịch bản cũ tụt AnsRel (đều là judge chấm P cho câu trả lời ĐÚNG: "
                "`exp-cypress-to-copilot`, `exp-nettacker-to-vnpost`, và `glo-sbom` tụt "
                "Faith 0,10 nhưng TĂNG AnsRel 0,50), 7 kịch bản cũ TĂNG ⇒ net dương. "
                "\n\n"
                "⚠️ HAI ĐIỀU PHẢI ĐỌC TRƯỚC KHI DIỄN GIẢI SỐ NÀY:\n"
                "(1) Lượt đo ĐẦU cho Faith **0,78** và suýt chặn merge — đó là **hồi quy "
                "GIẢ của bộ đo**, không phải của code: `_cited_context` dựng lại dòng index "
                "nén 115 token cho judge trong khi pipeline phục vụ model cả bài gốc ở ô "
                "sâu, nên mọi khẳng định rút từ thân bài bị chấm N. Luật đó viết từ thời "
                "chỉ có MỘT tin sâu (mode B). Nay `ChatContext.deep_blocks` mang block đúng "
                "như đã phục vụ; khoá bằng "
                "`test_cited_context_uses_served_depth_not_reconstructed_index`.\n"
                "(2) `_COMPARISON_RULE` bản đầu làm model **quên marker `[n]`** khi viết "
                "đoạn đối chiếu văn xuôi ⇒ `enforce_grounding` fail-closed xoá sạch câu trả "
                "lời đúng (`cmp-gemma-anaphora`, chập chờn ~25%). Chữa bằng một dòng nói rõ "
                "luật chỉ nới ĐỘ DÀI/BỐ CỤC, marker vẫn bắt buộc: nhóm đó 0,00 → 1,00. "
                "Đây là loại lỗi KHÔNG unit test nào bắt được.\n\n"
                "Nhóm mới: `comparison` 1,00 (8/8) · `comparison_anaphora` 0,88 · "
                "`comparison_partial` 1,00 · `comparison_expanded` 0,62. "
                "⚠️ `comparison_expanded` thấp vì nó đo đường **legacy** `insight_id`+sentinel "
                "— câu trả lời mở đầu 'Bài bạn đang xem không nhắc tới điều này', sai ngữ "
                "cảnh cho câu so sánh. Widget nay LUÔN đưa bài đang xem vào working set nên "
                "không còn gửi payload đó; nhãn giữ nguyên có chủ đích để đường legacy vẫn "
                "có lưới, chờ quyết định retire."
            ),
        },
        {
            "date": "2026-07-27",
            "reason": (
                "`chat-latency-thinking-budget`: nâng `google-genai` 0.8.0 → 1.75.0 và ghìm "
                "`thinking_budget=256` cho đường chat ⇒ đổi lượng suy luận của model ⇒ đo lại "
                "TOÀN BỘ bằng `--live` (luật bắt buộc khi đổi SDK/model). "
                "Faith 0,980→0,990 · AnsRel 0,910→0,910 · CitPrec giữ 1,000 · từ chối đúng 5/5 "
                "· lệch mode 0 · 77 lượt gọi sinh câu trả lời. PASS cả hai ngưỡng cứng nên "
                "KHÔNG phải nâng budget lên 512. "
                "Đổi lấy: độ trễ trung vị 4,7s (1 lượt gọi) / 6,9s (mở rộng) trên 62 câu, "
                "thinking 1.877–2.752 → 216–253 token/câu. Chi tiết: "
                "openspec/changes/archive/2026-07-27-chat-latency-thinking-budget/measurement.md."
            ),
        },
        {
            "date": "2026-07-27",
            "reason": (
                "`chat-hybrid-retrieval`: `_rank` đổi sang RRF(vector, lexical) ⇒ đổi context "
                "⇒ đo lại TOÀN BỘ bằng `--live` (luật bắt buộc khi đụng `_rank`). "
                "Faith 0,980→0,980 · AnsRel 0,930→0,910 · CitPrec giữ 1,000 · từ chối đúng 5/5 "
                "· 77 lượt gọi sinh câu trả lời. Bộ nhãn thêm 2 kịch bản nhóm `semantic` "
                "(rank-eol-khai-tu, rank-vram-semantic) đo đúng chế độ hỏng ⑥ chữa; cả hai "
                "faith/ansrel/citprec đều tốt, `must_have` 4/6 — phần sót nằm ở TẦNG XẾP HẠNG "
                "chứ không phải câu trả lời, và đó là việc của RS harness đo (xem "
                "openspec/changes/chat-hybrid-retrieval/measurement.md §4). "
                "⚠️ XUẤT XỨ: baseline này được SINH LẠI ngày 27/07 lúc tách commit — lượt "
                "`--live` gốc của change đã bị lượt của `chat-latency-thinking-budget` ghi đè "
                "trước khi kịp commit. Bản sinh lại chạy trên `google-genai` 1.75.0 với "
                "`thinking_budget` KHÔNG đặt (hành vi tương đương bản 0.8.0 pin trong chính "
                "commit này). Số vì thế lệch nhẹ so với lần đo gốc (Faith 0,990 · AnsRel "
                "0,930) — chênh lệch đó là nhiễu judge giữa hai lượt, không phải hồi quy."
            ),
        },
        {
            "date": "2026-07-27",
            "reason": (
                "`chat-rank-stability` thêm 6 kịch bản probe (nhóm ascii_short/role_trap/"
                "generic + ca 4b.2 mô hình mở) vào bộ nhãn dùng chung. Chỉ ĐO BÙ 6 câu mới — "
                "56 câu cũ giữ nguyên câu trả lời vì bản sửa `_roles_in_question` chỉ đổi trục "
                "của đúng 2 câu, và cả 2 đều là câu mới. Faith 0,991→0,992 · AnsRel 0,922→0,913 "
                "(6 câu probe khó hơn mức trung bình) · CitPrec giữ 1,000."
            ),
        },
        {
            "date": "2026-07-27",
            "reason": (
                "`chat-citation-integrity` 4.1: `_relevance` đổi sang khớp theo BIÊN TỪ ⇒ đổi "
                "context ⇒ phải đo lại TOÀN BỘ. Faith 0,992→0,980 · AnsRel 0,913→0,930 · "
                "CitPrec giữ 1,000 · từ chối đúng 5/5 · lệch mode 0/62. Bảy kịch bản đổi số, "
                "hai chiều (3 câu AnsRel +0,50, 1 câu −0,50) — nhiễu judge + đổi thứ hạng "
                "context, không có cạnh nào tụt dưới ngưỡng cứng."
            ),
        },
    ],
}

# Ngưỡng gate (design D1, từ báo cáo To-Be mục 3.2 #6).
FAITHFULNESS_FLOOR = 0.95
CITATION_PRECISION_FLOOR = 1.00
# Dung sai của Answer Relevance: judge không tất định, một kịch bản lật S→P đã đổi ~0,01
# điểm tổng. So bằng sẽ làm gate rung vô cớ; đây là ngưỡng "tụt thật sự".
ANSWER_RELEVANCE_TOLERANCE = 0.05

# Marker citation — cùng regex với `chat_grounding._MARKER_RE`. Cố ý CHÉP LẠI chứ không
# import: nếu ai đó nới marker ở sản phẩm, bộ đo phải fail để có người nhìn lại, chứ không
# lặng lẽ đo theo luật mới.
_MARKER_RE = re.compile(r"\[(\d+)\]")

_VERDICT_SCORE = {"S": 1.0, "P": 0.5, "N": 0.0}

FAITHFULNESS_JUDGE_PROMPT = """\
Bạn là giám khảo kiểm chứng, không phải trợ lý. Nhiệm vụ: xét CÂU TRẢ LỜI có bám DỮ LIỆU không.

Cách làm:
1. Tách CÂU TRẢ LỜI thành các khẳng định độc lập (tối đa 10). Bỏ qua câu dẫn nhập, câu
   hỏi lại, lời mời hỏi tiếp — chúng không phải khẳng định về sự việc.
2. Với MỖI khẳng định, in đúng một dòng theo định dạng:
   <số thứ tự>|<S hoặc P hoặc N>|<lý do, tối đa 12 từ>
   S = DỮ LIỆU bảo chứng trọn vẹn khẳng định này
   P = đúng một phần, hoặc suy rộng quá điều DỮ LIỆU nói
   N = DỮ LIỆU không hề nói điều này (kể cả khi ngoài đời nó đúng)

TUYỆT ĐỐI không in gì khác: không mở bài, không kết luận, không markdown, không đánh số lại.
Nếu CÂU TRẢ LỜI không chứa khẳng định nào, in đúng một dòng: 0|S|không có khẳng định
"""

RELEVANCE_JUDGE_PROMPT = """\
Bạn là giám khảo, không phải trợ lý. Nhiệm vụ: xét CÂU TRẢ LỜI có giải quyết đúng CÂU HỎI không.
Chỉ xét mức độ đúng-trọng-tâm, KHÔNG xét đúng/sai sự thật, KHÔNG xét văn phong.

In đúng MỘT dòng: <S hoặc P hoặc N>|<lý do, tối đa 15 từ>
  S = trả lời thẳng vào điều được hỏi
  P = có chạm tới nhưng lệch trọng tâm, thiếu vế chính, hoặc lan man sang chuyện khác
  N = lạc đề, hoặc né không trả lời (nói không biết / không có dữ liệu) dù được hỏi thẳng

TUYỆT ĐỐI không in gì khác.
"""


# ---------------------------------------------------------------------------
# Chạy pipeline chat thật trên fixture (không DB)
# ---------------------------------------------------------------------------


class _FixtureResult:
    """Bắt chước `Result` của SQLAlchemy đủ cho `_answer_insight` và `_load_refs`."""

    def __init__(self, insights: list) -> None:
        self._insights = insights

    def scalar_one_or_none(self):
        return self._insights[0] if self._insights else None

    def scalars(self):
        return self

    def all(self):
        return self._insights


class _FixtureSession:
    """`AsyncSession` giả — chỉ phục vụ `select(Insight).where(Insight.id == ...)`.

    `ChatService` chạm DB ở đúng hai chỗ: repo (đã thay bằng fixture) và một `execute`
    trực tiếp trong `_answer_insight`. Stub này lo chỗ thứ hai bằng cách đọc tham số bind
    của câu lệnh thay vì diễn giải SQL — không phụ thuộc hình dạng whereclause.
    """

    def __init__(self, by_id: dict[str, object]) -> None:
        self._by_id = by_id

    async def execute(self, stmt):
        # `_load_refs` dùng `IN (...)` nên có thể mang NHIỀU id; `_answer_insight` mang một.
        # Đọc tất cả rồi trả theo đúng thứ tự tham số — `_load_refs` tự sắp lại theo thứ tự
        # client gửi, nên thứ tự ở đây không phải hợp đồng, chỉ cần đủ phần tử.
        # `IN (...)` được SQLAlchemy render thành **expanding bindparam**, nên giá trị ở
        # đây là một LIST uuid chứ không phải từng uuid rời như `== ...`. Phải trải phẳng,
        # không thì `_load_refs` trông như "câu lệnh không mang id nào".
        wanted = []
        for value in stmt.compile().params.values():
            for item in value if isinstance(value, (list, tuple)) else [value]:
                if isinstance(item, uuid.UUID):
                    wanted.append(item)
        if not wanted:
            raise AssertionError(
                "Câu lệnh không mang id nào — pipeline đã đổi cách nạp insight, "
                "sửa _FixtureSession cho khớp trước khi tin vào số đo."
            )
        found = [self._by_id[str(i)] for i in wanted if str(i) in self._by_id]
        return _FixtureResult(found)


@dataclass
class _Capture:
    """Những gì server THẬT SỰ phục vụ cho một lượt trả lời — để chấm citation."""

    raw_answer: str = ""
    served: dict[int, str] = field(default_factory=dict)  # n → insight_id
    # Block ĐÚNG NHƯ ĐÃ PHỤC VỤ cho những tin nằm ở ô sâu (n → text). Không suy lại được từ
    # corpus: ô sâu mang cả `normalized_content`, mà fixture chỉ lưu content của anchor.
    deep_blocks: dict[int, str] = field(default_factory=dict)


def _make_service(corpus_insights: list, by_id: dict, chunk_ranks: dict | None = None):
    """Dựng `ChatService` chạy trên fixture, có gián điệp ghi lại context đã phục vụ.

    `chunk_ranks` là thứ hạng đoạn ĐÔNG LẠNH của kịch bản này (`chat_chunk_ranks.jsonl`).
    ⚠️ Bắt buộc phải tiêm: `_FixtureSession` chỉ phục vụ `select(Insight)`, nên truy vấn
    đoạn ném lỗi và `_chunk_ranks` **nuốt lỗi rồi rơi về hai tín hiệu** — đúng như thiết kế
    suy giảm êm. Hệ quả với bộ đo là nó lặng lẽ chấm một pipeline KHÁC production, và số đo
    trông hoàn toàn bình thường. Đã xảy ra thật ở lượt `--live` đầu tiên (28/07): log đầy
    dòng "Truy hồi mức đoạn lỗi — xếp hạng bằng 2 tín hiệu".
    """
    from app.ai.gemini_client import GeminiClient
    from app.services import chat_service as cs

    service = cs.ChatService(session=_FixtureSession(by_id), gemini=GeminiClient())

    async def _chunk_ranks(_query_vector):
        return dict(chunk_ranks or {})

    service.chunk_repo.retrieve_chunk_ranks = _chunk_ranks

    async def _list_for_chat(*_args, **_kwargs):
        return list(corpus_insights)

    async def _sum_calls():
        return 0

    async def _create_log(**_kwargs):
        return None

    service.insight_repo.list_for_chat = _list_for_chat
    service.chat_log_repo.sum_model_calls_today = _sum_calls
    service.chat_log_repo.create = _create_log
    return service


def _install_spy(capture: list[_Capture]):
    """Ghi lại `(câu trả lời thô, bảng ánh xạ đã phục vụ)` ngay trước khi grounding dọn.

    Đây là điểm duy nhất còn thấy được marker model bịa: `resolve_citations` xoá mọi
    marker ngoài bảng, nên đo sau nó thì Citation Precision luôn bằng 1,00.
    """
    from app.services import chat_service as cs

    original = cs.resolve_citations
    original_build = cs.build_context
    # Ô sâu của lượt gần nhất, ghi lại ngay lúc context được dựng. Phải bắt ở đây chứ không
    # suy từ `mapping`: mapping chỉ nói tin nào mang số nào, không nói tin nào được rót SÂU.
    latest_deep: dict = {}

    def spy_build(*args, **kwargs):
        ctx = original_build(*args, **kwargs)
        latest_deep.clear()
        latest_deep.update(ctx.deep_blocks)
        return ctx

    def spy(answer: str, mapping: dict):
        capture.append(
            _Capture(
                raw_answer=answer,
                served={n: str(i.id) for n, i in mapping.items()},
                deep_blocks=dict(latest_deep),
            )
        )
        return original(answer, mapping)

    cs.resolve_citations = spy
    cs.build_context = spy_build

    def restore():
        cs.resolve_citations = original
        cs.build_context = original_build

    return restore


def _history_for(scenario: dict, by_id: dict) -> list[ChatTurn]:
    """Lịch sử hội thoại của kịch bản. `[]` nếu kịch bản không khai báo.

    Kịch bản khai `turn1_question` + `turn1_cited` (nhóm `followup_new_topic`,
    `chat-followup-rewrite`) mô tả một lượt hỏi–đáp ĐÃ xảy ra. Truyền `history=[]` cho chúng
    là đo một câu hỏi khác hẳn câu người dùng thật gõ: *"Thế lúc triển khai thì cần chuẩn bị
    gì?"* không có chủ thể nào nếu tách khỏi lượt trước.

    Lượt trợ lý mang `citations` đầy đủ (`n` + `title` + `insight_id`) vì đó là thứ kích hoạt
    cả `_history_block` (giải marker thành tiêu đề) lẫn `_history_pin_ids` (ghim tin đã trích).
    Thiếu `insight_id` thì đường ghim của `chat-history-pinning` im lặng không chạy, và bộ đo
    lại tuyên bố đã phủ hội thoại đa lượt trong khi không phủ.

    Nội dung lượt trợ lý là marker `[n]` thuần chứ không phải câu trả lời thật: bộ đo cần
    **cấu trúc** tham chiếu (marker + nguồn), không cần văn bản, và bịa ra một câu trả lời
    trông-như-thật sẽ đưa chữ của chính người viết fixture vào ngữ cảnh model đọc.
    """
    turn1 = (scenario.get("turn1_question") or "").strip()
    cited = scenario.get("turn1_cited") or []
    if not turn1:
        return []
    citations = [
        TurnCitation(n=n, title=by_id[i].title, insight_id=uuid.UUID(i))
        for n, i in enumerate(cited, start=1)
        if i in by_id
    ]
    return [
        ChatTurn(role="user", content=turn1),
        ChatTurn(
            role="assistant",
            content=" ".join(f"[{c.n}]" for c in citations) or "(không có nguồn)",
            citations=citations,
        ),
    ]


async def _run_one(scenario: dict, corpus_insights: list, by_id: dict) -> dict:
    capture: list[_Capture] = []
    restore = _install_spy(capture)
    try:
        service = _make_service(
            corpus_insights, by_id, load_chunk_ranks().get(scenario["id"])
        )
        started = time.monotonic()
        anchor = scenario.get("anchor_insight_id")
        refs = [uuid.UUID(i) for i in scenario.get("referenced_insight_ids", [])]
        result = await service.answer(
            question=scenario["question"],
            history=_history_for(scenario, by_id),
            insight_id=uuid.UUID(anchor) if anchor else None,
            referenced_insight_ids=refs,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
    finally:
        restore()

    last = capture[-1] if capture else _Capture()
    return {
        "scenario_id": scenario["id"],
        "mode_expected": scenario["mode"],
        "group": scenario["group"],
        "question": scenario["question"],
        "anchor_insight_id": anchor,
        "referenced_insight_ids": [str(i) for i in refs],
        "expects_refusal": scenario.get("expects_refusal", False),
        "must_have": scenario.get("must_have", []),
        "mode_actual": result["mode"],
        "answer": result["answer"],
        "citations": [
            {"insight_id": str(c["insight_id"]), "title": c["title"]}
            for c in result["citations"]
        ],
        "raw_answer": last.raw_answer,
        "served": last.served,
        "deep_blocks": {str(n): b for n, b in last.deep_blocks.items()},
        "model_calls": service._calls_used,
        "steps": service._steps_used,
        "latency_ms": latency_ms,
    }


async def generate(scenarios: list[dict]) -> list[dict]:
    """Sinh câu trả lời cho từng kịch bản bằng **pipeline chat thật**. Tốn tiền."""
    corpus_rows = load_corpus()
    anchors = load_anchors()
    corpus_insights = rehydrate_corpus(corpus_rows, anchors)
    by_id = {str(i.id): i for i in corpus_insights}

    records = []
    for n, scenario in enumerate(scenarios, start=1):
        record = await _run_one(scenario, corpus_insights, by_id)
        records.append(record)
        flag = "" if record["mode_actual"] == record["mode_expected"] else "  ⚠️ lệch mode"
        print(
            f"  [{n:>2}/{len(scenarios)}] {scenario['id']:<28} "
            f"{record['mode_actual']:<9} {record['model_calls']} lượt "
            f"{record['latency_ms'] / 1000:>5.1f}s{flag}"
        )
    return records


# ---------------------------------------------------------------------------
# LLM-judge
# ---------------------------------------------------------------------------


def _judge_client():
    from google import genai

    from app.config import settings

    return genai.Client(
        vertexai=True,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location,
    )


def _judge(client, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    """Một lượt hỏi judge. Nhiệt độ 0 và trần output thấp — verdict phải ngắn, có biên.

    KHÔNG `response_schema` (bài học `gemini-structured-output`); định dạng dòng `a|b|c`
    parse được mà không có JSON để vỡ.
    """
    from google.genai import types

    from app.config import settings

    response = client.models.generate_content(
        model=settings.gemini_model_id,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.0,
            max_output_tokens=max_tokens,
        ),
    )
    return (response.text or "").strip()


def _cited_context(record: dict, corpus_by_id: dict, anchors: dict) -> str:
    """Dựng lại ĐÚNG context của những tin đã được trích dẫn — không hơn.

    Faithfulness hỏi "khẳng định này có được **tin đã cite** bảo chứng không", nên judge
    chỉ được nhìn thấy đúng chỗ đó. Cho judge xem cả corpus sẽ biến mọi câu bịa-nhưng-có-
    thật-ở-tin-khác thành "supported".
    """
    from app.services.chat_grounding import build_index_block, build_insight_block

    # Số thứ tự phải GIỮ NGUYÊN như lúc phục vụ: câu trả lời mang marker [3] mà context
    # của judge đánh số lại từ [1] thì judge phải đoán, và nó đoán sai.
    n_by_id = {v: int(n) for n, v in (record.get("served") or {}).items()}
    anchor_id = record.get("anchor_insight_id")
    deep_blocks = record.get("deep_blocks") or {}

    blocks = []
    for citation in record["citations"]:
        insight_id = citation["insight_id"]
        n = n_by_id.get(insight_id, 1)

        # ⚠️ Ô SÂU: dùng LẠI ĐÚNG block đã phục vụ. Dựng lại từ corpus không tương đương —
        # ô sâu mang cả `normalized_content`, mà fixture chỉ lưu content của anchor. Đo
        # 28/07: cho judge xem dòng index nén trong khi model đọc bài gốc làm Faithfulness
        # tụt 0,99 → 0,78 và MỌI khẳng định rút từ thân bài bị chấm N. Đó là hồi quy GIẢ —
        # bộ đo phải nhìn đúng thứ pipeline đã đưa cho model, không hơn không kém.
        if str(n) in deep_blocks:
            blocks.append(deep_blocks[str(n)])
            continue

        row = corpus_by_id.get(insight_id)
        if row is None:
            continue
        # Mode B (`_answer_insight`) không đi qua `build_context` nên không có deep_blocks.
        if insight_id == anchor_id:
            blocks.append(build_insight_block(rehydrate(row, anchors.get(insight_id)), anchors.get(insight_id)))
        else:
            blocks.append(build_index_block([rehydrate(row)], start=n)[0])
    return "\n\n".join(blocks)


def _parse_faithfulness(raw: str) -> list[dict]:
    claims = []
    for line in raw.splitlines():
        parts = [p.strip() for p in line.strip().strip("`").split("|")]
        if len(parts) < 2 or parts[1].upper()[:1] not in _VERDICT_SCORE:
            continue
        claims.append(
            {
                "claim": parts[0],
                "verdict": parts[1].upper()[:1],
                "reason": parts[2] if len(parts) > 2 else "",
            }
        )
    return claims


def _is_refusal(record: dict) -> bool:
    """Câu trả lời thuộc dạng 'không có dữ liệu' — không có khẳng định để kiểm chứng."""
    from app.services.chat_grounding import INSUFFICIENT_GROUNDS_MESSAGE, is_not_found_answer

    answer = record["answer"].strip()
    return answer == INSUFFICIENT_GROUNDS_MESSAGE or (
        not record["citations"] and is_not_found_answer(answer)
    )


def judge_all(records: list[dict]) -> None:
    """Chấm Faithfulness + Answer Relevance tại chỗ (ghi thẳng vào từng record)."""
    corpus_by_id = {row["id"]: row for row in load_corpus()}
    anchors = load_anchors()
    client = _judge_client()

    for n, record in enumerate(records, start=1):
        refusal = _is_refusal(record)
        record["refusal"] = refusal

        # Từ chối = không khẳng định nào để kiểm chứng ⇒ Faithfulness trọn vẹn theo định
        # nghĩa, không tốn lượt judge. Cái sai của một lần từ chối nhầm hiện ở Answer
        # Relevance, không phải ở đây.
        if refusal or not record["citations"]:
            record["faithfulness"] = {"score": 1.0, "claims": [], "skipped": "từ chối/không trích dẫn"}
        else:
            context = _cited_context(record, corpus_by_id, anchors)
            raw = _judge(
                client,
                FAITHFULNESS_JUDGE_PROMPT,
                f"DỮ LIỆU:\n{context}\n\nCÂU TRẢ LỜI:\n{record['answer']}",
                max_tokens=1024,
            )
            claims = _parse_faithfulness(raw)
            record["faithfulness"] = {
                "score": (
                    sum(_VERDICT_SCORE[c["verdict"]] for c in claims) / len(claims)
                    if claims
                    else None
                ),
                "claims": claims,
                "raw": raw if not claims else "",
            }

        if record.get("expects_refusal"):
            # Loại khỏi trung bình AnsRel (xem docstring): đo bằng cột "từ chối đúng".
            record["answer_relevance"] = {"score": None, "verdict": "n/a", "reason": "chờ từ chối"}
        else:
            raw = _judge(
                client,
                RELEVANCE_JUDGE_PROMPT,
                f"CÂU HỎI:\n{record['question']}\n\nCÂU TRẢ LỜI:\n{record['answer']}",
                max_tokens=128,
            )
            parts = [p.strip() for p in raw.strip().strip("`").split("|")]
            verdict = parts[0].upper()[:1] if parts else ""
            record["answer_relevance"] = {
                "score": _VERDICT_SCORE.get(verdict),
                "verdict": verdict if verdict in _VERDICT_SCORE else "?",
                "reason": parts[1] if len(parts) > 1 else raw[:80],
            }

        print(
            f"  [{n:>2}/{len(records)}] {record['scenario_id']:<28} "
            f"faith={_fmt(record['faithfulness']['score'])} "
            f"ansrel={_fmt(record['answer_relevance']['score'])}"
        )


# ---------------------------------------------------------------------------
# Chấm điểm (structural + tổng hợp) — 0 lượt gọi model
# ---------------------------------------------------------------------------


def citation_precision(record: dict) -> tuple[float, list[int]]:
    """Tỉ lệ marker model in ra mà trỏ đúng tin trong index đã phục vụ. **Không gọi model.**

    Trả `(điểm, danh sách marker bịa)`. Không có marker nào ⇒ 1,00 (không có gì để bịa).
    """
    served = {int(k) for k in record.get("served", {})}
    markers = [int(m) for m in _MARKER_RE.findall(record.get("raw_answer") or "")]
    if not markers:
        return 1.0, []
    bogus = sorted({m for m in markers if m not in served})
    good = sum(1 for m in markers if m in served)
    return good / len(markers), bogus


def score(records: list[dict]) -> dict:
    """Tính điểm per-kịch-bản + tổng hợp từ snapshot. Tất định, 0 lượt gọi model."""
    rows = []
    for record in records:
        precision, bogus = citation_precision(record)
        faith = (record.get("faithfulness") or {}).get("score")
        ansrel = (record.get("answer_relevance") or {}).get("score")
        must = set(record.get("must_have") or [])
        cited = {c["insight_id"] for c in record["citations"]}
        rows.append(
            {
                "scenario_id": record["scenario_id"],
                "mode_expected": record["mode_expected"],
                "mode_actual": record["mode_actual"],
                "group": record["group"],
                "expects_refusal": record.get("expects_refusal", False),
                "refusal": record.get("refusal", False),
                "faithfulness": faith,
                "answer_relevance": ansrel,
                "citation_precision": precision,
                "bogus_markers": bogus,
                "must_have_hit": len(must & cited),
                "must_have_total": len(must),
                "model_calls": record.get("model_calls", 0),
            }
        )

    def mean(values):
        values = [v for v in values if v is not None]
        return sum(values) / len(values) if values else None

    ansrel_rows = [r for r in rows if not r["expects_refusal"]]
    refusal_rows = [r for r in rows if r["expects_refusal"]]
    return {
        "rows": rows,
        "overall": {
            "faithfulness": mean(r["faithfulness"] for r in rows),
            "answer_relevance": mean(r["answer_relevance"] for r in ansrel_rows),
            "citation_precision": mean(r["citation_precision"] for r in rows),
        },
        "judge_errors": [r["scenario_id"] for r in rows if r["faithfulness"] is None
                         or (not r["expects_refusal"] and r["answer_relevance"] is None)],
        "mode_mismatch": [
            r["scenario_id"] for r in rows if r["mode_actual"] != r["mode_expected"]
        ],
        "refusal_correct": sum(1 for r in refusal_rows if r["refusal"]),
        "refusal_total": len(refusal_rows),
        "must_have_hit": sum(r["must_have_hit"] for r in rows),
        "must_have_total": sum(r["must_have_total"] for r in rows),
        "model_calls": sum(r["model_calls"] for r in rows),
    }


def verdict(scored: dict, baseline: dict | None) -> tuple[bool, list[str]]:
    """PASS/FAIL theo ngưỡng D1. Trả `(pass, danh sách lý do fail)`."""
    reasons = []
    overall = scored["overall"]

    if scored["judge_errors"]:
        reasons.append(
            f"{len(scored['judge_errors'])} kịch bản judge không đọc được verdict "
            f"({', '.join(scored['judge_errors'][:5])}) — không có số thì không tuyên bố đạt được"
        )

    faith = overall["faithfulness"]
    if faith is None or faith < FAITHFULNESS_FLOOR:
        reasons.append(f"Faithfulness {_fmt(faith)} < ngưỡng cứng {FAITHFULNESS_FLOOR:.2f}")

    precision = overall["citation_precision"]
    if precision is None or precision < CITATION_PRECISION_FLOOR:
        offenders = [r["scenario_id"] for r in scored["rows"] if r["citation_precision"] < 1.0]
        reasons.append(
            f"Citation Precision {_fmt(precision)} < 1,00 (tuyệt đối) — "
            f"citation bịa ở: {', '.join(offenders)}"
        )

    if baseline:
        # So trên CÙNG tập kịch bản. Chạy lọc (`--mode`/`--only`) mà đem trung bình của một
        # nhóm nhỏ so với trung bình toàn bộ là so nhầm thứ — đo 27/07 nó cho một FAIL giả
        # ngay lần đầu dùng `--only`. Kịch bản mới chưa có trong baseline cũng bị loại khỏi
        # phép so, và được nêu riêng bên dưới.
        measured = {r["scenario_id"] for r in scored["rows"]}
        comparable = [
            r
            for r in baseline["rows"]
            if r["scenario_id"] in measured and not r["expects_refusal"]
        ]
        base_values = [
            r["answer_relevance"] for r in comparable if r["answer_relevance"] is not None
        ]
        if base_values:
            base_mean = sum(base_values) / len(base_values)
            floor = base_mean - ANSWER_RELEVANCE_TOLERANCE
            ansrel = overall["answer_relevance"]
            if ansrel is None or ansrel < floor:
                reasons.append(
                    f"Answer Relevance {_fmt(ansrel)} tụt dưới baseline {base_mean:.3f} "
                    f"− dung sai {ANSWER_RELEVANCE_TOLERANCE:.2f} = {floor:.3f} "
                    f"(so trên {len(base_values)} kịch bản cùng có trong baseline)"
                )

        new_ids = sorted(measured - {r["scenario_id"] for r in baseline["rows"]})
        if new_ids:
            reasons.append(
                f"CHÚ Ý (không phải fail): {len(new_ids)} kịch bản chưa có trong baseline "
                f"({', '.join(new_ids[:6])}) — chốt lại baseline kèm lý do."
            )
            return not [r for r in reasons if not r.startswith("CHÚ Ý")], reasons

    return not reasons, reasons


# ---------------------------------------------------------------------------
# Báo cáo
# ---------------------------------------------------------------------------


def _fmt(value) -> str:
    return "  —  " if value is None else f"{value:.2f}"


def _delta(now, before) -> str:
    if now is None or before is None:
        return "     "
    diff = now - before
    if abs(diff) < 0.005:
        return "   ="
    return f" {'▲' if diff > 0 else '▼'}{abs(diff):.2f}"


def format_report(scored: dict, baseline: dict | None, live: bool) -> str:
    base_rows = {r["scenario_id"]: r for r in (baseline or {}).get("rows", [])}
    lines = []

    header = (
        f"{'kịch bản':<28}{'mode':<20}{'Faith':>7}{'':<5}"
        f"{'AnsRel':>7}{'':<5}{'CitPrec':>8}  {'must':>5}"
    )
    lines.append(header)
    lines.append("-" * len(header))

    for row in sorted(scored["rows"], key=lambda r: (r["mode_expected"], r["group"], r["scenario_id"])):
        base = base_rows.get(row["scenario_id"], {})
        mode = row["mode_expected"]
        if row["mode_actual"] != mode:
            mode = f"{mode}→{row['mode_actual']} ⚠️"
        must = (
            f"{row['must_have_hit']}/{row['must_have_total']}"
            if row["must_have_total"]
            else "  —"
        )
        flag = ""
        if row["bogus_markers"]:
            flag = f"  ❌ marker bịa {row['bogus_markers']}"
        elif row["expects_refusal"]:
            flag = "  từ chối đúng ✅" if row["refusal"] else "  ❌ đáng lẽ phải từ chối"
        lines.append(
            f"{row['scenario_id']:<28}{mode:<20}"
            f"{_fmt(row['faithfulness']):>7}{_delta(row['faithfulness'], base.get('faithfulness')):<5}"
            f"{_fmt(row['answer_relevance']):>7}{_delta(row['answer_relevance'], base.get('answer_relevance')):<5}"
            f"{_fmt(row['citation_precision']):>8}  {must:>5}{flag}"
        )

    lines.append("")
    lines.append("Theo nhóm câu hỏi:")
    groups: dict[str, list] = {}
    for row in scored["rows"]:
        groups.setdefault(row["group"], []).append(row)
    for group, rows in sorted(groups.items()):
        def mean(key, subset=rows):
            values = [r[key] for r in subset if r[key] is not None]
            return sum(values) / len(values) if values else None

        ansrel_rows = [r for r in rows if not r["expects_refusal"]]
        lines.append(
            f"  {group:<16} n={len(rows):<3} faith={_fmt(mean('faithfulness'))} "
            f"ansrel={_fmt(mean('answer_relevance', ansrel_rows))} "
            f"citprec={_fmt(mean('citation_precision'))}"
        )

    overall = scored["overall"]
    lines.append("")
    lines.append(
        f"TỔNG  Faithfulness {_fmt(overall['faithfulness'])} (ngưỡng ≥ {FAITHFULNESS_FLOOR:.2f})"
        f"   Answer Relevance {_fmt(overall['answer_relevance'])}"
        f"   Citation Precision {_fmt(overall['citation_precision'])} (ngưỡng = 1,00)"
    )
    lines.append(
        f"      từ chối đúng {scored['refusal_correct']}/{scored['refusal_total']}"
        f"   must_have (phụ trợ, không gate) {scored['must_have_hit']}/{scored['must_have_total']}"
        f"   lượt gọi sinh câu trả lời: {scored['model_calls']}"
    )
    if scored["mode_mismatch"]:
        lines.append(
            f"      ⚠️ lệch mode ({len(scored['mode_mismatch'])}): "
            + ", ".join(scored["mode_mismatch"])
        )
    if not live:
        lines.append(
            "\n(offline — chấm lại trên SNAPSHOT đã lưu, KHÔNG phải đo pipeline hiện tại. "
            "Thêm --live để sinh lại câu trả lời bằng model.)"
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def load_snapshot(path: Path = SNAPSHOT_PATH) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(
            f"Không thấy snapshot {path.name}. Chạy `--live` một lần để sinh."
        )
    return json.loads(path.read_text(encoding="utf-8"))["records"]


def save_snapshot(records: list[dict], path: Path = SNAPSHOT_PATH) -> None:
    """Ghi snapshot, GỘP với bản cũ theo `scenario_id`.

    Gộp chứ không ghi đè để `--live --mode expanded` (đo lại một nhóm sau khi sửa prompt
    sentinel) không xoá mất câu trả lời của 43 kịch bản còn lại — mất chúng nghĩa là phải
    trả tiền sinh lại toàn bộ chỉ để đọc được báo cáo tổng.

    Đồng thời **loại** bản ghi của kịch bản đã bị xoá/đổi tên khỏi fixture: giữ lại thì
    chúng lặng lẽ góp điểm vào trung bình của một bộ kịch bản không còn tồn tại.
    """
    from app.config import settings

    known = {s["id"] for s in load_scenarios()}
    merged: dict[str, dict] = {}
    if path.exists():
        for old in json.loads(path.read_text(encoding="utf-8"))["records"]:
            if old["scenario_id"] in known:
                merged[old["scenario_id"]] = old
    for record in records:
        merged[record["scenario_id"]] = record
    records = list(merged.values())

    path.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "model": settings.gemini_model_id,
                "chat_index_top_k": settings.chat_index_top_k,
                "chat_window_days": settings.chat_window_days,
                "records": records,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )


def load_baseline(path: Path = BASELINE_PATH) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Bộ đo chất lượng câu trả lời chat")
    parser.add_argument("--live", action="store_true",
                        help="sinh lại câu trả lời bằng pipeline thật rồi chấm (tốn tiền)")
    parser.add_argument("--rejudge", action="store_true",
                        help="chấm lại bằng judge trên câu trả lời đã lưu (không sinh mới)")
    parser.add_argument("--mode", choices=SCENARIO_MODES,
                        help="chỉ chạy/đọc kịch bản của một mode")
    parser.add_argument("--only",
                        help="chỉ chạy/đọc vài kịch bản, ngăn cách bằng dấu phẩy "
                             "(đo lại một ca lẻ mà không trả tiền cho cả bộ)")
    parser.add_argument("--freeze-baseline", action="store_true",
                        help="ghi kết quả hiện tại thành baseline — HÀNH ĐỘNG CÓ CHỦ ĐÍCH, kèm lý do")
    args = parser.parse_args()

    only = {s.strip() for s in args.only.split(",")} if args.only else None
    scenarios = load_scenarios()
    if args.mode:
        scenarios = [s for s in scenarios if s["mode"] == args.mode]
    if only:
        scenarios = [s for s in scenarios if s["id"] in only]
        unknown = only - {s["id"] for s in scenarios}
        if unknown:
            raise SystemExit(f"Không có kịch bản: {', '.join(sorted(unknown))}")

    if args.live:
        print(f"Sinh câu trả lời qua pipeline chat thật ({len(scenarios)} kịch bản)...")
        records = asyncio.run(generate(scenarios))
        print("\nChấm bằng LLM-judge...")
        judge_all(records)
        save_snapshot(records)
        print(f"\nĐã lưu snapshot vào {SNAPSHOT_PATH}")
    elif args.rejudge:
        records = load_snapshot()
        if args.mode:
            records = [r for r in records if r["mode_expected"] == args.mode]
        if only:
            records = [r for r in records if r["scenario_id"] in only]
        print(f"Chấm lại {len(records)} câu trả lời ĐÃ LƯU (không sinh mới)...")
        judge_all(records)
        save_snapshot(records)
    else:
        records = load_snapshot()
        if args.mode:
            records = [r for r in records if r["mode_expected"] == args.mode]
        if only:
            records = [r for r in records if r["scenario_id"] in only]

    scored = score(records)
    baseline = load_baseline()
    print()
    print(format_report(scored, baseline, live=args.live))

    passed, reasons = verdict(scored, baseline)
    print()
    print(f"VERDICT: {'PASS ✅' if passed else 'FAIL ❌'}")
    for reason in reasons:
        print(f"  - {reason}")

    if args.freeze_baseline:
        BASELINE_PATH.write_text(
            json.dumps({"meta": BASELINE_META, **scored}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"\nĐã chốt baseline vào {BASELINE_PATH} — nhớ ghi LÝ DO vào commit.")

    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
