## ADDED Requirements

### Requirement: Seed sources mở rộng China AI ecosystem

`scripts/seed_sources.py` MUST bao phủ tối thiểu 5 nguồn về China AI (HuggingFace org RSS yêu cầu auth — defer; thay thế bằng Substack newsletters + GitHub releases.atom cho flagship repos).

#### Scenario: Seed China AI organizations
- **WHEN** chạy `python -m app.scripts.seed_sources`
- **THEN** tạo (hoặc skip nếu đã tồn tại) các sources với `region = "china"`:
  - DeepSeek
  - Qwen / Alibaba
  - GLM / Zhipu
  - Yi / 01.AI
  - Kimi / Moonshot
  - Tencent Hunyuan
  - MiniMax
  - Baichuan

#### Scenario: Seed analyst newsletters về China AI
- **WHEN** chạy seed_sources
- **THEN** tạo 2 sources với `region = "china"`:
  - Interconnects (Substack)
  - ChinaTalk (Substack)

#### Scenario: URL feed verified trước seed
- **WHEN** thêm source mới vào seed list
- **THEN** URL feed phải được verify (trả non-empty entries) trước khi commit
- **THEN** nếu verify fail, source được defer sang phase sau (không seed)

### Requirement: Tất cả sources có `target_roles` non-empty

Mỗi source MUST có `target_roles` non-empty để dashboard filter theo vai trò hoạt động đúng.

#### Scenario: China AI sources có target roles
- **WHEN** seed China AI sources
- **THEN** mỗi source có `target_roles` chứa ít nhất {`Engineering`, `Data/AI`}

#### Scenario: Newsletters có target roles rộng hơn
- **WHEN** seed Interconnects, ChinaTalk
- **THEN** `target_roles` chứa `Executive`, `Data/AI`, `Engineering` (analyst content phù hợp leadership)
