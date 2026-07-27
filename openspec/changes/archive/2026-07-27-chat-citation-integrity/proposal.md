# Proposal: chat-citation-integrity

**Phase áp dụng:** Phase 2 (củng cố M8 Chatbot — vá bất biến của `chatbot-qa`, không thêm tính năng).

## Why

Backend và frontend của chat đang ký **hai hợp đồng khác nhau** về ý nghĩa con số `n` trong marker `[n]`:

```
prompts.py luật 3        : [n] = số thứ tự của tin trong INDEX (1..60)
resolve_citations()      : citations[] nén lại theo THỨ TỰ XUẤT HIỆN
ChatWidget.tsx:26        : citations[n-1]  ← giả định n = VỊ TRÍ trong mảng
```

Hai cái chỉ trùng nhau khi dãy marker phân biệt (theo thứ tự xuất hiện) đúng bằng `1,2,3,…,k` — liền
mạch, bắt đầu từ 1. Lệch một cái là hỏng:

| marker model phát ra | kết quả trên widget |
|---|---|
| `[1][2][3]` | ✅ đúng |
| `[2]` một mình | marker chết, không thành link |
| `[1][2][4]` | `[4]` chết |
| `[1][3][5]` | **`[3]` trỏ sang insight#5**, `[5]` chết |
| `[2][1]` (đảo) | **cả hai trỏ sai tin** |

Hiện tại nó **đang chạy đúng** — xác nhận bằng thử tay 22/07. Lý do là thiết kế của chính các bạn:
xếp hạng hai tầng (4b.2) đẩy tin liên quan nhất lên đầu index, còn prompt dặn *"dữ liệu đã xếp sẵn
theo độ ưu tiên nên tin ở đầu danh sách đáng chọn hơn"* — nên `[1][2][3]` là hành vi mặc định.

Đó chính là điều đáng lo: **thứ che lỗi lại là thứ 4b.2 sửa.** Marker chỉ nhảy cóc khi model bỏ qua
một tin ở giữa — tức khi xếp hạng đặt tin không hợp vào top. Xếp hạng càng tốt, lỗi càng ẩn kỹ; và
nó sẽ ló ra **đúng lúc recall tụt**, nghĩa là hai lỗi bùng cùng lúc và cái thứ hai im lặng. Đây là
bất biến đang được giữ nhờ **thói quen của model**, không nhờ cấu trúc — ngược hẳn tinh thần D4
(*chống bịa bằng cấu trúc, không bằng hậu kiểm*).

Kèm theo, hai nợ nhỏ hơn phát hiện cùng đợt review:

- **`_relevance` khớp chuỗi con, không khớp từ.** Ngưỡng độ dài hạ xuống 2 (4b.3, đúng cho tiếng Việt
  đơn âm) làm token ASCII 2 ký tự mất tác dụng: `"ai"` khớp bên trong *email, domain, training, chain,
  available, detail, fail, explain*. `"AI"` là từ khoá phổ biến nhất trên một sản phẩm tên *AI Radar* —
  khi nó khớp gần như mọi tin, tầng relevance mất khả năng phân biệt và **âm thầm** tụt về
  `score_for_role`, đúng chế độ hỏng mà 4b.2 mô tả. Bộ đo recall 91% chạy trên truy vấn tiếng Việt,
  không có ca token ASCII ngắn.
- **Tài liệu lệch code**: task 5.3 (viết docs) chạy **trước** section 4b (thêm top-K), không cập nhật
  lại. `CLAUDE.md:218` và `docs/system_overview.md:406` vẫn ghi *"nhét cả corpus/cả kho"* (thực tế
  top-K=60), ghi xếp hạng chỉ bằng `score_for_role()` (thực tế **hai tầng**), và thiếu hẳn
  `CHAT_INDEX_TOP_K` — *van xả chính*. Dòng nguy hiểm nhất là mô tả xếp hạng: người đọc có thể "dọn"
  tầng relevance đi mà không biết mình vừa hạ recall 91% → 42%.

## What Changes

- **`n` thành dữ liệu, không còn là kiến thức ngầm**: `Citation` mang thêm trường `n` (số marker do
  server cấp phát); widget tra theo `n` thay vì theo vị trí mảng. Danh sách nguồn dưới bong bóng đánh
  số **khớp** marker inline (hiện đang tự đánh lại `[1..N]`, mâu thuẫn với marker giữa câu).
- **Test xuyên hai tầng** cho đúng bất biến này — hiện `test_resolve_citations_maps_markers_in_order`
  khẳng định `[2]→B, [1]→A` (đúng ở backend) mà **chính ca đó làm widget trỏ sai cả hai**; test xanh,
  sản phẩm sai. Repo cũng **chưa có test frontend nào**.
- **`_relevance` khớp theo biên từ**, giữ nguyên ngưỡng 2 ký tự; thêm ca `"AI"` vào bộ đo recall.
- **Đồng bộ `CLAUDE.md` + `docs/system_overview.md`** với trạng thái sau-4b.
- **Bỏ 3 tham số chết** `topics`/`roles`/`keyword` của `InsightRepository.list_for_chat` — không caller
  nào dùng (D3 chọn nhét cả index nên không cần lọc).

## Capabilities

### New Capabilities
_(không có)_

### Modified Capabilities
- `chat-qa-service`: citation trả về SHALL mang số marker `n` tường minh; tầng độ-liên-quan SHALL khớp
  theo biên từ.
- `chat-web-widget`: render marker SHALL giải theo `n`, không theo vị trí mảng; đánh số danh sách nguồn
  SHALL khớp marker inline.

## Non-goals

- **Không** đổi cách model sinh marker, không đổi `CHAT_SYSTEM_PROMPT` luật citation.
- **Không** đổi thuật toán xếp hạng hai tầng hay `chat_index_top_k` — chỉ sửa cách so khớp từ khoá.
- **Không** thêm streaming, conversation store, vector search (giữ nguyên non-goals của `chatbot-qa`).
- **Không** dựng hạ tầng test frontend nặng — chỉ đủ để khoá bất biến citation.

## Dependencies

- `chatbot-qa` (đã archive 22/07) — code và specs bị sửa đều thuộc change đó.
- **`chat-rank-stability` — PHẢI land trước task 4.1** (đã land 27/07/2026). Task 4.1 sửa `_relevance`, tức
  sửa thẳng vào tầng xếp hạng; `tests.eval.chat_rank_harness` là công cụ duy nhất đo được hồi quy đó, và
  bộ câu hỏi của nó (nhóm `ascii_short`) tồn tại để đo đúng thay đổi này. Không có nó thì cam kết "recall
  không tụt dưới 91%" ở 4.3 là lời hứa không kiểm chứng được.
- `chat-eval-quality-gate` (land 27/07/2026) — 4.1 đổi context ⇒ đổi câu trả lời, nên phải chốt lại baseline
  của `tests.eval.chat_answer_harness` (task 4.4).

## Impact

- **Backend**: `schemas/chat.py` (`Citation.n`), `services/chat_grounding.py` (`resolve_citations`),
  `services/chat_service.py` (`_relevance`/`_question_terms`), `repositories/insight_repo.py`
  (bỏ param chết), tests.
- **Frontend**: `api/chat.ts` (type), `components/ChatWidget.tsx` (`renderAnswer`, danh sách nguồn),
  test mới.
- **Docs**: `CLAUDE.md`, `docs/system_overview.md`.
- **Không** đổi endpoint, không migration, không đụng pipeline analysis.
