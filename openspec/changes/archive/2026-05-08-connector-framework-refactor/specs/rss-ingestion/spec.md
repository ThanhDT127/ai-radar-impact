## MODIFIED Requirements

### Requirement: RSSConnector implements BaseConnector
`RSSConnector` giờ kế thừa `BaseConnector` và trả về `ConnectorEntry` thay vì `FeedEntry`.

#### Scenario: RSS fetch output
- **WHEN** `RSSConnector.fetch(source)` được gọi
- **THEN** trả về `list[ConnectorEntry]` thay vì `list[FeedEntry]`

#### Scenario: Backward compatibility
- **WHEN** RSS ingestion chạy với connector mới
- **THEN** kết quả `raw_documents` phải giống hệt trước refactor (cùng fingerprint, cùng normalized_content)

### Requirement: Normalizer nhận ConnectorEntry
`normalizer.py` giờ nhận `ConnectorEntry` thay vì `FeedEntry`.

#### Scenario: Normalize generic entry
- **WHEN** `normalize_entry(entry: ConnectorEntry)` được gọi
- **THEN** trả về `(normalized_content, fingerprint)` — logic xử lý không đổi
