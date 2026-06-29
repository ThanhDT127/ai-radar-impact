# Label Localization

## Scenarios

### WHEN user views InsightCard on dashboard
THEN tier badge shows Vietnamese: "Hành động ngay" | "Vận hành" | "Chiến lược" | "Tham khảo"
AND NOT English: "Tactical" | "Operational" | "Strategic" | "Informational"

### WHEN user views InsightDetail metadata ribbon
THEN tier badge shows Vietnamese label
AND adoption badge shows Vietnamese: "Áp dụng" | "Dùng thử" | "Đánh giá" | "Tạm hoãn"
AND NOT English: "Adopt" | "Trial" | "Assess" | "Hold"
AND practical indicators show full text: "Mã nguồn" | "Benchmark" | "API" | "Hướng dẫn chuyển đổi" | "Bản vá bảo mật"
AND NOT truncated: "Migr" | "Sec" | "Bench"

### WHEN user views Breadcrumb
THEN tier segment shows Vietnamese label matching TIER_LABEL map

### WHEN technical terms appear
THEN keep English for: "API", "Benchmark", "DevOps", "Engineering" (trong role badge)
AND localize non-technical terms: "Trial" → "Dùng thử", "Hold" → "Tạm hoãn"
