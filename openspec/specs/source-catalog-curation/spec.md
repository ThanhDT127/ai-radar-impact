# source-catalog-curation Specification

## Purpose
Tinh gọn và duy trì danh mục nguồn (source catalog): bật/tắt các nhánh nguồn theo giá trị áp dụng thực tế và đảm bảo seed upsert phản ánh đúng trạng thái nguồn khi re-seed.

## Requirements
### Requirement: Danh mục arXiv được tinh gọn theo giá trị áp dụng

Seed catalog MUST bật các nhánh arXiv lõi + thực dụng và tắt các nhánh nặng hàn lâm ít giá trị áp dụng, dùng host `rss.arxiv.org` nhất quán.

#### Scenario: Nhánh arXiv active
- **WHEN** chạy `seed_sources`
- **THEN** các nhánh sau `status="active"`, host `https://rss.arxiv.org/rss/<mã>`: `cs.AI`, `cs.CL`, `cs.LG`, `cs.IR`, `cs.CV`, `eess.AS`, `cs.RO`, `cs.HC`

#### Scenario: Nhánh arXiv bị tắt
- **WHEN** chạy `seed_sources`
- **THEN** `arXiv CS.SE` và `arXiv CS.CR` có `status="inactive"`
- **THEN** `run_ingestion` KHÔNG cào hai nguồn này

#### Scenario: Chuẩn hoá host cs.IR
- **WHEN** seed `arXiv CS.IR`
- **THEN** `feed_url = https://rss.arxiv.org/rss/cs.IR` (không còn `export.arxiv.org`)

### Requirement: Seed upsert phải cập nhật `status`

Hàm `seed()` khi cập nhật nguồn đã tồn tại MUST ghi cả trường `status` (không chỉ config/feed_url/trust_tier/topics/region/target_roles), để lệnh bật/tắt nguồn trong seed có hiệu lực khi re-seed.

#### Scenario: Re-seed tắt nguồn đang active
- **WHEN** nguồn đã tồn tại với `status="active"` và seed dict khai `status="inactive"`
- **THEN** sau `seed()`, row DB có `status="inactive"`

#### Scenario: Re-seed giữ nguồn active
- **WHEN** seed dict không khai `status`
- **THEN** dùng mặc định `status="active"` (không vô tình tắt nguồn đang chạy)

#### Scenario: Không đụng schema
- **WHEN** áp dụng thay đổi seed
- **THEN** KHÔNG cần migration DB (cột `status` đã tồn tại)
