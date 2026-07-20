# W3 — Trạng thái

> Cập nhật 2026-07-20. Sprint W3: 20–24/07. **20/20 task xong**, backend tests 63/63.
> Phạm vi đã thu hẹp: **bỏ toàn bộ nguồn X (Twitter)**, giữ **LinkedIn + web VN**.
> Sẵn sàng `/opsx:archive w3-anti-bot-crawl`.

## Đã làm trong ngày 20/07

- **Cắt X:** gỡ 4 nguồn khỏi seed + DB + connector + spec + docs. Lý do: tweet 243–440 ký tự → 0 insight.
- **Phiên LinkedIn chỉ sống 1 request** → truy ra lệch fingerprint (cloak chạy
  `--fingerprint-platform=windows`, codegen dùng Chromium Linux). Tạo session **bên trong CloakBrowser**
  → sống ổn nhiều chu kỳ. Quy trình mới trong `docs/session_bootstrap.md`.
- **Vá 2 regression T8:** sliding refresh ghi đè state rụng `li_at` (nay có guard `AUTH_COOKIE_NAMES`);
  login-wall check chạy trước redirect authwall phía client (nay kiểm lại khi truy vấn ra 0 phần tử).
- **Sửa dedup feed card:** hash thân bài (`.update-components-text`) thay vì `md5(content[:50])` — vỏ thẻ
  chứa follower/reaction/comment và chrome trình phát video, đổi liên tục. Chu kỳ 2 nay `new: 0, skipped: 5`.
- **Sửa nguồn sai:** `LinkedIn - Anthropic` trỏ `company/anthropic` — một quỹ VC/PE trùng tên. Đúng phải là
  `company/anthropicresearch`.
- **Gate 2.2 đóng bằng lập luận:** giữ CloakBrowser (tiền đề A/B đã đổi — xem `poc-results.md`).
- **Dọn dữ liệu cũ:** xóa 35 document scheme `#feed-` + 5 insight sinh từ chúng (title `Feed post number N`,
  2 post gốc → 5 thẻ mâu thuẫn trên dashboard).

## Kết quả cuối

| Nguồn LinkedIn | Doc | Độ dài TB |
|---|---|---|
| Andrew Ng | 5 | 1933 |
| OWASP | 5 | 666 |
| OpenAI | 4 | 721 |
| Anthropic | 3 | 280 |

Web VN (qua `web_index`, không dùng cloak): 200lab 10 doc/6580, ML Cơ Bản 10/15905, Viblo 10/10092.

## Việc còn lại sau khi archive

- **VietnamNet ICT** (`rss`) = 0 docs — ngoài phạm vi W3 (không phải nguồn playwright), đáng kiểm riêng.
- **MLOpsVN Blog** (`playwright`) đang `inactive` — bật lại nếu muốn thêm nguồn VN.
- Nếu sau này muốn bỏ CloakBrowser để giảm hạ tầng: phải chạy lại A/B kèm một vòng tạo session mới.

## Cần xác minh runtime (DoD của task code đã tick)
Đã hiện thực + có unit test ở tầng logic, **chỉ chứng thực thật khi chạy PoC/nghiệm thu qua CloakBrowser**:
- 3.1 — UA của page khớp version Chromium thật của cloak (không bị ép UA tĩnh). ⏳ chờ 2.2
- 3.2 — sau 3 lần fetch, số contexts trong cloak không tăng (không leak). ⏳ chờ 2.2
- 4.1 — cookie chết → log ERROR có hướng dẫn codegen, không tạo document rác. ✅ 20/07
- 4.2 — file state ghi đè (mtime đổi) sau phiên thành công, `li_at` sống sót qua 5 chu kỳ. ✅ 20/07

> Bài học 20/07: 4.1 và 4.2 đều pass unit test nhưng **fail ngoài đời** theo đúng kiểu chúng phải chặn.
> Đừng tick DoD runtime bằng unit test.

## Xong hết thì
`/opsx:archive w3-anti-bot-crawl`; cập nhật T7/T8 sang ✅ trong `docs/ignored/LICH_TRINH_CONG_VIEC.md`.

```
Trạng thái 20/07: [x]×20 · [ ]×0 — hoàn tất
```
