## Context

`insight-prompt-revamp` đã archive với 7 actionable fields. Khi user xem dashboard với insights mới, phát hiện UI hiển thị badge trùng và taxonomy thiếu các vai trò technical phổ biến. Đây là change "polish + coverage" để:

1. Fix 2 UI bugs nhỏ nhưng gây nhiễu
2. Đóng gap về taxonomy roles (5 role bổ sung)
3. Đóng gap về source granularity (sub-channel feeds)

### Modules bị ảnh hưởng

- **M4 (AI Analysis)**: `ALLOWED_ROLES` mở rộng → prompt thay đổi; cần document trong CLAUDE.md
- **M2 (Ingestion)**: Seed thêm sources với `target_roles` differentiated
- **M7 (Frontend)**: 3 component (`InsightCard`, `MomentumIndicator`, `RoleBadge`) update render logic

### Trạng thái hiện tại

- `ALLOWED_ROLES = ["Executive", "Engineering", "Data/AI", "Product", "Content/Marketing", "Legal/Compliance", "HR/L&D", "Toàn công ty"]` (8 entries)
- `InsightCard`: render `<UrgencyBadge>` + `<ImpactBadge>` SONG SONG → duplicate "Trung bình" khi cả 2 cùng giá trị
- `MomentumIndicator`: render cho cả `new` và `rising`, hide `mature`
- 18 sources hiện tại (xem `seed_sources.py`)

## Goals / Non-Goals

**Goals:**
- Card không còn 2 badge cùng text
- "Mới" pill không hiện trên hầu hết card mới
- Recommendations cho insight Kubernetes/CVE → có entry cho `DevOps`/`Security`
- Insight về security từ arXiv → có nguồn `arXiv CS.CR` riêng (target_roles=Security)

**Non-Goals:**
- Không backfill `affected_roles` của 407 insight cũ với 5 role mới
- Không refactor mapping rule cho `urgency`
- Không thay đổi schema (chỉ thay đổi closed set + UI conditional)

## Decisions

### D1: Hide ImpactBadge khi có UrgencyBadge

Logic:
```tsx
{insight.urgency
  ? <UrgencyBadge urgency={insight.urgency} />
  : <ImpactBadge label={insight.impact_label} />
}
```

Lý do: `urgency` derive từ `impact_label` + recency, nên thông tin đầy đủ hơn. Insight cũ (urgency=null) vẫn fallback `ImpactBadge`.

### D2: MomentumIndicator chỉ render `rising`

```tsx
if (!momentum || momentum !== 'rising') return null;
```

Lý do:
- `new` (cluster_size=1, age<3 days) → đã được `RelativeTime` ("2 giờ trước") thể hiện
- `mature` (>7 days hoặc cluster nhỏ) → không có signal value
- `rising` (≥3 nguồn cùng cluster trong <7 ngày) → tín hiệu thật về xu hướng đang leo

### D3: 5 vai trò mới — định nghĩa rõ ràng

| Role | Mô tả | Action examples |
|---|---|---|
| `DevOps` | CI/CD, IaC, observability, deployment automation | "Test với Argo CD trên cluster staging" |
| `Infrastructure` | Cloud architecture, network, hardware, capacity planning | "Đánh giá impact lên hạ tầng GPU hiện tại" |
| `Security` | AppSec, container security, compliance kỹ thuật | "Thêm vào checklist threat modeling" |
| `BA/QA` | Requirements analysis, test automation, quality processes | "Đánh giá impact lên test plan Q1" |
| `Designer/UX` | UI/UX, design system, design tools | "Thử áp dụng vào design system v2" |

Note: Có sự overlap nhẹ với `Engineering` — quy ước Gemini chọn role **specific nhất**. Engineering là default nếu không có role nào khớp.

### D4: Color mapping cho 5 role mới

`RoleBadge` hiện dùng pattern `roleSomething` className. Bổ sung:
- DevOps → cyan (#0891b2)
- Infrastructure → indigo (#4f46e5)
- Security → red-orange (#dc2626) — đặc biệt nổi bật
- BA/QA → emerald (#10b981)
- Designer/UX → fuchsia (#d946ef)

Tránh đụng với 8 role hiện có (Executive=purple, Engineering=blue, Data/AI=teal, Product=orange, Content/Marketing=pink, Legal/Compliance=amber, HR/L&D=lime, Toàn công ty=gray).

### D5: Sub-channel sources

Phải **verify URL** trước seed. Sources mới:

| Name | URL | trust_tier | target_roles | topics |
|---|---|---|---|---|
| AWS Security Blog | https://aws.amazon.com/blogs/security/feed/ | very_high | Security, DevOps, Engineering | An ninh mạng, Dịch vụ/Nền tảng |
| AWS Compute Blog | https://aws.amazon.com/blogs/compute/feed/ | very_high | DevOps, Infrastructure, Engineering | Công nghệ, Dịch vụ/Nền tảng |
| arXiv CS.IR | https://export.arxiv.org/rss/cs.IR | high | Data/AI, Engineering | Trí tuệ nhân tạo, Dữ liệu |
| arXiv CS.SE | https://export.arxiv.org/rss/cs.SE | high | Engineering, BA/QA | Quy trình phần mềm |
| arXiv CS.CR | https://export.arxiv.org/rss/cs.CR | high | Security, Engineering | An ninh mạng |
| HF Papers | https://huggingface.co/papers (cần verify RSS endpoint) | high | Data/AI, Engineering | Trí tuệ nhân tạo, Cập nhật nghiên cứu |

`AWS ML Blog` đã có. Google Research category feeds **defer** — known gap, document trong system_overview.

### D6: Idempotent seed

`seed_sources.py` script hiện đã pattern check exists by name → skip. 5 source mới sẽ skip nếu đã tồn tại. Run an toàn nhiều lần.

### API endpoints bị ảnh hưởng

Không có. Schema không đổi.

### Bảng DB bị ảnh hưởng

Không thay đổi schema. Chỉ INSERT vào `sources` (5-6 rows mới).

## Risks / Trade-offs

| Risk | Mitigation |
|:---|:---|
| arXiv RSS endpoint thay đổi format | Đã có RSSConnector resilient, log warning + return [] |
| HF Papers không có RSS chính thức | Verify trước seed; nếu không có, defer + ghi note |
| Gemini hallucinate role mới chưa thuộc closed set | `_validate_recommendations` đã có sẵn, drop key invalid |
| User không hiểu sự khác biệt giữa 5 role mới và Engineering | Document rõ trong CLAUDE.md + tooltip role badge (defer tooltip) |
| Source mới gây spam vì arXiv ra rất nhiều paper/ngày | `IngestionService` đã có rate limit; có thể đặt `max_items=10` trong config |
| ImpactBadge variant cho insight cũ vs mới gây UX không nhất quán | Acceptable — insight cũ regenerate dần sẽ chuyển sang UrgencyBadge |
