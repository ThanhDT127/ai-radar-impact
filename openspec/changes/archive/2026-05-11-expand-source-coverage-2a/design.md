## Context

Phase 2A là phần 2/3 của roadmap mở rộng nguồn:
- Phase 1 (`add-china-ai-sources`): bắc cầu China AI + thêm metadata `region`/`target_roles`
- **Phase 2A (this)**: Global AI/Dev/Security còn thiếu
- Phase 2B (`expand-source-coverage-2b`): Vietnam news + community

Hiện tại 18 + 10 (sau Phase 1) = 28 nguồn. Sau Phase 2A: ~41.

### Modules bị ảnh hưởng

- **M1 (Sources)**: chỉ thêm seed data
- **M2 (Ingestion)**: không đổi
- Schema `region`/`target_roles` đã có từ Phase 1

### Trạng thái hiện tại

- 18 nguồn gốc + 10 China AI = 28
- RSSConnector hỗ trợ feed chuẩn; Substack feed hoạt động; HF blog có RSS
- Source model có `region`/`target_roles` columns

## Goals / Non-Goals

**Goals:**
- 12-13 nguồn mới được seed thành công
- Coverage role: Bảo mật từ ~0 → ≥4 nguồn; DevOps từ ~2 → ≥5 nguồn
- Tất cả URL feed được verify trước seed (qua `verify_feeds.py` đã tạo)

**Non-Goals:**
- Không tạo helper/connector mới
- Không refactor existing code
- Không expand frontend filter

## Decisions

### D1: Source feed URLs (verify trước commit)

| Source | URL ước tính | Cluster |
|---|---|---|
| Anthropic | `https://www.anthropic.com/news/rss.xml` (verify) | Global AI |
| Hugging Face Blog | `https://huggingface.co/blog/feed.xml` | Global AI |
| Papers With Code | `https://paperswithcode.com/feed` | Global AI |
| Stack Overflow Blog | `https://stackoverflow.blog/feed/` | Dev |
| dev.to AI | `https://dev.to/feed/tag/ai` | Dev |
| dev.to ML | `https://dev.to/feed/tag/machinelearning` | Dev |
| JetBrains Blog | `https://blog.jetbrains.com/feed/` | Dev |
| Docker Blog | `https://www.docker.com/blog/feed/` | DevOps |
| Kubernetes Blog | `https://kubernetes.io/feed.xml` | DevOps |
| KrebsOnSecurity | `https://krebsonsecurity.com/feed/` | Security |
| BleepingComputer | `https://www.bleepingcomputer.com/feed/` | Security |
| Microsoft Security | `https://www.microsoft.com/security/blog/feed/` | Security |
| GitHub Security Lab | `https://securitylab.github.com/feed.xml` (verify) | Security |

13 URL — verify từng cái trước seed.

### D2: Trust tier mapping

| Source | trust_tier |
|---|---|
| Anthropic | very_high |
| Hugging Face Blog | very_high |
| Papers With Code | high |
| Stack Overflow Blog | high |
| dev.to feeds | medium (community-driven) |
| JetBrains Blog | high |
| Docker Blog | very_high |
| Kubernetes Blog | very_high |
| KrebsOnSecurity | very_high |
| BleepingComputer | high (đôi khi clickbait) |
| Microsoft Security Blog | very_high |
| GitHub Security Lab | very_high |

### D3: target_roles mapping

| Cluster | target_roles |
|---|---|
| Global AI (Anthropic, HF, Papers W/Code) | `[Engineering, Data/AI]` |
| Dev (SO, dev.to, JetBrains) | `[Engineering]` |
| DevOps (Docker, K8s) | `[Engineering, Toàn công ty]` (hạ tầng ai cũng phải biết) |
| Security (Krebs, BleepingC, MS Sec, GH Sec Lab) | `[Engineering, Legal/Compliance, Toàn công ty]` |

### D4: Topics theo Vietnamese taxonomy hiện có

Phải dùng đúng `ALLOWED_TOPICS`:
- Anthropic, HF, Papers W/Code: `["Trí tuệ nhân tạo", "Dữ liệu"]`
- Dev: `["Công nghệ", "Quy trình phần mềm"]`
- DevOps: `["Công nghệ", "Quy trình phần mềm"]`
- Security: `["An ninh mạng"]`

### D5: Skip nguồn nếu URL fail

Nếu `verify_feeds.py` báo URL không trả entries hoặc HTTP 404:
- Document trong tasks (note URL nào fail)
- Loại khỏi seed
- Có thể tạo follow-up change cho nguồn đó nếu thực sự cần

### API endpoints bị ảnh hưởng

Không có. Chỉ thay data trong `sources` table.

### Bảng DB bị ảnh hưởng

`sources` — chỉ INSERT mới (qua seed script), không thay schema.

## Risks / Trade-offs

| Risk | Mitigation |
|:---|:---|
| dev.to tag feed quá noisy với tin marketing/career | `max_items: 10` thay vì 20; theo dõi 1 tuần |
| Stack Overflow Blog đã rebrand → URL có thể đổi | Verify URL hiện tại trước seed |
| Microsoft Security Blog feed có thể yêu cầu UA hợp lệ | Test với feedparser; nếu fail, document |
| 13 nguồn cùng lúc tạo nhiều noise | Trust tier filter; dedup engine sẽ cluster lại; `urgency` rule (từ change 1) sẽ surface tin quan trọng |
| Một số feed chỉ trả summary ngắn | Insight quality giảm cho nguồn đó; không phải lỗi — design accepted |
| KrebsOnSecurity và BleepingComputer cùng cover 1 vụ | Dedup engine xử lý; primary chọn theo trust tier (Krebs > BleepingC) |
