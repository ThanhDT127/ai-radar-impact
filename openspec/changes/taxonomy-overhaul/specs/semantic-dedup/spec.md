## MODIFIED Requirements

### Requirement: Tính `vietnam_relevance` từ source + topics

Rule D4: high/medium/low từ source.config.language + topics MỚI.

#### Scenario: Tính `vietnam_relevance` từ source + topics mới
- **WHEN** tạo insight có `source.config.language` và `topics` (taxonomy mới)
- **THEN** `language = "vi"` OR `topics` chứa `"Legal & Regulation"` → `vietnam_relevance = "high"`
- **THEN** `topics` chứa Vietnamese-specific topic (`"Team & Process"`) → `medium`
- **THEN** còn lại → `low`
