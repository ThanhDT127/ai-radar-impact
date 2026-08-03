## Context

**Module: M8 (Chat Q&A) + M6 (Dashboard).** Không thêm/sửa bảng DB nào, không thêm endpoint
nào, không gọi model thêm lần nào. Thay đổi nằm ở: số lượng và nội dung sự kiện `status` trên
luồng SSE sẵn có, và cách widget render chúng.

**API bị ảnh hưởng:** `POST /api/v1/chat/stream` — sự kiện `status` thêm trường `key`. Sự kiện
`token` / `commit` / `error` **không đổi**. `POST /api/v1/chat` (blocking) **không đổi** — nó
không có `emit`, nên toàn bộ change này là no-op ở đó theo đúng thiết kế một-pipeline.

**AI/LLM:** không có lượt gọi model mới. Không đụng prompt, không đụng grounding.

Ràng buộc kế thừa, không được phá:
- Một pipeline, hai lối ra (`chat-streaming-sse`): mọi thứ ở đây đi qua `self._status()` sẵn
  có, `emit=None` thì im lặng. **Không** rẽ nhánh logic theo mode.
- Status phát từ **mốc thật**, mang số liệu của lượt (`chat_service.py:83-86`, `98-110`).
- `build_context()` là **hàm thuần** — không được nhét việc phát sự kiện vào nó.

Hiện trạng đo được:

| | |
|---|---|
| Số chuỗi status cứng | 4 (`STATUS_READING_INSIGHT/SEARCHING/EXPANDING/COMPOSING`) |
| Mốc mang số liệu thật | 1 (`_reading_status`) |
| Số mốc câu toàn cục điển hình thấy | 2 |
| Cách widget xử lý mốc mới | **ghi đè** (`ChatWidget.tsx:188`) |
| TTFT (SSE, client ấm) | 2,6–3,9s; status đầu ~0,0s, status thứ hai ~0,44s |

## Goals / Non-Goals

**Goals:**
- Người dùng nhìn thấy **chuỗi việc** server đang làm, không phải một dòng nhấp nháy.
- Mỗi mốc mới phải mang **dữ liệu của lượt này**, không phải chuỗi tĩnh.
- Chi phí: 0 lượt gọi model, 0 token thêm vào prompt, 0 truy vấn DB thêm.
- Đặt sẵn chỗ cho mốc `web_search` của `chat-web-fallback` mà không phải sửa lại hợp đồng.

**Non-Goals:** xoay vòng đồng nghĩa; tiến trình giả theo đồng hồ; làm mượt token; đụng nội
dung câu trả lời.

## Decisions

### D1 — Status mới phải mang số liệu, nếu không thì không thêm

Tiêu chí nhận một mốc: **nó nói được điều gì đó chỉ đúng cho lượt này**. Bốn mốc đạt tiêu chí:

| Mốc | Dữ liệu mang theo | Vì sao đáng |
|---|---|---|
| `ranked` | số tin khớp / tổng corpus | Mốc **đầu tiên** có số thật; hiện rơi vào khoảng im lặng dài nhất (embed + DB + `_rank`) |
| `pinned` | tiêu đề tin ghim từ history | Giải thích vì sao bot "nhớ" chuyện cũ — hiện hoàn toàn vô hình |
| `reading` | tên tin đọc kỹ + tổng khớp | **Đã có** (`_reading_status`), giữ nguyên |
| `retrying` | — | Người dùng đang chờ **một lượt gọi model nữa** mà không biết. Đây là mốc im lặng đắt nhất hiện nay |

`retrying` không mang số nhưng vẫn nhận, vì nó giải thích một khoảng chờ **bất thường** (gấp
đôi bình thường). Im lặng ở đó là tệ hơn cả lặp lại.

Bị loại: intent tầng 2 (nằm trước khi biết là câu tra cứu — xem Non-goals), tín hiệu đoạn thân
bài (không tách bạch được với `ranked` về mặt thời gian, gộp vào số của `ranked` thì đủ).

### D2 — `key` ổn định, tách khỏi chuỗi hiển thị

Sự kiện thành `{"type":"status","key":"ranked","text":"…"}`. Widget dùng `key` để quyết định
*thêm dòng mới* hay *cập nhật dòng hiện có*.

Vì sao không để widget so chuỗi: chuỗi mang số liệu nên **luôn khác nhau** giữa hai lượt phát
cùng loại; so chuỗi sẽ đẻ ra dòng trùng. Và sửa câu chữ tiếng Việt sẽ âm thầm đổi hành vi
render — đúng loại lỗi "sống ở khe giữa hai tầng" mà `chat-citation-integrity` đã trả giá.

`key` là tập đóng, khai báo ở **một chỗ** dùng chung backend/frontend. Widget gặp `key` lạ thì
**hiển thị bình thường như một dòng mới** (không nuốt) — client cũ và server mới không được
làm mất thông tin của nhau.

### D3 — Widget xếp chồng, giữ tối đa 4 dòng

```
✓ Lọc 179 tin, 23 tin khớp                    ← mờ
✓ Nhắc lại «NVIDIA Nemotron 3 Embed…»         ← mờ
⟳ Đọc kỹ 3 tin: «Optimizing RAG at Scale…»    ← đậm
```

Trần 4 dòng: quá đó thì bỏ dòng cũ nhất. Panel chat hẹp, và mốc cũ nhất là mốc ít liên quan
nhất tới việc đang chờ. Khi `commit` tới, cả khối biến mất — không đổi so với hiện nay.

**Không** dựng thanh tiến trình %: ta không biết còn bao lâu (85% thời gian nằm ở model), và
một thanh chạy sai là lời hứa sai.

### D4 — Mốc `ranked` đặt SAU `_rank`, không phải sau truy vấn DB

Cám dỗ: phát ngay sau `list_for_chat` để lấp khoảng chờ sớm hơn. Từ chối — lúc đó chưa có số
"tin khớp", chỉ có "tin đã nạp", mà nói *"đã nạp 179 tin"* là nói một con số **không mang
thông tin gì về câu hỏi**. Thà im thêm 0,2s.

Mốc đầu tiên vẫn tới ở ~0,0s như hiện nay (`STATUS_SEARCHING`), nên khoảng im lặng đầu không
dài thêm.

## Risks / Trade-offs

- **Nhiều dòng hơn có thể thành nhiễu.** Giảm thiểu bằng trần 4 dòng + chữ mờ cho mốc đã qua.
  Nếu vẫn ồn thì van xả là hạ trần xuống 2, không phải bỏ mốc — mốc là dữ liệu, trần là trình bày.
- **`retrying` để lộ một sự cố nội bộ ra giao diện.** Chấp nhận: `chat-answer-completeness` đã
  chọn "không bao giờ trả lời dở dang", nên lượt hỏi lại là hành vi **đúng**, không phải lỗi
  cần giấu. Câu chữ nói về câu trả lời (*"đang rút gọn lại"*), không nói về lỗi hệ thống.
- **Không có lưới tự động cho chất lượng câu chữ status.** Test chỉ khoá được *mốc nào phát,
  key nào, đúng thứ tự không*. Nội dung tiếng Việt vẫn là đánh giá của người.

## Migration Plan

Không có migration DB. Triển khai thuận: server phát thêm `key` + mốc mới → client cũ bỏ qua
`key`, vẫn hiển thị `text` như một dòng bị ghi đè (hành vi cũ, không vỡ). Client mới + server
cũ: không có `key` ⇒ mọi mốc coi như dòng mới, xếp chồng vẫn chạy.

Rollback: không có cờ env riêng — change này không có chế độ hỏng cần tắt gấp. Muốn quay lại
thì revert commit.

## Đo thật sau khi land (task 5.1)

Câu toàn cục *"có tin gì về bảo mật tuần này"*, corpus 179 tin, qua SSE thật, **client đã
được làm ấm bằng một lượt chào trước đó** (bắt buộc — xem cảnh báo ở `chat-context-depth`):

| Thời điểm | Mốc | Nội dung |
|---|---|---|
| **0,30s** | `searching` | Đang tìm trong hệ thống… |
| **2,29s** | `ranked` | Đã lọc 179 tin, **58 tin khớp** câu hỏi… |
| **2,29s** | `reading` | Đang đọc kỹ 3 tin: «Kubernetes Production checklist…», «Microsoft Patches a Record 570…» và 1 tin nữa |
| 5,26s | *(token đầu)* | |
| 6,78s | *(commit)* | 5 nguồn |

Hai điều đo ra **ngược với dự đoán của design**, cả hai đáng ghi lại:

**① `ranked` và `reading` tới CÙNG một thời điểm (2,29s).** Dự đoán ban đầu là `ranked` sẽ
lấp khoảng giữa; thực tế `build_context` chạy hết trong vài ms sau `_rank` nên hai mốc dính
nhau. Ghi chú cũ trong code — *"không phát thêm một sự kiện nữa: hai status cách nhau vài
chục ms chỉ làm dòng chữ nhấp nháy"* — **không còn áp dụng**, và lý do là thứ change này vừa
đổi: nhấp nháy là hệ quả của mô hình **ghi đè một dòng**. Khi các mốc **xếp chồng**, hai dòng
xuất hiện cùng lúc chỉ là hai dòng xuất hiện cùng lúc; không có gì nhấp nháy. `ranked` giữ
lại vì nó mang một con số mà `reading` không có (58/179) và nó ở lại trên màn hình.

**② Khoảng im lặng thật nằm ở 0,30 → 2,29s (~2,0s), không phải ở chỗ design đoán.** Đó là
`asyncio.gather(list_for_chat, embed → chunk_ranks)` — trước khi nó xong thì **không có số
thật nào tồn tại** để mà nói. Vượt mốc "≤1,5s" mà task 5.1 đặt ra.

Không chữa, và đây là quyết định có chủ đích: trong suốt 2,0s đó màn hình **không trống** —
dòng `searching` đang hiển thị và nó **mô tả đúng việc đang diễn ra**. Thứ duy nhất có thể
chèn vào là một mốc bịa (đếm ngược, phần trăm, hoặc "đang nạp dữ liệu…" phát trước khi có số),
mà cả ba đều vi phạm luật gốc: *phát từ mốc thật, nói sai còn tệ hơn nói chung chung*. Đổi
"≤1,5s giữa hai sự kiện" thành ràng buộc đúng hơn: **không khoảnh khắc nào giao diện không
nói gì** — điều này đạt, vì mốc đầu tới ở 0,30s và ở lại.

## Quyết định chốt (task 5.2)

**Có phát `ranked` khi số tin khớp bằng 0.** Nó là thông tin thật, nó chuẩn bị trước cho câu
từ chối sắp tới (thay vì để người dùng bất ngờ), và bỏ nó đi sẽ tạo ra một chuỗi mốc khác
nhau tuỳ kết quả — tức là người dùng không học được nhịp của hệ thống.

Ca **câu hỏi rỗng từ khoá** thì khác và đã xử lý riêng: ở đó `_rank` cố ý tắt cả tầng vector
lẫn tầng đoạn, **không có phép khớp nào diễn ra**, nên nói "0 tin khớp" là nói sai việc.
`_ranked_status(None, total)` đổi câu thành *"Đang xếp N tin theo mức quan trọng…"*.
