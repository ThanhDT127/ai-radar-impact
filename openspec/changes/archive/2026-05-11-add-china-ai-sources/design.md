## Context

Source model hiện tại có:
- `name`, `source_type`, `feed_url`, `trust_tier`, `topics` (ARRAY), `status`, `config` (JSONB)
- Không có metadata về region, ngôn ngữ chuyên về region nào, hay vai trò nào hưởng lợi nhất từ nguồn

Khi mở rộng từ 18 → ~46 nguồn (qua 3 changes Phase 2), việc filter theo region và slice cho role là cần thiết. Nếu không thêm metadata này từ change đầu tiên, các change sau sẽ phải migrate dữ liệu.

### Modules bị ảnh hưởng

- **M1 (Sources)**: Schema mở rộng + seed data mới
- **M2 (Ingestion)**: Không đổi (RSSConnector dùng `feed_url` như cũ)

### Trạng thái hiện tại

- 18 nguồn seeded, không có region/role tagging
- HuggingFace có RSS feed cho papers tổ chức nhưng không phải tất cả org đều active
- Substack chuẩn cung cấp `/feed` URL

## Goals / Non-Goals

**Goals:**
- 10 nguồn mới về China AI ecosystem được seed thành công
- Source model có 2 columns metadata mới: `region`, `target_roles`
- Tất cả 18 nguồn cũ được backfill `region`, `target_roles` (không null)
- Verification: chạy ingestion trên 1 nguồn TQ cụ thể, raw_documents được tạo đúng

**Non-Goals:**
- Không build region filter trong dashboard
- Không thêm các site tiếng Trung (Sina, 36kr, etc.)
- Không thêm GitHub releases làm nguồn (defer cho github-trending-connector)

## Decisions

### D1: `region` enum string — không tạo lookup table

```python
# models/source.py
region: Mapped[str] = mapped_column(VARCHAR(20), default="global", nullable=False)
# Allowed: "global", "china", "vietnam"
```

3 giá trị đủ cho roadmap hiện tại. Nếu sau này thêm "japan", "korea" thì chỉ cần thêm string. Không cần FK table.

### D2: `target_roles` là ARRAY[VARCHAR], khớp với taxonomy hiện có

```python
target_roles: Mapped[list[str]] = mapped_column(
    ARRAY(VARCHAR(50)),
    default=lambda: [],
    nullable=False
)
```

Closed set giống `affected_roles` của insight (`Executive`, `Engineering`, `Data/AI`, `Product`, `Content/Marketing`, `Legal/Compliance`, `HR/L&D`, `Toàn công ty`).

Khác `topics` — `target_roles` cho biết "nguồn này phục vụ vai trò nào", còn `topics` là "nguồn này nói về chủ đề gì".

### D3: Thứ tự verify URL trước khi seed

Tạo helper `scripts/verify_feeds.py` chạy parallel `feedparser.parse()` cho mọi URL. Output JSON: `{url, status, num_entries, sample_title}`. Manually review trước khi merge seed.

### D4: HuggingFace org RSS strategy

Test 2 endpoints theo thứ tự:

1. `https://huggingface.co/api/organizations/{org}/papers/rss` — papers feed
2. `https://huggingface.co/{org}/feed` — nếu (1) không hoạt động

Nếu cả 2 fail cho 1 org → loại org đó khỏi batch này, document trong tasks và proposal Phase sau.

### D5: Substack — chuẩn `/feed`

Interconnects: `https://www.interconnects.ai/feed`
ChinaTalk: `https://www.chinatalk.media/feed`

Verify trước seed.

### D6: Backfill 18 sources cũ

Migration:

```sql
ALTER TABLE sources
  ADD COLUMN region VARCHAR(20) NOT NULL DEFAULT 'global',
  ADD COLUMN target_roles VARCHAR(50)[] NOT NULL DEFAULT '{}';

-- Backfill known regions
UPDATE sources SET region='vietnam' WHERE name='VnExpress Số hóa';
UPDATE sources SET region='global' WHERE region IS NULL OR region='';

-- Backfill target_roles by topic match (best effort)
UPDATE sources SET target_roles='{Engineering,Data/AI}'
  WHERE 'Trí tuệ nhân tạo' = ANY(topics);
-- (etc., done in migration data step)
```

### D7: Trust tier mapping

| Source | trust_tier | Lý do |
|---|---|---|
| DeepSeek (HF) | very_high | Official org, paper releases verified |
| Qwen (HF) | very_high | Alibaba official |
| GLM/Zhipu (HF) | very_high | Đối tác lớn của OpenAI ở TQ |
| Yi/01.AI | high | Independent lab |
| Kimi/Moonshot | high | Tier 2 lab |
| Hunyuan (Tencent) | high | Big tech but ít paper hơn |
| MiniMax | high | |
| Baichuan | high | |
| Interconnects | high | Nathan Lambert ML researcher |
| ChinaTalk | high | Editorial dày, Jordan Schneider |

### API endpoints bị ảnh hưởng

- `GET /api/v1/admin/sources` — response thêm `region`, `target_roles` (nếu admin-api expose Source full)

### Bảng DB bị ảnh hưởng

`sources` table — thêm 2 cột.

## Risks / Trade-offs

| Risk | Mitigation |
|:---|:---|
| HuggingFace org RSS endpoint không có thật / unstable | Verify từng URL; nếu fail, defer org đó cho phase sau |
| Substack feed có rate limit | Set `max_items: 10` trong config, ingest 1 lần/ngày là đủ |
| Migration `target_roles` backfill cần manual mapping | Best-effort qua topic match; admin có thể chỉnh sửa sau qua DB hoặc admin-api |
| Trust tier lạm phát "very_high" | Chỉ 3 nguồn TQ tier cao nhất; còn lại `high`. Tinh chỉnh sau 1 tuần |
| Newsletter Substack có thể trùng nội dung với HF org (cùng cover DeepSeek) | Dedup engine sẽ cluster lại → primary insight chọn theo trust_tier |
