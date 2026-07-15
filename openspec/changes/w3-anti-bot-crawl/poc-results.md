# PoC CloakBrowser vs Chromium local — kết quả (task 2.2 / gate T7)

> Điền khi chạy PoC. Bật/tắt CloakBrowser qua `CLOAK_CDP_URL` (rỗng = local). Mỗi nguồn chạy 2 chế độ,
> so số bài lấy được + độ dài trung bình + độ đầy đủ so bản gốc. **Cần** session X/LinkedIn (mục 1–2
> của `docs/session_bootstrap.md`) trước khi chạy 2 nguồn MXH.

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
| ICTNews Công nghệ | local | | | | |
| ICTNews Công nghệ | cloak | | | | |
| X (Twitter) - OpenAI | local | | | | |
| X (Twitter) - OpenAI | cloak | | | | |
| LinkedIn - OpenAI | local | | | | |
| LinkedIn - OpenAI | cloak | | | | |

## Chẩn đoán ICTNews (task 2.3)

- Trước W3: 16 document trùng hệt (title trang listing, 629 chars, đều `failed`).
- Câu hỏi: anti-bot hay `link_selector`/`link_pattern` bắt sai URL?
- Kết luận: _(điền)_

## Kết luận gate

- [ ] CloakBrowser cải thiện rõ → tiếp tục toàn bộ task cloud-specific.
- [ ] CloakBrowser KHÔNG cải thiện → hạ ưu tiên task cloak, giữ Playwright + cookie làm đường chính (fallback theo lịch trình W3).
