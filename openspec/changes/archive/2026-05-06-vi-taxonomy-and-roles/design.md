# Design: Vietnamese Taxonomy & Roles/Published_at

## 1. Taxonomy tiếng Việt — Mapping hoàn chỉnh

### 1.1 Chủ đề (ALLOWED_TOPICS)

| Giá trị hiện tại (EN) | Giá trị mới (VI) |
|---|---|
| AI | Trí tuệ nhân tạo |
| Technology | Công nghệ |
| Data | Dữ liệu |
| Software Process | Quy trình phần mềm |
| Security | An ninh mạng |
| Legal/Compliance | Pháp lý/Tuân thủ |
| Content/Marketing | Nội dung/Marketing |
| Service/Platform | Dịch vụ/Nền tảng |
| Market/Competitor | Thị trường/Đối thủ |
| Internal Governance | Quản trị nội bộ |

### 1.2 Loại sự kiện (ALLOWED_EVENT_TYPES)

| EN | VI |
|---|---|
| New release | Phát hành mới |
| Policy change | Thay đổi chính sách |
| Regulation update | Cập nhật quy định |
| Security alert | Cảnh báo bảo mật |
| Deprecation | Ngừng hỗ trợ |
| Trend signal | Tín hiệu xu hướng |
| Community discussion | Thảo luận cộng đồng |
| Research update | Cập nhật nghiên cứu |
| Operational incident | Sự cố vận hành |

### 1.3 Tính chất (ALLOWED_NATURES)

| EN | VI |
|---|---|
| Risk | Rủi ro |
| Opportunity | Cơ hội |
| Compliance | Tuân thủ |
| Informational | Thông tin chung |
| Watchlist | Theo dõi |

### 1.4 Mức ảnh hưởng (Impact Labels)

| EN | VI |
|---|---|
| Critical | Nghiêm trọng |
| High | Cao |
| Medium | Trung bình |
| Low | Thấp |
| Watch | Theo dõi |

### 1.5 Đối tượng ảnh hưởng (ALLOWED_ROLES)

Theo spec `02_frd` section 6.7:

```python
ALLOWED_ROLES = [
    "Executive",
    "Engineering",
    "Data/AI",
    "Product",
    "Content/Marketing",
    "Legal/Compliance",
    "HR/L&D",
    "Toàn công ty",
]
```

> Lưu ý: Giữ role names bằng tiếng Anh (trừ "All company" → "Toàn công ty") vì đây là tên phòng ban/vai trò quốc tế phổ biến trong doanh nghiệp.

## 2. Prompt Gemini — Cập nhật

### 2.1 Prompt mới (tiếng Việt)

```
Bạn là chuyên gia phân tích AI. Phân tích bài viết sau và trả về JSON.

QUY TẮC:
- Chỉ sử dụng thông tin có trong bài viết
- KHÔNG suy đoán hoặc thêm kiến thức bên ngoài
- summary_short tối đa 200 ký tự, 1-2 câu, bằng tiếng Việt
- summary_medium tối đa 500 ký tự, 1 đoạn, bằng tiếng Việt
- topics chỉ chứa giá trị từ danh sách cho phép
- event_type chỉ chọn 1 giá trị từ danh sách
- nature chỉ chọn 1 giá trị từ danh sách
- affected_roles: chọn 1 hoặc nhiều vai trò bị ảnh hưởng
- Nếu không chắc chắn, đặt confidence dưới 0.5

CHỦ ĐỀ CHO PHÉP: {topics}
LOẠI SỰ KIỆN CHO PHÉP: {event_types}
TÍNH CHẤT CHO PHÉP: {natures}
VAI TRÒ CHO PHÉP: {roles}

Trả về JSON hợp lệ (không markdown, không code block):
{{
  "topics": ["<chủ đề>"],
  "event_type": "<loại sự kiện>",
  "nature": "<tính chất>",
  "summary_short": "<1-2 câu tối đa 200 ký tự bằng tiếng Việt>",
  "summary_medium": "<1 đoạn tối đa 500 ký tự bằng tiếng Việt>",
  "affected_roles": ["<vai trò>"],
  "confidence": <0.0 đến 1.0>
}}

TIÊU ĐỀ BÀI VIẾT: {title}

NỘI DUNG BÀI VIẾT:
{content}
```

### 2.2 Build function update

`build_prompt()` cần thêm param `roles` và format vào prompt.

## 3. Data model — Thay đổi

### 3.1 Model Insight — Thêm columns

```python
# Trong backend/app/models/insight.py
affected_roles: Mapped[list[str]] = mapped_column(
    ARRAY(String), default=list
)
published_at: Mapped[datetime | None] = mapped_column(
    nullable=True
)
```

### 3.2 Migration

```
alembic revision --autogenerate -m "add affected_roles and published_at"
```

Cả 2 columns đều nullable → không break data cũ.

### 3.3 published_at logic

`published_at` lấy từ `raw_document.published_date` (đã có từ RSS `<pubDate>`).
Nếu không có thì fallback `raw_document.created_at`.

## 4. API — Cập nhật

### 4.1 Schemas

```python
# InsightListItem thêm:
affected_roles: list[str]
published_at: datetime | None

# InsightDetail thêm:
affected_roles: list[str]
published_at: datetime | None
```

### 4.2 Routes — Query params mới

```python
GET /api/v1/insights?role=Engineering        # filter theo role
GET /api/v1/insights?sort_by=published_at    # sort mới
GET /api/v1/insights?sort_by=impact_label    # sort theo impact
```

### 4.3 Repository — Filter logic

```python
# Trong list_paginated():
if role:
    query = query.where(Insight.affected_roles.any(role))

if sort_by == "published_at":
    query = query.order_by(Insight.published_at.desc().nullslast())
elif sort_by == "impact_label":
    # Custom ordering: Nghiêm trọng > Cao > Trung bình > Thấp > Theo dõi
    impact_order = case(...)
    query = query.order_by(impact_order)
else:
    query = query.order_by(Insight.created_at.desc())
```

## 5. Analyzer service — Cập nhật

```python
# Trong analyzer.py, khi tạo insight:
insight = Insight(
    ...
    affected_roles=ai_result.get("affected_roles", []),
    published_at=raw_doc.published_date or raw_doc.created_at,
)
```

## 6. Frontend labels tiếng Việt

| Component | Thay đổi |
|-----------|----------|
| `InsightList.tsx` | "Bản tin Radar AI", "Chưa có bản tin", "Không thể tải dữ liệu" |
| `InsightDetail.tsx` | Labels tiếng Việt cho sections |
| `Layout.tsx` | Header: "AI Radar Impact" (giữ tên app EN) hoặc đổi |
| `InsightCard.tsx` | Thêm hiển thị published_at, roles badges |
| `insight.ts` | Thêm `affected_roles`, `published_at` vào interfaces |
| `insights.ts` | Thêm optional query params |

## 7. Impact label mapping trong analyzer

```python
IMPACT_LABELS_VI = {
    "Critical": "Nghiêm trọng",
    "High": "Cao",
    "Medium": "Trung bình",
    "Low": "Thấp",
    "Watch": "Theo dõi",
}
```

Logic hiện tại trong `analyzer.py` trả impact_label dựa trên event_type. Cần map sang tiếng Việt tại điểm gán.
