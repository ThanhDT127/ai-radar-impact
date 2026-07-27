# Xác minh tay — chat-streaming-sse (27/07/2026)

Đo trên stack thật (`docker compose`, Vertex AI, corpus production), gọi qua HTTP như client
thật. Không phải mock.

## 5.1 — Chuỗi status → token → citations (mode A)

Câu: *"Tuần này có tin gì đáng chú ý cho vai trò Security? Nêu rủi ro và khuyến nghị."*

```
HTTP 200 text/event-stream | x-accel-buffering: no
[ 0.65s] status: Đang tìm trong hệ thống…
[ 0.97s] status: Đang soạn câu trả lời…
[34.91s] token ĐẦU TIÊN: 'Dưới đây là 5 tin đáng chú ý nhất'
[36.14s] commit: mode=global citations=5
tổng 6 token, TTFT 34,9s, tổng 36,2s
```

**Số quan trọng nhất của cả change: TTFT 34,9s trên câu nặng.** Toàn bộ khoảng đó là
thinking — chưa có token nào để stream. Streaming KHÔNG rút ngắn nó; thứ lấp nó là hai dòng
status đến ở giây 0,65 và 0,97. Đây đúng là giới hạn mà design D3 đã nói trước, và số đo thật
còn nặng hơn dự đoán 5–15s trong design.

Đo thêm ba câu khác: TTFT **8,0s / 12,9s / 36,7s**. Câu mode B đơn giản: **2,2s**.

Vertex gộp chunk khá thô — chỉ 6 sự kiện `token` cho một câu ~900 ký tự, chảy trong ~1,2s.
Nên phần "chữ chảy dần" mượt ít hơn kỳ vọng; giá trị thực tế của change nằm ở **status lấp
khoảng thinking**, không phải ở hiệu ứng gõ chữ.

## 5.2 — Trạng thái chốt trùng bản blocking

Chạy cùng câu hỏi qua `/chat` và `/chat/stream`:

| Câu hỏi | mode khớp | citations trùng |
|---|---|---|
| "Có tin gì về mô hình mã nguồn mở không?" | ✅ global | 4/5 |
| "Tuần này có gì cho vai trò Dev?" | ✅ global | 5/5 |
| "Có tin nào về sa thải nhân sự ngành công nghệ không?" | ✅ global | 0/0 (cả hai từ chối, 44 ký tự y hệt) |

Lệch 4/5 ở câu đầu là **nhiễu của model** (`temperature=0.2`, hai lần gọi khác nhau), không
phải lệch pipeline: hai lối ra dùng chung đúng một đoạn code retrieval/xếp hạng/grounding.

**Ca fail‑closed thật không ép được live**: câu về chủ đề vắng làm model trả lời đúng dạng
"không tìm thấy" — nhánh HỢP LỆ, không phải nhánh fail‑closed. Nhánh fail‑closed (khẳng định
mà không marker) hiếm theo thiết kế; nó được khoá bằng test hai phía:
`tests/test_chat_streaming.py::test_fail_closed_duoi_streaming_hoan_sach_text_ungrounded`
(commit hoán sạch text ungrounded) và `ChatWidget.streaming.test.tsx` (widget thay bong bóng).

### Ghi chú: `commit.answer` gần như LUÔN khác text đã stream

Không phải chỉ ở ca fail‑closed. `resolve_citations` chuẩn hoá khoảng trắng
(`re.sub(r"[ \t]{2,}", " ")`), nên `*   Lỗ hổng…` của model thành `* Lỗ hổng…`. Diff trên một
câu trả lời 5 gạch đầu dòng: **khác đúng khoảng trắng sau dấu `*`, nội dung y nguyên**.

Hệ quả nhìn thấy được: bong bóng thụt lề nhẹ một lần khi `commit` về. Chấp nhận — sửa nó
nghĩa là đổi `resolve_citations`, tức đổi luôn output của endpoint blocking và baseline của
`chat-eval-quality-gate` (④).

## 5.3 — Ngắt giữa luồng

Đóng kết nối ngay sau token đầu tiên (giây 9,68 của một câu mode A):

```
chat_logs trước: ('meta', 0, 0, 0)
chat_logs sau:   ('global', 1, 2, 9847)
```

Budget **vẫn được ghi** đúng 1 lượt đã tốn tiền, không lỗi phía server. Đây là D5 chạy thật.

## Các mốc status đo được theo chế độ

| Chế độ | Chuỗi status | Lượt gọi |
|---|---|---|
| A (toàn cục) | Đang tìm trong hệ thống… → Đang soạn câu trả lời… | 1 |
| B (trong bài) | Đang đọc bài đang xem… → Đang soạn câu trả lời… | 1 |
| Mở rộng | Đang đọc bài… → Đang soạn… → **Bài đang xem không đề cập — đang tìm trên toàn hệ thống…** → Đang soạn… | 2 |
| meta (chào) | *(không có status, không token)* — 1 `commit` ở giây 0,05 | 0 |

## Lỗi thật do streaming đẻ ra, đã sửa trong change này

Lượt đầu của chế độ B phát sentinel thành **đúng một token** `[[NGOÀI_PHẠM_VI_BÀI]]`, và bản
đầu tiên của code phát thẳng nó ra client — người dùng nhìn thấy chuỗi đó nhấp nháy trước khi
lượt mở rộng ghi đè. Bản blocking miễn nhiễm vì chỉ nhìn câu hoàn chỉnh. Sửa bằng
`_SentinelGate` (giữ token đầu chừng nào nó còn có thể là tiền tố của sentinel). Đo lại sau
khi sửa: chuỗi status mở rộng đúng như bảng trên, 0 mảnh sentinel lọt ra.
