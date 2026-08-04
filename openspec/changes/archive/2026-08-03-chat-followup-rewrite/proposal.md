> ## ⛔ TRẠNG THÁI: DỪNG — kết quả âm, 31/07/2026
>
> Cơ chế đề xuất **đã được cài, đo, và gỡ**. Cổng 4.2 (do chính change này đặt ra) cho:
> recall@5 nhóm loại B `off` **0,79** → `add` **0,71** ▼. Phương án đề xuất làm xếp hạng
> **tệ đi**, nên `tasks.md` §4.2 buộc dừng. Chi tiết + nguyên nhân: `measurement.md` §11.
>
> **Phần LAND lại:** bộ kịch bản `followup_new_topic` (14 ca, lần đầu bộ kịch bản mang
> `history`), bất biến `must_have ∩ turn1_cited = ∅` nổ khi vi phạm, `_history_for()` cho
> `chat_answer_harness` (trước đó runner truyền `history=[]` cho **mọi** kịch bản), và hai
> baseline chốt lại. Đó là lưới đo — thứ có giá trị độc lập với cơ chế.
>
> **Phần GỠ:** toàn bộ nhóm 3 và 5 của `tasks.md` (cờ config, prompt viết lại,
> `rewrite_query()`, số hạng RRF thứ tư trong `_rank`).
>
> Phần *Why* / *What Changes* dưới đây giữ **nguyên văn** như lúc đề xuất, cố ý: nó là bản
> ghi của một giả thuyết hợp lý đã bị dữ liệu bác bỏ. Đọc kèm `measurement.md` §11.

## Why

`_rank()` chỉ nhận `question`. `history` chảy vào `_history_block` → prompt và **không chạm**
truy hồi — `chat-history-pinning` đi vòng qua `_rank` bằng cách tiêm thẳng id vào index, chứ
không dạy `_rank` đọc lịch sử. Hệ quả: câu nối tiếp **lược chủ ngữ** (*"Thế lúc triển khai thì
cần chuẩn bị gì?"* sau một lượt về Kubernetes) đi vào xếp hạng với đúng phần còn lại của nó.

Ghim và working set **không che được ca này theo định nghĩa**: tin cần để trả lời chưa từng
được trích, và người dùng chưa bấm gì.

Đo 31/07/2026 trên 14 kịch bản mới (`followup_new_topic`, mỗi cái neo vào một cặp tin có thật,
`must_have ∩ turn1_cited = ∅` được assert):

| | recall@5 | recall@60 | vào ô sâu | hạng xấu nhất |
|---|---|---|---|---|
| nguyên trạng | **0,786** | 1,000 | 0,643 | **29** |
| + tiêu đề tin ghim (0 gọi model) | 0,786 | 1,000 | 0,786 | 26 |
| viết lại, **không** embed lại | 0,786 | 1,000 | 0,786 | 29 |
| viết lại **+ embed lại** | **1,000** | 1,000 | 0,893 | 5 |

Hai dòng giữa là **hai phương án rẻ, cả hai đo được là bằng không**. Kết quả này lặp lại độc
lập trên nhóm hồi chỉ (`comparison_anaphora`): tiêm từ khoá cho recall@5 **0,000**, embed lại
cho **1,000**. ⇒ **Reformulator là can thiệp vào vector truy vấn, không phải vào từ khoá.**

> ⚠️ Đính chính hồ sơ: ba proposal đã archive và CLAUDE.md đều ghi *"câu nối tiếp hiện được
> chữa bằng bản gộp‑từ‑khoá tất định"*. **Nó chưa bao giờ tồn tại** — `_question_terms` có đúng
> hai caller, cả hai truyền `question` trần.

## What Changes

- Câu hỏi được **viết lại thành truy vấn độc lập** dựa trên `history`, rồi embed. Bản viết lại
  chỉ nuôi **truy hồi**; prompt vẫn nhận **nguyên văn** lời người dùng.
- Vector bản viết lại vào `_rank` như **số hạng RRF THỨ TƯ**, **không thay** vector gốc.
- Bộ kịch bản `followup_new_topic` + baseline vào `tests/eval/` làm cổng thường trực; bản viết
  lại **đông lạnh** trong fixture để RS harness giữ được "miễn phí, offline, tất định".
- Env: `CHAT_QUERY_REWRITE_ENABLED` (mặc định **false**), `CHAT_QUERY_REWRITE_MODEL_ID`.

## Capabilities

### New Capabilities
<!-- Không có: đây là thêm một tín hiệu vào tầng truy hồi đã tồn tại. -->

### Modified Capabilities
- `chat-qa-service`: tầng độ‑liên‑quan nhận số hạng RRF thứ tư từ truy vấn viết lại; ràng buộc
  *bản viết lại không bao giờ đi vào prompt*.
- `chat-rank-eval-harness`: kịch bản lần đầu mang `history`; baseline có nhóm `followup_new_topic`.

## Non-goals

- **KHÔNG** sửa cổng `if not terms` của `_rank`. Đó là bug **độc lập** (câu hồi chỉ lọt cổng
  ⇒ hạng 1 → 58), phải là change riêng để công của nó không bị ghi nhầm cho change này. Nhưng
  design **phải** xử lý tương tác: cổng hiện vô hiệu hoá mọi vector khi terms rỗng.
- **KHÔNG** ghim tin vào ô sâu. Change riêng, ưu tiên cao hơn — nó chữa loại A (recall@5
  **0,000**), nặng hơn loại B nhiều.
- **KHÔNG** thay vector gốc bằng vector viết lại (đo: viết lại sai ⇒ hạng 1 → **79**).
- **KHÔNG** rerank cross-encoder; **KHÔNG** đụng đường `insight_id` (mode B / expanded).

## Phase

**Phase 2** — sau khi khung truy hồi (hybrid, chunk) và context depth đã land.

## Dependencies

- `chat-hybrid-retrieval` + `chat-chunk-retrieval` — cứng: RRF nhiều số hạng là cơ chế nền.
- `chat-history-pinning` — đường truyền `history` xuống service.
- `chat-rank-stability` — RS harness là cổng; **bắt buộc** chốt lại baseline kèm lý do.
- `chat-eval-quality-gate` — `--live` chạy lại: đổi context là đổi câu trả lời.

## Impact

`chat_service.py` (`_rank`, `_answer_global`), `gemini_client.py` + `prompts.py` (lượt viết
lại), `config.py`, `tests/eval/`. **Không** đụng bảng DB, **không** đụng endpoint.
