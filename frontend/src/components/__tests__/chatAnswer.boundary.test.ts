import { describe, it, expect } from 'vitest';
import { parseAnswer } from '../chatAnswer';
import type { Citation } from '../../api/chat';

// VÌ SAO TEST NÀY TỒN TẠI: lỗi nó chặn sống ở **khe giữa hai tầng**, nơi không tầng nào tự
// bảo vệ được. Backend đánh số marker theo INDEX (1..60); widget cũ tra `citations[n - 1]`,
// tức theo VỊ TRÍ MẢNG (1..k, k≤5). Hai hệ chỉ trùng khi model trích dẫn liền mạch từ [1].
//
// Bằng chứng cụ thể: `test_resolve_citations_maps_markers_in_order` ở backend khẳng định
// `[2]→B, [1]→A` và nó **XANH** — trong khi chính ca đó làm widget trỏ sai CẢ HAI marker
// ([2] lấy citations[1] = A, [1] lấy citations[0] = B). Test đứng một bên ranh giới không
// bảo vệ được ranh giới. Các test dưới đây dựng dữ liệu ĐÚNG như backend trả về rồi chạy qua
// logic giải marker của widget.
//
// Lỗi này còn bị che bởi chất lượng xếp hạng: model trích liền mạch chỉ vì prompt dặn "tin ở
// đầu danh sách đáng chọn hơn". Nó sẽ lộ ra đúng lúc xếp hạng kém đi — hai lỗi bùng cùng lúc,
// cái thứ hai im lặng.

/** Dựng citations y như `resolve_citations` của backend: `n` = số marker, thứ tự = xuất hiện. */
function citationsFor(markers: number[]): Citation[] {
  const seen: number[] = [];
  for (const n of markers) if (!seen.includes(n)) seen.push(n);
  return seen.map((n) => ({
    n,
    insight_id: `insight-${n}`,
    title: `Tin ${n}`,
    source_url: `https://example.test/${n}`,
  }));
}

function linkedIds(answer: string, citations: Citation[]): (string | null)[] {
  return parseAnswer(answer, citations)
    .filter((segment) => /^\[\d+\]$/.test(segment.text))
    .map((segment) => segment.citation?.insight_id ?? null);
}

describe('marker [n] luôn trỏ đúng insight mang n đó', () => {
  const cases: Array<{ name: string; markers: number[] }> = [
    { name: 'liền mạch từ 1', markers: [1, 2, 3] },
    { name: 'đơn lẻ không phải 1', markers: [2] },
    { name: 'có lỗ hổng', markers: [1, 2, 4] },
    { name: 'cách quãng', markers: [1, 3, 5] },
    { name: 'đảo thứ tự', markers: [2, 1] },
    { name: 'cách quãng xa', markers: [3, 7, 12] },
  ];

  for (const { name, markers } of cases) {
    it(name, () => {
      const answer = markers.map((n) => `Ý về tin ${n} [${n}].`).join(' ');
      const citations = citationsFor(markers);

      // Mỗi marker phải trỏ đúng `insight-<n>` — quan hệ này là toàn bộ hợp đồng.
      expect(linkedIds(answer, citations)).toEqual(markers.map((n) => `insight-${n}`));
    });
  }
});

it('marker không có citation tương ứng hiển thị như text thường', () => {
  const citations = citationsFor([1]);

  const segments = parseAnswer('Có tin [1] và một số lạ [99].', citations);
  const markers = segments.filter((s) => /^\[\d+\]$/.test(s.text));

  expect(markers.map((s) => s.citation?.insight_id ?? null)).toEqual(['insight-1', null]);
});

it('không bao giờ trỏ sang insight khác khi thiếu citation', () => {
  // Chỉ có citation cho [7]; [3] phải là text thường, TUYỆT ĐỐI không mượn tạm [7].
  const citations: Citation[] = [
    { n: 7, insight_id: 'insight-7', title: 'Tin 7', source_url: 'https://example.test/7' },
  ];

  expect(linkedIds('Ba [3] và bảy [7].', citations)).toEqual([null, 'insight-7']);
});

it('marker lặp lại trỏ cùng một insight', () => {
  const citations = citationsFor([4]);
  expect(linkedIds('Nói [4] rồi nhắc lại [4].', citations)).toEqual([
    'insight-4',
    'insight-4',
  ]);
});

it('giữ nguyên phần text quanh marker', () => {
  const segments = parseAnswer('Trước [2] sau.', citationsFor([2]));
  expect(segments.map((s) => s.text).join('')).toBe('Trước [2] sau.');
});

it('ĐỐI CHỨNG: cách cũ `citations[n-1]` sai ở đúng những ca này', () => {
  // Test này không kiểm code sản phẩm — nó chứng minh bộ ca ở trên THẬT SỰ phân biệt được
  // bản đúng với bản sai. Không có nó thì "6 ca đều pass" có thể chỉ vì ca quá dễ.
  const byArrayPosition = (answer: string, citations: Citation[]) =>
    (answer.match(/\[(\d+)\]/g) ?? []).map((marker) => {
      const n = Number(marker.slice(1, -1));
      return citations[n - 1]?.insight_id ?? null;
    });

  const broken = [
    [1, 2, 4],
    [1, 3, 5],
    [2, 1],
    [3, 7, 12],
    [2],
  ].filter((markers) => {
    const answer = markers.map((n) => `[${n}]`).join(' ');
    const citations = citationsFor(markers);
    const expected = markers.map((n) => `insight-${n}`);
    return JSON.stringify(byArrayPosition(answer, citations)) !== JSON.stringify(expected);
  });

  expect(broken.length).toBe(5);
});
