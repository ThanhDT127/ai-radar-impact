/**
 * Lưu bền luồng hội thoại chat THEO TAB.
 *
 * Vì sao tồn tại: toàn bộ cuộc hội thoại sống trong `useState` của `ChatWidget`, mà `history`
 * lại do client dựng lại và gửi lên mỗi lượt — server cố ý không lưu nội dung (`chat_logs`:
 * chỉ metadata). Nên client mất trí nhớ = cuộc hội thoại chết, kể cả khi server vẫn khoẻ, và
 * một lần F5 lỡ tay xoá sạch cả những lượt đã trả tiền cho model.
 *
 * BA BẤT BIẾN của module này:
 *
 *   A — Luồng hội thoại thuộc về TAB, KHÔNG thuộc về ngữ cảnh. Không thao tác ngữ cảnh nào
 *       (bỏ chip, bỏ HẾT chip, đổi bài, điều hướng) được phép làm mất câu chữ đã trao đổi.
 *   B — Mỗi tab một luồng riêng.
 *   C — Chỉ nội dung ĐÃ CHỐT mới chạm storage.
 *
 * Bất biến A không phải lời hứa suông — nó là lý do khoá lưu trữ **PHẲNG**. Phiên bản đầu của
 * widget (`chat-context-isolation`) đánh khoá `threads` theo scope, nên rời bài là luồng của
 * bài đó biến khỏi màn hình. Đánh khoá blob theo scope/bài đang xem/working set cho "gọn" sẽ
 * hồi sinh đúng lỗi đó, ở dạng khó thấy hơn: bỏ hết chip = đổi khoá = hội thoại "mất".
 *
 *   ❌  sessionStorage[`radar-chat:${scopeKey}`]
 *   ✅  sessionStorage['radar-chat-v1']   ← một khoá cho cả tab; workingSet là TRƯỜNG bên trong
 *
 * `sessionStorage` chứ không `localStorage`: yêu cầu là per-tab. Nó phủ đúng F5, back/forward
 * qua trang ngoài, và khôi phục tab sau crash; đổi lại mất khi đóng tab — chấp nhận có chủ đích.
 */

import type { Citation } from '../api/chat';

/** Một tin trong working set — chỉ cần id để gửi lên và title để hiển thị. */
export interface Ref {
  id: string;
  title: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  isError?: boolean;
  // Server tự mở rộng sang toàn hệ thống khi câu hỏi vượt phạm vi bài đang xem. Phải gắn
  // nhãn, vì người dùng đang ở scope "Bài đang xem" mà câu trả lời lại đến từ tin khác —
  // không nói ra thì trông như bot bịa từ bài đang mở.
  expanded?: boolean;
  /**
   * HTML Search Suggestions của Google, chỉ có khi lượt đó CÓ tra cứu ngoài. Hiển thị là
   * yêu cầu tuân thủ điều khoản Grounding with Google Search, không phải tuỳ chọn.
   *
   * KHÔNG được lưu xuống storage — xem `stripVolatile`.
   */
  searchSuggestions?: string | null;
}

export interface PersistedSession {
  v: number;
  messages: Message[];
  workingSet: Ref[];
  open: boolean;
}

/**
 * Khoá PHẲNG, một cho cả tab. Không bao giờ được nối thêm scope/id/working set vào đây —
 * xem bất biến A ở đầu file.
 */
export const STORAGE_KEY = 'radar-chat-v1';

/**
 * Phiên bản hình dạng dữ liệu. Lệch ⇒ **VỨT**, không migrate (xem `loadSession`).
 *
 * Tăng số này khi `Message`/`Citation`/`Ref` đổi hình dạng theo kiểu làm blob cũ hiểu sai —
 * ví dụ `Citation.n` (thêm ở `chat-citation-integrity`) hay `Citation.kind` (thêm ở
 * `chat-web-fallback`). Blob cũ hồi sinh vào code mới sẽ giải marker `[n]` sang tin KHÁC mà
 * không có gì đỏ ở đâu.
 */
export const SESSION_VERSION = 1;

/**
 * Trần số message ghi xuống. `sessionStorage` ~5MB/origin và một câu trả lời ~1–4KB nên đây
 * là dư rộng; nó chỉ để một cuộc hội thoại rất dài không bao giờ chạm trần quota.
 *
 * Cắt ở đây KHÔNG đụng tới thứ server nhìn thấy: `MAX_HISTORY_TURNS` vốn chỉ gửi 10 tin nhắn
 * gần nhất lên. Phần dôi ra thuần tuý để người dùng đọc lại.
 */
export const MAX_PERSISTED_MESSAGES = 50;

/**
 * Bỏ các trường KHÔNG được lưu khỏi một message.
 *
 * `searchSuggestions` là HTML đi thẳng vào `dangerouslySetInnerHTML`. Hai lý do độc lập để
 * không lưu: (1) hồi sinh HTML từ storage mở rộng ranh giới tin cậy từ "response server trả
 * trong phiên này" sang "bất cứ thứ gì nằm trong storage"; (2) nó là UI tuân thủ gắn với MỘT
 * truy vấn tại MỘT thời điểm — hiện lại một khối gợi ý đã cũ không phục vụ mục đích tuân thủ
 * nào.
 *
 * `citations` thì ngược lại — giữ NGUYÊN VẸN. Cám dỗ tự nhiên là rút gọn blob còn
 * `{role, content}`; làm thế thì sau F5 mọi lượt cũ mất `insight_id`, cơ chế ghim của
 * `chat-history-pinning` tắt trong im lặng, giao diện trông y hệt, và người dùng chỉ thấy bot
 * "quên" chuyện vừa bàn.
 */
function stripVolatile(message: Message): Message {
  const { searchSuggestions: _dropped, ...rest } = message;
  return rest;
}

/**
 * Đọc luồng đã lưu của tab hiện tại. Trả `null` khi không có gì dùng được — và mọi lý do
 * đều gộp về đúng `null` đó: chưa có gì, JSON hỏng, lệch phiên bản, storage bị chặn.
 *
 * KHÔNG có nhánh migrate. Chuyển đổi dữ liệu chat cũ không đáng giá bằng rủi ro một citation
 * trỏ sai tin.
 */
export function loadSession(): PersistedSession | null {
  let raw: string | null;
  try {
    raw = window.sessionStorage.getItem(STORAGE_KEY);
  } catch {
    // Storage bị chặn (Safari private, một số cấu hình doanh nghiệp). Chat mất trí nhớ còn
    // hơn chat không mở được.
    return null;
  }
  if (!raw) return null;

  try {
    const parsed = JSON.parse(raw) as Partial<PersistedSession>;
    if (parsed?.v !== SESSION_VERSION) return null;
    if (!Array.isArray(parsed.messages) || !Array.isArray(parsed.workingSet)) return null;
    return {
      v: SESSION_VERSION,
      messages: parsed.messages,
      workingSet: parsed.workingSet,
      open: parsed.open === true,
    };
  } catch {
    return null;
  }
}

/**
 * Ghi luồng của tab hiện tại. Thất bại thì im lặng — người dùng mất khả năng khôi phục, chứ
 * không mất widget.
 *
 * Người gọi chịu trách nhiệm KHÔNG truyền vào phần câu trả lời đang stream (bất biến C).
 */
export function saveSession(session: Omit<PersistedSession, 'v'>): void {
  try {
    const payload: PersistedSession = {
      v: SESSION_VERSION,
      messages: session.messages.slice(-MAX_PERSISTED_MESSAGES).map(stripVolatile),
      workingSet: session.workingSet,
      open: session.open,
    };
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
  } catch {
    /* quota đầy hoặc storage bị chặn — bỏ qua */
  }
}

/** Xoá luồng của tab hiện tại. Dùng cho thao tác "Cuộc trò chuyện mới". */
export function clearSession(): void {
  try {
    window.sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    /* xoá không được thì thôi — lần ghi kế tiếp sẽ đè lên */
  }
}
