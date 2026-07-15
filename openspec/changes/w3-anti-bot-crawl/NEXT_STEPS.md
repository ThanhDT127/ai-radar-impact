# W3 — Việc còn lại (làm tiếp tuần sau)

> Cập nhật 2026-07-11. Sprint W3: 20–24/07. Phần **code + test + docs đã xong** (13/19 task,
> backend tests 26/26 xanh). 6 việc dưới đây **cần tài khoản thật + crawl live** nên để lại cho
> người dùng. Làm theo đúng thứ tự này. Chi tiết DoD xem `tasks.md`; hướng dẫn session xem
> `docs/session_bootstrap.md`.

## Thứ tự thực hiện

### Bước 1 — Tạo session đăng nhập (task 1.1, 1.2) · cần máy có GUI
Playwright CLI đã cài sẵn trên host. Chạy từ thư mục gốc repo, login tay bằng **tài khoản riêng**
(throwaway, không cần follow ai), lướt feed vài giây rồi **đóng cửa sổ**:

```bash
cd ~/Intern/ai-radar-impact
playwright codegen --save-storage=secrets/states/linkedin_state.json https://www.linkedin.com/login
playwright codegen --save-storage=secrets/states/x_state.json https://x.com/login
```
- ✅ DoD: `linkedin_state.json` chứa cookie `li_at`; `x_state.json` chứa cookie `auth_token`.

### Bước 2 — Bật hệ thống + seed lại (để nạp cookie_file nguồn X)
```bash
docker compose up -d
docker compose exec backend python -m app.scripts.seed_sources
```
- ✅ DoD (phần 1.4): query DB thấy `config.cookie_file` trên cả 4 nguồn X.

### Bước 3 — PoC CloakBrowser vs local (task 2.2, 2.3) · GATE quyết định hướng
Điền bảng trong `poc-results.md`. Mỗi nguồn chạy 2 chế độ: mặc định (cloak) và `CLOAK_CDP_URL=` rỗng
trong `.env` (local). Nguồn thử: ICTNews + 1 nguồn X + 1 nguồn LinkedIn.
- ✅ DoD: có bảng so sánh + kết luận **giữ hay bỏ cloak**. Nếu cloak không cải thiện rõ → giữ
  Playwright + cookie làm chính (fallback theo lịch trình), hạ ưu tiên task cloak-specific.
- ⚠️ Kiểm luôn `CLOAK_HEADLESS=False` trong compose có chạy được trên server không GUI không (open
  question trong `design.md`).

### Bước 4 — Nghiệm thu T7/T8 (task 5.1, 5.2)
- **5.1 (T7):** chạy ingestion 8 nguồn X/LinkedIn + ICTNews, spot-check 5–10 bài so bản gốc → nội
  dung thật, đầy đủ.
- **5.2 (T8):** chạy 2 chu kỳ ingestion liên tiếp → xác nhận `mtime` file state đổi (cookie tự gia
  hạn) và phiên còn sống; xoá tạm cookie → thấy log ERROR login-wall đúng chỗ, 0 doc rác.

## Cần xác minh runtime (DoD của các task code đã tick)
Các hành vi này đã hiện thực + có unit test ở tầng logic, nhưng **chỉ chứng thực thật khi chạy PoC/
nghiệm thu qua CloakBrowser**:
- 3.1 — UA của page khớp version Chromium thật của cloak (không bị ép UA tĩnh).
- 3.2 — sau 3 lần fetch, số contexts trong cloak không tăng (không leak).
- 4.1 — cookie chết → log ERROR có hướng dẫn codegen, không tạo document rác.
- 4.2 — file state được ghi đè (mtime đổi) sau phiên thành công.

## Xong hết thì
`/opsx:archive w3-anti-bot-crawl` để đóng change; cập nhật trạng thái T7/T8 sang ✅ trong
`docs/ignored/LICH_TRINH_CONG_VIEC.md`.
```
Trạng thái hiện tại (11/07): [x]×13 code+docs · [ ]×6 chờ session/crawl thật (1.1 1.2 2.2 2.3 5.1 5.2)
```
