## ADDED Requirements

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
