# Tasks: chat-context-depth

Phase: **P2**. Thứ tự bắt buộc: Backend context builder → API → Frontend → Eval.

## Backend

- [x] **1.1 (P2)** `CHAT_DEEP_SLOTS` (mặc định 3) + `CHAT_DEEP_INCLUDE_CONTENT` (mặc định true) vào
      `config.py`; `.env.example` cập nhật.
      *DoD:* `settings.chat_deep_slots` đọc được; test đọc mặc định khi env vắng.
- [x] **1.2 (P2)** `build_insight_block(insight, content, n=1)` — nhận số thứ tự thay vì chốt cứng `[1]`.
      *DoD:* `build_insight_block(i, None, n=2)` cho khối mở đầu `[2] …`; test cũ của `[1]` vẫn xanh.
- [x] **1.3 (P2)** `build_context(refs, ranked, k_deep) -> (context_block, mapping)` trong
      `chat_grounding.py` — lấp ô sâu tất định (refs trước, rank sau), loại ô sâu khỏi index, một dãy số
      liên tục, một mapping. **Hàm thuần** (design D1).
      *DoD:* test: 2 refs + k=3 → ô sâu `[1][2]` là refs, `[3]` là tin rank 1, index từ `[4]`, không tin
      nào xuất hiện hai lần; 0 refs → 3 ô sâu là top‑3.
      *Dep:* 1.2
- [x] **1.4 (P2)** `_history_block()` thay marker `[n]` bằng `[«tiêu đề»]` (design D4). Nhận thêm bảng
      `n → title` của các lượt trước, hoặc giải bằng chính citations client gửi kèm.
      *DoD:* test: history chứa `[3]` + citations lượt đó → khối history không còn chữ số marker nào.
- [x] **1.5 (P2)** Đường có refs: nạp insight + `raw_document` (`_load_refs`), gọi `build_context`,
      **một** lượt gọi model, không sentinel (design D5). `mode="focused"`.
      ⚠️ **Gộp vào `_answer_global(refs=...)` thay vì tách `_answer_focused()`** — ba ca (toàn cục ·
      working set · mở rộng) chỉ khác nhau ở *ai chọn tin để rót sâu*, tức là đúng một tham số.
      Tách method là để hai lối ra trôi khỏi nhau trong im lặng (bài học `chat-streaming-sse`).
      *DoD:* test: 2 refs → 1 lượt gọi, `mode == "focused"`, mapping có đúng 2 ô sâu.
      *Dep:* 1.3
- [x] **1.6 (P2)** Ô sâu tự động cho câu toàn cục không refs (②′): `_answer_global` dùng `build_context`
      với `refs=[]`.
      *DoD:* test: 0 refs → top‑3 rót đầy đủ 7 field + raw content; index bắt đầu từ `[4]`.
      *Dep:* 1.3
- [x] **1.7 (P2)** Suy giảm êm (design D7): ref không tồn tại / không `published` → bỏ qua lặng lẽ;
      refs dư quá `k_deep` → cắt; refs rỗng → hành vi trùng khít 1.6.
      *DoD:* 3 test tương ứng, không test nào mong đợi HTTP 4xx.
      *Dep:* 1.5
- [x] **1.8 (P2)** `selectinload(Insight.raw_document)` cho đường nạp ô sâu; đo lại thời gian truy vấn.
      *DoD:* không N+1; log DEBUG ghi số bài nạp raw content mỗi lượt.

## AI / Prompt

- [x] **2.1 (P2)** `CHAT_SYSTEM_PROMPT` nới hình dạng khi ≥2 ô sâu (design D6): cho phép đối chiếu theo
      chiều; giữ trần "TỐI ĐA 5 tin" và luật marker.
      *DoD:* prompt mới ở `prompts.py`; **kích hoạt 4.2 (`--live`) trước khi merge**.
- [x] **2.2 (P2)** `build_chat_focused_prompt()` — prompt riêng cho đường refs. **Không** tái dùng
      `build_chat_expanded_prompt` (nó mở đầu bằng "Bài bạn đang xem không nhắc tới điều này" — sai ngữ
      cảnh; đã thấy trong spike C1).
      *DoD:* câu trả lời không mở đầu bằng câu dẫn của chế độ mở rộng.

## API

- [x] **3.1 (P2)** `ChatRequest` thêm `referenced_insight_ids: list[UUID] | None`, cap ở schema.
      *DoD:* Pydantic từ chối phần tử không phải UUID; thiếu field → `None`.
- [x] **3.2 (P2)** Route `/chat` và `/chat/stream` truyền refs xuống `ChatService.answer(...)`;
      `mode="focused"` ghi được vào `chat_logs`.
      *DoD:* test cho cả hai endpoint; SSE vẫn phát `status`/`token`/`commit` như cũ.
      *Dep:* 1.5, 3.1

## Frontend

- [x] **4.1 (P2)** State `workingSet: Insight[]` trong `ChatWidget`; thêm khi mở trang chi tiết và khi
      bấm citation; cap `CHAT_DEEP_SLOTS`, giữ mục mới nhất.
      *DoD:* `ChatWidget.workingset.test.tsx` — 3 ca: mở A→B, bấm citation, vượt cap.
- [x] **4.2 (P2)** Hàng chip working set (thay `scopeBar`), mỗi chip bỏ được 1 click.
      *DoD:* aria-label rõ ràng; test bỏ chip → refs gửi lên không còn id đó.
      ⚠️ `ChatWidget.scope.test.tsx` **được thay bằng** `ChatWidget.workingset.test.tsx`: badge
      hai chiều không còn tồn tại (spec `REMOVED Requirements`), nên test của nó không thể "viết
      lại" — nó test một control đã bị gỡ. 6 test mới phủ đúng phần thay thế.
- [x] **4.3 (P2)** Gộp `threads` về **một** luồng; `send()` dựng history từ luồng duy nhất; `pending`
      vẫn nằm ngoài luồng.
      *DoD:* `ChatWidget.drift.test.tsx` **viết lại** quanh bất biến mới (design D3) — không xoá file.
      ⚠️ Kéo theo `ChatWidget.streaming.test.tsx`: block "huỷ khi đổi scope (D6)" mất lý do tồn tại
      (một luồng ⇒ điều hướng không đổi luồng ⇒ huỷ là **mất** dữ liệu đã trả tiền sinh ra). Ba test
      cũ thay bằng một test đảo chiều + một test GIỮ bất biến "phần dở không vào history".
      *Dep:* 4.1
- [x] **4.4 (P2)** `chat.ts` gửi `referenced_insight_ids` ở cả `chat()` và `streamChat()`.
      *DoD:* `api/__tests__/chatStream.test.ts` khẳng định field có trong payload.

## Test / Eval

- [x] **5.1 (P2)** Land 19 kịch bản so sánh từ `eval/cmp_scenarios.json` vào
      `tests/eval/chat_scenarios.jsonl` (thêm `group: comparison`, `label_reason` bắt buộc), rồi chạy
      `python -m tests.eval.build_fixture_chat` sinh query vector.
      *DoD:* `load_scenarios()` không ném lỗi; `chat_rank_harness` chạy không báo thiếu vector.
      ⚠️ Phải thêm `build_fixture_chat --top-up`: bản không cờ **ghi đè `chat_corpus.jsonl` bằng DB
      hiện tại**, tức là thêm kịch bản sẽ vô tình đổi luôn ảnh chụp corpus và mọi baseline mất tính
      so sánh được. `--top-up` chỉ bổ sung anchor + query vector cho kịch bản mới.
- [x] **5.2 (P2)** `chat_rank_harness` → `--freeze-baseline` **kèm lý do** trong `BASELINE_META.revisions`.
      *DoD:* baseline mới ghi rõ "thêm nhóm `comparison`, C2 dự kiến đỏ theo thiết kế".
      *Dep:* 5.1
- [x] **5.3 (P2)** `chat_answer_harness --live` sau khi 2.1 xong; chốt lại baseline Faith/AnsRel/CitPrec.
      *DoD:* Faithfulness ≥ 0,95 **và** Citation Precision = 1,00; AnsRel trong dung sai 0,05 hoặc có lý do.
      *Dep:* 2.1, 1.6
- [x] **5.4 (P2)** Test hồi quy cho D4: history mang marker số của lượt trước không làm model trỏ sai.
      *DoD:* `tests/test_chat_history_markers.py` → thực tế nằm trong `tests/test_chat_context_depth.py`
      (2 test: giải thành tiêu đề, và lượt thiếu citations thì bỏ marker) — gom một file cho cả change.
- [x] **5.5 (P2)** Đo lại C1/C2 bằng script trong `eval/` sau khi apply, ghi kết quả vào `measurement.md`
      dưới mục "sau khi apply".
      *DoD:* C2 cả‑hai@5 = 4/4; C1 Comparison Adequacy ≥ 1,9.

## Việc tách riêng (không chặn change này)

- [x] **6.1 (P2)** Bổ sung `hai, cái, bài, chỗ, khác, sánh, nhau` vào `STOPWORDS` để cổng
      `if not terms → tắt vector` bắn đúng cho câu hồi chỉ. **Chạy lại `chat_rank_harness`** (sửa
      `STOPWORDS` là một trong các trigger bắt buộc).
      *DoD:* `_question_terms("Hai cái này khác nhau chỗ nào?") == []`; harness không có câu nào tụt.
