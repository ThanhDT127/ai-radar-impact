# Proposal: chat-context-depth

**Phase áp dụng:** Phase 2 (M8 Chatbot). Vá chỗ hổng mà khung To‑Be **không mô tả**.

## Why

Độ sâu context hiện do **phạm vi** quyết định, không do **nhu cầu** quyết định: mode B rót cả bài gốc
(~2.600 token), mode A rót 115 token/tin cho mọi tin. Ba phép đo trên fixture 179 tin (27–28/07/2026,
chi tiết ở `measurement.md`) cho thấy hệ quả:

1. **So sánh hai bài đã đọc riêng — hồi chỉ: recall@5 = 0/4.** "Hai cái này khác nhau chỗ nào?" không
   mang từ khoá nội dung nào, nên `_rank` xếp hai bài đúng ở hạng 8–141. **Không mức tinh chỉnh retrieval
   nào chữa được** — thông tin "hai bài nào" không có trong câu hỏi.
2. **So sánh tường minh — retrieval hoàn hảo nhưng câu trả lời nông.** 8/8 câu đưa cả hai tin lên hạng 1&2
   và trích đủ cả hai, nhưng điểm đối chiếu chỉ **1,25/2** (liệt kê song song, không có số liệu). Ghim hai
   tin ở mức 7 field phân tích: **2,00/2 trên cả 8 câu, +50ms**. Số liệu quyết định (16GB vs 18GB VRAM)
   nằm ở `why_it_matters`/`so_what` — những field `build_index_block` không đưa vào.
3. **Câu hỏi chi tiết — từ chối sai 4/5.** Bài đúng đứng **hạng 1 cả 6/6 lần**, nhưng toàn cục trả lời
   "Không tìm thấy thông tin này trong hệ thống", trong khi mode B trên **chính bài đó** trả lời đúng 5/5.
   Không có ca bịa nào (0/6) — thiệt hại là **khẳng định sai về độ phủ**, cùng họ với lỗi `empty_roles`.

Khung To‑Be §3.2 mục 1 đặt tên scope 2 là *"SCOPE SO SÁNH & MỞ RỘNG"* nhưng chỉ định nghĩa phần *mở rộng*.
Ba scope đã land đủ (`chat-scope-routing`); phần "so sánh" chưa từng có cơ chế nào.

## What Changes

- **`referenced_insight_ids` — tham chiếu CÓ CẤU TRÚC, tách khỏi câu hỏi.** Client gửi kèm danh sách
  insight người dùng đang thao tác; server tự nạp. **KHÔNG** nhét URL/UUID vào text câu hỏi: vi phạm D4
  (`chat-citation-integrity`) và làm nhiễu `_question_terms`.
- **Ô SÂU (deep slot) — 3 chỗ, lấp tất định.** Lấp bằng `referenced_insight_ids` trước, còn chỗ thì lấp
  bằng tin xếp hạng cao nhất. Ô sâu mang **cả 7 field phân tích + bài gốc**; phần còn lại vẫn là index nén.
  Một luật, không heuristic "câu này có vẻ cần chi tiết".
- **Một hàm dựng context duy nhất** cho ghim thủ công và hydration tự động — chúng chỉ khác *ai chọn bài*.
- **Marker trong history giải thành TIÊU ĐỀ, không phải số.** `[3]` → `[«Gemma 4 12B»]`. Chữa một lỗi
  **đang tồn tại**: mỗi lượt `_rank` dựng bảng ánh xạ mới nên `[3]` ở lượt trước trỏ tin khác lượt này.
- **Widget: MỘT luồng + hàng chip working set.** Mở bài / bấm citation → thêm vào tập; bỏ được từng chip.
- **`CHAT_SYSTEM_PROMPT` cho phép hình dạng so sánh** khi có ≥2 ô sâu (nới luật "MỘT gạch đầu dòng, tối đa
  2 câu" vốn cấm đúng hình dạng câu trả lời đối chiếu).

## Capabilities

### Modified Capabilities
- `chat-qa-service`: SHALL nhận tham chiếu insight có cấu trúc; SHALL rót ô sâu tất định; SHALL giải marker
  history thành tiêu đề.
- `chat-web-widget`: SHALL giữ working set một luồng thay cho luồng-theo-scope.

## Non-goals

- **Không** chunk/embed `raw_documents` — đó là `chat-chunk-retrieval` (③), giải bài toán *khám phá bằng
  chi tiết*, khác hẳn.
- **Không** bỏ đường `insight_id` cũ: giữ nguyên cho client cũ, test, và `chat_answer_harness`. Retire là
  change sau.
- **Không** đổi grounding/fail‑closed/citation granularity/streaming/quota.
- **Không** làm Query Reformulator (To‑Be §3.2#4) — vẫn treo, và refs mạnh hơn nó ở đúng ca này.

## Dependencies

- `chat-scope-routing`, `chat-context-isolation`, `chat-citation-integrity` (archive) — change này **đảo
  ngược có chủ đích** bất biến "history theo scope" của `chat-context-isolation`; lý do ở `design.md` D3.
- `chat-rank-stability` + `chat-eval-quality-gate`: **bắt buộc** chạy lại (RS miễn phí; answer harness `--live`).

## Impact

- **Không có DB migration.** Không cột mới, không bảng mới.
- API: `POST /api/v1/chat` và `/chat/stream` thêm field optional `referenced_insight_ids`.
- Prompt lớn hơn: ước ~15–17k token (hiện ~19k trần thực tế) — trong biên, và độ trễ không do prompt size.
- `ChatWidget.drift.test.tsx` phải viết lại: bất biến cũ được **thay** bằng bất biến mới, không phải xoá.
