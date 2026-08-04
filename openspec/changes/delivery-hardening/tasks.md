# Tasks: delivery-hardening

> Rủi ro chính của change này là **gây hồi quy cho thứ đang chạy tốt**. 26 test hiện có phải xanh
> nguyên vẹn sau mỗi section; không đụng logic chọn tin, xếp hạng, hay render.

## 1. Vòng đời adapter

- [ ] 1.1 Đổi `ChannelRegistry` sang cấp **factory**: `register(EmailAdapter)` (class, không phải instance) + `create(channel_type)` trả instance mới. Giữ nguyên interface `ChannelAdapter` và hook `open()`/`close()`. **DoD:** hai lần `create("email")` trả hai object khác nhau.
- [ ] 1.2 Sửa các điểm lấy adapter (`scheduler.py`, `scripts/run_delivery.py`) để dựng adapter mới cho mỗi lượt `run_brief`. **DoD:** grep không còn chỗ nào giữ adapter ở phạm vi module.
- [ ] 1.3 Test: adapter không sống sót qua lượt gửi — sau `run_brief`, instance dùng trong lượt đó không được tái sử dụng ở lượt kế. **DoD:** test khẳng định bằng tính chất kiểm được, không mô phỏng đồng thời thật (dễ flaky — xem design D1).

## 2. Giải phóng kết nối

- [ ] 2.1 Nhánh `except` của `EmailAdapter.send()` gọi `close()` thay vì đặt `self._client = None` trực tiếp — dùng lại đường đóng đã có `try/except/finally` đúng chuẩn, không viết logic đóng thứ hai. **DoD:** gửi lỗi → `quit()` được gọi (hoặc đã thử và nuốt lỗi), `self._client` về `None`.
- [ ] 2.2 Test: SMTP raise giữa chừng → kết nối được đóng, người nhận còn lại vẫn gửi được, `delivery_log` không ghi cho người lỗi. **DoD:** test cũ `test_send_failure_is_not_logged` vẫn xanh, cộng khẳng định mới về việc đóng.

## 3. Khả năng quan sát

- [ ] 3.1 `run_brief` trả `{sent, failed, skipped_cadence, skipped_empty}` thay cho `skipped` gộp. **KHÔNG** giữ khoá `skipped` cũ song song (hai nguồn sự thật). **DoD:** không còn chỗ nào cộng hai loại vào một biến.
- [ ] 3.2 Dòng log cuối kỳ nêu đủ 4 con số; nhánh "không có tin" log kèm **vai trò** của người nhận, để phân biệt "vai trò chưa có dữ liệu" (ca đã biết: `Data Analyst`, `Người dùng phổ thông`) với "pipeline đói tin". Mức INFO, không WARNING — tránh nhiễu mỗi kỳ (design Open Question).
- [ ] 3.3 Cập nhật `scripts/run_delivery.py` đọc counter mới; `--dry-run` in đủ 4 con số. **DoD:** chạy `--dry-run` thấy rõ ai bị bỏ qua vì lý do gì.
- [ ] 3.4 Cập nhật test đang đọc `skipped`. **DoD:** toàn bộ test delivery xanh.

## 4. Vụn

- [ ] 4.1 `select_for_subscriber`: `is None` thay `or` cho cả `max_per_role` và `max_per_email`. **DoD:** truyền `0` → không chọn tin nào, không rơi về mặc định 2.
- [ ] 4.2 Test cho ca trần bằng `0` (cả hai tham số).
- [ ] 4.3 `datetime.now(timezone.utc)` thay `datetime.utcnow()` trong `run_brief`; kiểm tra so sánh với `Insight.published_at` (naive) vẫn đúng — chỉnh cho khớp quy ước hiện hành của repo, **không** đổi quy ước.

## 5. Kiểm chứng

- [ ] 5.1 Chạy toàn bộ `pytest` — 26 test delivery cũ xanh nguyên vẹn, không sửa nội dung khẳng định của chúng ngoài phần counter ở 3.4. **DoD:** liệt kê test nào phải sửa và vì sao.
- [ ] 5.2 `run_delivery --dry-run` trên dữ liệu thật; đối chiếu số tin/vai trò với kỳ gần nhất để chắc không đổi hành vi chọn tin. **DoD:** danh sách tin chọn ra giống hệt trước khi sửa.
- [ ] 5.3 `run_delivery --send --force` tới một hộp thư thật; xác nhận email tới nơi, đủ text + HTML, link hủy nhận chạy được. **DoD:** nhận được email, bấm hủy nhận → `active=false`.
