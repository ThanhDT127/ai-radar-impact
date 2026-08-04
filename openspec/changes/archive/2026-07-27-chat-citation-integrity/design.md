## Context

`chatbot-qa` (archive 22/07/2026) chống bịa citation **bằng cấu trúc**: server đánh số candidate, model
chỉ trả text có marker `[n]`, server tra bảng `n → insight_id`. Model không bao giờ thấy UUID nên không
có gì để bịa. Thiết kế đó đúng và nên giữ nguyên.

Chỗ vỡ nằm ở **ranh giới backend↔frontend**, nơi `n` chưa bao giờ được nói ra thành lời:

```
prompts.py luật 3   :  [n] = số thứ tự trong INDEX          (1..60)
resolve_citations() :  citations[] nén theo THỨ TỰ XUẤT HIỆN (1..k, k≤5)
ChatWidget.tsx:26   :  citations[n-1]                        ← trộn hai hệ quy chiếu
```

Hai hệ chỉ trùng khi dãy marker phân biệt theo thứ tự xuất hiện đúng bằng `1,2,3,…,k`.

Điều đáng chú ý nhất: **hiện tại nó đang đúng**, và đúng vì một lý do không phải bất biến. Xếp hạng hai
tầng (4b.2) đẩy tin liên quan nhất lên đầu index, prompt lại dặn *"tin ở đầu danh sách đáng chọn hơn"* +
*"tối đa 5 tin"* — nên model trích `[1][2][3]` là hành vi mặc định. Marker chỉ nhảy cóc khi model **bỏ
qua** một tin ở giữa, tức khi xếp hạng đặt tin không hợp vào top.

Nói cách khác: **lỗi được che bởi chính chất lượng xếp hạng, và sẽ lộ ra đúng lúc xếp hạng kém đi.** Hai
lỗi bùng cùng lúc, cái thứ hai im lặng. Đây là bất biến đang dựa vào *thói quen của model* — ngược hẳn
tinh thần D4 của `chatbot-qa`.

**Module ảnh hưởng:** M8 (Chatbot/Search).
**API endpoints:** `POST /api/v1/chat` — response `citations[]` **thêm trường `n`** (thêm trường, không
đổi/xoá trường cũ → tương thích ngược với client cũ).
**Bảng DB:** không đụng, không migration.
**AI/LLM:** Gemini 2.5 Flash qua Vertex; `CHAT_SYSTEM_PROMPT` và luật citation **giữ nguyên**. Grounding
strategy không đổi — vẫn là server cấp phát định danh, model chỉ đánh dấu.
**n8n:** không liên quan.

## Goals / Non-Goals

**Goals:**
- Biến `n` từ kiến thức ngầm thành **dữ liệu** — hai tầng không còn phải cùng đoán đúng.
- Có test chạy qua **cả hai tầng**, vì lỗi này sống đúng ở khe giữa chúng.
- Trả tầng độ-liên-quan về đúng ý định của 4b.2 cho cả từ khoá ASCII ngắn.
- Docs khớp code sau-4b.

**Non-Goals:**
- Không đổi cách model sinh marker, không sửa `CHAT_SYSTEM_PROMPT`.
- Không đổi thuật toán xếp hạng, `chat_index_top_k`, hay hành vi fail-closed.
- Không dựng hạ tầng test frontend nặng.

## Decisions

### D1 — `n` đi vào payload, không sửa bằng cách tra ngược ở client

Thêm `n: int` vào `Citation`. Widget giải marker bằng cách tìm citation có `n` khớp.

*Đã cân nhắc:* để widget tự `citations.find(c => c.n === n)` mà không thêm trường — bất khả, vì client
không có gì để so. *Hoặc:* sửa 1 dòng thành tra theo thứ tự xuất hiện — vẫn là hợp đồng ngầm, đúng dạng
đã sinh ra lỗi. Trường tường minh làm ranh giới **tự mô tả** và test được ở đúng chỗ nó vỡ.

### D2 — Giữ nguyên số marker trong answer, KHÔNG đánh số lại

Phương án thay thế: server viết lại text, đổi `[3][7][12]` thành `[1][2][3]` cho khớp mảng nén — frontend
khỏi sửa, và output nhìn gọn hơn.

Bỏ phương án đó vì nó **mở rộng việc mutate output của model**. Hiện `resolve_citations` chỉ *xoá* marker
ngoài phạm vi; đánh số lại là *viết lại* nội dung, và sẽ đá nhau khi câu trả lời tự nhắc tới số thứ tự
("tin số 3 ở trên"), hoặc khi văn bản có sẵn số trong ngoặc vuông vì lý do khác. Giữ marker nguyên trạng
thì server vẫn là nguồn sự thật duy nhất về `n`, và text model trả về càng ít bị đụng càng dễ suy luận.

Hệ quả: danh sách nguồn dưới bong bóng phải hiện **đúng `n`** (hiện đang tự đánh lại `[1..N]`, nên inline
nói `[12]` mà list nói `[3]`).

### D3 — Khớp theo biên từ, giữ ngưỡng 2 ký tự

Ngưỡng 2 ký tự của 4b.3 là **đúng** và phải giữ (tiếng Việt đơn âm: `mã`, `mở`, `dữ`). Vấn đề không nằm
ở ngưỡng mà ở **cách so khớp**: `t in haystack` là substring, nên `"ai"` khớp trong *email, domain,
training, chain, available, detail, fail, explain*.

Sửa bằng cách so theo biên từ trên cùng bộ token đã tách (`re.findall(r"[0-9a-zA-ZÀ-ỹ]+", …)` cho cả
haystack, rồi so tập hợp), thay vì `in` trên chuỗi thô. Ngưỡng, stopword và cấu trúc hai tầng giữ nguyên.

*Đã cân nhắc:* nâng ngưỡng lên 3 cho token ASCII và giữ 2 cho token có dấu — phức tạp, và vẫn sai với
`"ML"`, `"OS"`, `"Go"`. So theo từ giải đúng gốc vấn đề.

### D4 — Test phải cắt qua ranh giới, không chỉ đứng hai bên

Bài học cụ thể: `test_resolve_citations_maps_markers_in_order` khẳng định `[2]→B, [1]→A` — **đúng ở
backend**, và chính ca đó làm widget trỏ sai cả hai. Test xanh, sản phẩm sai. Test một bên của ranh giới
không bảo vệ được ranh giới.

Cần một test dựng answer + mapping ở backend, chạy qua logic render của widget, và khẳng định **mọi
marker trỏ đúng insight** — với các dãy marker: liền từ 1, đơn lẻ `[2]`, có lỗ hổng, đảo thứ tự, cách
quãng xa. Repo hiện **chưa có test frontend nào**, nên đây cũng là lần đầu dựng.

### D5 — Bỏ tham số chết thay vì để dành

`list_for_chat(topics, roles, keyword)` — 3 tham số, ~15 dòng SQL, không caller nào dùng. Sinh ra vì task
1.7 yêu cầu, rồi D3 chọn nhét cả index nên không cần lọc. Xoá; cần lại thì `git` còn đó.

## Risks / Trade-offs

- **[Sửa `_relevance` có thể đổi thứ hạng, kéo theo đổi recall]** → Chạy lại bộ đo recall 4b.2 trước/sau,
  không chỉ bộ 15 câu (bộ 15 câu **vẫn "đạt"** khi recall tụt 42% — nó không phát hiện được loại lỗi này).
- **[Thêm trường vào `Citation` chạm client đang chạy]** → Chỉ *thêm*, không đổi/xoá; client cũ bỏ qua
  trường lạ. Không có consumer nào ngoài widget.
- **[Test frontend đầu tiên kéo theo hạ tầng mới]** → Giữ tối thiểu: chỉ đủ chạy hàm render thuần, không
  dựng bộ test toàn diện cho toàn dashboard.
- **[Sửa docs không có gì cưỡng chế]** → Đây là lần thứ ba `CLAUDE.md` lệch code (sau `ALLOWED_TOPICS`,
  sau `roles` hai taxonomy). Đặt task docs **sau** task code trong cùng change để nội dung viết ra là
  trạng thái đã chạy, không phải trạng thái dự định.

## Migration Plan

1. Backend: thêm `n`, sửa `_relevance`, bỏ param chết + test backend.
2. Frontend: sửa `renderAnswer` + danh sách nguồn + test ranh giới.
3. Đo lại recall, đối chiếu 4b.2.
4. Docs (sau cùng, chép lại trạng thái thật).

Rollback: không migration, không đổi dữ liệu — revert commit là đủ.

## Quyết định đã chốt (22/07/2026)

- Danh sách nguồn dưới bong bóng hiện **`[3][7][12]` — khớp marker inline**, không đánh số lại thành
  `[1][2][3]`. Bản đánh số lại nhìn gọn hơn nhưng tạo **hệ quy chiếu thứ hai** cho `n`, đúng thứ vừa
  gây ra lỗi này. Trung thực thắng đẹp mắt ở chỗ đã từng vỡ.
- **Có** log khi model phát ra marker không liền mạch (mức DEBUG/INFO, không WARNING). Nó là tín hiệu
  sớm cho việc xếp hạng đang đặt tin lệch vào top — rẻ, và biến thứ hiện đang vô hình thành đo được.
  Sau khi sửa, marker nhảy cóc **không còn gây hỏng**, nên đây thuần là quan sát, không phải cảnh báo lỗi.
