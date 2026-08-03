"""GHIM tin đã trích ở lượt trước vào ngữ cảnh lượt hiện tại (`chat-history-pinning`).

Vấn đề được chữa: `_rank` chỉ nhìn câu hỏi của lượt HIỆN TẠI, không nhìn lịch sử. Đo
29/07/2026 trên ma trận 6×6 chủ đề, **47/90 = 52%** cặp (tin đã bàn, chủ đề mới) rơi khỏi
top-60 — tệ nhất hạng 118/179 — trong khi `_history_block` vẫn đưa *tên* tin đó vào prompt.
Model đọc được cái tên mà không có dòng dữ liệu nào của nó.

Bất biến cần khoá:
- tin đã trích rơi khỏi top-K VẪN có mặt trong index;
- một insight KHÔNG BAO GIỜ mang hai số `[n]` (khử trùng với ô sâu VÀ với index);
- ghim nằm TRONG `index_limit` — trần top-K không được thành lời nói suông;
- tin ghim đứng CUỐI index (prompt dặn "tin ở đầu đáng chọn hơn", mà tin ghim theo định
  nghĩa không liên quan tới câu hỏi lượt này);
- `chat_history_pin_slots = 0` cho index TRÙNG KHÍT bản chưa có cơ chế này;
- client cũ không gửi `insight_id` ⇒ không ghim, không lỗi.
"""

import uuid
from datetime import datetime

from app.services.chat_grounding import build_context
from app.services.chat_service import _history_pin_ids


class _FakeInsight:
    def __init__(self, title):
        self.id = uuid.uuid4()
        self.title = title
        self.signal = f"Ý nghĩa của {title}"
        self.why_it_matters = f"Vì sao {title} quan trọng"
        self.so_what = f"Nên làm gì với {title}"
        self.summary_short = "ngắn"
        self.summary_medium = "vừa"
        self.risks = []
        self.affected_roles = ["Security"]
        self.topics = ["Security & Compliance"]
        self.source_url = f"https://example.com/{title}"
        self.published_at = datetime(2026, 7, 20, 10, 0)
        self.created_at = datetime(2026, 7, 21, 10, 0)
        self.impact_label = "Trung bình"
        self.actionability_score = 0.5
        self.intelligence_tier = "Tactical"
        self.trust_score = 0.8
        self.practical_indicators = None
        self.recommendations = {
            "Security": {"action_type": "read", "note": "n", "urgency": "medium"}
        }
        self.raw_document = None


class _Turn:
    def __init__(self, role, content, citations=()):
        self.role = role
        self.content = content
        self.citations = list(citations)


class _Cit:
    """Nguồn của một lượt trước. `insight_id=None` mô phỏng client CŨ."""

    def __init__(self, n, title, insight_id=None):
        self.n = n
        self.title = title
        self.insight_id = insight_id


# --- _history_pin_ids: hàm thuần, tất định ----------------------------------------------


def test_pin_ids_quet_theo_lop_uu_tien_luot_moi():
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    history = [
        _Turn("user", "câu 1"),
        _Turn("assistant", "đáp 1 [1]", [_Cit(1, "A", a)]),
        _Turn("user", "câu 2"),
        _Turn("assistant", "đáp 2 [2][3]", [_Cit(2, "B", b), _Cit(3, "C", c)]),
    ]
    # Lớp 1: nguồn ĐẦU của mỗi lượt, lượt mới trước → b, a. Lớp 2: nguồn thứ hai → c.
    assert _history_pin_ids(history, limit=3) == [b, a, c]


def test_pin_ids_mot_luot_khong_doc_chiem_het_cho():
    """HỒI QUY — bản 'cạn từng lượt' để một lượt chen giữa xoá sạch tin trước đó.

    Đo 29/07/2026: lượt trả lời toàn cục trích tới 5 nguồn, mà chỉ có 3 chỗ ghim. Duyệt cạn
    lượt gần nhất trước ⇒ tin X bàn ở lượt 1 đứng thứ **6** trong danh sách và văng khỏi trần,
    tức cơ chế chỉ phủ được đúng lượt liền trước.
    """
    X = uuid.uuid4()
    moi = [uuid.uuid4() for _ in range(5)]
    history = [
        _Turn("assistant", "bàn X [1]", [_Cit(1, "X", X)]),
        _Turn("assistant", "chủ đề khác", [_Cit(i + 1, f"M{i}", m) for i, m in enumerate(moi)]),
    ]
    pin = _history_pin_ids(history, limit=3)
    assert X in pin, "một lượt 5 nguồn không được chiếm hết 3 chỗ ghim"
    # Lớp 1: nguồn đầu của lượt mới, rồi X. Lớp 2: nguồn thứ hai của lượt mới.
    assert pin == [moi[0], X, moi[1]]


def test_pin_ids_mot_luot_duy_nhat_van_lap_day_nhu_cu():
    """Ca phổ biến nhất — hỏi tiếp NGAY sau một lượt — phải TRÙNG KHÍT hành vi cũ."""
    a, b, c, d = (uuid.uuid4() for _ in range(4))
    history = [
        _Turn("user", "câu"),
        _Turn("assistant", "đáp [1][2][3][4]",
              [_Cit(1, "A", a), _Cit(2, "B", b), _Cit(3, "C", c), _Cit(4, "D", d)]),
    ]
    assert _history_pin_ids(history, limit=3) == [a, b, c]


def test_pin_ids_cat_o_limit_va_uu_tien_gan_nhat():
    a, b, c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    history = [
        _Turn("assistant", "cũ [1]", [_Cit(1, "A", a)]),
        _Turn("assistant", "mới [2][3]", [_Cit(2, "B", b), _Cit(3, "C", c)]),
    ]
    # Lớp 1 lấy nguồn đầu của cả hai lượt — tin cũ KHÔNG bị lượt mới nuốt.
    assert _history_pin_ids(history, limit=2) == [b, a]


def test_pin_ids_khu_trung_khi_mot_tin_duoc_trich_nhieu_luot():
    a = uuid.uuid4()
    history = [
        _Turn("assistant", "đáp 1 [1]", [_Cit(1, "A", a)]),
        _Turn("assistant", "đáp 2 [4]", [_Cit(4, "A", a)]),
    ]
    assert _history_pin_ids(history, limit=3) == [a]


def test_pin_ids_bo_qua_citation_khong_co_dinh_danh():
    """Client CŨ gửi `{n, title}` không kèm id → không có gì để ghim, KHÔNG được lỗi."""
    b = uuid.uuid4()
    history = [
        _Turn("assistant", "đáp 1 [1]", [_Cit(1, "A", None)]),
        _Turn("assistant", "đáp 2 [2]", [_Cit(2, "B", b)]),
    ]
    assert _history_pin_ids(history, limit=3) == [b]


def test_pin_ids_tat_khi_limit_bang_khong():
    a = uuid.uuid4()
    history = [_Turn("assistant", "đáp [1]", [_Cit(1, "A", a)])]
    assert _history_pin_ids(history, limit=0) == []


# --- build_context: ghim vào index ------------------------------------------------------


def test_tin_da_trich_roi_khoi_topk_van_co_mat():
    """Ca chính: 52% số lần trong đo thật."""
    ranked = [_FakeInsight(f"T{i}") for i in range(10)]
    da_ban = _FakeInsight("CISA vá khẩn")  # không nằm trong `ranked` của lượt này

    ctx = build_context(
        refs=[], ranked=ranked, k_deep=1, index_limit=5, pinned=[da_ban]
    )

    assert da_ban.id in {i.id for i in ctx.mapping.values()}


def test_ghim_nam_trong_tran_index_limit():
    """Ngân sách token không được phình: 5 tin vẫn là 5 tin."""
    ranked = [_FakeInsight(f"T{i}") for i in range(20)]
    pinned = [_FakeInsight(f"P{i}") for i in range(3)]

    ctx = build_context(
        refs=[], ranked=ranked, k_deep=1, index_limit=5, pinned=pinned
    )

    assert len(ctx.mapping) == 5
    # 1 ô sâu + 1 tin xếp hạng còn sống + 3 tin ghim.
    assert ctx.deep_count == 1


def test_tin_ghim_dung_CUOI_index():
    ranked = [_FakeInsight(f"T{i}") for i in range(10)]
    pinned = [_FakeInsight("P0"), _FakeInsight("P1")]

    ctx = build_context(
        refs=[], ranked=ranked, k_deep=1, index_limit=6, pinned=pinned
    )

    so_ghim = sorted(n for n, i in ctx.mapping.items() if i in pinned)
    so_xep_hang = [n for n, i in ctx.mapping.items() if i not in pinned]
    # Mọi tin xếp hạng đứng TRƯỚC mọi tin ghim, và dãy số liên tục không đứt.
    assert min(so_ghim) > max(so_xep_hang)
    assert sorted(ctx.mapping) == list(range(1, 7))


def test_khu_trung_voi_index_tin_da_co_khong_nhan_so_thu_hai():
    """Tin vừa được trích vừa còn trong top-K nhận đúng MỘT số."""
    ranked = [_FakeInsight(f"T{i}") for i in range(5)]
    van_con_trong_topk = ranked[2]

    ctx = build_context(
        refs=[], ranked=ranked, k_deep=1, index_limit=5, pinned=[van_con_trong_topk]
    )

    so_lan = [i.id for i in ctx.mapping.values()].count(van_con_trong_topk.id)
    assert so_lan == 1
    assert len(ctx.mapping) == 5


def test_khu_trung_voi_o_sau_tin_trong_working_set_khong_bi_ghim_lai():
    """Tin ở ô sâu KHÔNG được xuất hiện lại trong index — bẫy 'một tin hai số'."""
    ranked = [_FakeInsight(f"T{i}") for i in range(5)]
    dang_doc_ky = ranked[0]

    ctx = build_context(
        refs=[dang_doc_ky],
        ranked=ranked,
        k_deep=2,
        index_limit=5,
        pinned=[dang_doc_ky],
    )

    so_lan = [i.id for i in ctx.mapping.values()].count(dang_doc_ky.id)
    assert so_lan == 1
    assert ctx.mapping[1] is dang_doc_ky  # vẫn ở ô sâu, không bị đẩy xuống index


def test_tat_bang_slots_0_cho_ket_qua_TRUNG_KHIT():
    """Đường rollback: `chat_history_pin_slots = 0` ⇒ không gì đổi."""
    ranked = [_FakeInsight(f"T{i}") for i in range(10)]
    da_ban = _FakeInsight("CISA vá khẩn")

    goc = build_context(refs=[], ranked=ranked, k_deep=1, index_limit=5)
    tat = build_context(refs=[], ranked=ranked, k_deep=1, index_limit=5, pinned=[])
    # `_history_pin_ids(..., 0)` trả `[]`, nên đường tắt đi qua đúng nhánh này.
    assert tat.index_block == goc.index_block
    assert tat.mapping == goc.mapping
    assert da_ban.id not in {i.id for i in tat.mapping.values()}


def test_ghim_vuot_tran_khong_lam_phinh_prompt():
    """Cấu hình bệnh hoạn (ghim nhiều hơn cả trần) vẫn phải tôn trọng `index_limit`."""
    ranked = [_FakeInsight(f"T{i}") for i in range(10)]
    pinned = [_FakeInsight(f"P{i}") for i in range(8)]

    ctx = build_context(
        refs=[], ranked=ranked, k_deep=1, index_limit=3, pinned=pinned
    )

    assert len(ctx.mapping) == 3


def test_khong_gioi_han_index_van_ghim_duoc():
    """`index_limit <= 0` = không cắt; ghim vẫn phải có mặt, không đẩy ai ra."""
    ranked = [_FakeInsight(f"T{i}") for i in range(4)]
    da_ban = _FakeInsight("ngoài cửa sổ")

    ctx = build_context(
        refs=[], ranked=ranked, k_deep=1, index_limit=0, pinned=[da_ban]
    )

    ids = {i.id for i in ctx.mapping.values()}
    assert da_ban.id in ids
    assert all(i.id in ids for i in ranked)


def test_hidden_khong_bi_thoi_phong_boi_tin_ghim_ngoai_ranked():
    """`hidden` đếm tin của `ranked` chưa lên mặt — tin ghim từ ngoài không được tính vào.

    Sai chỗ này thì con số "còn N tin khác" trong prompt bị THIẾU, và model nói sai với
    người dùng về quy mô corpus.
    """
    ranked = [_FakeInsight(f"T{i}") for i in range(10)]
    ngoai_ranked = _FakeInsight("ngoài cửa sổ thời gian")

    ctx = build_context(
        refs=[], ranked=ranked, k_deep=1, index_limit=5, pinned=[ngoai_ranked]
    )

    # 5 chỗ: 1 ô sâu + 3 tin xếp hạng + 1 tin ghim ⇒ 4 tin của `ranked` lên mặt.
    assert ctx.total_matched == 10
    assert ctx.hidden == 6


def test_duong_mo_rong_danh_so_lien_tuc_tu_2():
    """Chế độ mở rộng: `[1]` là bài đang xem, index từ `[2]`, tin ghim nối cuối cùng dãy."""
    bai_dang_xem = _FakeInsight("bài đang xem")
    ranked = [_FakeInsight(f"T{i}") for i in range(5)]
    da_ban = _FakeInsight("đã bàn lượt trước")

    ctx = build_context(
        refs=[bai_dang_xem],
        ranked=ranked,
        k_deep=1,
        index_limit=4,
        pinned=[da_ban],
    )

    assert ctx.mapping[1] is bai_dang_xem
    assert sorted(ctx.mapping) == [1, 2, 3, 4]
    # Tin ghim nhận số CUỐI của cùng một dãy, không mở không gian số thứ hai.
    assert ctx.mapping[4] is da_ban
