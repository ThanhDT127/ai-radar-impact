import type { Citation } from '../api/chat';

/**
 * Cắt câu trả lời thành các đoạn text và marker `[n]` đã giải sẵn thành citation.
 *
 * Tách khỏi component có chủ đích: đây là **phía frontend của một hợp đồng cắt qua ranh giới**
 * backend↔frontend, và hợp đồng đó từng vỡ mà test cả hai bên đều xanh. Là hàm thuần thì nó
 * test được trực tiếp bằng chính dãy marker mà backend sinh ra — xem
 * `__tests__/chatAnswer.boundary.test.ts`.
 *
 * ⚠️ `n` là **số index do server cấp phát**, KHÔNG phải vị trí trong mảng `citations`. Bản cũ
 * dùng `citations[n - 1]`: nó chỉ đúng khi model trích dẫn liền mạch từ `[1]`, mà điều đó
 * đúng vì prompt dặn "tin ở đầu danh sách đáng chọn hơn" — tức là một *thói quen của model*,
 * không phải bất biến. Ngay khi model bỏ qua một tin ở giữa (`[1][2][4]`), mọi marker sau chỗ
 * hổng trỏ sang insight khác. Đừng "tối ưu" về phép tính chỉ số.
 */
export interface AnswerSegment {
  text: string;
  /** Có giá trị khi đoạn này là marker `[n]` giải được sang một citation. */
  citation?: Citation;
}

const MARKER_SPLIT = /(\[\d+\])/g;
const MARKER_EXACT = /^\[(\d+)\]$/;

export function parseAnswer(content: string, citations: Citation[]): AnswerSegment[] {
  return content.split(MARKER_SPLIT).map((part) => {
    const match = MARKER_EXACT.exec(part);
    if (!match) return { text: part };

    const n = Number(match[1]);
    const citation = citations.find((c) => c.n === n);
    // Không tìm thấy → text thường. TUYỆT ĐỐI không rơi sang citation khác: trỏ sai tin còn
    // tệ hơn không trỏ, vì người đọc tin vào link.
    return citation ? { text: part, citation } : { text: part };
  });
}
