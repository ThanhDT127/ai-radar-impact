## ADDED Requirements

### Requirement: Seed sources mở rộng layer Global AI/Dev/Security

`scripts/seed_sources.py` MUST bao phủ thêm tối thiểu 11 nguồn region=global thuộc 3 cluster: Global AI missing (HF Blog, Stack Overflow), Dev/DevOps (dev.to AI/ML, JetBrains, Docker, K8s), Security (KrebsOnSecurity, BleepingComputer, MS Security, GH Security Blog). Anthropic + Papers With Code defer — không tìm thấy RSS endpoint hợp lệ.

#### Scenario: Seed Global AI missing
- **WHEN** chạy `seed_sources`
- **THEN** tạo (hoặc skip nếu tồn tại):
  - Anthropic
  - Hugging Face Blog
  - Papers With Code
- **THEN** tất cả `region = "global"`, `trust_tier ∈ {very_high, high}`, `target_roles ⊇ {Engineering, Data/AI}`

#### Scenario: Seed Dev/DevOps cluster
- **WHEN** chạy `seed_sources`
- **THEN** tạo:
  - Stack Overflow Blog
  - dev.to (tag-specific feeds: ai, machinelearning)
  - JetBrains Blog
  - Docker Blog
  - Kubernetes Blog
- **THEN** `target_roles ⊇ {Engineering}`; DevOps sources thêm `Toàn công ty`

#### Scenario: Seed Security cluster
- **WHEN** chạy `seed_sources`
- **THEN** tạo:
  - KrebsOnSecurity
  - BleepingComputer
  - Microsoft Security Blog
  - GitHub Security Lab
- **THEN** `topics ⊇ ["An ninh mạng"]`, `target_roles ⊇ {Engineering, Legal/Compliance, Toàn công ty}`

#### Scenario: URL verify trước seed
- **WHEN** thêm URL vào seed list
- **THEN** URL phải pass `verify_feeds.py` (returns ≥1 entry, HTTP 200)
- **THEN** URL fail → loại khỏi batch và document trong tasks
