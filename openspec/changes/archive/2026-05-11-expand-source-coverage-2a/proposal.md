## Why

Sau `add-china-ai-sources` đã bắc cầu cho hệ sinh thái Trung Quốc, Phase 2A mở rộng các lỗ hổng còn lại trong **layer toàn cầu**: AI labs còn thiếu (Anthropic, HuggingFace blog), nguồn dev/DevOps (Stack Overflow, Docker, K8s, JetBrains), và security (KrebsOnSecurity, Microsoft Security, GitHub Security Lab, BleepingComputer).

Hiện tại Engineering/AI dày, nhưng Dev/DevOps coverage chỉ 5/12, Security gần như trống. Sau Phase 2A, các vai trò Bảo mật và DevOps sẽ có nguồn tin chuyên ngành thực sự.

## What Changes

Thêm **~13 nguồn RSS-friendly** vào `seed_sources.py`, chia 3 cluster:

**Cluster 1 — Global AI missing (3)**:
- Anthropic (news/blog RSS)
- Hugging Face Blog
- Papers With Code

**Cluster 2 — Dev/DevOps (5-6)**:
- Stack Overflow Blog
- dev.to (top tags: ai, javascript, python)
- JetBrains Blog
- Docker Blog
- Kubernetes Blog
- CNCF Blog (optional, có thể defer)

**Cluster 3 — Security (4-5)**:
- KrebsOnSecurity
- BleepingComputer
- Microsoft Security Blog
- GitHub Security Lab
- Google Security Blog (optional, có thể defer)

Tất cả `region = "global"`. Mỗi cluster có `target_roles` phù hợp.

**Verify trước seed**: Tương tự change 2, dùng `verify_feeds.py` đã tạo.

## Capabilities

### Modified Capabilities
- `rss-ingestion`: Mở rộng seed với 3 cluster nguồn mới + `region="global"` cho tất cả

## Impact

- **Backend code**: `scripts/seed_sources.py` (chỉ data, không code mới)
- **Database**: Không thay đổi schema (đã có `region`/`target_roles` từ change 2)
- **Frontend**: Không đổi
- **API**: Không đổi
- **Dependencies**: Không thêm
- **Phase**: Phase 2

## Non-goals

- Không thêm nguồn Trung Quốc (đã làm)
- Không thêm nguồn VN (sẽ làm Phase 2B)
- Không thêm GitHub Trending (sẽ là connector riêng — change 5)
- Không thêm Twitter/X qua RSSHub (defer)
- Không thêm Product Hunt (defer)
- Không thêm Design/Content sources (defer Phase 3)

## Lưu ý quan trọng

- **Phụ thuộc**: Change này phải chạy **sau** `add-china-ai-sources` vì cần `region`/`target_roles` columns. Nếu chạy song song, OpenSpec apply phải sequence theo thứ tự.
- Một số RSS có thể đã ngưng (ví dụ một số dev.to category feed) — verify trước seed
- dev.to chia feed theo tag: cần chọn 2-3 tag relevant nhất (ai, machine-learning, devops) thay vì lấy main feed (quá noisy)
- Stack Overflow Blog đã chuyển sang Stack Overflow Labs gần đây — verify URL hiện tại
