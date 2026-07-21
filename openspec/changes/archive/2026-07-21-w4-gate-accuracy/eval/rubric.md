# Rubric chấm tay SIGNAL / NOISE — T10 (w4-gate-accuracy)

> Viết TRƯỚC khi chấm để nhãn nhất quán giữa các dòng và giữa các vòng đo (design D-rủi ro:
> single-annotator dễ trôi). Khi phân vân → theo rubric, không theo cảm tính từng bài.

## Câu hỏi trung tâm

Với **đội ngũ kỹ thuật Rạng Đông**, bài này là tin **CÓ ẢNH HƯỞNG** (đáng để engineer đọc/hành động/theo
dõi) hay chỉ là **THÔNG BÁO / HÀN LÂM off-pillar** (đọc xong không làm gì khác ngoài "thú vị đấy")?

Chấm mỗi doc **độc lập với việc gate nói gì** — bạn là ground truth, gate là thứ đang được đo. Đọc
`title` + `content_preview` (+ mở `source_url` khi cần) rồi quyết.

## Bước 1 — TRỤ CỘT: bài có chạm trụ nào không?

Chỉ cần chạm **một** là qua bước này:

- **① IoT & thiết bị** — dữ liệu thiết bị, Edge AI, nhúng/vật lý, robotics/automation, sản xuất/nông nghiệp thông minh.
- **② Agent / AI / Data Science** — LLM, AI agent, RAG, mô hình nền tảng, MLOps, pipeline & phân tích dữ liệu.
- **③ Smart Home & Smart Lighting** — nhà/chiếu sáng thông minh, kết nối gia dụng.
- **④ Bảo mật hệ thống & dữ liệu** — CVE/lỗ hổng, chuỗi cung ứng, rò rỉ & bảo vệ dữ liệu, hardening.

→ **Không chạm trụ nào** (crypto/tài chính, game, Web3/NFT, điện thoại-tai nghe tiêu dùng, drama nhân
sự, tin ngành xa) ⇒ **NOISE**. Dừng ở đây.

## Bước 2 — CHUYỂN-GIAO: đã chạm trụ, nhưng có đáng không?

Đã chạm trụ cột thì hỏi tiếp — **SIGNAL** nếu ÍT NHẤT một điều đúng:

- Đưa ra kỹ thuật/kiến trúc/kết quả engineer **CÓ THỂ DÙNG** (code/SDK/patch/hướng dẫn/model chạy được).
- Là **thay đổi năng-lực-lõi PHẢI THEO DÕI**: model/agent/kiến trúc nền tảng mới, cách infer/train rẻ hơn.
- **Breaking change / deprecate / cấm vận** buộc migrate.
- **Bảo mật** trụ ④ có lỗ hổng/rủi ro cụ thể + việc cần làm → **luôn SIGNAL** (duyệt mạnh).

→ **NOISE** nếu chạm trụ nhưng chỉ:

- **Incrementalism leaderboard** (+0.x% SOTA, biến thể nhỏ không đổi cách làm).
- **Lý thuyết thuần** không góc triển khai (chứng minh hội tụ, bound toán học).
- **PR fluff / thông báo suông** (ra mắt sản phẩm không kèm kỹ thuật, tuyển dụng, sa thải, gọi vốn).

## Ranh giới hay nhầm

| Tình huống | Nhãn | Vì sao |
|---|---|---|
| Paper arXiv về model nhỏ chạy được trên edge | SIGNAL | Trụ ② + chuyển-giao |
| Paper arXiv +0.3% BLEU dịch máy tiếng Iceland | NOISE | Off-pillar + incrementalism (chính là VÍ DỤ 3 của gate) |
| "Meta sa thải 5% nhân sự AI" | NOISE | Không action kỹ thuật, dù nhắc "AI" |
| CVE trên thư viện team có thể đang dùng | SIGNAL | Trụ ④ duyệt mạnh |
| Blog PR "chúng tôi dùng AI để..." không có kiến trúc | NOISE | Buzzword, không chuyển-giao |
| OpenAI deprecate một API model đang phổ biến | SIGNAL | Disruption, buộc migrate |

> Khi thật sự lưỡng lự giữa SIGNAL và NOISE: nghiêng về **NOISE** nếu một engineer đọc xong **không đổi
> việc gì họ đang làm**. Ghi rõ lý do vào `human_reason` để vòng sau tra lại được.

## Điền vào file CSV (`gate_eval.csv`)

`eval_gate.py` xuất sẵn file này với các cột đọc (`title`, `source_url`, `content_preview`, verdict của
gate) + **2 cột trống bạn điền**:

- `human_label` → viết đúng **`SIGNAL`** hoặc **`NOISE`**.
- `human_reason` → 1 câu ngắn: trụ cột nào (hoặc off-pillar) + vì sao (vd: *"Trụ ④, CVE trên stack"* /
  *"Off-pillar, chỉ incrementalism"*).

**Đừng** sửa các cột `gate_pass_new` / `gate_reason` / `old_status` — đó là dữ liệu để so, không phải chỗ chấm.

## Nhãn của bạn dùng để làm gì (không cần tự tính)

Sau khi chấm xong, `human_label` ghép với verdict gate ra confusion matrix:

```
gate_pass_new = true  + human = SIGNAL → TP (đúng)
gate_pass_new = true  + human = NOISE  → FP (gate cho rác qua)
gate_pass_new = false + human = SIGNAL → FN (gate GIẾT NHẦM tin tốt) ← soi kỹ nhóm này
gate_pass_new = false + human = NOISE  → TN (đúng)
```

So cột `old_status` (prompt cũ) với `gate_pass_new` (prompt mới) trên cùng nhãn của bạn = bảng trước/sau.
Bỏ dòng có `gate_skipped = true` khỏi thống kê (doc chưa từng được gate chấm).
