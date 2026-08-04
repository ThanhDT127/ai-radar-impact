# Design: chat-rank-stability

## Context

`_rank()` (`chat_service.py:260`) quyết định tin nào lọt vào index gửi cho model. Cắt sai ở đây thì
model **không bao giờ nhìn thấy** tin đúng — và vẫn trả lời trôi chảy từ phần còn lại. Đó là chế độ hỏng
`chatbot-qa` 4b.2 đã đo: recall 42% tổng thể, 11% cho câu "mô hình mã nguồn mở".

Hiện trạng bảo vệ:

| Tầng | Có test? |
|---|---|
| Grounding, quota, mode routing, citation | ✅ 4 file test |
| Tiêu chí gate (`GATE_PROMPT`) | ✅ `tests/eval/` — fixture 54 mẫu, baseline chốt |
| **Chất lượng xếp hạng `_rank()`** | ❌ **không có gì** |

Bộ đo cho ra con số 91% chưa từng được commit. Đây là lần thứ hai lặp lại hoàn cảnh của
`gate-benchmark-durability` (công cụ đo bị xoá, số đo còn lại trong tài liệu nhưng không tái lập được).

Ràng buộc thời điểm: `chat-citation-integrity` task 4.1 **sửa `_relevance`** rồi cam kết ở 4.3 rằng
recall không tụt dưới 91%. Lời hứa đó hiện không kiểm chứng được — nên harness phải land trước.

**Module ảnh hưởng:** M8 (Chatbot/Search).
**API endpoints:** không thêm, không sửa, không xoá. `POST /api/v1/chat` giữ nguyên request/response.
**Bảng DB:** không đụng bảng nào, **không migration**. Harness cố ý không truy vấn DB.
**AI/LLM:** harness **không gọi model nào** (xem D1) — khác `gate-eval-harness` ở đúng điểm này.
Grounding strategy của chat giữ nguyên hoàn toàn: server cấp phát `n`, model chỉ đánh dấu, fail-closed.
`CHAT_SYSTEM_PROMPT` không đụng tới.
**n8n:** không liên quan (không thuộc delivery).

## Goals / Non-Goals

**Goals:**
- Biến "recall 91%" từ số trong tài liệu thành **assertion chạy được**.
- Phát hiện hồi quy xếp hạng **trước** khi merge, không phải sau khi người dùng nhận câu trả lời thiếu.
- Bịt lỗ `_roles_in_question` — lỗi cùng họ với 4.1 nhưng hậu quả rộng hơn.
- Chỉ ra được **câu hỏi nào** tụt, không chỉ tổng số.

**Non-Goals:**
- Không rate-limit (MVP chưa cần — chốt 22/07/2026).
- Không đổi thuật toán xếp hạng, `score_for_role()`, `chat_index_top_k`.
- Không đụng `_relevance` — thuộc `chat-citation-integrity` 4.1; change này chỉ *đo* nó.
- Không đo chất lượng câu trả lời của model, không đo grounding — đã có test riêng.
- Không xây bảng đồng nghĩa vai trò (xem D6).

## Decisions

### D1 — Đo `_rank()`, không đo câu trả lời ⇒ harness **không gọi model**

Đại lượng cần bảo vệ là **recall@K**: trong tin thực sự liên quan tới câu hỏi, bao nhiêu phần trăm lọt
vào `matched[:chat_index_top_k]`. Đó là hàm thuần, tất định, không có Gemini trong đường đi.

Hệ quả khác hẳn `gate-eval-harness`: **không có chế độ `--live`, không tốn đồng nào, chạy tức thì**, nên
có thể để chạy trong `pytest` mặc định thay vì phải skip. Gate buộc phải gọi model vì thứ nó đo là phán
đoán của model; ở đây thứ quyết định là code của chúng ta.

*Đã cân nhắc:* đo end-to-end (hỏi thật, chấm câu trả lời). Bỏ vì nhiễu — câu trả lời phụ thuộc cả model,
prompt, độ dài; hồi quy xếp hạng sẽ chìm trong dao động và mỗi lần chạy tốn tiền. Muốn đo hồi quy thì
phải cô lập biến.

### D2 — Fixture tự chứa, rehydrate thành `Insight` ORM tách rời (detached)

Fixture JSONL lưu đủ field mà `_rank` đọc: `_relevance` cần `title`/`signal`/`so_what`/`summary_short`/
`topics`/`affected_roles`; `score_for_role` cần `recommendations`/`impact_label`/`practical_indicators`/
`actionability_score`/`intelligence_tier`/`trust_score`/`published_at`/`created_at`.

Harness dựng lại thành **instance `Insight` thật nhưng không gắn session**. SQLAlchemy cho phép, và đó là
điểm mấu chốt: nếu ai đổi tên cột hoặc `score_for_role` bắt đầu đọc field mới, harness **vỡ ngay và rõ**
thay vì lặng lẽ đo trên dữ liệu thiếu.

*Đã cân nhắc:* dùng `SimpleNamespace`/dataclass cho nhẹ. Bỏ vì nó chấp nhận mọi thuộc tính, kể cả cái
không còn tồn tại — đúng loại "test xanh, sản phẩm sai" mà D4 của change kia vừa phải trả giá.

Giữ `build_fixture_chat.py` làm bằng chứng xuất xứ, y như gate. Fixture chụp corpus 22/07/2026 (179
insight `published` + `is_primary`).

### D3 — Nhãn tay dạng **must-have**, không gán nhãn nhị phân toàn corpus

Mỗi câu hỏi kèm một tập nhỏ `must_have` — những insight mà **bỏ sót là hỏng rõ ràng**, gán tay bằng cách
đọc. Recall@K tính trên tập đó.

Vì sao không gán relevant/irrelevant cho cả 179 tin × N câu: tốn hàng nghìn phán đoán, phần lớn là ca
biên mà chính người chấm cũng lưỡng lự, và chúng không phải thứ gây hỏng. Chế độ hỏng thật là **tin
hiển nhiên liên quan bị cắt mất** — `must_have` bắt đúng nó.

Đánh đổi: không tính được precision. Chấp nhận — tin lạc đề lọt vào index chỉ tốn ~108 token và model
đã được dặn "tối đa 5 tin"; tin đúng bị cắt thì mất hẳn. Bất đối xứng này giống hệt FN-tệ-hơn-FP của gate.

### D4 — Bộ câu hỏi phải phủ đúng những ca đã từng làm hỏng

Bộ 15 câu cũ **không đủ** — chính proposal của `chat-citation-integrity` ghi: nó vẫn "đạt" khi recall tụt
còn 42%. Bộ mới bắt buộc có:

| Nhóm | Ví dụ | Bắt lỗi gì |
|---|---|---|
| Chủ đề ngách, urgency thấp | "mô hình mã nguồn mở" | ca 11% của 4b.2 |
| Token ASCII ngắn | "AI", "ML", "Go" | substring `_relevance` (đo cho 4.1) |
| Có tên vai trò | "Security cần chú ý gì" | trục xếp hạng theo vai trò |
| **Bẫy `device`/`Dev`** | "tin về device IoT mới" | D5 |
| Chung chung | "có gì mới không" | tầng 1 hoà, rơi về `score_for_role` |
| Vai trò rỗng | "Data Analyst" (0 entry thật) | `empty_roles` |

### D5 — `_roles_in_question` khớp **chuỗi token liên tiếp**, không phải tập token

Khác `_relevance` ở chỗ dễ sai: vai trò là **cụm nhiều từ** — `Data Analyst` (2), `Người dùng phổ thông`
(4). Nên không thể so tập hợp token; phải khớp dãy token của vai trò như **đoạn con liên tiếp** trong
dãy token câu hỏi, dùng cùng regex `[0-9a-zA-ZÀ-ỹ]+`.

Kiểm lại bằng chính các ca sai hiện nay: `device` → token `device` ≠ `dev` ✅ loại đúng;
`DevOps` → token `devops` ≠ `dev` ✅ loại đúng; `Dev` đứng riêng ✅ vẫn nhận.

Kèm **log DEBUG trục xếp hạng đã chọn** — hiện việc chọn trục hoàn toàn vô hình, không cách nào biết
production đang xếp theo trục nào. Rẻ, và biến thứ đang mù thành đo được (cùng tinh thần với quyết định
log marker nhảy cóc của change kia).

### D6 — Không xây bảng đồng nghĩa vai trò ở đợt này

Hệ quả đã biết: "có tin gì cho **developer** không" sẽ **không** kích hoạt trục `Dev`. Chấp nhận, vì khi
đó `importance()` rơi về `max` trên `affected_roles` — suy giảm êm, không sai lệch.

Ngược lại, một bảng đồng nghĩa đoán sai sẽ **đổi trục xếp hạng một cách im lặng** — đúng loại lỗi đang
phải sửa. Cần dữ liệu thật trước: log DEBUG ở D5 cho biết người dùng thực sự gõ gì, rồi hẵng quyết.

### D7 — Baseline đóng băng kèm dung sai, báo cáo theo từng câu

Chốt baseline recall trên code hiện tại, ghi kèm ngày. Harness fail khi **recall tổng tụt dưới baseline**
hoặc **bất kỳ câu nào tụt**. Báo cáo in per-question, vì "tổng 88%" không nói được câu nào vỡ — mà 4b.2
cho thấy hỏng nặng thường tập trung ở một loại câu (11% ở đúng một chủ đề trong khi tổng vẫn 42%).

### D8 — recall@K **bão hoà**; đại lượng nhạy là recall@5 (thêm khi implement, 27/07/2026)

Đo lần đầu: recall@60 = **1,000 trên cả 47 câu**. Bộ đo như đặc tả ban đầu **không phân biệt được gì** —
nó chỉ bắt được hồi quy đủ lớn để đẩy một tin bắt buộc văng khỏi top-60 trên corpus 179 tin.

Vì sao: `must_have` được chọn vì tin đó *hiển nhiên liên quan* tới câu hỏi ⇒ nó khớp từ khoá ⇒ tầng độ
liên quan (tầng 1 của `_rank`) đẩy nó lên đầu. Nói cách khác K = 60/179 quá rộng so với một tập nhãn được
định nghĩa bằng chính tiêu chí của tầng 1. Con số 42% của 4b.2 đo ở thời điểm xếp hạng **chỉ có**
`score_for_role` — chế độ đó không còn tồn tại.

Thêm **recall@5** làm đại lượng gate thứ hai, với 5 = trần tin trong `CHAT_SYSTEM_PROMPT` ("TỐI ĐA 5 tin").
Đây mới là funnel thật: tin xếp hạng 40 lọt index nhưng model gần như chắc chắn không dùng tới — đúng
cảnh 4b.2 mô tả ("model vẫn trả lời trôi chảy từ 2 tin sót lại"). Đo 27/07: recall@5 = **0,812**, và nó
phân biệt rõ theo nhóm — `ascii_short` 0,00 · `role_trap` 0,25 · `open_model` 0,50 · `security` 0,88.
Kèm cột `worst_rank` (hạng xấu nhất trong `must_have`) để đọc được "trượt sát nút" hay "trượt xa".

Kiểm chứng độ nhạy (task 4.2) trên bản nháp `_relevance` khớp biên từ: **6/47 kịch bản đổi số**,
recall@60 1,000 → 0,988, `exp-gemma-to-eol` hạng 48 → 76. Bộ đo có răng — nhưng chỉ vì có recall@5 và
`worst_rank`; nếu chỉ nhìn recall@60 thì 41/47 câu vẫn im lặng.

Giữ recall@K trong gate như spec yêu cầu (nó vẫn bắt hồi quy thảm hoạ), nhưng **đừng đọc nó như thước đo
chính** — con số 1,000 ở đó là bình thường, không phải bằng chứng chất lượng.

## Risks / Trade-offs

- **[Nhãn tay chủ quan]** → Ghi `label_reason` cho từng `must_have`, y như `human_reason` của gate. Đo
  hồi quy *so với chính nó*, không tuyên bố chất lượng tuyệt đối.
- **[Fixture là ảnh chụp 7/2026, corpus thật sẽ lớn lên]** → Ghi rõ giới hạn diễn giải. Recall@60 trên
  179 tin không suy ra recall@60 trên 1000 tin; khi corpus tăng đáng kể thì sinh lại fixture, không suy diễn.
- **[Đổi schema `Insight` làm fixture lệch]** → D2 rehydrate ORM thật nên vỡ ngay; thêm kiểm tra tính
  toàn vẹn khi khởi động (đối chiếu tập field), giống cách gate đối chiếu `GATE_CONTENT_LIMIT`.
- **[Baseline quá chặt gây fail giả]** → Dung sai rõ ràng thay vì so bằng; sửa baseline phải là hành động
  **có chủ đích** kèm lý do trong change, không phải chỉnh số cho test xanh.
- **[Hai change cùng sửa `chat_service.py`]** → Tách sạch: change này chỉ đụng `_roles_in_question`, change
  kia chỉ đụng `_relevance`/`_question_terms`. Land change này trước.

## Migration Plan

1. Sinh fixture từ DB hiện tại (179 insight) + gán nhãn `must_have` cho bộ câu hỏi.
2. Dựng harness, chốt baseline trên code **chưa sửa gì**.
3. Sửa `_roles_in_question` → chạy lại harness → ghi số trước/sau.
4. Bàn giao cho `chat-citation-integrity`: bỏ task 4.3 ở đó, thêm dependency; task 4.1 dùng harness này.
5. Docs: thêm dòng "chạy lại benchmark khi sửa xếp hạng chat" vào `CLAUDE.md`.

Rollback: không migration, không đổi dữ liệu, không đổi API — revert commit là đủ. Harness là code test,
gỡ ra không ảnh hưởng production.

## Open Questions

- **Bảng đồng nghĩa vai trò** (`developer`→`Dev`, `bảo mật`→`Security`, `thiết bị`→IoT): hoãn theo D6,
  quyết lại sau khi có log DEBUG từ dùng thật.
- **Bao nhiêu câu hỏi là đủ?** Xuất phát từ các nhóm ở D4; nếu một nhóm chỉ có 1 câu thì kết luận cho
  nhóm đó chỉ là tín hiệu, không phải bằng chứng — cùng cảnh báo `n < 5` mà gate harness đã ghi.
- **Có nên chạy harness trong CI mặc định?** D1 nói được (miễn phí, tức thì), nhưng repo hiện chưa có CI
  pipeline — để lại khi dựng CI.
