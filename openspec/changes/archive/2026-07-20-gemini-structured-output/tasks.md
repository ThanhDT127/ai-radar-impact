# Tasks: gemini-structured-output

> Số liệu nền để đối chiếu (đo 20/07/2026, 438 doc / 9 vòng): lỗi parse gate 3→4→4→9 mỗi 50 doc;
> tỉ lệ qua gate **thật** 13% / 17% / 20% / 22% (thô 18/24/26/36%). Sau change, con số sẽ đổi —
> đó là mục đích, không phải hồi quy.

## 1. Đánh dấu fail-open (làm trước để đo được)

- [x] 1.1 Migration Alembic: thêm `raw_documents.gate_skipped BOOLEAN NOT NULL DEFAULT false`. **DoD:** `alembic upgrade head` chạy sạch, `downgrade -1` cũng sạch. ✅ `009_add_gate_skipped.py`; upgrade + downgrade -1 + upgrade lại đều sạch.
- [x] 1.2 `AnalyzerService`: nhánh gate lỗi (fail-open) set `gate_skipped = true` trước khi vào deep analysis. **DoD:** unit test 2 nhánh (gate ok → false, gate lỗi → true). ✅ `mark_gate_skipped()`; 4 test chạy thẳng `analyze_document` (gate lỗi / gate pass / gate loại).
- [x] 1.3 Ghi chú trong `CLAUDE.md`: thống kê tỉ lệ qua gate phải lọc `gate_skipped = false`; số liệu trước 20/07/2026 có nhiễu vì chưa có cột này. **DoD:** người tính thống kê sau đọc là biết. ✅ Mục Known Gotchas, kèm cảnh báo số liệu trước 20/07 có nhiễu.

## 2. Schema cho gate

- [x] 2.1 Dựng schema cho gate response **từ hằng số trong `prompts.py`** (không chép tay), gồm enum cho `content_type` và kiểu cho `evidence`/`noise_signals`/`actionability_score`/`pass_gate`. **DoD:** thêm một giá trị vào hằng số → schema đổi theo, có test khẳng định điều này. ✅ `app/ai/schemas.py` sinh từ hằng số; thêm `ALLOWED_CONTENT_TYPES` (trước hardcode ở 2 nơi); 9 test gồm test reload khẳng định schema bám hằng số.
- [x] 2.2 Truyền `response_schema` vào `gate_analyze`. **DoD:** chạy 30 doc thật, **0 lỗi parse JSON của gate** (nền: 3–9 lỗi/50 doc). ✅ **0 lỗi parse gate** trên 50 doc (nền 3–9/50). Batch 2: 1 lỗi.
- [x] 2.3 Nâng log raw ở nhánh parse lỗi lên ~2000 ký tự (cả gate lẫn deep analysis). **DoD:** cố tình ép một lỗi parse, log hiển thị tới vị trí vỡ. ✅ `RAW_LOG_CHARS = 2000` cho cả 2 nhánh + log thêm tổng độ dài. Chính log này chẩn đoán ra lỗi runaway ở 3.2.

## 3. Schema cho deep analysis — ĐÃ THỬ VÀ BỎ KHỎI PHẠM VI

> **Quyết định 20/07/2026: không áp `response_schema` cho `analyze`.** Đã dựng schema, bật, đo trên
> 2 batch (~80 doc) rồi revert. Code `build_analysis_schema()` và test của nó **đã xoá** — lấy lại từ
> git history nếu cần.
>
> **Đạt được:** 0 vi phạm `action_type` (nền: ~2 lần/30 doc).
> **Đánh đổi:** model sinh `why_it_matters` lặp vô nghĩa tới ~6500 ký tự (giới hạn 300) cho tới khi
> chạm `max_output_tokens` và bị cắt → **16/16 doc qua gate lỗi `Unterminated string`, 0 insight tạo
> được**. Thêm `max_length` không cứu được: Vertex không thực thi ràng buộc đó. Tăng
> `max_output_tokens` cũng không — nó chỉ cho đoạn văn rác chạy hết rồi đóng ngoặc, mà
> `why_it_matters` được render thẳng ra dashboard và tin Telegram.
>
> **Không đáng:** thứ nó mua (~2.4% entry recommendation) đã được `_validate_recommendations` xử lý
> an toàn — mất một khuyến nghị chứ không sinh dữ liệu bẩn. Đổi lại là rủi ro chất lượng nội dung
> trên mọi insight cộng chi phí token cao hơn vĩnh viễn.
>
> **Hướng đi tiếp nếu muốn lại (change riêng):** đưa vào schema các trường enum (`event_type`,
> `nature`, `action_type`, `adoption_ring`) nhưng để `why_it_matters`/`summary_*` NGOÀI schema — giữ
> lợi ích tập đóng mà không chạm trường gây runaway.

- [x] 3.3 Giữ nguyên lớp validate post-parse làm lưới an toàn — schema không thay thế nó. **DoD:** test validate cũ vẫn xanh. ✅ Càng đúng sau quyết định trên: validate post-parse nay là lớp duy nhất chặn tập đóng ở nhánh analyze.

## 4. Đo lại và đối chiếu

- [x] 4.1 Chạy ≥100 doc, đo: số lỗi parse, số vi phạm tập đóng, tỉ lệ qua gate (đã lọc `gate_skipped`). **DoD:** bảng so với số nền ở đầu file. ✅ Bảng trong `measurement.md`. ⚠️ **Mẫu 48 doc, không phải ≥100** — chốt sớm theo quyết định vận hành. Lỗi parse gate 1, `Dropping affected_role` 0, `invalid urgency` 0.
- [x] 4.2 Kiểm rủi ro "schema quá chặt": đo tỉ lệ trường null trong `evidence` và tỉ lệ `pass_gate=true`. **DoD:** kết luận rõ — schema không làm model câm. ✅ **Không câm**: tỉ lệ qua gate 62.5%, `gate_reason` vẫn là câu cụ thể theo từng bài, gate vẫn loại 18/48. ⚠️ **Không đo được tỉ lệ null của `evidence`** — kết quả gate không lưu xuống DB (design D3 cố ý). Kết luận dựa trên tỉ lệ pass + chất lượng `gate_reason` trong log.
- [x] 4.3 Dựng lại **bảng tỉ lệ qua gate theo nguồn** với dữ liệu sạch, thay bảng đã đo 20/07 (bảng cũ nhiễu vì fail-open). **DoD:** bảng mới lưu trong change, dùng được cho quyết định giữ/cắt nguồn. ✅ 9 nguồn trong `measurement.md`. **Phát hiện chính: arXiv qua gate 100% (20/20)** do NGOẠI LỆ HỌC THUẬT trong gate prompt — gate gần như không lọc nguồn này, chất lượng phụ thuộc hoàn toàn vào việc chọn category lúc seed. Ngược lại dev.to bị loại 15/18 (83%). Đầu vào tốt cho T10.

## 5. Dọn dẹp

- [x] 5.1 Rà phần hướng dẫn định dạng JSON trong prompt: schema đã ép cấu trúc thì phần nào rút gọn được để tiết kiệm token? **DoD:** quyết định rõ giữ/rút, kèm lý do; nếu rút thì đo lại chất lượng đầu ra. ✅ **QUYẾT ĐỊNH: GIỮ NGUYÊN.** Chỉ còn gate dùng schema nên phạm vi rà gọn lại chỉ ở `GATE_PROMPT` (4879 ký tự). Đo tỉ trọng: dòng template JSON **327 ký tự = 6.7%**, hai few-shot **843 ký tự = 17.3%**. Lý do giữ: (a) hai few-shot là ví dụ **quyết định** NOISE/SIGNAL, không phải ví dụ định dạng — cắt là đổi hành vi gate, vi phạm Non-Goal "không đổi tiêu chí đánh giá của gate"; (b) dòng template chỉ 6.7%, cắt được ~60 token/lượt trong khi phải chạy đo lại toàn bộ để chứng minh không hồi quy — không đáng; (c) cấu hình hiện tại đã đo là tốt (0–1 lỗi parse/50 doc), không sửa thứ đang chạy đúng để lấy 6.7% token.
