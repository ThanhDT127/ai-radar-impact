"""Benchmark recall của TẦNG XẾP HẠNG chat (`_rank`) — thuần, miễn phí, tất định.

Vì sao tồn tại: `_rank()` quyết định tin nào lọt vào index gửi cho model. Cắt sai ở đây thì
model **không bao giờ nhìn thấy** tin đúng — và vẫn trả lời trôi chảy từ phần còn lại. Đó là
chế độ hỏng `chatbot-qa` 4b.2 đã đo: recall tổng 42%, riêng câu "mô hình mã nguồn mở" còn
2/18 tin (11%). Bản sửa đưa lên ~91%, nhưng con số đó **chưa từng được commit** — bốn file
test chat hiện có đều bảo vệ *cơ chế* (grounding, quota, mode routing), không file nào bảo vệ
*chất lượng xếp hạng*. Đây là thứ duy nhất bắt được hồi quy đó.

CHẠY
    docker compose exec backend python -m tests.eval.chat_rank_harness      # báo cáo đầy đủ
    docker compose exec backend python -m tests.eval.chat_rank_harness --freeze-baseline
    docker compose exec backend python -m tests.eval.chat_rank_harness --lexical-only
    docker compose exec backend python -m pytest tests/eval/ -q             # chạy luôn trong suite

**KHÔNG có `--live`, không tốn đồng nào, không đụng model.** Khác `tests.eval.harness` (gate) và
`tests.eval.chat_answer_harness` (chất lượng câu trả lời) ở đúng điểm đó: thứ đo ở đây là **code
của chúng ta**, không phải phán đoán của model. Nên nó chạy được trong `pytest` mặc định.

Bất biến "miễn phí" vẫn đứng sau khi `_rank` có tầng vector (`chat-hybrid-retrieval`,
27/07/2026): vector của corpus VÀ của từng câu hỏi đều **đông lạnh trong fixture**
(`chat_embeddings.jsonl`, `chat_query_vectors.jsonl`), nên harness không gọi Vertex lần nào và
`_NoModel` vẫn nổ nếu ai đó lỡ tay gọi model. Thêm kịch bản mới ⇒ phải chạy lại
`build_fixture_chat` để sinh vector câu hỏi, không thì harness NỔ chứ không lặng lẽ đo lối lexical.

`--lexical-only` đo đúng pipeline **trước** khi có tầng vector (truyền vector rỗng), dùng để dựng
cột "trước" trong bảng so sánh trước/sau. Nó KHÔNG phải một chế độ chạy hằng ngày.

KHI NÀO **BẮT BUỘC** CHẠY LẠI
    Sửa bất kỳ thứ nào sau đây: `_rank`, `_relevance`, `_question_terms`, `_roles_in_question`,
    `STOPWORDS` (`chat_service_terms.py`), `score_for_role` / `role_urgency` /
    `has_practical_indicator` (`delivery_engine.py`), `settings.chat_index_top_k`, hoặc bất cứ
    thứ gì đụng tới tầng vector: `RRF_K`, `_cosine`, `_competition_ranks`, `_vector_ranks`,
    `build_embedding_text`, `settings.embedding_model_id`.
    Harness đọc K từ `settings.chat_index_top_k` chứ không chép cứng — đổi K là đổi phép đo.

LUẬT BASELINE
    Baseline đầu tiên chốt trên code **chưa sửa gì**. Mỗi lần một thay đổi **có chủ đích** làm
    recall tăng, phải **chốt lại baseline ở mức mới** kèm lý do. Không chốt lại thì guard vẫn nằm
    ở mức cũ thấp hơn, và một lần revert sẽ tụt về đúng baseline cũ ⇒ **harness pass, lỗi quay lại
    im lặng**. Đó chính là ca harness sinh ra để chặn. Chốt lại để test chuyển xanh là tự tháo lưới.

ĐỌC KẾT QUẢ
    recall@K  = |must_have ∩ top-K| / |must_have|. `must_have` là nhãn tay: tin mà **bỏ sót là
                hỏng rõ ràng** (design D3). Câu không có `must_have` in `—` và không vào trung bình.
    KHÔNG có precision — cố ý (D3). Tin lạc đề lọt vào index chỉ tốn ~108 token và model đã bị dặn
    "tối đa 5 tin"; tin đúng bị cắt thì mất hẳn. Bất đối xứng này giống FN-tệ-hơn-FP của gate.
    Mỗi miss in kèm **thứ hạng thật** của tin bị cắt — số đó cho biết trượt sát nút hay trượt xa.

GIỚI HẠN DIỄN GIẢI
    - Fixture là ảnh chụp corpus 27/07/2026 (179 tin). Đo **hồi quy so với chính nó**; recall@60
      trên 179 tin KHÔNG suy ra recall@60 trên 1000 tin. Corpus lớn lên đáng kể thì sinh lại
      fixture và chốt lại baseline, đừng suy diễn.
    - Nhóm nào chỉ có 1 câu thì đọc như **tín hiệu**, không phải bằng chứng (cùng cảnh báo n<5 của
      gate harness).
    - Nhãn tay chủ quan → mỗi `must_have` có `label_reason` đọc được trong `chat_scenarios.jsonl`.
"""

import argparse
import json
from pathlib import Path

from app.config import settings
from app.services.chat_service import ChatService, _question_terms, _roles_in_question
from tests.eval.chat_fixture import (
    FIXTURE_DIR,
    load_chunk_ranks,
    load_corpus,
    load_query_vectors,
    load_scenarios,
    rehydrate_corpus,
)

BASELINE_PATH = FIXTURE_DIR / "chat_rank_baseline.json"

BASELINE_META = {
    "measured_at": "2026-07-28",
    "commit": "(chat-chunk-retrieval, chưa commit)",
    "corpus": (
        "chat_corpus.jsonl @ 27/07/2026 — 179 insight published+is_primary; "
        "vector từ chat_embeddings.jsonl + chat_query_vectors.jsonl (chat-hybrid-retrieval)"
    ),
    "note": (
        "Nhóm `comparison_anaphora` cố ý đỏ — nó là mốc đo cho working set, không phải "
        "mục tiêu của `_rank`. Đừng 'chữa' nó bằng cách sửa câu hỏi cho gần chữ trong tin."
    ),
    "revisions": [
        {
            "date": "2026-07-28",
            "recall_at_k": "0,968 → 0,968 (không đổi)",
            "recall_at_answer": "0,900 → 0,900 (không đổi)",
            "reason": (
                "Chốt lại để bản ghi khớp bộ kịch bản, KHÔNG phải vì xếp hạng đổi — cả hai "
                "số y nguyên. Hai việc: "
                "(a) `det-gpai-annex` đổi câu hỏi (nhãn cũ có TIỀN ĐỀ SAI: nghĩa vụ GPAI "
                "nằm ở Chapter V chứ không ở Annex nào; xem revision cùng ngày trong "
                "`chat_answer_harness`), nên dòng đông lạnh phải mang câu hỏi mới. "
                "(b) Suất ô sâu cho tin có đoạn khớp nhất là thay đổi ở `build_context`, "
                "**không** ở `_rank` — RS đo `_rank` nên không thấy gì, đúng như thiết kế. "
                "Ghi ra đây để người đọc sau không đi tìm một thay đổi số liệu không tồn tại."
            ),
        },
        {
            "date": "2026-07-28",
            "recall_at_k": "0,969 → 0,968",
            "recall_at_answer": "0,876 → 0,900",
            "reason": (
                "`chat-chunk-retrieval`: tầng độ‑liên‑quan thêm số hạng RRF THỨ BA — tương "
                "đồng ở mức ĐOẠN thân bài (`document_chunks`, 535 đoạn / 179 bài). "
                "Kèm 15 kịch bản mới nhóm `detail_discovery`. "
                "\n\n"
                "⚠️ HAI CON SỐ TỔNG KHÔNG SO ĐƯỢC với dòng dưới (bộ kịch bản đi từ 83 lên "
                "98 câu). So sánh ĐÚNG là trên cùng 98 câu, đo bằng `--without-chunks` "
                "cùng ngày: **recall@5 0,832 → 0,900** và recall@60 0,975 → 0,968. "
                "\n\n"
                "THẮNG (cái change nhắm tới): `detail_discovery` r@5 **0,67 → 1,00** — "
                "15/15 câu hỏi bằng định danh chỉ có trong thân bài (`SquashFS`, `SPDX`, "
                "`HMAC-SHA256`, `ChunkingStrategy`) nay đưa đúng bài lên top‑5; hạng xấu "
                "nhất 29 → 4. Lan sang nhóm khác: `security` r@5 0,88 → 0,94, "
                "`open_model` 0,78 → 0,89. "
                "\n\n"
                "TRẢ GIÁ — 4 câu tụt, ghi rõ để đừng ai đọc nhầm là 'không mất gì': "
                "(a) `glo-iot-security` r@5 1,00 → 0,50, `rank-device-trap` 1,00 → 0,50, "
                "`cmp-pq-partial` 1,00 → 0,50 — cả ba GIỮ NGUYÊN `must_have` chính ở hạng "
                "1, cái rơi là tin THỨ HAI của một câu hỏi rộng, và chỗ nó nhường lại cho "
                "tin cùng chủ đề khớp sâu hơn ở thân bài. Đây là đổi thứ tự TRONG một vùng "
                "liên quan, không phải tin đúng bị đẩy ra ngoài. "
                "(b) ⚠️ `rank-eol-khai-tu` r@60 **0,50 → 0,00** — nặng nhất, vì mất luôn "
                "chỗ trong index chứ không chỉ trong top‑5 (hai tin rơi xuống hạng 80 và "
                "92). Câu 'công nghệ nào sắp bị khai tử' vốn đã là ca đỏ có chủ đích: "
                "embedding không nối được thành ngữ đó với 'end of support', và tầng đoạn "
                "thêm nhiễu vào đúng câu mà cả hai tín hiệu cũ đều mù. Nó GIỮ NGUYÊN vai "
                "trò mốc đo cho rerank cross‑encoder — **đừng chữa bằng cách sửa câu hỏi "
                "cho gần chữ trong tin hơn**, làm thế là xoá phép đo."
            ),
        },
        {
            "date": "2026-07-28",
            "recall_at_k": "0,922 → 0,969",
            "recall_at_answer": "0,821 → 0,876",
            "reason": (
                "SỬA PHÉP ĐO, không phải cải thiện xếp hạng — `_rank` không đổi một dòng. "
                "Hai việc: "
                "(a) 4 kịch bản `comparison_expanded` chuyển sang đường THẬT: người dùng "
                "đang xem một bài rồi hỏi so sánh thì widget đã đưa bài đó vào working set, "
                "nên payload là `referenced_insight_ids`, KHÔNG phải `insight_id`+sentinel. "
                "Nhóm đổi tên `comparison_expanded` → `comparison_in_article`. "
                "(b) Tin đi qua `referenced_insight_ids` nay bị LOẠI khỏi cả tập ứng viên "
                "lẫn `must_have`: chúng vào thẳng ô sâu, **không đi qua xếp hạng**, nên "
                "chấm recall cho chúng là chấm một phép tính không tồn tại. "
                "\n\n"
                "⚠️ Đây là lý do con số TĂNG: nhóm `comparison_anaphora` trước đó bị chấm "
                "0,00 vĩnh viễn cho một việc `_rank` không được giao — nay hiện `—` và ra "
                "khỏi trung bình. **Một đại lượng đỏ mãi vì thiết kế sẽ dạy người đọc bỏ "
                "qua nó**, đúng thứ harness này sinh ra để chống; nó cũng làm trung bình "
                "tổng bớt nhạy với hồi quy thật. "
                "Bằng chứng 'xếp hạng thuần KHÔNG giải được câu hồi chỉ' vẫn còn nguyên ở "
                "`openspec/changes/chat-context-depth/measurement.md` + `eval/` — chỗ đúng "
                "của nó là tài liệu đo một lần, không phải một cổng chạy mãi. "
                "`comparison_in_article` r@5 = 1,00 (3 ca có việc để đo; ca thứ tư "
                "`cmp-gemma-expanded` có cả hai bài trong working set nên `must_have` rỗng)."
            ),
        },
        {
            "date": "2026-07-28",
            "recall_at_k": "0,970 → 0,922",
            "recall_at_answer": "0,859 → 0,821",
            "reason": (
                "`chat-context-depth`: (a) THÊM 19 kịch bản so sánh (4 nhóm mới) và "
                "(b) thêm 7 từ khung câu hồi chỉ vào `STOPWORDS`. "
                "⚠️ HAI CON SỐ TỔNG KHÔNG SO ĐƯỢC với dòng dưới — bộ kịch bản đi từ 42 lên "
                "61 câu và nhóm mới `comparison_anaphora` **CỐ Ý đỏ**: 'Hai cái này khác "
                "nhau chỗ nào?' không chứa thông tin 'hai bài nào', nên không mức tinh chỉnh "
                "`_rank` nào chữa được — đó đúng là phần mà working set "
                "(`referenced_insight_ids`) chữa, và nhóm này giữ lại làm MỐC ĐO cho nó, "
                "không phải để chữa bằng xếp hạng. "
                "KHÔNG kịch bản cũ nào tụt (0 dấu ▼). "
                "Nhóm mới: `comparison` r@5=1,00 (8/8 — retrieval vốn đã ổn cho câu gọi tên "
                "cả hai; cái thiếu là ĐỘ SÂU, xem `measurement.md`), "
                "`comparison_expanded` 1,00, `comparison_partial` 0,67, "
                "`comparison_anaphora` 0,00. "
                "Riêng phần (b) đo được: r@5 tổng 0,805 → 0,821 và `comparison_expanded` "
                "r@5 0,75 → 1,00 (câu 'Bài này khác gì so với bài kia' nay rỗng từ khoá ⇒ "
                "tắt tầng vector ⇒ rơi về độ quan trọng thay vì xếp theo nhiễu). "
                "Đổi lại `comparison_anaphora` r@60 0,38 → 0,25: thứ hạng cũ là MAY MẮN của "
                "nhiễu, không phải tín hiệu — đối chứng bật/tắt vector cho thứ hạng nhảy "
                "loạn không theo hướng nào (141↔105, 22↔66, 45↔1)."
            ),
        },
        {
            "date": "2026-07-27",
            "recall_at_k": "0,988 → 0,970",
            "recall_at_answer": "0,812 → 0,859",
            "reason": (
                "`chat-hybrid-retrieval`: tầng độ‑liên‑quan đổi từ lexical thuần sang RRF "
                "(vector + lexical). ⚠️ Hai con số 'trước' ở đây KHÔNG so được với dòng trên: "
                "bộ kịch bản vừa thêm 2 ca nhóm `semantic` (42 câu thay vì 40), và cả hai câu "
                "mới đều là ca khó (0,50 và 0,50 ở lexical) nên chúng KÉO TỔNG XUỐNG chứ không "
                "phải hybrid làm tụt. So sánh đúng là trên cùng 42 câu, đo bằng "
                "`--lexical-only` cùng ngày: recall@60 0,964 → 0,970, recall@5 0,780 → 0,859, "
                "và KHÔNG câu nào tụt. "
                "Thắng rõ nhất (recall@5): `rank-devops-trap` 0,00 → 1,00 (hạng 47 → 1), "
                "`glo-supply-chain` 0,00 → 1,00, `rank-device-trap` 0,50 → 1,00, "
                "`exp-nettacker-to-vnpost` 0,50 → 1,00, `rank-open-source-models` 0,00 → 0,33. "
                "Còn sót: `rank-eol-khai-tu` đứng yên 0,50 — embedding không nối được thành ngữ "
                "'khai tử' với 'end of support'. Chi tiết per‑câu ở "
                "openspec/changes/chat-hybrid-retrieval/eval/."
            ),
        },
        {
            "date": "2026-07-27",
            "recall_at_k": "1,000 → 0,988",
            "recall_at_answer": "0,812 → 0,812",
            "reason": (
                "`chat-citation-integrity` 4.1: `_relevance` đổi sang khớp theo BIÊN TỪ. "
                "recall@60 giảm vì `exp-gemma-to-eol` mất một khớp NHẦM (`kế` khớp chuỗi con "
                "trong `kết`) — tin Cypress trước nay lọt top-60 nhờ tai nạn. recall@5 net "
                "không đổi: `glo-open-model-analysis` +0,50, `exp-nettacker-to-vnpost` −0,50 "
                "(`sql` không còn khớp `MySQL`). Chi tiết + ba kết luận ở "
                "openspec/changes/chat-citation-integrity/measurement.md."
            ),
        }
    ],
}

# Dung sai: recall là tỉ lệ trên tập must_have nhỏ, một tin trượt đã đổi 0,33 ở câu 3 tin.
# So bằng tuyệt đối sẽ fail giả khi thêm/bớt kịch bản; dung sai này là "tụt thật sự".
TOLERANCE = 0.01

# Trần số tin model được phép dùng trong MỘT câu trả lời (`CHAT_SYSTEM_PROMPT`: "TỐI ĐA 5 tin").
# recall@60 đo "tin có lọt index không"; recall@5 đo "tin có thực sự tới tay người đọc không".
# Đo 27/07/2026: recall@60 bão hoà 1,000 trên cả 47 câu ⇒ tự nó không bắt được hồi quy nào
# nhỏ hơn "văng khỏi top-60". recall@5 và `worst_rank` mới là phần nhạy.
ANSWER_BUDGET = 5


class _NoModel:
    """Client model NỔ khi bị chạm tới.

    `_rank` là method của `ChatService` nên phải gọi qua một instance. Thay vì tạo
    `GeminiClient` thật (cần credentials, và mở đường cho một lượt gọi lọt vào bộ đo lẽ ra
    miễn phí), tiêm cái này: mọi truy cập thuộc tính đều ném lỗi. Bộ đo **không thể** gọi
    model — đó là bất biến được bảo đảm bằng cấu trúc, không phải bằng lời hứa.
    """

    def __getattr__(self, name):
        raise AssertionError(
            f"Benchmark xếp hạng vừa chạm tới model (`{name}`) — nó phải thuần và miễn phí. "
            "Xem lại thay đổi vừa rồi ở `_rank`."
        )


def _rank(
    candidates: list,
    question: str,
    query_vector: list | None = None,
    chunk_ranks: dict | None = None,
) -> list:
    """`ChatService._rank` thật, gắn vào một service không có DB và không có model.

    `chunk_ranks` đến từ fixture đông lạnh (`chat_chunk_ranks.jsonl`) chứ không từ DB —
    đó là cách tầng đoạn giữ được bất biến "miễn phí, offline, tất định" (design D4-C).
    """
    service = ChatService(session=None, gemini=_NoModel())
    return service._rank(candidates, question, query_vector, chunk_ranks)


def _candidates(scenario: dict, corpus: list) -> list:
    """Tập ứng viên ĐÚNG như `_answer_global` dựng ra cho kịch bản đó.

    Chế độ mở rộng loại bài đang xem khỏi index toàn cục (nó đã đi kèm ở `[1]`), nên harness
    phải loại y hệt — không thì đo trên tập ứng viên khác production.

    Chế độ `focused` cũng vậy với `referenced_insight_ids`: tin do người dùng chọn vào thẳng
    ô sâu, **không đi qua xếp hạng**. Giữ chúng trong tập ứng viên là đo một việc mà
    production không nhờ `_rank` làm.
    """
    anchor = scenario.get("anchor_insight_id")
    if scenario["mode"] == "expanded" and anchor:
        return [i for i in corpus if str(i.id) != anchor]
    refs = set(scenario.get("referenced_insight_ids") or [])
    if refs:
        return [i for i in corpus if str(i.id) not in refs]
    return list(corpus)


def measure(
    scenarios: list[dict] | None = None,
    use_vectors: bool = True,
    use_chunks: bool = True,
) -> dict:
    """Chạy `_rank()` thật trên fixture. Không gọi model, tất định.

    `use_vectors=False` tắt tầng vector ở CẢ HAI phía (corpus và câu hỏi) để tái hiện
    pipeline trước `chat-hybrid-retrieval` — chỉ dùng cho bảng so sánh trước/sau.
    """
    scenarios = scenarios if scenarios is not None else load_scenarios()
    # Mode B không đi qua `_rank` (context là đúng 1 bài) — đo nó ở đây là đo cái không tồn tại.
    scenarios = [s for s in scenarios if s["mode"] != "insight"]

    corpus = rehydrate_corpus(load_corpus(), embeddings=None if use_vectors else {})
    query_vectors = load_query_vectors() if use_vectors else {}
    chunk_ranks = load_chunk_ranks() if (use_vectors and use_chunks) else {}
    if use_vectors and use_chunks:
        missing_chunks = [s["id"] for s in scenarios if s["id"] not in chunk_ranks]
        if missing_chunks:
            raise ValueError(
                f"{len(missing_chunks)} kịch bản chưa có thứ hạng đoạn "
                f"({missing_chunks[:5]}). Chạy `python -m tests.eval.build_fixture_chat "
                "--top-up` — đo tiếp sẽ cho những câu đó đi lối HAI tín hiệu và số sẽ sai "
                "một cách im lặng."
            )
    if use_vectors:
        missing = [s["id"] for s in scenarios if s["id"] not in query_vectors]
        if missing:
            raise ValueError(
                f"{len(missing)} kịch bản chưa có vector câu hỏi ({missing[:5]}). Chạy "
                "`python -m tests.eval.build_fixture_chat` sau khi thêm kịch bản — đo tiếp "
                "sẽ cho những câu đó đi lối lexical và số sẽ sai một cách im lặng."
            )

    top_k = settings.chat_index_top_k
    rows = []

    for scenario in scenarios:
        candidates = _candidates(scenario, corpus)
        ranked = _rank(
            candidates,
            scenario["question"],
            query_vectors.get(scenario["id"]),
            chunk_ranks.get(scenario["id"]),
        )
        position = {str(insight.id): n for n, insight in enumerate(ranked, start=1)}
        selected = {str(i.id) for i in (ranked[:top_k] if top_k > 0 else ranked)}

        # Tin đi qua `referenced_insight_ids` được BẢO ĐẢM có mặt (ô sâu), nên chấm recall
        # xếp hạng cho chúng là chấm một phép tính không tồn tại — và cho ra 0,00 vĩnh viễn
        # ở nhóm mà production trả lời hoàn hảo. Một đại lượng đỏ mãi vì thiết kế sẽ dạy
        # người đọc bỏ qua nó, đúng thứ harness này sinh ra để chống.
        refs = set(scenario.get("referenced_insight_ids") or [])
        must = [i for i in (scenario.get("must_have") or []) if i not in refs]
        # Thứ hạng thật của từng tin bắt buộc. Đây là đại lượng NHẠY: recall@60 trên corpus
        # 179 tin bão hoà ở 1,00 (đo 27/07) nên tự nó không phân biệt được gì — xem
        # `recall_at_answer` và `worst_rank` bên dưới.
        ranks = [position.get(i) for i in must]
        misses = [
            {
                "insight_id": insight_id,
                "title": next(
                    (i.title for i in corpus if str(i.id) == insight_id), "?"
                ),
                "rank": position.get(insight_id),
            }
            for insight_id in must
            if insight_id not in selected
        ]
        rows.append(
            {
                "scenario_id": scenario["id"],
                "group": scenario["group"],
                "mode": scenario["mode"],
                "question": scenario["question"],
                "recall": (len(must) - len(misses)) / len(must) if must else None,
                # Trần thật của câu trả lời là 5 tin (`CHAT_SYSTEM_PROMPT`), không phải 60.
                # Tin xếp hạng 40 tuy lọt index nhưng model gần như chắc chắn không dùng tới —
                # đúng cảnh 4b.2: "model vẫn trả lời trôi chảy từ 2 tin sót lại".
                "recall_at_answer": (
                    sum(1 for r in ranks if r is not None and r <= ANSWER_BUDGET) / len(must)
                    if must
                    else None
                ),
                "worst_rank": max((r for r in ranks if r is not None), default=None),
                "must_total": len(must),
                "misses": misses,
                "terms": _question_terms(scenario["question"]),
                "roles": _roles_in_question(scenario["question"]),
            }
        )

    scored = [r["recall"] for r in rows if r["recall"] is not None]
    at_answer = [r["recall_at_answer"] for r in rows if r["recall_at_answer"] is not None]
    return {
        "top_k": top_k,
        "answer_budget": ANSWER_BUDGET,
        "corpus_size": len(corpus),
        "rows": rows,
        "overall": sum(scored) / len(scored) if scored else None,
        "overall_at_answer": sum(at_answer) / len(at_answer) if at_answer else None,
        "questions_scored": len(scored),
    }


def verdict(result: dict, baseline: dict | None) -> tuple[bool, list[str]]:
    """FAIL khi recall tổng tụt, HOẶC bất kỳ câu nào tụt so với baseline của chính nó."""
    if not baseline:
        return True, []

    reasons = []
    for key, label in (("overall", f"recall@{result['top_k']}"),
                       ("overall_at_answer", f"recall@{result['answer_budget']}")):
        now, before = result[key], baseline.get(key)
        if now is not None and before is not None and now < before - TOLERANCE:
            reasons.append(
                f"{label} tổng {now:.3f} tụt dưới baseline {before:.3f} (dung sai {TOLERANCE})"
            )

    base_rows = {r["scenario_id"]: r for r in baseline["rows"]}
    for row in result["rows"]:
        base = base_rows.get(row["scenario_id"], {})
        for key, label in (("recall", f"recall@{result['top_k']}"),
                           ("recall_at_answer", f"recall@{result['answer_budget']}")):
            before, now = base.get(key), row[key]
            if before is None or now is None or now >= before - TOLERANCE:
                continue
            detail = "; ".join(
                f"cắt mất «{m['title'][:44]}» (hạng thật {m['rank']})" for m in row["misses"]
            ) or f"tin bắt buộc tụt xuống hạng {row['worst_rank']}"
            reasons.append(
                f"{row['scenario_id']} ({row['group']}): {label} {now:.2f} tụt từ {before:.2f} — {detail}"
            )

    # Kịch bản mới chưa có trong baseline: không fail, nhưng phải nói ra — im lặng thì
    # người đọc tưởng baseline đang phủ hết.
    new = [r["scenario_id"] for r in result["rows"] if r["scenario_id"] not in base_rows]
    if new:
        reasons.append(
            f"CHÚ Ý (không phải fail): {len(new)} kịch bản chưa có trong baseline "
            f"({', '.join(new[:6])}) — chốt lại baseline kèm lý do."
        )
        return not [r for r in reasons if not r.startswith("CHÚ Ý")], reasons

    return not reasons, reasons


def format_report(result: dict, baseline: dict | None) -> str:
    base_rows = {r["scenario_id"]: r for r in (baseline or {}).get("rows", [])}
    lines = [
        f"Corpus {result['corpus_size']} tin · K = {result['top_k']} "
        f"(settings.chat_index_top_k) · {result['questions_scored']} câu có nhãn must_have",
        "",
    ]
    header = (f"{'kịch bản':<28}{'nhóm':<14}{'r@' + str(result['top_k']):>6}{'':<6}"
              f"{'r@' + str(result['answer_budget']):>5}{'':<6}{'hạng xấu nhất':>13}  "
              f"{'trục vai trò':<18}từ khoá")
    lines.append(header)
    lines.append("-" * 118)

    for row in sorted(result["rows"], key=lambda r: (r["group"], r["scenario_id"])):
        base = base_rows.get(row["scenario_id"], {})

        def cell(key):
            value = row[key]
            text = "   — " if value is None else f"{value:>5.2f}"
            before = base.get(key)
            delta = "     "
            if value is not None and before is not None:
                diff = value - before
                delta = "    =" if abs(diff) < 1e-9 else f" {'▲' if diff > 0 else '▼'}{abs(diff):.2f}"
            return text, delta

        recall, d_recall = cell("recall")
        answer, d_answer = cell("recall_at_answer")
        worst = "  —" if row["worst_rank"] is None else str(row["worst_rank"])
        roles = ", ".join(row["roles"]) or "(không có)"
        terms = ", ".join(row["terms"][:4]) or "(rỗng — mọi từ là stopword)"
        lines.append(
            f"{row['scenario_id']:<28}{row['group']:<14}{recall}{d_recall:<6}"
            f"{answer}{d_answer:<6}{worst:>13}  {roles:<18}{terms}"
        )
        for miss in row["misses"]:
            lines.append(
                f"    ❌ cắt mất «{miss['title'][:56]}» — hạng thật {miss['rank']}/{result['corpus_size']}"
            )

    lines.append("")
    lines.append("Theo nhóm:")
    groups: dict[str, list] = {}
    for row in result["rows"]:
        groups.setdefault(row["group"], []).append(row)
    for group, rows in sorted(groups.items()):
        def mean(key):
            values = [r[key] for r in rows if r[key] is not None]
            return f"{sum(values) / len(values):.2f}" if values else "  — "

        flag = "   (n=1, chỉ là tín hiệu)" if len(rows) == 1 else ""
        lines.append(
            f"  {group:<14} n={len(rows):<3} r@{result['top_k']}={mean('recall')} "
            f"r@{result['answer_budget']}={mean('recall_at_answer')}{flag}"
        )

    lines.append("")
    for key, label in (("overall", f"recall@{result['top_k']:<3}"),
                       ("overall_at_answer", f"recall@{result['answer_budget']:<3}")):
        value = result[key]
        base = f"   (baseline {baseline[key]:.3f})" if baseline and baseline.get(key) is not None else "   (chưa có baseline)"
        lines.append(f"TỔNG {label} = " + ("  —  " if value is None else f"{value:.3f}") + base)
    lines.append(
        f"      recall@{result['top_k']} bão hoà là BÌNH THƯỜNG trên corpus {result['corpus_size']} tin — "
        f"phần nhạy là recall@{result['answer_budget']} và cột hạng xấu nhất."
    )
    return "\n".join(lines)


def load_baseline(path: Path = BASELINE_PATH) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark recall xếp hạng chat (0 lượt gọi model)")
    parser.add_argument("--freeze-baseline", action="store_true",
                        help="ghi kết quả hiện tại thành baseline — CÓ CHỦ ĐÍCH, kèm lý do")
    parser.add_argument("--lexical-only", action="store_true",
                        help="tắt tầng vector (tái hiện pipeline trước chat-hybrid-retrieval)")
    parser.add_argument("--without-chunks", action="store_true",
                        help="tắt tầng ĐOẠN (tái hiện pipeline trước chat-chunk-retrieval)")
    args = parser.parse_args()

    if (args.lexical_only or args.without_chunks) and args.freeze_baseline:
        raise SystemExit(
            "Không chốt baseline từ lượt --lexical-only/--without-chunks: baseline phải "
            "mô tả pipeline THẬT."
        )

    result = measure(use_vectors=not args.lexical_only, use_chunks=not args.without_chunks)
    if args.lexical_only:
        print("⚠️  LƯỢT ĐO KHÔNG CÓ TẦNG VECTOR — chỉ để dựng cột 'trước'.\n")
    elif args.without_chunks:
        print("⚠️  LƯỢT ĐO KHÔNG CÓ TẦNG ĐOẠN — chỉ để dựng cột 'trước'.\n")
    baseline = load_baseline()
    print(format_report(result, baseline))

    passed, reasons = verdict(result, baseline)
    print()
    print(f"VERDICT: {'PASS ✅' if passed else 'FAIL ❌'}")
    for reason in reasons:
        print(f"  - {reason}")

    if args.freeze_baseline:
        BASELINE_PATH.write_text(
            json.dumps({"meta": BASELINE_META, **result}, ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        print(f"\nĐã chốt baseline vào {BASELINE_PATH} — nhớ ghi LÝ DO vào commit.")

    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
