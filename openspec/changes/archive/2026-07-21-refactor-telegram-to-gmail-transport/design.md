## Context

Transport Telegram bị gỡ 21/07/2026. Còn lại lớp channel-neutral hoạt động tốt nhưng **không có
adapter nào**: `scheduler.py:28,58,68` gọi `ChannelRegistry.get("email")` → `channels/base.py:56-60`
raise `ValueError`. Ngoài ra `main.py:32` đang hardcode `include_delivery=False` nên job delivery
chưa từng được đăng ký, và `settings.delivery_enabled` (`config.py:59`) là config chết.

Phần tái dùng được nguyên vẹn: `ChannelAdapter`/`ChannelRegistry`, `delivery_log` idempotency
(`ON CONFLICT DO NOTHING`), `display_title()`/`shorten()` (`delivery_engine.py:49-72` — luật tiêu đề
khớp dashboard), và bộ lọc theo vai trò `alert_roles_match`/`matched_alert_roles` (`:88-120`) — chính
là logic "ảnh hưởng cao theo vai trò" mà bản tin mới cần.

Hiện trạng dữ liệu (đã kiểm): alembic head `009`; `subscribers` có 1 bản ghi test; `delivery_log`
rỗng và **không có FK** tới `subscribers` → đổi schema gần như không tốn gì.

**Module ảnh hưởng**: M7 Delivery (chính), M6 Dashboard (tab quản lý), M10 Admin/Config (env mới).

## Goals / Non-Goals

**Goals:**
- Nối lại kênh phân phối bằng Gmail, giấu sau `EmailAdapter` để đổi nhà cung cấp sau không phải viết lại engine.
- Đổi định danh người nhận sang email, quản lý được ngay trên dashboard.
- Nhịp gửi Thứ Hai + Thứ Năm, mỗi email chỉ chứa tin nổi bật theo vai trò người nhận.

**Non-Goals:**
- Self-serve đăng ký, magic-link, `verified_at`, auth/RBAC trên tab quản lý.
- Bảng `delivery_batch`, dashboard thống kê delivery.
- OAuth2/Gmail API/service account; n8n; Teams.

## Decisions

### D1 — SMTP + App Password, không OAuth2, không service account
Quy mô thực tế vài chục email/tháng nên mọi hạn mức đều thừa; chọn phương án setup rẻ nhất và nhiều
đường lùi nhất (đổi `SMTP_HOST` sang SendGrid/SES là xong).

- *OAuth2 refresh token*: loại — app ở trạng thái "Testing" thì refresh token hết hạn sau 7 ngày,
  phải publish app mới ổn định; client Google là sync nên phải bọc thread.
- *Service account + domain-wide delegation*: loại — đòi Google Workspace + quyền Super Admin, và
  **không impersonate được `@gmail.com`**.
- **Không tái dùng `secrets/sa-key.json`**: đã kiểm, đó là GCP service account thường
  (`type=service_account`, không gắn Workspace nào), mount `:ro` cho Vertex. Thêm scope `gmail.send`
  vào cùng key = key rò rỉ thì mất cả quota AI lẫn quyền gửi mail dưới danh nghĩa công ty.

### D2 — Gửi thẳng từ backend, KHÔNG qua n8n
Project context đặt n8n làm nơi gửi email digest. Change này đi khác: n8n không có trong
`docker-compose.yml` hiện tại, và logic chọn người nhận / chống gửi trùng / render đã nằm sẵn trong
`delivery_engine.py`. Đưa sang n8n nghĩa là thêm một service, một nơi giữ secret, và tách đôi logic
đang liền mạch. Với team 1 người, `aiosmtplib` trong chính backend là lựa chọn đơn giản hơn.

### D3 — `aiosmtplib` + hook `open()/close()` trên `ChannelAdapter`
`ChannelAdapter.send()` (`base.py:41`) là per-message, mỗi email sẽ mở một kết nối SMTP mới → chậm và
dễ bị Google throttle. Thêm hai hook **mặc định no-op** `async def open(self)` / `async def close(self)`
để engine mở kết nối một lần cho cả run. Thay đổi additive, adapter khác không ảnh hưởng.
`smtplib` + `asyncio.to_thread` là phương án 0-dependency nhưng lệch stack async thuần của repo.

### D4 — Nhịp: cron `day_of_week="mon,thu"`, idempotency dựa vào `delivery_log`
- *`IntervalTrigger(days=3)`*: loại — APScheduler dùng memory jobstore, mỗi lần restart mốc kế tiếp
  tính lại từ lúc start ⇒ nhịp trôi; restart nhiều có thể không bao giờ gửi.
- *cron `day='*/3'`*: loại — là ngày-trong-tháng, chạy 1,4,…,31 rồi nhảy mùng 1 (cách nhau 1 ngày).
- *Bảng `delivery_batch` làm guard*: hoãn — thay bằng truy vấn `sent_within()` trên chính
  `delivery_log` (xem D10). `delivery_batch` chỉ còn thêm giá trị quan sát (phân biệt `skipped_empty`
  vs `failed`), để change sau.

Mon/Thu thay vì đúng 3 ngày: khoảng cách 3–4 ngày nhưng luôn rơi ngày làm việc — nhịp 3 ngày cứng sẽ
có lần rơi Chủ nhật, email nằm chết tới thứ Hai. Lookback 108h (4.5 ngày) > khoảng cách lớn nhất (4
ngày) + đệm 12h, để job trễ vài giờ không làm mất tin.

### D5 — `delivery_log.subscriber_id UUID FK`, không lưu chuỗi email
Người nhận đổi email vẫn giữ nguyên lịch sử gửi, và không nhân bản PII vào bảng log.

### D8 — Chọn tin bằng xếp hạng + trần cứng, không lọc theo ngưỡng
Đo trên dữ liệu thật (cửa sổ 108h): vai trò `Security` có **26** insight đạt
`recommendations[role].urgency = "high"`, `AI Engineer` 13, trong khi `Data Scientist` có **0** (dù
khớp 29 tin) và `Data Engineer` chỉ 1. Lọc theo ngưỡng `high` vừa làm ngập người này vừa bỏ đói người
kia — cùng một luật cho hai kết cục đều sai.

Vì vậy: xếp hạng mọi tin khớp vai trò rồi lấy **2 tin/vai trò, trần 3 tin/email**, sắp từ khẩn cấp
cao xuống thấp. `urgency` theo vai trò trở thành tiêu chí xếp hạng số 1 thay vì cửa vào. Mọi người
nhận có tin khớp vai trò đều nhận được email, và không ai nhận quá 3 tin.

Đổi lại, trần thấp buộc mỗi tin phải **đủ chi tiết để đọc ngay trong email** (đọc dashboard là tuỳ
chọn, không bắt buộc): tiêu đề đầy đủ không cắt + badge + `signal` + `so_what` + `why_it_matters` +
`summary_medium` + khuyến nghị đúng vai trò + `risks` + link. Kiểm tra độ phủ trường trên 106 insight:
`signal`/`so_what`/`why_it_matters`/`summary_medium` **106/106**, `risks` 91/106,
`practical_indicators` 106/106 → đủ dữ liệu, không sợ card rỗng. Ước tính ~250 từ/tin, 3 tin ≈ 3 phút đọc.

### D9 — `delivery_log` chỉ ghi tin đã gửi, KHÔNG ghi tin bị loại vì trần
Luật cũ của digest ("ghi log cả phần vượt cap, tin dư không dồn sang kỳ sau") sinh ra khi digest gửi
**mọi** tin khớp vai trò, cap 15 chỉ giới hạn hiển thị. Với trần 3 tin/email, giữ luật đó sẽ chôn
vĩnh viễn hàng chục tin chưa ai đọc ngay trong kỳ đầu.

Nên: log = "đã tới tay người này". Tin bị loại vì trần còn quyền cạnh tranh ở kỳ kế tiếp nếu vẫn nằm
trong lookback 108h. Đánh đổi: một tin đứng hạng 4 có thể lại thua ở kỳ sau và trôi khỏi lookback —
chấp nhận được, vì nó vẫn nằm trên dashboard và link "+N tin khác" dẫn tới đó.

### D10 — Chốt chặn chu kỳ `sent_within()`, vì unique constraint KHÔNG đủ
Phát hiện khi chạy thật (21/07): chạy `run_delivery --send` hai lần liên tiếp thì lần hai **gửi thêm
3 tin nữa** cho mỗi người, `delivery_log` tăng từ 9 lên 18 dòng, 0 tin trùng.

Đây là hệ quả trực tiếp của D9: khi chỉ log tin đã gửi, lần chạy thừa sẽ lấy lô xếp hạng kế tiếp —
toàn tin khác nên unique constraint không đụng tới. Lập luận ban đầu ở D4 ("delivery_log unique đã đủ
idempotent nên không cần `delivery_batch`") **đúng với luật cũ và sai sau khi D9 đổi luật** — hai
quyết định mâu thuẫn nhau mà không được rà lại.

Cách chữa rẻ nhất, không thêm bảng: `DeliveryLogRepository.sent_within(subscriber_id, kind, hours)`
đếm log trong `DELIVERY_MIN_GAP_HOURS` giờ gần đây (mặc định **48** — nhỏ hơn khoảng cách hai kỳ 3–4
ngày nên không chặn nhầm). Engine bỏ qua người nhận đã có log gần đây. `--force` bỏ qua chốt này khi
test. So sánh đặt trong SQL bằng `now()` của DB để không lẫn với `datetime.utcnow()` phía Python.

### D6 — Template bằng f-string thuần, không thêm jinja2
Repo chưa có template engine. Module mới `channels/email_templates.py` trả `(subject, text_body,
html_body)` — 0 dependency, unit-test bằng assert chuỗi. HTML phải CSS inline + layout `<table>`
(Gmail/Outlook không hỗ trợ `<style>` ngoài, flex, grid) nên không bê CSS Modules của dashboard sang.

### D7 — `/api/v1/subscribers` không auth ở MVP
Theo yêu cầu "chưa cần phân quyền". Siết sau chỉ tốn một dòng
`dependencies=[Depends(verify_admin_key)]` như `routes/admin.py:19-23`.

### API endpoints
| Method | Path | Ghi chú |
|---|---|---|
| GET | `/api/v1/subscribers` | liệt kê |
| POST | `/api/v1/subscribers` | tạo (email + roles + display_name) |
| PATCH | `/api/v1/subscribers/{id}` | sửa roles / active |
| DELETE | `/api/v1/subscribers/{id}` | xoá |
| GET | `/api/v1/unsubscribe?token=` | trang xác nhận HTML tối giản |
| POST | `/api/v1/unsubscribe?token=` | one-click của Gmail → `active=false` |

### Bảng DB
- `subscribers` **(sửa)**: bỏ `chat_id`; thêm `id UUID PK`, `email VARCHAR(320) UNIQUE`,
  `unsubscribe_token VARCHAR(64) UNIQUE`. Giữ `roles[]`, `display_name`, `active`, timestamps.
- `delivery_log` **(sửa)**: `chat_id BigInteger` → `subscriber_id UUID FK ON DELETE CASCADE`; unique
  đổi thành `(insight_id, subscriber_id, kind)`; `kind` nới `String(10)` → `String(16)`.
- Không thêm bảng mới.

### AI/LLM
Delivery **không gọi LLM** — render thuần template từ field có sẵn của insight. Không có grounding
strategy nào áp dụng. Tiêu chí chọn tin đọc từ field do `AnalyzerService` sinh sẵn.

## Risks / Trade-offs

- **Không auth trên `/api/v1/subscribers`** → ai mở được dashboard cũng thêm được email bất kỳ, tức
  dùng được tài khoản Gmail chung để gửi ra ngoài. *Mitigation*: chỉ chạy nội bộ ở MVP; gắn
  `verify_admin_key` khi mở ra ngoài mạng nội bộ.
- **Rơi vào spam** → *Mitigation*: gửi riêng từng địa chỉ (không BCC), luôn kèm `text/plain`, header
  `List-Unsubscribe` + one-click POST, subject tiếng Việt không viết HOA/không `!!!`; lần đầu nhờ
  người nhận đánh dấu "Không phải spam".
- **Hai vai trò `Data Analyst` và `Người dùng phổ thông` hiện có 0 insight** trong `affected_roles` →
  ai đăng ký sẽ không bao giờ nhận mail. *Mitigation*: MVP hiển thị cảnh báo trên tab; xử lý gốc
  thuộc về prompt, ngoài phạm vi change này.
- **Chưa đo được sản lượng "tin nổi bật mỗi kỳ"** (DB vừa reset) → cap 5/12 có thể lệch.
  *Mitigation*: chạy `run_delivery --dry-run` một kỳ thật trước khi bật gửi.
- **Naive datetime**: `delivery_engine.py:179,244` dùng `datetime.utcnow()` còn `sent_at` dùng
  `func.now()` của DB. Hiện cả hai container đều UTC nên khớp. *Mitigation*: giữ nguyên quy ước, mọi
  so sánh thời gian mới đặt trong SQL.
- **Lộ PII trong log**: `delivery_engine.py:201-207` đang log định danh người nhận → mask email dạng
  `ab***@domain` khi đổi sang email.

## Migration Plan

1. Alembic `010`: thêm cột mới vào `subscribers` → xoá bản ghi test (`chat_id 8805269993`) → đổi PK
   sang `id`, drop `chat_id` → sửa `delivery_log` (`delivery_log` rỗng nên không cần backfill).
   `downgrade()` viết đầy đủ; rollback bằng `alembic downgrade -1`, không drop bảng thủ công.
2. Thêm env vào `.env`/`.env.example`, xoá `TELEGRAM_BOT_TOKEN` còn sót.
3. Xoá `backend/tests/test_bot_router.py` (đang làm gãy pytest collection) trước khi chạy suite.
4. Bật delivery: `main.py` đọc `settings.delivery_enabled`, mặc định **false** — bật thủ công sau khi
   `--dry-run` cho kết quả đúng.
5. Rollback: tắt `DELIVERY_ENABLED`, `alembic downgrade -1`.

## Kết quả kiểm chứng thật (21/07/2026)

Gửi thật qua Gmail SMTP tới hộp thư thật: chọn tin theo vai trò, thứ tự khẩn cấp, trần 3 tin, chống
gửi trùng theo tin, chốt chặn chu kỳ, link hủy nhận — tất cả đúng. Render HTML trên Gmail chấp nhận
được.

**Email rơi vào Spam.** Đây là vấn đề danh tính người gửi, không phải lỗi template, và không sửa được
bằng cách chỉnh CSS hay câu chữ. Ba nguyên nhân theo thứ tự sức nặng:

1. **Người gửi là `@gmail.com` cá nhân.** SPF/DKIM của Google có pass, nhưng không có domain nào đứng
   sau để tích luỹ danh tiếng gửi hàng loạt. Mail dạng bulk từ tài khoản cá nhân là hồ sơ mà bộ lọc
   vốn không tin.
2. **Mọi link trong email trỏ `localhost`** (`DASHBOARD_BASE_URL=http://localhost:5173`,
   `PUBLIC_API_BASE_URL=http://localhost:8000`). Link không phân giải được là tín hiệu spam mạnh.
3. **Header `List-Unsubscribe`** khai báo đây là thư hàng loạt — đúng chuẩn và nên giữ, nhưng cộng với
   (1) và (2) thì càng khớp hồ sơ đáng ngờ. Ngoài ra lần test bắn 6 email gần giống nhau trong vài
   phút tới các alias của cùng một hộp thư, đúng khuôn mẫu spam.

Thứ tự việc thực sự có tác dụng khi triển khai: gửi từ tài khoản **Google Workspace của domain công
ty** (DKIM/DMARC gắn domain) → thay `localhost` bằng URL công khai thật → người nhận đánh dấu "Không
phải thư rác" và thêm người gửi vào danh bạ (hiệu quả nhanh với danh sách nội bộ nhỏ) → giữ nhịp đều
Mon/Thu thay vì bắn từng đợt.

## Open Questions

- Tài khoản gửi là `@gmail.com` chung hay user thuộc Google Workspace công ty? (Ảnh hưởng hạn mức,
  DMARC, và khả năng mở DWD sau này. Không chặn implement — chỉ khác giá trị env.)
- Ai giữ và xoay App Password ở production, `.env` đặt ở đâu trên VPS?
- Change `chatbot-qa` đang mở giả định nút `ask:` và `app.state.bot_router` — respec khi nào?
