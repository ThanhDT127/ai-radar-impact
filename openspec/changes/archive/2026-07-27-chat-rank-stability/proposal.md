# Proposal: chat-rank-stability

**Phase áp dụng:** Phase 2 (củng cố M8 Chatbot — bảo vệ chất lượng xếp hạng, không thêm tính năng).

## Why

`chatbot-qa` section 4b.2 phát hiện và sửa một chế độ hỏng **im lặng**: xếp hạng chỉ bằng
`score_for_role()` cho recall 42% (câu "mô hình mã nguồn mở" chỉ vớt 2/18 tin), mà model vẫn trả lời
trôi chảy từ 2 tin sót lại. Bản sửa đưa recall lên 91%.

Con số 91% đó **không có gì giữ**. `backend/tests/eval/` chỉ chứa fixture của gate; bộ đo recall chat
chưa từng được commit. Bốn file test chat hiện có đều bảo vệ *cơ chế* (grounding, quota, mode routing),
không file nào bảo vệ *chất lượng xếp hạng*. Sửa `_STOPWORDS`, đổi ngưỡng độ dài 2, hay chỉnh
`chat_index_top_k` — không có gì bắt lỗi. Đây đúng là hoàn cảnh đã sinh ra `gate-benchmark-durability`,
lặp lại lần thứ hai.

Việc này đang chặn thật: `chat-citation-integrity` **sửa thuật toán xếp hạng** (task 4.1) rồi cam kết
"recall không tụt dưới 91%" ở task 4.3 — một lời hứa hiện không có cách nào kiểm chứng.

Kèm theo, một lỗi cùng họ với 4.1 nhưng bị bỏ sót: **`_roles_in_question` cũng khớp chuỗi con.**

```
'tin về device IoT mới'  -> ['Dev']   ← sai
'DevOps cần chú ý gì'    -> ['Dev']   ← sai (DevOps thuộc taxonomy Source.target_roles, khác hẳn)
'thiết bị nào bị lỗi'    -> []        ← hỏi đúng device thì lại không nhận ra
```

Đây là công ty có trụ cột IoT/Smart Home — `device` xuất hiện dày đặc. Hậu quả nặng hơn `_relevance`:
`_relevance` sai thì lệch điểm một tin, còn `_roles_in_question` sai thì **đổi cả trục xếp hạng** của
toàn bộ danh sách sang vai trò `Dev`, và ảnh hưởng luôn `empty_roles` (có thể tuyên bố nhầm "không có
tin nào cho Dev"). Không log, không dấu hiệu.

## What Changes

- **Benchmark recall xếp hạng, tự chứa và chạy lại được** — dựng theo đúng mẫu `tests/eval/` của
  `gate-eval-harness`: fixture trong repo, chạy offline mặc định, không cần DB sống, không tốn quota.
  Đo `_rank()` chứ không đo câu trả lời của model, nên **không gọi Gemini** — khác gate ở điểm này.
- **`_roles_in_question` khớp theo biên từ** thay cho `role.lower() in question.lower()`.
- **Tiếp nhận task 4.3 dời từ `chat-citation-integrity`** — phép đo recall trước/sau khi sửa
  `_relevance` chuyển về đây, vì công cụ đo nằm ở change này. Change kia bỏ task 4.3 và khai dependency.

## Capabilities

### New Capabilities
- `chat-rank-eval-harness`: bộ đo recall của tầng xếp hạng chat — fixture tự chứa, baseline đối chiếu
  được, chạy lại bắt buộc khi đụng `_rank`/`_relevance`/`_question_terms`/`_STOPWORDS`/`top_k`.

### Modified Capabilities
- `chat-qa-service`: việc chọn **trục xếp hạng theo vai trò** SHALL nhận diện vai trò theo biên từ, và
  SHALL không suy ra vai trò từ chuỗi con nằm trong từ khác.

## Non-goals

- **Không** rate-limit / per-IP throttling — MVP chưa cần (chốt 22/07/2026).
- **Không** đổi thuật toán xếp hạng hai tầng, `score_for_role()`, hay `chat_index_top_k`.
- **Không** đụng `_relevance` (thuộc `chat-citation-integrity` task 4.1) — change này chỉ *đo* nó.
- **Không** đụng `CHAT_SYSTEM_PROMPT`, grounding, fail-closed, hay hợp đồng `n`.
- **Không** thêm streaming, vector search, conversation store.

## Dependencies

- `chatbot-qa` (archive 22/07/2026) — code bị sửa và số đo baseline đều thuộc change đó.
- `gate-eval-harness` (archive 21/07/2026) — mẫu kiến trúc cho harness.
- **Quan hệ hai chiều với `chat-citation-integrity`** (đang mở, chưa implement): change này phải land
  **trước** task 4.1 của change kia, để 4.1 có công cụ đo hồi quy.

## Impact

- **Backend**: `services/chat_service.py` (`_roles_in_question`), `tests/eval/` (fixture + harness mới),
  test mới cho role matching.
- **Change khác**: `chat-citation-integrity` bỏ task 4.3, thêm dependency.
- **Docs**: `CLAUDE.md` — thêm dòng "chạy lại benchmark khi sửa xếp hạng chat", song song dòng đã có
  cho `GATE_PROMPT`.
- **Không** đổi endpoint, không migration, không đụng frontend, không đụng pipeline analysis.
