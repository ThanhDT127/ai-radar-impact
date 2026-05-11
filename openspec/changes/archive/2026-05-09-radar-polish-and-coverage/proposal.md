## Why

Sau khi `insight-prompt-revamp` lên production, phát hiện 2 vấn đề UX và 2 gap về coverage:

**Vấn đề UI hiện tại** (sau khi regenerate insight v2):
1. Card hiện **2 badge cùng text "TRUNG BÌNH"** chồng lên nhau (1 từ `urgency=medium` → "Trung bình", 1 từ `impact_label="Trung bình"`). User confusion vì redundant — `urgency` đã derive từ `impact_label` nên không cần hiện cả 2.
2. Momentum pill `"✨ Mới"` xuất hiện trên hầu hết card mới (52/407 insight có `momentum=new` ở thời điểm dedup chạy đầu tiên) — gây nhiễu vì thông tin "mới" đã được `created_at` thể hiện. Chỉ giữ `🔥 Đang nổi lên` (`momentum=rising`) vì đây mới là tín hiệu thật sự có giá trị (≥3 nguồn cùng cluster trong < 7 ngày).

**Gap về coverage**:
3. Taxonomy `ALLOWED_ROLES` chỉ có 8 vai trò (Executive, Engineering, Data/AI, Product, Content/Marketing, Legal/Compliance, HR/L&D, Toàn công ty) — thiếu các vai trò user đã liệt kê: **DevOps, Hạ tầng (Infrastructure), Bảo mật (Security), BA/QA, Designer/UX**. Hệ quả: insight về Kubernetes/CI-CD không có khuyến nghị riêng cho DevOps; insight về CVE không có recommendations cho Security.
4. Các nguồn lớn hiện tại bị "đóng bao" thành 1 feed tổng, mất signal phân nhánh: AWS What's New (58 insights) gộp tất cả mọi thứ; arXiv CS.AI (29 insights) bỏ qua CS.IR, CS.SE, CS.CR; Hugging Face chỉ có blog tổng, không có Papers feed riêng. Khi target_role = Security, không có cách filter ra nội dung security-specific.

## What Changes

### Bug fixes (UI)

- **Hide ImpactBadge khi UrgencyBadge có giá trị** — tránh duplicate label. Insight cũ chưa regenerate (urgency=null) vẫn hiện ImpactBadge như cũ.
- **MomentumIndicator chỉ render `momentum=rising`** — `new` và `mature` đều hide. Reasoning: `new` redundant với `created_at`; `mature` không có signal value.

### Mở rộng taxonomy

- Thêm 5 vai trò vào `ALLOWED_ROLES`:
  - `DevOps` — CI/CD, observability, deployment
  - `Infrastructure` — hạ tầng (cloud, network, hardware)
  - `Security` — bảo mật ứng dụng, compliance technical
  - `BA/QA` — Business Analyst + Quality Assurance
  - `Designer/UX` — UI/UX designer, design system
- Cập nhật prompt + frontend `RoleBadge` color mapping cho 5 role mới.

### Bổ sung sub-channel feeds

Phân nhánh các nguồn tổng hợp lớn:

**AWS** (hiện 1 nguồn `What's New` tổng):
- Tách thêm `AWS Security Blog` (security category)
- `AWS ML Blog` đã có
- `AWS Compute Blog` cho EC2/Lambda/containers

**arXiv** (hiện CS.AI/CS.LG/CS.CL):
- Thêm `CS.IR` — Information Retrieval (RAG, search)
- `CS.SE` — Software Engineering
- `CS.CR` — Cryptography & Security (target_roles ⊇ Security)

**Hugging Face**:
- Hiện có `HF Blog` nội dung chung
- Thêm `HF Papers` feed (https://huggingface.co/papers/rss) — nếu có RSS chính thức; fallback skip nếu không

**Google Research** (defer — endpoint không ổn định, đánh dấu là known gap):
- Note trong design, không seed trong scope này

Tổng cộng **~5-6 sub-channel feeds mới**, mỗi nguồn có `target_roles` chính xác để insights được route đúng vai trò.

## Capabilities

### Modified Capabilities

- `ai-analysis`: Mở rộng `ALLOWED_ROLES` thêm 5 entries; prompt phải reflect role mới
- `insight-dashboard`: Card hide ImpactBadge khi có UrgencyBadge; MomentumIndicator chỉ render `rising`; RoleBadge thêm color cho 5 role
- `rss-ingestion`: Seed 5-6 sub-channel sources mới với `target_roles` differentiated

## Impact

- **Backend code**:
  - `app/ai/prompts.py` — thêm 5 entries vào `ALLOWED_ROLES`
  - `app/scripts/seed_sources.py` — thêm 5-6 source records (idempotent)
- **Frontend code**:
  - `components/InsightCard.tsx` — conditional render ImpactBadge
  - `components/MomentumIndicator.tsx` — return null cho `new` và `mature`
  - `components/RoleBadge.tsx` — color mapping cho 5 role mới
- **Database**: Không thay đổi schema. `affected_roles` đã là `VARCHAR[]` chấp nhận giá trị mới.
- **Phase**: Phase 2

## Non-goals

- Không backfill `affected_roles` của insight cũ với 5 role mới (phải re-analyze qua Gemini)
- Không thay đổi `urgency` mapping rule (vẫn derive từ `impact_label` + recency)
- Không thay đổi mapping `event_type → impact_label`
- Không xóa `momentum` khỏi schema — chỉ ẩn `new`/`mature` khỏi UI, giá trị vẫn lưu DB cho future use
- Không seed Google Research category-specific feeds (defer — endpoint không ổn định)

## Lưu ý

- 5 role mới phải được thêm vào prompt **trước** khi merge, nếu không Gemini sẽ trả role không thuộc closed set và `_validate_recommendations` sẽ drop hết
- `RoleBadge` đang tách màu theo role; cần định nghĩa color cho 5 role mới, tránh trùng màu với 8 role hiện tại
- Sub-channel sources phải verify URL hoạt động trước khi seed (xem `verify_feeds.py`)
