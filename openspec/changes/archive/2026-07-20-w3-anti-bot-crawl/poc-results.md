# PoC CloakBrowser vs Chromium local — kết quả (task 2.2 / gate T7)

> Điền khi chạy PoC. Bật/tắt CloakBrowser qua `CLOAK_CDP_URL` (rỗng = local). Mỗi nguồn chạy 2 chế độ,
> so số bài lấy được + độ dài trung bình + độ đầy đủ so bản gốc. **Cần** session LinkedIn (mục 1
> của `docs/session_bootstrap.md`) trước khi chạy nguồn MXH.

## Cách chạy

```bash
# Chế độ CloakBrowser (mặc định)
docker-compose exec backend python -m app.scripts.run_ingestion --source-id <UUID>

# Chế độ local: đặt CLOAK_CDP_URL= (rỗng) trong .env rồi chạy lại
```

Đếm kết quả trong DB:
```sql
SELECT s.name, COUNT(rd.id) AS docs, ROUND(AVG(LENGTH(rd.raw_content))) AS avg_len
FROM sources s JOIN raw_documents rd ON rd.source_id = s.id
WHERE s.name = '<tên nguồn>' GROUP BY s.name;
```

## Bảng so sánh

| Nguồn | Chế độ | Số bài | Độ dài TB | Đầy đủ so bản gốc (5–10 mẫu) | Ghi chú |
|---|---|---|---|---|---|
| Web VN (nguồn thay ICTNews) | local | | | | |
| Web VN (nguồn thay ICTNews) | cloak | | | | |
| LinkedIn - OpenAI | local | | | | |
| LinkedIn - OpenAI | cloak | 5 | 646 | nội dung post thật, đầy đủ | crawl 18/07 qua cloak; title sai (xem dưới) |

## Kết quả X (Twitter) — cơ sở cắt phạm vi (20/07)

Crawl 18/07 qua CloakBrowser, đo lại ngày 20/07 trước khi xóa:

| Nguồn | Số bài | Độ dài | Trạng thái xử lý | Insight sinh ra |
|---|---|---|---|---|
| X (Twitter) - OpenAI | 5 | 297–440 | 5 `low_signal` | 0 |
| X (Twitter) - Anthropic | 4 | 243–304 | 2 `low_signal`, 2 `pending` | 0 |
| X (Twitter) - Project Zero | 0 | — | — | 0 |
| X (Twitter) - Kelsey Hightower | 0 | — | — | 0 |

Nội dung lấy được **là tweet thật** (không phải trang shell hay login-wall) — cơ chế cookie + cloak
hoạt động đúng. Vấn đề là **giá trị nguồn**, không phải kỹ thuật: một tweet chỉ là câu dẫn + link
`t.co` trỏ về bài blog mà nguồn RSS chính thức của cùng tổ chức đã cào đầy đủ. → **Bỏ X.**

## Chẩn đoán web VN (task 2.3)

- Trước W3: ICTNews cào ra 16 document trùng hệt (title trang listing, 629 chars, đều `failed`).
- ⚠️ **Drift:** nguồn "ICTNews Công nghệ" không còn trong seed/DB hiện tại (VN đang có 200lab, Viblo,
  Machine Learning Cơ Bản qua `web_index` — mỗi nguồn 10 docs; "VietnamNet ICT" dạng `rss` = 0 docs).
  Cần chọn lại nguồn đại diện cho PoC trước khi chạy 2.2/2.3.
- Câu hỏi: anti-bot hay `link_selector`/`link_pattern` bắt sai URL?
- Kết luận: _(điền)_

## Vấn đề mở phát hiện khi đo lại (20/07) — CHẶN 5.1

Chạy `run_ingestion` cho `LinkedIn - OpenAI` ngày 20/07 (crawl trước đó 18/07): **5 new, 0 skipped**.
Không bài nào bị dedup, dù đó vẫn là những post cũ.

**1. Dedup gãy hoàn toàn ở LinkedIn — mỗi lần crawl nhân bản toàn bộ post.**
`source_url` = URL index + `#feed-<hash>`, với `hash = md5(content[:50])`
(`playwright_connector.py`, nhánh feed-card). Hash **không** ngẫu nhiên — nhưng 50 ký tự đầu của card
chứa **số follower**, thứ đổi liên tục:

| | 18/07 | 20/07 |
|---|---|---|
| content[:50] | `Feed post number 3 ⏎ OpenAI ⏎ OpenAI ⏎ 11,296,538 f…` | `… ⏎ 11,306,369 f…` |
| → `#feed-` | `c55a9a77…` | `3e4dbff9…` |

Fingerprint = SHA256(source_url + title) ⇒ đổi mỗi lần ⇒ luôn là "bài mới". `_dedup_by_content`
(task 3.4) chỉ chặn trùng **trong cùng batch**, không chặn được liên phiên. Chạy đều 2–4 lần/ngày sẽ
bơm document trùng vô hạn và đốt quota Gemini.

**⚠️ Chỉ strip fragment `#…` là SAI — sẽ đổi bug ồn ào thành mất dữ liệu âm thầm.** Bỏ fragment thì
mọi card của cùng nguồn có `source_url` giống hệt (URL index), nên identity rơi hết về `title` =
`Feed post number N` — đó là **vị trí slot trong feed**, không phải danh tính post. Feed dịch chuyển
khi có post mới, nên "slot 3" hôm nay là bài khác "slot 3" hôm kia ⇒ post mới bị dedup nhầm thành
trùng và bị bỏ. Nguồn LinkedIn sẽ đứng yên ở ~5 document vĩnh viễn.

**2. Title LinkedIn sai:** lấy `Feed post number N` (nhãn accessibility của container feed) thay vì
trích từ thân post — chính là lý do cách sửa trên không an toàn.

**Thăm dò DOM 20/07 — không có định danh bền nào trong card.** Chạy trên phiên sống, 9 card
`.feed-shared-update-v2` của `linkedin.com/company/openai/posts/`:

| Thứ tìm | Kết quả |
|---|---|
| `data-urn` / `data-id` / `data-activity-urn` (card + mọi hậu duệ) | **không có** |
| link permalink (`activity`, `/posts/`, `/feed/update/`) | **không có** — card không chứa `<a>` nào loại này |
| attribute `id` | `ember173`, `ember230`, `ember85` — **ID render của Ember, đổi mỗi lần load** |

⇒ Phương án `data-urn`/permalink tôi đề xuất **không dùng được** trên view này. Trang company posts
công khai không phát permalink ra DOM.

Các hướng còn lại, chưa cái nào được kiểm chứng:
- **Hash một lát nội dung ỔN ĐỊNH** thay vì `content[:50]`: bỏ phần header (tên tổ chức, số follower,
  timestamp tương đối `1w •`) rồi hash phần thân post. Cần xác định ranh giới header đáng tin.
- **Trích thân post qua selector** (`.update-components-text` / `.break-words`) và dùng nó cho cả title
  lẫn fingerprint — gọn hơn, nhưng phụ thuộc class LinkedIn hay đổi.
- **Đổi nguồn LinkedIn sang view khác** có permalink (ví dụ trang `recent-activity`), nếu có.

### ✅ ĐÃ FIX (20/07) — hash thân bài thay vì vỏ thẻ

Chẩn đoán cuối: nhiễu **không** nằm ở bài viết mà ở các phần tử UI xung quanh trong cùng thẻ. Diff hai
lần cào cùng một post chỉ khác 4 dòng: số follower, số reaction, số comment, số repost. Riêng post có
video còn đổi theo trạng thái trình phát (`Play` / `Pause` / `Media is loading` / `Loaded: 3.80%`).

Đánh giá offline trên 35 document đã cào (7 lần × ~5 post), ground truth = **6 nhóm**:

| Chiến lược | Số nhóm |
|---|---|
| `md5(content[:50])` (cũ) | **35** — mỗi doc một nhóm |
| `sha256(toàn bộ content)` | 35 |
| `sha256(body lọc dòng biến động)` | 9 |
| `sha256(body lọc + chrome media)` | **6** ✅ |

Lời giải chọn dùng là **cấu trúc**, không phải regex: LinkedIn render thân post trong
`.update-components-text` — probe xác nhận trả về đúng thân bài, không header/engagement/media chrome.
Regex `VOLATILE_CARD_LINE` giữ làm **dự phòng** khi class LinkedIn đổi.

**Thay đổi:** `source_url` = `<index>#post-<sha256(body)[:16]>`; `title` = dòng đầu có nghĩa của thân
bài (hết `Feed post number N`); `raw_content` = thân bài (Gemini không còn phải đọc vỏ thẻ).

**Nghiệm thu thật:** 2 chu kỳ liên tiếp → chu kỳ 2 `new: 0, skipped: 5`. Probe 5 card cho 5 thân bài
khác nhau, không card nào bị gộp nhầm.

⚠️ **Tác dụng phụ đã lường:** bỏ vỏ thẻ làm `raw_content` ngắn lại, nên post có thân bài dưới
`min_content_length` (200) nay bị lọc đúng như thiết kế — ví dụ post podcast: 501 ký tự vỏ thẻ → 190
ký tự thân bài → skip. Trước đây nó lọt qua ngưỡng chỉ nhờ ~311 ký tự nhiễu. LinkedIn vì thế cho ít
document hơn, nhưng đều là bài có nội dung thật.

### Thiệt hại đã hiện ra trong dữ liệu published (20/07, sau khi chạy analysis)

LinkedIn **có** sinh insight — 5 insight, `published`, confidence 0.90. Nhưng chúng đến từ chỉ
**2 post gốc**, và cùng một post bị phân loại mâu thuẫn:

| Post gốc | event_type | impact_label |
|---|---|---|
| `1c19ff` | Tín hiệu xu hướng | Thấp |
| `1c19ff` | Tín hiệu xu hướng | Thấp |
| `1c19ff` | **Phát hành mới** | **Trung bình** |
| `66e576` | Nghiên cứu/Paper | Thấp |
| `66e576` | Tín hiệu xu hướng | Thấp |

Bug dedup không còn là vấn đề nội bộ tầng `RawDocument`: nó **đẩy bài trùng lên dashboard** dưới dạng
nhiều thẻ, với phân loại và mức tác động khác nhau cho cùng một nội dung, đồng thời **đốt quota Gemini**
(3 lượt phân tích cho 1 bài). Ưu tiên fix tăng lên.

Thêm: title `Feed post number N...` đã **lọt vào insight published** → hiển thị nguyên trên dashboard.

## 🔴 Sliding refresh làm rụng cookie auth (regression T8/4.2 — đã vá 20/07)

Chuỗi quan sát được trong ngày:

| Thời điểm | Sự kiện | `linkedin_state.json` |
|---|---|---|
| 07:47 | codegen tạo phiên | 13437 B, **có `li_at`** |
| 08:00 | crawl OK (5 doc) → sliding refresh ghi đè | 10958 B, **mất `li_at`** |
| 08:10 | crawl kế tiếp | authwall, 0 card, **không log ERROR** |

**Sự kiện chắc chắn:** `context.storage_state()` qua CDP CloakBrowser trả về state **thiếu `li_at`**
(cookie xác thực chính của LinkedIn), và file đã bị ghi đè bằng state đó. Đây là lỗi độc lập, đủ để
vá: cứ ghi đè kiểu này thì phiên sẽ chết, sớm hay muộn.

**⚠️ Đính chính (đo lại 08:19–08:33):** ban đầu tôi kết luận mất `li_at` *là nguyên nhân* của authwall
lúc 08:10. **Không chứng minh được** — xem mục "phiên chỉ sống một lần" bên dưới: phiên chết cả khi
`li_at` còn nguyên. Quan hệ nhân quả giữa "mất `li_at`" và "authwall 08:10" là **chưa xác định**.

**Vá (vẫn đúng và cần thiết):** `_save_storage_state` so cookie xác thực (`AUTH_COOKIE_NAMES`) giữa
file cũ và state mới; mất thì **bỏ qua ghi đè** + log WARNING, giữ file cũ. Unit test 2 nhánh.

## 🔴🔴 Phiên LinkedIn chỉ sống được MỘT request — nghi vấn nền tảng cho T8

Hai phiên độc lập, cùng một mẫu hình:

| Phiên tạo lúc | Request 1 | Request 2 trở đi |
|---|---|---|
| 07:47 (codegen) | 08:00 → **5 doc thật** ✅ | 08:10 → authwall |
| 08:19 (codegen lại) | 08:21 → **9 card** ✅ | 08:23, 08:25, 08:33 → authwall |

Kiểm chứng loại trừ:
- **Không phải sliding refresh ghi hỏng file:** phiên thứ hai chưa hề bị ghi đè (mtime giữ nguyên
  08:19:22, `li_at` còn đủ) mà vẫn authwall.
- **Không phải rate-limit ngắn hạn:** chờ cooldown 7 phút rồi thử lại → vẫn authwall.
- **Cookie còn phía client, bị vô hiệu phía server:** `li_at` vẫn nằm trong file JSON, LinkedIn vẫn
  đẩy về `/authwall`.

Giả thuyết còn lại (**chưa kiểm chứng**): LinkedIn ràng phiên theo fingerprint thiết bị. Phiên được
tạo bằng Chromium thường của `playwright codegen`, nhưng được dùng lại từ **CloakBrowser qua CDP** —
fingerprint lệch → LinkedIn thu hồi phiên sau lần dùng đầu tiên.

**Hệ quả nếu đúng:** tiền đề của T8 ("cookie tự gia hạn → phiên không bao giờ hết hạn khi dùng đều
đặn") **không thành lập cho LinkedIn** — không có gì để gia hạn nếu phiên chết sau một request.
Sliding refresh, login-wall detection, guard `AUTH_COOKIE_NAMES` đều vẫn đúng về mặt code, nhưng
không cứu được mô hình vận hành.

### ✅ ĐÃ XÁC NHẬN + KHẮC PHỤC (20/07, 08:45)

Bằng chứng trực tiếp trong tiến trình cloak:

```
chrome --fingerprint=19916 --fingerprint-platform=windows ...
```

CloakBrowser **giả lập Windows**; `playwright codegen` trên host tạo phiên bằng Chromium **Linux**.
Cùng `li_at` xuất hiện từ hai nền tảng khác nhau → LinkedIn thu hồi sau lần dùng đầu.

**Khắc phục:** tạo session **bên trong chính CloakBrowser** (đăng nhập tay qua x11vnc + noVNC vào Xvfb
`:99`, rồi `contexts[0].storage_state(path=...)`). Kết quả:

| Chu kỳ | Kết quả | Sliding refresh |
|---|---|---|
| 1 | 5 card ✅ | ghi thành công |
| 2 | 5 card ✅ | ghi thành công |
| 3 | 5 card ✅ | — |
| 4 (sau nghỉ 6 phút) | 5 card ✅ | — |
| 5 (sau khi dọn hạ tầng tạm) | 5 card ✅ | — |

`li_at` còn nguyên sau cả 5 chu kỳ. So với trước: phiên codegen **luôn** chết ở chu kỳ 2.
→ **Giả thuyết fingerprint xác nhận. LinkedIn giữ lại trong W3, không cắt.**

**Hệ quả phụ — cũng giải thích nốt bug 4.2:** `storage_state()` rụng `li_at` chỉ xảy ra với context
nạp từ phiên *lệch fingerprint*. Với phiên CloakBrowser-native, sliding refresh ghi bình thường và
guard `AUTH_COOKIE_NAMES` không phải chặn lần nào. Guard vẫn giữ — nó là lưới an toàn đúng chỗ.

**Quy trình tạo session đã cập nhật trong `docs/session_bootstrap.md`** (codegen trên host bị đánh dấu
KHÔNG dùng được). Lưu ý vận hành: đổi trình duyệt cào (bật/tắt `CLOAK_CDP_URL`) ⇒ phải tạo lại session.

## 🔴 Login-wall detection có lỗ timing (regression T8/4.1 — đã vá 20/07)

Phiên chết ở trên **không** kích hoạt ERROR: `_is_login_wall` chỉ chạy ngay sau `goto(...
wait_until="domcontentloaded")`, mà redirect authwall của LinkedIn xảy ra phía client **sau** mốc đó.
Kết quả: `extracted 0 cards`, im lặng — đúng chế độ hỏng mà T8 phải loại bỏ.

**Vá:** kiểm lại login-wall khi truy vấn ra **0 phần tử**, ở cả nhánh feed-card lẫn nhánh extract-links.
**Nghiệm thu thật (20/07):** chạy lại trên phiên chết → log ERROR kèm lệnh codegen, 0 document rác.
→ DoD runtime của 4.1 ✅ (trước đó mới có unit test).

## Sản lượng LinkedIn sau khi sửa (20/07, dữ liệu sạch)

17 document sạch → chạy analysis → **1 insight**: *"OWASP Dependency-Track 5.0 is now generally
available"* (Phát hành mới / Trung bình) — đúng loại tin hữu ích, title lấy từ thân bài.

| Nguồn | analyzed | low_signal |
|---|---|---|
| OWASP | 1 | 4 |
| OpenAI | 0 | 4 |
| Andrew Ng | 0 | 5 |
| Anthropic | 0 | 3 |

**Đánh giá thẳng:** tỉ lệ 1/17 là thấp. Gate lọc phần lớn vì post doanh nghiệp trên LinkedIn chủ yếu
là PR/thông báo sản phẩm — cùng bản chất đã khiến X bị cắt. Khác biệt giữ LinkedIn lại: post dài hơn
nhiều (TB 280–1933 ký tự so với 243–440 của tweet) và **có** sinh insight thật, trong khi X sinh 0.
Nguồn kỹ thuật (OWASP) cho tín hiệu tốt hơn hẳn nguồn thương hiệu.

Nếu vòng cào tới vẫn ~1 insight/17 doc, nên cân nhắc: bỏ nguồn thương hiệu (OpenAI/Anthropic — trùng
RSS chính thức của họ), giữ nguồn kỹ thuật/cá nhân (OWASP, Andrew Ng).

## Kết luận gate (20/07) — GIỮ CloakBrowser

**A/B đầy đủ không được chạy; gate đóng bằng lập luận.** Lý do tiền đề đã đổi so với lúc mở change:

1. **Nhánh "web VN bị chặn" mất đối tượng.** Nguồn VN nay là `source_type: web_index`, không đi qua
   CloakBrowser. 200lab / ML Cơ Bản / Viblo đều ra 10 doc, 6.5k–16k ký tự, có sinh insight — không
   còn triệu chứng anti-bot nào để đo.
2. **LinkedIn là nguồn `playwright` active duy nhất** (MLOpsVN Blog inactive), nên phép so thu về
   đúng một nguồn.
3. **Chạy nhánh "local" cho LinkedIn tốn một vòng đăng nhập tay.** Phát hiện fingerprint 20/07: session
   phải được tạo *trong chính trình duyệt sẽ cào*. Đổi sang Chromium local ⇒ phải dựng lại VNC và
   người vận hành đăng nhập lại.

**Bằng chứng đã có, đủ để quyết:** qua CloakBrowser, cả 4 nguồn LinkedIn từ 0 doc nay ra nội dung thật
(Andrew Ng 5 doc TB 1933 ký tự, OWASP 5/666, OpenAI 4/721, Anthropic 3/280); phiên sống ổn định qua
nhiều chu kỳ; không dính login-wall. Đó chính là điều mà nhánh "cloak" của A/B cần chứng minh.

⚠️ **Điều KHÔNG được chứng minh:** rằng cloak *tốt hơn* Chromium local. Có thể local cũng làm được
việc tương tự. Quyết định giữ cloak là vì nó **đã chạy được** và chi phí chuyển đổi (tạo lại session)
lớn hơn lợi ích của việc biết câu trả lời. Nếu sau này cần bỏ cloak để giảm hạ tầng, phải chạy lại
phép so này kèm một vòng tạo session mới.
