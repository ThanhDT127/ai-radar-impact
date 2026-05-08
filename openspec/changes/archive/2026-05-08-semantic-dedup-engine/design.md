## Context

Với 15+ RSS sources + HN + Reddit (sau Change 2), cùng một sự kiện sẽ xuất hiện từ nhiều nguồn. Ví dụ: "OpenAI ra GPT-5" có thể xuất hiện trong OpenAI Blog, HN top story, Reddit r/MachineLearning, Ars Technica, VnExpress — tạo ra 5 insights gần giống nhau.

### Modules bị ảnh hưởng
- **M5 (Insight Repository):** Thêm cluster logic
- **M6 (Dashboard):** InsightDetail hiển thị references
- **M4 (AI Analysis):** Chạy dedup sau khi tạo insight

### Trạng thái hiện tại
- Dedup hiện tại: fingerprint (SHA-256 trên URL + title) — chỉ bắt exact duplicate
- Chưa có cross-source semantic dedup

## Goals / Non-Goals

**Goals:**
- Implement `DeduplicationEngine` với TF-IDF + Cosine Similarity
- Thêm `cluster_id`, `is_primary` vào bảng `insights`
- Chọn Primary insight (bài từ nguồn `trust_tier` cao nhất)
- API trả references khi xem insight detail
- Frontend hiển thị "Bài viết liên quan từ nguồn khác"
- Cập nhật `docs/system_overview.md`

**Non-Goals:**
- Không dùng vector embedding (TF-IDF đủ cho Phase 1, pgvector cho Phase 2)
- Không merge insights — chỉ nhóm
- Không real-time dedup — chạy batch

## Decisions

### D1: TF-IDF + Cosine Similarity
Dùng `sklearn.feature_extraction.text.TfidfVectorizer` + `sklearn.metrics.pairwise.cosine_similarity`:

```python
class DeduplicationEngine:
    SIMILARITY_THRESHOLD = 0.6  # 60% similarity → coi là cùng sự kiện

    def find_clusters(self, insights: list[Insight]) -> list[Cluster]:
        texts = [f"{i.title} {i.summary_short}" for i in insights]
        tfidf_matrix = TfidfVectorizer().fit_transform(texts)
        sim_matrix = cosine_similarity(tfidf_matrix)
        # Group by similarity > threshold
        ...
```

### D2: Primary selection logic
Trong mỗi cluster, chọn primary theo thứ tự ưu tiên:
1. `trust_tier` cao nhất (very_high > high > medium > low)
2. Nếu tie → `published_at` sớm nhất (bài gốc)
3. Nếu tie → `confidence` cao nhất

### D3: Database changes
```sql
ALTER TABLE insights ADD COLUMN cluster_id UUID NULL;
ALTER TABLE insights ADD COLUMN is_primary BOOLEAN NOT NULL DEFAULT TRUE;
CREATE INDEX idx_insights_cluster_id ON insights(cluster_id) WHERE cluster_id IS NOT NULL;
```

### D4: Dedup timing
Chạy dedup **sau mỗi batch ingestion**, trên insights mới tạo trong batch đó + insights hiện có (so sánh new vs existing).

### D5: API changes
`GET /api/v1/insights/{id}` trả thêm field:
```json
{
  "cluster_id": "uuid-or-null",
  "is_primary": true,
  "references": [
    {"id": "uuid", "title": "...", "source_name": "...", "source_url": "..."}
  ]
}
```

`GET /api/v1/insights` — chỉ hiển thị primary insights (filter `is_primary=true` hoặc `cluster_id IS NULL`).

### Bảng DB bị ảnh hưởng
- `insights`: thêm `cluster_id` (UUID, nullable), `is_primary` (Boolean, default true)

### API endpoints bị ảnh hưởng
- `GET /api/v1/insights` — filter chỉ hiện primary
- `GET /api/v1/insights/{id}` — trả kèm `references` array

## Risks / Trade-offs

| Risk | Mitigation |
|:---|:---|
| TF-IDF chất lượng kém hơn vector embedding | Threshold 0.6 + manual tuning, upgrade sang pgvector ở Phase 2 |
| Performance khi có nhiều insights | Chỉ so new vs existing 7 ngày gần nhất, không toàn bộ DB |
| False positives (nhóm sai) | Threshold bảo thủ (0.6), user có thể feedback |
