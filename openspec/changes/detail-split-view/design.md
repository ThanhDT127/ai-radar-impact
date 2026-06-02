## Context

`InsightDetail.tsx` (240 LOC) hiện render 1 cột dọc: back link → header → meta → body sections (signal, so_what, why_it_matters, summary, recommendations, risks, roles, topics, practical_indicators, score bar) → timeline → footer (source + "Xem bài gốc" link).

API trả `source_url` (link bài gốc), `title` (tiêu đề gốc), và tất cả AI fields. Đủ data để split-view.

## Goals / Non-Goals

**Goals:**
- Split layout: CSS Grid `grid-template-columns: 1fr 1fr` với gap
- Panel trái: tổ chức lại nội dung AI summary, thêm verification badge
- Panel phải: iframe với loading state + error fallback
- Mobile responsive: stack vertical dưới 1024px
- Smooth transition khi iframe load

**Non-Goals:**
- Không resizable divider (cố định 50/50)
- Không fetch/cache bài gốc HTML vào DB
- Không parse images từ bài gốc
- Không dịch bài gốc real-time

## Decisions

### 1. Iframe approach cho bài gốc
```tsx
<iframe
  src={insight.source_url}
  title="Bài viết gốc"
  sandbox="allow-same-origin allow-scripts"
  className={styles.originalIframe}
/>
```
**Rationale:** Zero backend change, hiện bài gốc đầy đủ. Nhược điểm: X-Frame-Options block. Fallback khi bị block.

### 2. Iframe error detection
Dùng `onLoad` event + check nếu iframe content accessible. Nếu không → hiện fallback UI.

### 3. Panel trái restructure
```
┌─────────────────────────┐
│ [Strategic] [AI/ML]      │  ← tags
│ 🔗 Bài gốc  📅 12/05    │  ← links + time
│ ─────────────────────── │
│ Tiêu đề tiếng Việt      │
│ ─────────────────────── │
│ • Bullet 1               │  ← tóm tắt 5 bullets
│ • Bullet 2               │
│ • Bullet 3               │
│ • Bullet 4               │
│ • Bullet 5               │
│ ─────────────────────── │
│ 💡 ĐIỂM MẤU CHỐT        │  ← so_what highlight
│ Text highlighted...      │
│ ─────────────────────── │
│ 👥 Khuyến nghị           │
│ DevOps → "Vào roadmap"  │
│ ─────────────────────── │
│ ⚡ 73%  🛡️ 80%  [Adopt]  │
│ ─────────────────────── │
│ 🤖 Phân tích bởi Gemini │
│ Confidence: 85%          │
└─────────────────────────┘
```

### 4. Verification badge pattern
```tsx
<div className={styles.verificationBadge}>
  <span>🤖 Phân tích bởi Gemini AI</span>
  <span>Confidence: {Math.round(insight.confidence * 100)}%</span>
</div>
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Iframe bị block bởi X-Frame-Options | Fallback: button "Mở bài gốc trong tab mới" |
| Split view quá chật trên laptop 13" | Min-width per panel 400px, scroll internal |
| Iframe load chậm | Loading spinner, lazy load |

## Module ảnh hưởng
- **M6: Dashboard** — frontend only
- **API endpoints**: Không thay đổi
- **Bảng DB**: Không thay đổi
