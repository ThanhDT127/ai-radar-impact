# Design: Expand Sources & UI Tabs Redesign

## 1. Nguồn dữ liệu Phase 1 — Danh sách 15 nguồn

### 1.1 Tier A — Official AI/Tech Vendors (9 nguồn)

| # | Tên nguồn | RSS URL | Trust Tier | Topics chính | Ngôn ngữ |
|---|-----------|---------|------------|-------------|----------|
| 1 | GitHub Changelog | `github.blog/changelog/feed/` | Very High | Công nghệ, Quy trình phần mềm | EN |
| 2 | OpenAI Blog | `openai.com/blog/rss.xml` | Very High | Trí tuệ nhân tạo | EN |
| 3 | Anthropic News | `anthropic.com/news/rss` | Very High | Trí tuệ nhân tạo, An ninh mạng | EN |
| 4 | Google AI Blog | `blog.google/technology/ai/rss/` | Very High | Trí tuệ nhân tạo | EN |
| 5 | Google DeepMind | `deepmind.google/blog/rss.xml` | Very High | Trí tuệ nhân tạo, Dữ liệu | EN |
| 6 | AWS What's New | `aws.amazon.com/about-aws/whats-new/recent/feed/` | Very High | Dịch vụ/Nền tảng | EN |
| 7 | AWS ML Blog | `aws.amazon.com/blogs/machine-learning/feed/` | Very High | Trí tuệ nhân tạo, Dữ liệu | EN |
| 8 | NVIDIA Blog | `blogs.nvidia.com/feed/` | Very High | Trí tuệ nhân tạo, Công nghệ | EN |
| 9 | Cloudflare Blog | `blog.cloudflare.com/rss/` | Very High | An ninh mạng, Dịch vụ/Nền tảng | EN |

### 1.2 Tier B — Research/Professional (4 nguồn)

| # | Tên nguồn | RSS URL | Trust Tier | Topics chính | Ngôn ngữ |
|---|-----------|---------|------------|-------------|----------|
| 10 | arXiv CS.AI | `rss.arxiv.org/rss/cs.AI` | High | Trí tuệ nhân tạo | EN |
| 11 | arXiv CS.CL (NLP) | `rss.arxiv.org/rss/cs.CL` | High | Trí tuệ nhân tạo, Dữ liệu | EN |
| 12 | arXiv CS.LG (ML) | `rss.arxiv.org/rss/cs.LG` | High | Trí tuệ nhân tạo, Dữ liệu | EN |
| 13 | IEEE Spectrum | `spectrum.ieee.org/feeds/feed.rss` | High | Công nghệ, Trí tuệ nhân tạo | EN |

### 1.3 Tier B-C — Tech Press + Nguồn Việt (2 nguồn)

| # | Tên nguồn | RSS URL | Trust Tier | Topics chính | Ngôn ngữ |
|---|-----------|---------|------------|-------------|----------|
| 14 | Ars Technica | `feeds.arstechnica.com/arstechnica/technology-lab` | High | Công nghệ, An ninh mạng | EN |
| 15 | VnExpress Số hóa | `vnexpress.net/rss/so-hoa.rss` | Medium | Công nghệ, Trí tuệ nhân tạo | VI |

### 1.4 arXiv — Lưu ý đặc biệt

- arXiv RSS có volume cao (~30-100 items/ngày mỗi category)
- Config `max_items: 15` để giới hạn
- RSS connector hiện tại đã hỗ trợ `max_items` → không cần sửa connector
- Tuy nhiên, arXiv RSS format có thể khác RSS thông thường → cần verify normalizer
- arXiv title thường dài + có authors trong description → verify parsing

### 1.5 Verify script

Tạo `backend/app/scripts/verify_feeds.py`:
- Loop qua tất cả feed URLs
- Fetch + parse mỗi feed
- In: tên, số items, sample title, status
- Giúp debug nhanh khi có URL bị lỗi

## 2. UI Tabs Redesign

### 2.1 Architecture tổng thể

```
┌──────────────────────────────────────────────────────┐
│ HEADER: AI Impact Radar        [Search]  [User ▼]   │
├──────────────────────────────────────────────────────┤
│  [Tổng quan]  [Theo nguồn]  [Theo vai trò]          │
├──────────────────────────────────────────────────────┤
│  KPI Bar: [127 bản tin] [12 Nghiêm trọng] [8 Cơ hội]│
│           [15 nguồn hoạt động]                       │
├──────────────────────────────────────────────────────┤
│  Sắp xếp: [Mới nhất ▼]                              │
│                                                      │
│  ┌──────────────────────────────────────────┐        │
│  │ Insight Card...                          │        │
│  └──────────────────────────────────────────┘        │
│  ┌──────────────────────────────────────────┐        │
│  │ Insight Card...                          │        │
│  └──────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────┘
```

### 2.2 Tab 1 — Tổng quan

**Mô tả:** Feed tất cả insights, sắp xếp mặc định theo thời gian mới nhất hoặc mức ảnh hưởng tùy lựa chọn người dùng.

**Thành phần:**
- KPI Summary Bar (4 cards):
  - Tổng bản tin (count all insights trong filter time)
  - Bản tin nghiêm trọng (count impact = "Nghiêm trọng" hoặc "Cao")
  - Cơ hội (count nature = "Cơ hội")
  - Nguồn hoạt động (count sources active)
- Sort Dropdown: Mới nhất / Ảnh hưởng cao nhất / Tin cậy cao nhất
- Insight Card List (pagination với dãy số trang + jump page)

**Insight Card redesign:**
```
┌────────────────────────────────────────────────┐
│ 📰 Tiêu đề bản tin                 [Cao]      │
│ Tóm tắt ngắn 1-2 dòng...                      │
│                                                │
│ [Trí tuệ nhân tạo] [Phát hành mới]           │
│ 👥 Engineering, Data/AI                        │
│ 📅 2 giờ trước  •  Nguồn: OpenAI Blog         │
│ 🔗 Xem chi tiết →                              │
└────────────────────────────────────────────────┘
```

Thay đổi so với card hiện tại:
- Thêm dòng roles (👥)
- Thêm nguồn name
- Thêm published_at (relative time: "2 giờ trước", "Hôm qua")
- Badge impact dùng tiếng Việt
- Thêm dòng "Điều thay đổi" để giải thích ngắn gọn tín hiệu chính
- Thêm dòng "Vì sao đáng chú ý" để gắn insight với giá trị thực tế cho người đọc

### 2.2.1 Product framing cho Insight Card

Mỗi insight card phải trả lời được 3 câu hỏi trong một lần quét mắt:
- **Chuyện gì thay đổi?** — tín hiệu mới hoặc thay đổi chính của bài viết
- **Vì sao đáng chú ý?** — ý nghĩa thực tế hoặc lý do cần quan tâm
- **Ai bị ảnh hưởng?** — vai trò/phòng ban liên quan

Card không chỉ là summary của bài báo; card phải là lớp diễn giải ngắn gọn để người dùng nội bộ hiểu tác động thực tế.

### 2.3 Tab 2 — Theo nguồn

**Mô tả:** Filter insights theo source. Multi-select support.

**Thành phần:**
- Filter Chips Row:
  - Mỗi chip = 1 source name + count badge
  - Click để toggle on/off (multi-select)
  - Chip active có highlight color
  - Không phụ thuộc vào horizontal scroll dài gây khó quét
  - Trên desktop/tablet, chips nên wrap hoặc chia nhóm để nhìn thấy nhiều source cùng lúc
  - Trên mobile, nếu cần scroll phải có affordance rõ và không che nội dung
- Same Insight Card List như Tab 1
- Sort Dropdown (giống Tab 1)

**API call:**
```
GET /api/v1/insights?source_id=<uuid1>,<uuid2>&sort_by=created_at
```

**Cần API mới:**
```
GET /api/v1/sources → [{ id, name, status, insight_count }]
```

### 2.4 Tab 3 — Theo vai trò

**Mô tả:** Filter insights theo affected_roles. Multi-select support.

**Thành phần:**
- Filter Chips Row:
  - Chips: Executive | Engineering | Data/AI | Product | Content/Marketing | Legal/Compliance | HR/L&D | Toàn công ty
  - Click để toggle (multi-select)
  - Count badge trên mỗi chip
  - Layout phải ưu tiên khả năng quét nhanh, không làm người dùng phải kéo ngang liên tục
- Same Insight Card List
- Sort Dropdown

**API call:**
```
GET /api/v1/insights?role=Engineering,Data/AI&sort_by=created_at
```

### 2.5 New components

| Component | Mô tả |
|-----------|--------|
| `TabBar.tsx` | 3 tabs navigation, active state, responsive |
| `KPISummary.tsx` | 4 KPI cards, nhận data từ stats API |
| `SortDropdown.tsx` | Dropdown: Mới nhất / Ảnh hưởng / Tin cậy |
| `FilterChips.tsx` | Generic multi-select chips, badge counts |
| `RoleBadge.tsx` | Small badge hiển thị role name |
| `RelativeTime.tsx` | Component hiển thị "2 giờ trước", "Hôm qua" |

### 2.5.1 Refine components

- `FilterChips.tsx` cần hỗ trợ layout dễ quét hơn khi số lượng chip lớn
- `Pagination.tsx` cần hỗ trợ:
  - dãy số trang
  - ellipsis khi nhiều trang
  - nhập số trang để nhảy nhanh
- `ImpactBadge.tsx` cần chuẩn hóa kích thước và alignment giữa các mức độ
- `RelativeTime.tsx` cần làm rõ hơn cách hiển thị relative time và fallback ngày tuyệt đối

### 2.6 Design tokens / Colors

```css
/* Tab bar */
--tab-active-bg: var(--primary-500);
--tab-active-text: #fff;
--tab-inactive-bg: transparent;
--tab-inactive-text: var(--gray-500);

/* Filter chips */
--chip-active-bg: var(--primary-100);
--chip-active-border: var(--primary-500);
--chip-inactive-bg: var(--gray-50);
--chip-inactive-border: var(--gray-200);
--chip-count-bg: var(--primary-500);
--chip-count-text: #fff;

/* KPI cards */
--kpi-bg: var(--gray-50);
--kpi-border: var(--gray-100);
--kpi-value-color: var(--gray-900);
--kpi-label-color: var(--gray-500);
```

### 2.7 Responsive design

- **Desktop (>1024px):** KPI bar 4 columns, cards full width
- **Tablet (768-1024px):** KPI bar 2x2, cards full width
- **Mobile (<768px):** KPI bar stack, tabs dropdown/scroll, cards stack
- **Mobile verification target (375px):**
  - Tab bar không vỡ layout
  - Filters không che nội dung card
  - Card metadata không chồng lấn
  - Pagination vẫn thao tác được bằng ngón tay

### 2.8 Backend API mới cần thiết

**`GET /api/v1/sources`** — list sources cho filter chips
```json
[
  {
    "id": "uuid",
    "name": "OpenAI Blog",
    "source_type": "rss",
    "status": "active",
    "insight_count": 23
  }
]
```

**`GET /api/v1/insights/stats`** — KPI data
```json
{
  "total": 127,
  "critical_high": 12,
  "opportunities": 8,
  "active_sources": 15
}
```

### 2.9 Insight Detail page update

Thêm sections:
- **Vai trò ảnh hưởng:** Hiển thị roles badges
- **Thời gian:** published_at (thời gian bài gốc) + created_at (thời gian phân tích)
- **Nguồn:** Source name + link

## 3. Refinement decisions bổ sung

### 3.1 Pagination

- Giữ pagination thay vì infinite scroll
- UI pagination phải hỗ trợ:
  - Previous / Next
  - dãy số trang gần trang hiện tại
  - nút tới trang đầu/trang cuối khi cần
  - nhập số trang để nhảy trực tiếp

### 3.2 Title hiển thị

- Trong phạm vi change này, UI phải ưu tiên một tiêu đề dễ đọc hơn cho người dùng tiếng Việt
- Nếu chưa có `title_vi` từ pipeline AI, UI cần có chiến lược hiển thị giảm mỏi mắt:
  - ưu tiên wrap tốt
  - tránh card bị quá dày chữ
  - ưu tiên phần “chuyện gì thay đổi” để người dùng không phải đọc hết title gốc

### 3.3 Impact badge

- Badge impact là metadata hệ thống, không phải phần minh họa trang trí
- Tất cả badge phải có cấu trúc, chiều cao, và alignment nhất quán
- Khác biệt chính nằm ở màu và label, không phải ở kích thước khối nền
