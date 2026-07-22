## Context

`refactor-telegram-to-gmail-transport` (archive 21/07/2026) đã chuyển kênh push từ Telegram sang email
và đi kèm 26 test phủ chọn tin, render, cadence guard, `--force`, "gửi lỗi thì không ghi log", "tin bị
cap vẫn cạnh tranh kỳ sau". Rà lại toàn bộ điểm nội suy HTML trong `email_templates.py` — title, badge,
signal, so_what, why_it_matters, summary, khuyến nghị, risks, role — tất cả đều qua `escape()`, không có
đường injection từ nội dung RSS.

Nợ còn lại thuộc loại **hỏng lúc vận hành bất thường, không hỏng lúc test**:

```
channels/email.py:98   ChannelRegistry.register(EmailAdapter())
                       └─ MỘT instance cho cả tiến trình, giữ self._client

  cron mon,thu ──┐
                 ├──▶ cùng một EmailAdapter ──▶ cùng một kết nối SMTP
  run_delivery ──┘         close() của bên này giật kết nối của bên kia
```

Cộng thêm: nhánh lỗi bỏ `self._client` mà không `quit()` (rò socket); `run_brief` gộp "bị chốt chặn chu
kỳ" và "không có tin" vào cùng biến `skipped`; `per_role = max_per_role or settings...` nuốt giá trị `0`;
`datetime.utcnow()` đã deprecated.

**Module ảnh hưởng:** M7 (Delivery).
**API endpoints:** không thêm, không sửa. `GET/POST /api/v1/unsubscribe` và CRUD `/api/v1/subscribers`
giữ nguyên.
**Bảng DB:** không đụng `subscribers`/`delivery_log`, không migration.
**AI/LLM:** không liên quan — delivery thuần template, **không** gọi Gemini (giữ nguyên ràng buộc đó).
**n8n:** không dùng; delivery chạy trong backend qua APScheduler.

## Goals / Non-Goals

**Goals:**
- Hai lượt gửi chạy chồng nhau không phá kết nối của nhau.
- Mỗi lỗi SMTP đóng sạch socket của nó.
- Đọc log một kỳ là biết hệ thống đang khoẻ hay đang đói tin.

**Non-Goals:**
- Không đổi luật chọn tin, xếp hạng, trần, nhịp `mon,thu`, hay nội dung email.
- Không chạm hồ sơ spam (domain gửi, URL công khai) — việc hạ tầng, không sửa được bằng code.
- Không thêm hàng đợi, retry nền, hay gửi song song.

## Decisions

### D1 — Adapter theo từng lượt gửi, registry cấp factory

Hiện `ChannelRegistry.register(EmailAdapter())` đăng ký một **instance**. Với adapter không giữ state
(Telegram cũ chỉ gọi HTTP mỗi lần) thì vô hại; `EmailAdapter` giữ `self._client` nên nó thành state
dùng chung toàn tiến trình.

Đổi registry sang cấp **factory** (`register(EmailAdapter)` + `create(channel_type)`), engine dựng adapter
riêng cho mỗi `run_brief`. Vòng đời khớp đúng phạm vi mà `open()`/`close()` vốn định nghĩa: một kết nối
cho một lượt gửi.

*Đã cân nhắc:* (a) khoá `asyncio.Lock` quanh lượt gửi — biến lỗi thành chờ, và không giúp gì khi hai
tiến trình khác nhau (cron trong container vs `docker compose exec` chạy tay) vì lock không xuyên tiến
trình; (b) giữ singleton, thêm đếm tham chiếu cho `open`/`close` — phức tạp hơn hẳn phương án chỉ đơn
giản là *đừng chia sẻ*.

Lưu ý: hai **tiến trình** riêng vẫn mở hai kết nối SMTP riêng — điều đó vốn đã đúng và không đổi. D1
chỉ sửa phần chia sẻ trong **cùng** tiến trình.

### D2 — `close()` luôn giải phóng socket

Nhánh `except` của `send()` hiện đặt `self._client = None` thẳng. Đổi thành gọi `close()` (vốn đã có
`try/except/finally` đúng chuẩn: cố `quit()`, nuốt lỗi đóng, luôn xoá tham chiếu). Không viết logic đóng
lần thứ hai — dùng lại đường đã có.

### D3 — Tách counter theo nguyên nhân, không theo kết quả

`skipped` hiện trộn hai tín hiệu ngược nhau:

| Nguyên nhân | Ý nghĩa vận hành |
|---|---|
| Chốt chặn chu kỳ (`sent_within`) | Bình thường — đúng thiết kế, đang chống gửi thừa |
| Không có tin khớp | **Đáng ngờ** — pipeline đói tin, hoặc vai trò subscriber lệch taxonomy |

Trả `{sent, failed, skipped_cadence, skipped_empty}`. Đây là kênh push **duy nhất** tới người dùng thật;
một con số không phân biệt được "im lặng vì đúng" với "im lặng vì hỏng" là một điểm mù không đáng có.

*Đã cân nhắc:* giữ `skipped` tổng + log chi tiết riêng — người đọc log vẫn phải cộng tay để đối chiếu.

### D4 — `is None` thay `or` cho mọi tham số trần

`max_per_role or settings.…` biến `0` thành mặc định. `0` là giá trị hợp lệ ("không lấy tin nào từ vai
trò này") và là thứ một test hoặc một lần chỉnh cấu hình sẽ dùng. Sửa cả `max_per_role` và
`max_per_email`.

## Risks / Trade-offs

- **[Đổi registry từ instance sang factory chạm `ChannelAdapter` interface]** → Chỉ có **một** adapter
  đang tồn tại (`EmailAdapter`); Telegram đã gỡ sạch 21/07. Bề mặt hồi quy nhỏ, nhưng phải sửa cả
  `scheduler` và `run_delivery.py` — nơi lấy adapter theo `DELIVERY_CHANNEL`.
- **[Đổi kiểu trả về của `run_brief`]** → `run_delivery.py` và test đang đọc `skipped`. Sửa đồng bộ;
  không giữ khoá cũ để tránh hai nguồn sự thật.
- **[Không có test cho ca đồng thời]** → Viết test mô phỏng hai `run_brief` chồng nhau là khó và dễ
  flaky. Thay vào đó khẳng định tính chất **kiểm được**: hai lần `create()` trả hai instance khác nhau,
  và instance không sống sót qua lượt gửi.
- **[Tất cả đều là nợ tiềm ẩn, không cái nào đang cháy]** → Rủi ro thật của change này là *gây hồi quy
  cho thứ đang chạy tốt*. Vì vậy 26 test hiện có phải xanh nguyên vẹn, và không đụng gì tới logic chọn
  tin / render.

## Migration Plan

1. `channels/base.py` sang factory + `channels/email.py` đăng ký class.
2. Điểm lấy adapter (`scheduler`, `run_delivery.py`) dựng adapter mới mỗi lượt.
3. `close()` trong nhánh lỗi; `is None`; tách counter; `datetime.now(timezone.utc)`.
4. Chạy `run_delivery --dry-run` rồi `--send --force` trên dữ liệu thật, đối chiếu với kỳ trước.

Rollback: không migration, không đổi dữ liệu hay config — revert commit là đủ.

## Quyết định đã chốt (22/07/2026)

- `skipped_empty > 0` cho subscriber **active** log ở mức **INFO kèm tên vai trò**, không WARNING. Ca
  phổ biến nhất là vai trò chưa có tin nào (`Data Analyst`, `Người dùng phổ thông` — đã biết 0 entry),
  nên WARNING mỗi kỳ sẽ thành nhiễu và làm mòn giá trị cảnh báo thật. Tên vai trò trong log là thứ phân
  biệt "vai trò chưa có dữ liệu" với "pipeline đói tin".
