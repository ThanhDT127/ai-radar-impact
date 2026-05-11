## Context

Phase 2B là phần 3/3 của roadmap mở rộng nguồn (`add-china-ai-sources` → `expand-source-coverage-2a` → `expand-source-coverage-2b`).

Sau Phase 2B: ~41 + 12 = ~53 nguồn. Đạt mục tiêu MVP "35-45 nguồn sạch" mà GPT đề xuất, hơi vượt nhưng có lý do (VN team cần coverage VN dày).

### Modules bị ảnh hưởng

- **M1 (Sources)**: chỉ thêm seed data, dùng schema có sẵn

### Trạng thái hiện tại

- 28 + 13 (sau 2A) = 41 nguồn
- Source model đã có `region`, `target_roles`
- 1 nguồn VN duy nhất (VnExpress Số hóa) — coverage cực thấp

## Goals / Non-Goals

**Goals:**
- 12 nguồn VN mới được seed thành công
- Coverage VN: 1 → 13 nguồn
- Cluster `vietnam` có cả news (top-down) và community (bottom-up)
- `target_roles` cho VN community sources phản ánh phổ rộng (Engineering, Data/AI, Content, Product...)

**Non-Goals:**
- Không thêm scraper cho VN sites không RSS
- Không thêm các source cần auth (Facebook, LinkedIn)
- Không build VN-specific UI

## Decisions

### D1: Source feed URLs (verify trước commit)

| Source | URL ước tính | Cluster |
|---|---|---|
| GenK | `https://genk.vn/rss/home.rss` | VN News |
| VietnamNet ICT | `https://vietnamnet.vn/rss/cong-nghe.rss` | VN News |
| ICT News | `https://ictnews.vietnamnet.vn/rss/home.rss` (verify) | VN News |
| CafeF Kinh tế số | `https://cafef.vn/kinh-te-so.rss` (verify) | VN News |
| VietTimes | `https://viettimes.vn/rss/cong-nghe-251.rss` (verify) | VN News |
| Viblo | `https://viblo.asia/rss/posts` (chính thức) | VN Community |
| Daynhauhoc | `https://daynhauhoc.com/latest.rss` | VN Community |
| MLOpsVN | `https://mlops.vn/feed.xml` (verify) | VN Community |
| ML Cơ Bản | `https://machinelearningcoban.com/feed.xml` (verify) | VN Community |
| 200lab Blog | `https://200lab.io/blog/rss.xml` (verify) | VN Community |
| AI Vietnam HF | (HF org papers RSS, similar to China AI strategy) | VN Community |
| AIO Conquer | (verify, có thể không có RSS) | VN Community |

12 URL — nhiều cái cần verify, sẵn sàng skip cái fail.

### D2: Trust tier mapping (thấp hơn quốc tế vì community-driven)

| Source | trust_tier |
|---|---|
| GenK, VietnamNet ICT, ICT News | medium |
| CafeF, VietTimes | medium |
| Viblo, Daynhauhoc | medium (community) |
| MLOpsVN, ML Cơ Bản, 200lab | high (chuyên môn cao) |
| AI Vietnam HF | high |
| AIO Conquer | medium |

### D3: target_roles mapping (rộng hơn nguồn quốc tế)

| Cluster | target_roles |
|---|---|
| VN News (GenK, VnNet, ICT News) | `[Engineering, Product, Content/Marketing, Toàn công ty]` |
| VN Business (CafeF, VietTimes) | `[Executive, Product, Toàn công ty]` |
| VN Tech Community (Viblo, Daynhauhoc) | `[Engineering, Data/AI]` |
| VN ML/AI Community (MLOpsVN, ML Cơ Bản, 200lab, AI VN HF, AIO Conquer) | `[Engineering, Data/AI]` |

### D4: Topics theo Vietnamese taxonomy

Tất cả nguồn VN có thể có ≥1 trong: `["Trí tuệ nhân tạo", "Công nghệ", "Quy trình phần mềm", "Dữ liệu"]`

VN business sources thêm: `["Thị trường/Đối thủ"]` (nếu phù hợp)

### D5: language config

Tất cả nguồn VN: `config = {"max_items": 20, "language": "vi"}`

Trừ AI Vietnam HF có thể là `"en"` (papers HF chủ yếu tiếng Anh).

### D6: Skip nguồn fail verify

Tương tự change 2A — nếu URL không trả entries:
- Document trong tasks
- Loại khỏi seed
- Phase sau có thể thử endpoint khác hoặc scraper

### API endpoints bị ảnh hưởng

Không có. Chỉ thay data trong `sources` table.

### Bảng DB bị ảnh hưởng

`sources` — chỉ INSERT mới.

## Risks / Trade-offs

| Risk | Mitigation |
|:---|:---|
| Nhiều VN news site dùng URL feed không chuẩn / đã đổi | Verify từng URL; có thể fallback sang RSSHub deploy nếu cần (defer) |
| Nội dung VN có encoding issue (mojibake với một số platform) | Test với feedparser; spot-check 1-2 entries trước seed |
| Daynhauhoc có thể chứa tin spam/quảng cáo trong "latest" feed | Set `max_items: 10`; theo dõi chất lượng 1 tuần; nếu noisy, đổi sang `/categories/latest.rss` cụ thể |
| Viblo/Daynhauhoc post quality không đồng đều | Trust tier `medium` reflect đúng thực tế |
| Một số blog VN (MLOpsVN, ML Cơ Bản) không update thường xuyên | OK — vẫn ingest, dedup engine handle nếu trùng |
| Gemini analyze tiếng Việt có thể có hiệu năng khác content tiếng Anh | Theo dõi confidence distribution của VN insights; nếu thấp, có thể tạo prompt riêng cho VN content (defer) |
