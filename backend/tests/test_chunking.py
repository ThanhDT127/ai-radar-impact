"""`split_content` — hằng số ở đây là hợp đồng embedding, nên test khoá cả hằng số.

Bài học từ `build_embedding_text`: đổi cách dựng text embed mà không backfill thì cột vector
mang hai họ khác nhau và **không có gì báo lỗi**. Chunk có đúng cái bẫy đó, to hơn một bậc.
"""

from app.ai.chunking import MAX_CHARS, MIN_CHARS, OVERLAP_CHARS, TARGET_CHARS, split_content


def _body(sentences: int) -> str:
    return " ".join(
        f"Câu số {n} nói về một chi tiết kỹ thuật cụ thể trong bài viết gốc." for n in range(sentences)
    )


def test_empty_and_tiny_content_yields_no_chunks():
    # Đoạn quá ngắn chỉ thêm một vector nhiễu vào bảng, không thêm tín hiệu nào.
    assert split_content(None) == []
    assert split_content("") == []
    assert split_content("x" * (MIN_CHARS - 1)) == []


def test_short_article_is_one_chunk():
    text = _body(10)
    assert len(text) < TARGET_CHARS
    assert split_content(text) == [text]


def test_full_length_article_stays_within_six_chunks():
    # Trần ingest là 8.000 ký tự ⇒ design D3 hứa ≤ 6 đoạn. Đây là phần "≤6" của DoD 2.1.
    chunks = split_content(_body(400)[:8000])
    assert 1 < len(chunks) <= 6
    assert all(len(c) <= MAX_CHARS for c in chunks)


def test_no_chunk_cuts_a_word_in_half():
    text = _body(400)[:8000]
    words = set(text.split())
    for chunk in split_content(text):
        # Từ đầu và từ cuối của mỗi đoạn phải là từ nguyên vẹn của bài gốc.
        assert chunk.split()[0] in words
        assert chunk.split()[-1] in words


def test_prefers_sentence_boundary():
    text = "A. " * 5 + "x" * (TARGET_CHARS * 2)
    for chunk in split_content(text)[:-1]:
        assert chunk.endswith((".", "!", "?", "…")) or " " not in chunk[-40:]


def test_overlap_keeps_a_fact_spanning_a_boundary_intact():
    # Lý do DUY NHẤT của overlap: sự thật vắt qua ranh giới vẫn nguyên vẹn ở ít nhất một đoạn.
    marker = "CVE-2026-9770 nằm vắt qua ranh giới hai đoạn."
    text = _body(120)
    cut = TARGET_CHARS
    text = text[: cut - len(marker) // 2] + marker + text[cut + len(marker) // 2 :]
    assert any(marker in chunk for chunk in split_content(text))


def test_is_deterministic():
    text = _body(400)[:8000]
    assert split_content(text) == split_content(text)


def test_constants_are_the_embedding_contract():
    # Đổi ba số này ⇒ PHẢI `chunk_documents --redo`. Test đỏ ở đây là lời nhắc đó,
    # không phải một con số tuỳ tiện cần chỉnh cho xanh.
    assert (TARGET_CHARS, MAX_CHARS, OVERLAP_CHARS) == (2000, 2400, 300)
