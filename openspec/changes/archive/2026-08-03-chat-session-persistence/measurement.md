# Đo & kiểm chứng — `chat-session-persistence`

## Trạng thái

| Hạng mục | Trạng thái |
|---|---|
| Test tự động (task 5.1–5.10) | ✅ đã chạy |
| `tsc --noEmit` + `npm run build` | ✅ sạch |
| Kiểm chứng trên trình duyệt thật (task 6.1–6.3) | ✅ **người dùng tự chạy, đạt** — 03/08/2026 |

Phiên implement không có công cụ điều khiển trình duyệt, mà 6.1–6.3 đo đúng thứ chỉ tồn tại
trong trình duyệt thật (F5, hai tab, ngắt giữa luồng SSE). Các bước được viết ra ở mục cuối và
**người dùng chạy tay, xác nhận đạt kỳ vọng** trước khi archive. Không có số đo định lượng cho
ba ca này — chúng là kiểm chứng hành vi có/không, không phải phép đo.

## Đã đo tự động

```
npx vitest run          → 8 file, 68 test, PASS
npx tsc --noEmit        → sạch
npm run build           → 385.87 kB (gzip 121.82 kB)
```

Phân rã test mới:

| File | Số test | Cái được khoá |
|---|---|---|
| `chatSession.test.ts` | 12 | round-trip giữ `citations[].insight_id`; lệch `v` / JSON hỏng / sai hình dạng ⇒ `null`; storage ném lỗi ở cả 3 thao tác ⇒ không throw; blob không chứa `searchSuggestions`; cắt còn 50 message |
| `ChatWidget.persistence.test.tsx` | 7 | khôi phục sau unmount→mount (DOM **và** payload lượt kế); citation sống sót; **bất biến A**; text tạm không vào storage; lượt gián đoạn + Thử lại; không nhân đôi bong bóng; "Cuộc trò chuyện mới"; storage trống ⇒ luồng độc lập |

### Xác minh test THẬT SỰ bắt lỗi (không phải xanh rỗng)

Tạm khôi phục `retryLast()` bản cũ rồi chạy lại:

```
× Thử lại gửi lại đúng một lượt — không nhân đôi bong bóng câu hỏi
  AssertionError: expected [ <div/>, <div/> ] to have a length of 1 but got 2
  Tests  1 failed | 6 passed (7)
```

⇒ Bug nhân đôi câu hỏi là **thật** và test là lưới thật cho nó. Đã hoàn nguyên bản sửa.

## Phát hiện ngoài dự kiến: 24 test cũ đỏ vì rò trạng thái

Lần chạy toàn bộ đầu tiên sau khi nối persistence: **24 failed / 44 passed**.

Nguyên nhân: các test trong cùng một file dùng chung một môi trường jsdom, nên
`sessionStorage` mang trạng thái từ test trước sang test sau. Widget khôi phục `open: true` và
không còn nút `Mở trợ lý hỏi đáp` để bấm ⇒ `getByRole` ném lỗi ở helper `openWidget`.

Chữa ở **`src/test/setup.ts`** — `beforeEach` xoá `sessionStorage` cho mọi test file, tức "mỗi
test là một tab mới". **Không sửa một dòng nào trong các test file cũ** (task 5.10 cấm việc đó:
test cũ đỏ phải được đọc là hồi quy thật, không phải cái để chỉnh cho xanh). Sau khi chữa:
8 file / 68 test PASS.

## Kiểm chứng tay trên trình duyệt — ĐÃ CHẠY, ĐẠT (03/08/2026)

Stack lúc chạy: `backend` up, `db` healthy, vite 5173 trả 200. Các bước đã thực hiện:

**6.1 — F5 giữa hội thoại**
1. Mở `http://localhost:5173`, mở widget, hỏi 3 lượt sao cho có câu trả lời kèm citation.
2. Mở một trang chi tiết insight để có chip working set.
3. F5.
4. Kỳ vọng: panel mở lại, đủ 3 lượt, chip working set còn, câu hỏi tiếp theo vẫn ghim được tin
   đã bàn (hỏi lại về một tin đã trích ở lượt trước và xem bot có dữ liệu của nó không).

**6.2 — Hai tab**
1. Mở dashboard ở hai tab, hỏi câu khác nhau ở mỗi tab.
2. Kỳ vọng: không tab nào thấy luồng của tab kia; đóng một tab không ảnh hưởng tab còn lại.

**6.3 — F5 giữa lúc câu trả lời đang chảy**
1. Gửi một câu hỏi nặng (câu so sánh/tổng hợp) rồi F5 ngay khi token bắt đầu về.
2. Kỳ vọng: thấy bong bóng *"Câu trả lời bị gián đoạn vì trang được tải lại."* + nút Thử lại;
   bấm Thử lại chạy được và chỉ có **một** bong bóng câu hỏi.
3. Kiểm bất biến D5 của `chat-streaming-sse` không bị change này phá:
   ```bash
   docker compose exec db psql -U radar -d ai_radar \
     -c "SELECT mode, model_calls, latency_ms, created_at FROM chat_logs ORDER BY created_at DESC LIMIT 3;"
   ```
   Kỳ vọng: lượt bị bỏ dở **vẫn có dòng** — client ngắt không được cắt ngang `finally` ghi log.
