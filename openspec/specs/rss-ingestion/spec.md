## Purpose

RSS Ingestion fetch RSS feeds từ whitelisted sources, normalize content, và lưu thành raw_documents để analyzer xử lý. Hỗ trợ sub-channel feeds với target_roles để route nội dung theo vai trò.
## Requirements
### Requirement: RSS feed fetching

Hệ thống MUST fetch được RSS feed từ URL đã cấu hình, parse XML thành danh sách entries, và lưu mỗi entry thành 1 raw document trong database.

#### Scenario: Fetch RSS feed thành công
- **WHEN** chạy ingestion cho source có `ingest_method=rss` và `feed_url=https://github.blog/changelog/feed/`
- **THEN** hệ thống fetch RSS XML, parse ra danh sách entries, mỗi entry tạo 1 record trong `raw_documents`

#### Scenario: Feed không truy cập được
- **WHEN** RSS feed URL trả về HTTP error hoặc timeout (>30s)
- **THEN** ghi log error với source_id, URL, HTTP status, không tạo raw document nào, không crash pipeline

#### Scenario: Feed XML không hợp lệ
- **WHEN** RSS feed trả về nội dung không phải XML hợp lệ
- **THEN** ghi log warning, skip source này, tiếp tục pipeline cho source khác (nếu có)

### Requirement: HTML normalization

Raw content từ RSS thường chứa HTML tags, entities, inline styles. Normalizer MUST clean thành plain text có cấu trúc.

#### Scenario: Clean HTML thành plain text
- **WHEN** raw document có `raw_content` chứa HTML tags (`<p>`, `<a>`, `<code>`, `<ul>`)
- **THEN** normalizer trả về plain text giữ nguyên nội dung ngữ nghĩa, bỏ HTML tags, giữ line breaks hợp lý

#### Scenario: Extract metadata từ RSS entry
- **WHEN** parse 1 RSS entry
- **THEN** extract được: `title`, `published_date` (ISO 8601), `source_url` (link gốc), `author` (nếu có)

### Requirement: Deduplication bằng fingerprint

Không lưu trùng document đã xử lý trước đó. Dùng content fingerprint (hash) để detect duplicate. Hệ thống MUST skip document trùng fingerprint.

#### Scenario: Document mới (chưa có trong DB)
- **WHEN** fingerprint (SHA-256 của `source_url + title`) chưa tồn tại trong `raw_documents`
- **THEN** tạo record mới với status `pending`

#### Scenario: Document trùng (đã ingest trước)
- **WHEN** fingerprint đã tồn tại trong `raw_documents`
- **THEN** skip document này, ghi log debug "duplicate skipped", không tạo record mới

### Requirement: CLI trigger

Ingestion MUST được trigger thủ công bằng CLI command (chưa cần scheduler tự động).

#### Scenario: Trigger ingestion cho tất cả active sources
- **WHEN** chạy `python -m backend.scripts.run_ingestion`
- **THEN** fetch + normalize + dedup cho tất cả sources có `status=active`, log kết quả (số new, số skipped, số errors)

#### Scenario: Trigger ingestion cho 1 source cụ thể
- **WHEN** chạy `python -m backend.scripts.run_ingestion --source-id <uuid>`
- **THEN** chỉ xử lý source có id đó

### Requirement: RSSConnector implements BaseConnector
`RSSConnector` MUST kế thừa `BaseConnector` và trả về `ConnectorEntry` thay vì `FeedEntry`.

#### Scenario: RSS fetch output
- **WHEN** `RSSConnector.fetch(source)` được gọi
- **THEN** trả về `list[ConnectorEntry]` thay vì `list[FeedEntry]`

#### Scenario: Backward compatibility
- **WHEN** RSS ingestion chạy với connector mới
- **THEN** kết quả `raw_documents` phải giống hệt trước refactor (cùng fingerprint, cùng normalized_content)

### Requirement: Normalizer nhận ConnectorEntry
`normalizer.py` MUST nhận `ConnectorEntry` thay vì `FeedEntry`.

#### Scenario: Normalize generic entry
- **WHEN** `normalize_entry(entry: ConnectorEntry)` được gọi
- **THEN** trả về `(normalized_content, fingerprint)` — logic xử lý không đổi

### Requirement: Sub-channel sources được seed với target_roles differentiated

`scripts/seed_sources.py` MUST seed thêm 5-6 sub-channel sources với `target_roles` chính xác để insights được route đúng vai trò.

#### Scenario: AWS sub-channels
- **WHEN** `seed_sources` chạy
- **THEN** tạo (hoặc skip nếu đã có) 2 sources mới:
  - `AWS Security Blog` (https://aws.amazon.com/blogs/security/feed/, target_roles=Security/DevOps/Engineering)
  - `AWS Compute Blog` (https://aws.amazon.com/blogs/compute/feed/, target_roles=DevOps/Infrastructure/Engineering)

#### Scenario: arXiv sub-channels
- **WHEN** `seed_sources` chạy
- **THEN** tạo thêm 3 sources arXiv:
  - `arXiv CS.IR` (Information Retrieval, target_roles=Data/AI, Engineering)
  - `arXiv CS.SE` (Software Engineering, target_roles=Engineering, BA/QA)
  - `arXiv CS.CR` (Cryptography & Security, target_roles=Security, Engineering)

#### Scenario: HuggingFace Papers
- **WHEN** `seed_sources` chạy AND HF Papers RSS endpoint hoạt động
- **THEN** tạo source `HF Papers` (target_roles=Data/AI, Engineering, topics=["Trí tuệ nhân tạo", "Cập nhật nghiên cứu"])
- **WHEN** endpoint không tồn tại / 404
- **THEN** skip source HF Papers, log warning, không crash seed

#### Scenario: Idempotent
- **WHEN** `seed_sources` chạy lần thứ 2 trên DB đã có 5-6 source mới
- **THEN** skip tất cả, không tạo duplicate, không lỗi

### Requirement: Sub-channel sources kế thừa pattern đã có

5-6 source mới MUST tuân theo pattern hiện tại của `Source` model: có `source_type="rss"`, `feed_url`, `trust_tier`, `topics`, `target_roles` (nếu schema có), `status="active"`.

#### Scenario: Phù hợp ConnectorRegistry
- **WHEN** `IngestionService` xử lý source mới
- **THEN** `ConnectorRegistry.get("rss")` trả `RSSConnector` instance
- **THEN** fetch + normalize hoạt động như source RSS hiện tại

#### Scenario: target_roles hợp lệ
- **WHEN** seed source mới
- **THEN** mỗi role trong `target_roles` MUST ∈ `ALLOWED_ROLES` (13 entries sau mở rộng)

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

