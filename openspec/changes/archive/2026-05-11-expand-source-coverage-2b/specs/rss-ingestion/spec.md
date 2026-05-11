## ADDED Requirements

### Requirement: Seed sources mở rộng layer Vietnam

`scripts/seed_sources.py` MUST bao phủ thêm tối thiểu 5 nguồn `region=vietnam`. Mục tiêu ban đầu là 10 nguồn nhưng nhiều RSS endpoint (CafeF, ICTNews, VietTimes, MLOpsVN, 200lab, AIO Conquer) không hoạt động — defer cho future change với web scraper hoặc auth.

#### Scenario: Seed VN News cluster
- **WHEN** chạy `seed_sources`
- **THEN** tạo (hoặc skip nếu tồn tại):
  - GenK
  - VietnamNet ICT
  - ICT News (nếu URL verify pass)
  - CafeF Kinh tế số (nếu URL verify pass)
- **THEN** tất cả `region = "vietnam"`, `language = "vi"` (config), `target_roles ⊇ {Engineering, Product, Toàn công ty}`

#### Scenario: Seed VN Community cluster
- **WHEN** chạy `seed_sources`
- **THEN** tạo:
  - Viblo
  - Daynhauhoc
  - MLOpsVN (nếu URL verify pass)
  - Machine Learning Cơ Bản (nếu URL verify pass)
  - 200lab Blog (nếu URL verify pass)
  - AI Vietnam HuggingFace (nếu accessible)
- **THEN** `region = "vietnam"`, `target_roles ⊇ {Engineering, Data/AI}`

#### Scenario: VN sources có ngôn ngữ tiếng Việt
- **WHEN** seed VN News và VN Community sources
- **THEN** `config.language = "vi"` (trừ AI Vietnam HF có thể là `"en"` vì papers tiếng Anh)

#### Scenario: URL verify trước seed
- **WHEN** thêm URL vào seed list
- **THEN** URL phải pass `verify_feeds.py`
- **THEN** URL fail → loại khỏi batch và document trong tasks
