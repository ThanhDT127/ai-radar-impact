## Context

- **arXiv hiện tại** (`seed_sources.py`): active = cs.AI, cs.CL, cs.LG (host `rss.arxiv.org`), cs.IR, cs.SE, cs.CR (host `export.arxiv.org`). Note: `cs.CL` **đã active** (bản note cũ tưởng phải bật lại).
- **seed() upsert** (`seed_sources.py:867–876`): khi nguồn đã tồn tại, chỉ ghi đè `config/feed_url/trust_tier/topics/region/target_roles` — **cố tình bỏ `status`**. ⇒ set `status="inactive"` trong seed **không** tắt được row đang active.
- **target_roles**: 51/70 nguồn có tag, 19 nguồn không. Tag trộn ALLOWED_ROLES + chức danh. `target_roles` là metadata tự do (không ràng buộc prompt) — khác `affected_roles` (Gemini sinh, đóng theo ALLOWED_ROLES).
- **ALLOWED_ROLES (13)** (CLAUDE.md): Executive, Engineering, Data/AI, Product, Content/Marketing, Legal/Compliance, HR/L&D, DevOps, Infrastructure, Security, BA/QA, Designer/UX, Toàn công ty.

## Goals / Non-Goals

**Goals:** danh mục arXiv tinh gọn & thực dụng; `seed()` tắt được nguồn; `target_roles` một bộ từ vựng nhất quán (ALLOWED_ROLES); đo được độ phủ vai trò; lấp gap thật với chi phí quota tối thiểu.

**Non-Goals:** không đổi `affected_roles`; không seed ồ ạt; không đụng connector/prompt; không migration schema.

## Decisions

### 1. Trạng thái arXiv mục tiêu
| Nhánh | Host | Status | Ghi chú |
|---|---|---|---|
| cs.AI, cs.CL, cs.LG | rss.arxiv.org | active | giữ (đã đúng host) |
| cs.IR | rss.arxiv.org | active | **đổi host** từ export→rss |
| cs.CV, eess.AS, cs.RO, cs.HC | rss.arxiv.org | active | **thêm mới** |
| cs.SE, cs.CR | — | **inactive** | tắt (hàn lâm, tốn quota) |

### 2. Sửa `seed()` để upsert `status`
Thêm `existing.status = data.get("status", "active")` vào nhánh update.
**Tác dụng phụ:** nguồn nào bị tắt tay trong DB sẽ bị re-seed bật lại nếu seed dict ghi `active`. Chấp nhận được: seed trở thành nguồn chân lý (khớp convention `config.yaml` — soft-delete bằng `status`), và môi trường chạy local. Nếu cần tắt vĩnh viễn thì đặt `status="inactive"` ngay trong seed dict.

### 3. Hợp nhất `target_roles` → ALLOWED_ROLES
Ánh xạ tag chức danh hiện có sang ALLOWED_ROLES:
| Tag cũ (chức danh) | → ALLOWED_ROLES |
|---|---|
| Tech Lead | Engineering |
| Data Scientist | Data/AI |
| AI Engineer | Data/AI |
| Data Engineer | Data/AI |
| Dev | Engineering |
Sau ánh xạ, closed set `target_roles` = đúng 13 ALLOWED_ROLES (cập nhật spec `source-region-tagging`, vốn chỉ liệt 8).

### 4. T6 làm theo thứ tự: tag trước, seed sau (0 quota trước)
```
① Backfill target_roles cho 19 nguồn (dùng ALLOWED_ROLES)   — 0 quota
② Audit: đếm số nguồn/vai trò → bảng độ phủ                 — 0 quota
③ Seed bù tối thiểu cho vai trò mỏng                        — ít quota
```
Bước ① làm nhiều vai trò tự đủ. Gap thật (dự kiến) dồn vào: **Infrastructure, Legal/Compliance, BA/QA, Product, Designer/UX**.

### 5. Quyết định MỞ — phạm vi vai trò cần phủ
`Content/Marketing` và `HR/L&D` gần như 0 nguồn. Với radar AI cho team kỹ thuật, đề xuất **hạ ưu tiên** hai vai trò này (không bắt buộc đủ 5). Cần Hưng/anh Thanh xác nhận:
- (a) chỉ phủ các vai trò kỹ thuật đã triển khai (đề xuất), hoặc
- (b) phủ đủ cả 13 vai trò kể cả Marketing/HR.
Mục tiêu độ phủ: **≥5 nguồn/vai trò khi khả thi**; tối thiểu **không vai trò kỹ thuật nào 0 nguồn** sau backfill.

## Risks / Trade-offs
| Risk | Mitigation |
|---|---|
| Re-seed bật lại nguồn đã tắt tay | Đặt `status` mong muốn ngay trong seed dict; chạy local |
| Đổi host arXiv làm gãy feed | Verify từng feed `rss.arxiv.org/rss/<mã>` trả bài trước khi chốt |
| Seed bù nguồn mới đội quota | Ưu tiên tag trước; chỉ seed số ít; mỗi feed verify chạy thật |
| Ánh xạ chức danh làm mất chi tiết (DA vs DS) | Chấp nhận — ALLOWED_ROLES là bộ chuẩn hệ thống; note_2.csv chỉ là tham khảo |

## Module ảnh hưởng
- **M1: Source Management** — catalog, trust tier, target_roles
- **M2: Ingestion** — arXiv feeds bật/tắt
- **API/DB**: không đổi schema; Admin API vẫn trả `target_roles` (giá trị mới nằm trong set mở rộng)
- **AI/LLM**: không đổi (target_roles không vào prompt)
