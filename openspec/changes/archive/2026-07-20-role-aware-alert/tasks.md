# Tasks: role-aware-alert

> Thứ tự bắt buộc: sinh dữ liệu trước (nhóm 1–2), đổi điều kiện gửi sau (nhóm 3). Làm ngược lại sẽ có
> giai đoạn không insight nào đủ điều kiện alert. Nghiệm thu ở tầng service + DB, không cần gửi
> Telegram thật cho tới task 4.3.

## 0. Chốt taxonomy vai trò (tiền đề — T9 "xác định các vai trò đã triển khai")

> Làm trước nhóm 1: prompt sắp chấm `urgency` theo vai trò, nên phải chắc "vai trò" là bộ nào.

- [x] 0.1 Chốt `ALLOWED_ROLES` (9 chức danh) là bộ duy nhất cho `affected_roles` / `recommendations` / `Subscriber.roles`. Không mở rộng thêm vai trò — DevOps/Tester/Hạ tầng/PM nêu trong lịch trình W4 thuộc taxonomy `target_roles` của Source, không phải bộ này. **DoD:** code đã nhất quán sẵn (`prompts.py:35`, `bot/handlers.py`, `RoleBadge.tsx`), không cần sửa code.
- [x] 0.2 Sync tài liệu gọi sai tên hai taxonomy. **DoD:** `CLAUDE.md` liệt kê đúng 9 chức danh + cảnh báo phân biệt `target_roles`; `openspec/specs/ai-analysis/spec.md` thay requirement "mở rộng 13 vai trò" (chưa từng khớp code) bằng "9 chức danh"; `openspec/specs/source-region-tagging/spec.md` gọi bộ 13 là `TARGET_ROLE_TAXONOMY`.

## 1. Sinh `urgency` theo vai trò

- [x] 1.1 Thêm tập đóng `ALLOWED_ROLE_URGENCY = ["high", "medium", "low"]` vào `app/ai/prompts.py`, tách bạch với 4 mức của `insights.urgency`. **DoD:** hằng số tồn tại, có comment nêu rõ khác biệt hai khái niệm. ✅ `prompts.py:49`.
- [x] 1.2 Sửa prompt phân tích: mỗi entry `recommendations` sinh thêm `urgency`; hướng dẫn chấm tiết kiệm, `high` chỉ cho tin vai trò đó cần đọc ngay trong ngày. Cập nhật cả JSON schema mẫu trong prompt. **DoD:** gọi Gemini thật trên 3 doc, output có `urgency` hợp lệ ở mọi entry. ✅ Vượt DoD: 30 doc ở task 2.1 (83 entry, **0 thiếu khoá, 0 giá trị sai**) + 16 insight thật ở nhóm 4 (16/16 mang `urgency`).
- [x] 1.3 Validate post-parse trong `AnalyzerService`: `urgency` thiếu hoặc ngoài tập đóng → đặt `medium` + log warning, KHÔNG drop cả entry. **DoD:** unit test 3 nhánh (hợp lệ / sai giá trị / thiếu khoá). ✅ `tests/test_role_urgency_validation.py`, 9 test xanh.
- [x] 1.4 **(phát sinh khi implement)** Ép `affected_roles ⊆ ALLOWED_ROLES` bằng `_validate_affected_roles`, và sửa 2 few-shot example trong prompt vốn đang dạy Gemini dùng taxonomy `target_roles` (`DevOps`, `Data/AI`, `Infrastructure`). **Lý do:** `_validate_recommendations` chỉ kiểm `role ∈ affected_roles` — vòng tròn, giá trị ngoài tập đóng lọt qua miễn Gemini tự nhất quán. Nếu không sửa, subscriber (chọn role từ bộ 9 qua bot) không bao giờ khớp `recommendations["DevOps"]` → change này ra 0 alert. **DoD:** test drop giá trị target_roles + few-shot chỉ còn vai trò hợp lệ. ✅

## 2. Đo trước khi đổi hành vi gửi

- [x] 2.1 Chạy phân tích trên ≥30 doc thật, đo **phân bố `urgency` theo vai trò**. **DoD:** bảng tỉ lệ high/medium/low; ghi vào change. ✅ 30 doc → `measurement.md`. high 4.8% / medium 59.0% / low 36.1%; 0 lỗi parse, 0 entry thiếu `urgency`, 0 role ngoài tập đóng.
- [x] 2.2 Đối chiếu kỳ vọng: tỉ lệ `high` quá cao (spam) hay quá thấp (không còn alert)? **DoD:** kết luận rõ — giữ ngưỡng `high`, hay chỉnh prompt rồi đo lại. Đây là **gate**: chưa đạt thì chưa làm nhóm 3. ✅ **ĐẠT — giữ ngưỡng `high`.** 13% doc có ≥1 vai trò `high` ≈ tỉ lệ alert hiện hành (11%), không spam; AI Engineer nhận `high` — vai trò phi bảo mật đã có đường ra alert. Theo dõi: Tech Lead/Dev 0 `high` trên mẫu này.

## 3. Đổi điều kiện gửi alert

- [x] 3.1 `insight_repo.list_for_delivery`: bỏ lọc `Insight.urgency == 'critical'` cho nhánh alert; trả insight trong lookback để tầng service lọc theo vai trò. **DoD:** không còn tham chiếu `urgency == 'critical'` trong đường alert. ✅ Bỏ luôn tham số `critical` — cả alert lẫn digest cùng dùng một truy vấn.
- [x] 3.2 `DeliveryEngine`: chọn người nhận alert theo `recommendations[role].urgency == "high"` giao với vai trò subscriber; vai trò vắng trong `recommendations` → không alert. **DoD:** unit test 4 nhánh. ✅ `alert_roles_match()` + 5 test (high nhận / medium không / vắng recommendations không / thiếu khoá urgency không / recommendations NULL không). Thêm `matched_alert_roles()` để log lý do gửi (DoD 4.1).
- [x] 3.3 Kiểm không hồi quy digest: insight không alert vẫn phải vào digest đúng người. **DoD:** test digest hiện có vẫn xanh + 1 test mới cho tin bị loại khỏi alert. ✅ **Digest KHÔNG giữ nguyên logic cũ** — xem ghi chú lệch bên dưới. 79 test xanh.

> **Lệch so với artifact (3.2/3.3):** tasks.md gốc viết "Digest giữ nguyên logic cũ", nhưng giữ nguyên
> `critical=False` sẽ gửi trùng: tin `Phát hành mới` có AI Engineer ở `high` vừa alert vừa vào digest
> của chính người đó. Spec delta (`specs/delivery-engine/spec.md:15`) đã định nghĩa đúng — "tin đó rơi
> vào digest của họ" với *họ* là người KHÔNG được alert. Nên digest nay là **phần bù của alert theo
> từng subscriber**: `roles_match AND NOT alert_roles_match`. Hệ quả: tin `urgency=critical` toàn cục
> mà không vai trò nào `high` giờ **vào digest** (trước kia bị loại) — test
> `test_digest_excludes_critical` được thay bằng 2 test phản ánh luật mới.

## 4. Nghiệm thu

- [x] 4.1 Chạy `run_delivery --alert` với dữ liệu thật trên môi trường local. **DoD:** đúng những vai trò có `urgency = high` nhận tin; log liệt kê rõ ai nhận vì lý do gì. ✅ 5 alert gửi cho subscriber `{AI Engineer, Security}`; đối chiếu DB: cả 5 đều có đúng 1 trong 2 vai trò đó ở `high`. Thêm log `matched_alert_roles()` nêu rõ vai trò nào kích hoạt.
- [x] 4.2 Kiểm insight cũ (chưa có khoá `urgency`) không sinh alert hồi tố. **DoD:** 0 alert cho nhóm này. ✅ 171 insight published có `recommendations`, **0 cái có khoá `urgency`**; `run_delivery --alert` trả `{'sent': 0, 'skipped': 0}`.
- [x] 4.3 Gửi thử Telegram thật 1 chu kỳ alert + 1 digest. **DoD:** tin đến đúng nhóm, nội dung render đúng, không trùng lặp. ✅ 5 alert + 1 digest, Telegram trả 200 hết. Trùng lặp alert↔digest: **0 với insight mới**; phát hiện 13 insight **cũ** bị nhắc lại (từng alert theo luật `critical`, nay không có role urgency nên lọt vào digest) → đã vá bằng chốt chặn `delivery_log kind='alert'` trong `run_digest` + test. Digest đã gửi trước khi vá vẫn chứa 13 tin đó; từ chu kỳ sau không tái diễn.

## 5. Tài liệu

- [x] 5.1 Ghi vào `CLAUDE.md`: phân biệt `insights.urgency` (mức ảnh hưởng của tin nói chung, dùng cho dashboard/sort) với `recommendations[role].urgency` (mức ảnh hưởng tới riêng vai trò, dùng để quyết định alert). **DoD:** người đọc sau không nhầm hai khái niệm. ✅ Bảng so sánh 4 dòng trong mục "Insight Schema v2".
- [x] 5.2 Cập nhật `docs/system_overview.md` phần delivery: ngữ nghĩa alert nay là "đáng đọc ngay với vai trò của bạn", không phải "khẩn cấp phải xử lý". **DoD:** mô tả khớp hành vi thật. ✅ Mục "Alert được gửi cho ai" + sửa dòng tổng kết cuối file.
