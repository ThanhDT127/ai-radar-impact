# Proposal: chat-context-isolation

**Phase áp dụng:** Phase 2 (củng cố M8 Chatbot — vá Nguy hiểm #3 của báo cáo kiến trúc To‑Be, không thêm tính năng).

## Why

Widget giữ **một** mảng `messages` cho cả phiên và không bao giờ xoá nó khi người dùng đổi ngữ cảnh
(`ChatWidget.tsx:43`). `send()` dựng `history` từ **toàn bộ** bong bóng không‑lỗi (`ChatWidget.tsx:115`),
rồi gửi kèm `insight_id` của ngữ cảnh **hiện tại**. Hệ quả: hội thoại của bài A vẫn bám theo khi người
dùng đã chuyển sang bài B, hoặc đã rời về danh sách để hỏi toàn cục.

```
Xem bài A (Nvidia) → hỏi "tóm tắt bài này"      history=[]                    insight_id=A  ✅
Chuyển sang bài B (OpenAI) → hỏi "rủi ro của nó" history=[…hội thoại A…]        insight_id=B  ✗
```

Câu nối tiếp mập mờ ("nó", "rủi ro thì sao") lúc này mang ngữ cảnh A trong khi server đọc bài B →
model resolve "nó" sai → trích dẫn nhầm hoặc bị fail‑closed. Đây đúng là **Nguy hiểm #3 (Context Drift /
History Poisoning)** của báo cáo To‑Be, và nó **không lộ ra qua test nào** — repo chưa có test frontend,
lỗi sống ở state của widget.

Context chip đã đồng bộ theo route (`chat-web-widget` requirement hiện có), nhưng **history thì không** —
chip đúng mà dữ liệu gửi đi vẫn nhiễm. Sửa chip mà quên history là sửa nửa vời.

## What Changes

- **Cô lập hội thoại theo ngữ cảnh (sub‑thread isolation)**: mỗi "scope" — một `insight_id` cụ thể, hoặc
  "toàn cục" — có luồng hội thoại riêng. Đổi scope thì widget hiển thị luồng của scope đó (rỗng nếu chưa
  từng hỏi) và **không** kéo theo luồng của scope cũ. Luồng cũ được giữ lại, quay về là thấy lại.
- **`history` gửi lên chỉ chứa lượt của scope hiện tại** — đây là bất biến cần khoá, dù cài đặt bằng
  tách‑luồng hay xoá‑khi‑đổi.
- **Test frontend đầu tiên cho drift**: đổi scope A→B→toàn cục, khẳng định `history` gửi lên không bao giờ
  chứa lượt của scope khác. (Repo chưa có test frontend; dựng tối thiểu — trùng nhu cầu với
  `chat-citation-integrity` task 2.4, hai change điều phối để không dựng trùng.)

## Capabilities

### New Capabilities
_(không có)_

### Modified Capabilities
- `chat-web-widget`: hội thoại SHALL được cô lập theo ngữ cảnh; `history` gửi kèm câu hỏi SHALL chỉ gồm
  các lượt thuộc ngữ cảnh hiện tại.

## Non-goals

- **Không** nén/tóm tắt history (sliding window + summarization) — cần một lượt gọi model, thuộc
  `chat-intent-router`. Change này chỉ *cô lập*, không *nén*.
- **Không** thêm scope thứ ba hay auto‑fallback — thuộc `chat-scope-routing`.
- **Không** đổi backend: `chat-qa-service` giữ nguyên request/response, vẫn stateless, vẫn nhận tối đa
  10 lượt. Sửa thuần frontend.
- **Không** đổi cách render citation, grounding, quota, hay hợp đồng `n`.

## Dependencies

- `chatbot-qa` (archive 22/07/2026) — widget và spec bị sửa thuộc change đó.
- **Điều phối với `chat-citation-integrity`** (đang mở): cả hai lần đầu dựng hạ tầng test frontend. Change
  nào land trước dựng khung; change sau dùng lại. Không chồng lấn code: change này đụng state hội thoại +
  `send()`, change kia đụng `renderAnswer` + type `Citation`.

## Impact

- **Frontend**: `components/ChatWidget.tsx` (state hội thoại theo scope, `send()` lấy history theo scope),
  test mới cho drift.
- **Backend**: không đụng.
- **Docs**: `CLAUDE.md` mục chat — thêm một dòng gotcha "history phải cô lập theo scope".
- **Không** đổi endpoint, không migration, không đụng pipeline analysis.
