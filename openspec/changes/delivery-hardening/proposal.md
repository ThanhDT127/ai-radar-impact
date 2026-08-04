# Proposal: delivery-hardening

**Phase áp dụng:** Phase 1 (củng cố M7 Delivery — vá độ bền, không đổi hành vi bản tin).

## Why

Review `refactor-telegram-to-gmail-transport` (archive 21/07) cho thấy phần chọn tin, render và chống
trùng đều chắc — 26 test phủ cả cadence guard, `--force`, "gửi lỗi thì không ghi log", "tin bị cap vẫn
cạnh tranh kỳ sau"; toàn bộ điểm nội suy HTML đều qua `escape()` nên không có injection từ RSS. Nợ còn
lại nằm ở **vòng đời kết nối và khả năng quan sát**, không ở logic nghiệp vụ:

1. **`EmailAdapter` là singleton module-level giữ state đổi được.** `ChannelRegistry.register(EmailAdapter())`
   (`channels/email.py:98`) tạo **một** instance dùng chung cho cả tiến trình, mà instance đó giữ
   `self._client`. Hai lượt gửi chồng nhau — cron `mon,thu` bắn đúng lúc đang chạy tay
   `run_delivery --send` — sẽ dùng chung một kết nối SMTP, và `close()` của lượt này giật kết nối khỏi
   tay lượt kia. Tuần tự thì an toàn tuyệt đối; nhưng "chạy tay gần giờ cron" đúng là thao tác đã làm
   hôm 21/07 khi phát hiện nhu cầu `sent_within()`.
2. **Rò socket khi gửi lỗi.** Nhánh `except` đặt `self._client = None` mà **không** `quit()` — kết nối
   hỏng bị bỏ rơi thay vì đóng. Với job 2 lần/tuần thì nhẹ, nhưng nó biến mọi lỗi SMTP thành một socket
   treo cho tới khi GC dọn.
3. **`skipped` gộp hai nghĩa trái ngược.** `run_brief` đếm chung "bị chặn bởi cadence guard" (bình
   thường, đúng thiết kế) và "không có tin nào để gửi" (dấu hiệu pipeline đói tin hoặc lọc role sai).
   Nhìn số `skipped=2` không biết hệ thống đang khoẻ hay đang hỏng — mà đây là kênh push duy nhất tới
   người dùng thật.
4. **`per_role = max_per_role or settings...`** — truyền `0` (nghĩa là "không lấy tin nào") âm thầm rơi
   về mặc định `2`. Cần `is None`. Chưa cắn ai vì test luôn truyền số dương, nhưng nó là bẫy đặt sẵn.
5. `datetime.utcnow()` (deprecated từ Python 3.12) trong `run_brief`.

Không cái nào đang gây thiệt hại đo được. Gom một mẻ vì chúng cùng một vùng file và cùng một loại rủi
ro: **hỏng lúc vận hành bất thường, không hỏng lúc test**.

## What Changes

- **Adapter theo từng lượt gửi thay vì singleton toàn tiến trình**: registry cấp *factory* (hoặc engine
  tự dựng adapter cho mỗi `run_brief`), để state kết nối không bị chia sẻ giữa hai lượt chạy song song.
  Giữ nguyên interface `ChannelAdapter` và hook `open()`/`close()`.
- **`close()` đúng cách khi lỗi**: cố `quit()` rồi mới bỏ tham chiếu, nuốt lỗi đóng để không che lỗi gửi.
- **Tách counter**: `skipped_cadence` (bị chốt chặn chu kỳ) và `skipped_empty` (không có tin) báo cáo
  riêng trong log và giá trị trả về của `run_brief`.
- **`is None` thay cho `or`** ở `select_for_subscriber` cho cả `max_per_role` và `max_per_email`.
- **`datetime.now(timezone.utc)`** thay `utcnow()`.

## Capabilities

### New Capabilities
_(không có)_

### Modified Capabilities
- `gmail-transport`: vòng đời kết nối SMTP SHALL không chia sẻ state giữa các lượt gửi đồng thời; đóng
  kết nối SHALL luôn giải phóng socket kể cả khi gửi lỗi.
- `delivery-engine`: kết quả một kỳ SHALL phân biệt "bỏ qua vì chốt chặn chu kỳ" với "bỏ qua vì không
  có tin".

## Non-goals

- **Không** đổi luật chọn tin, xếp hạng, trần `DELIVERY_MAX_ITEMS_PER_*`, hay nhịp `mon,thu`.
- **Không** đổi template email, subject, hay nội dung hiển thị.
- **Không** động tới hồ sơ spam (domain gửi, `DASHBOARD_BASE_URL`/`PUBLIC_API_BASE_URL` công khai) —
  đó là việc hạ tầng đã ghi rõ ở gotcha `CLAUDE.md`, không sửa được bằng code.
- **Không** thêm hàng đợi, retry nền, hay gửi song song nhiều người nhận.

## Dependencies

- `refactor-telegram-to-gmail-transport` (đã archive 21/07) — toàn bộ code bị sửa thuộc change đó.

## Impact

- **Backend**: `channels/base.py` (đăng ký factory), `channels/email.py` (`open`/`close`/`send`),
  `services/delivery_engine.py` (`select_for_subscriber`, `run_brief`), `scripts/run_delivery.py`
  (đọc counter mới), tests.
- **Không** migration, không đổi config env, không đổi API.
