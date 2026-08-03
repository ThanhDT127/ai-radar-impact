import { apiClient as api } from './client';

export interface TurnCitation {
  n: number;
  title: string;
  /**
   * Định danh insight của nguồn này. Server dùng nó để GHIM tin đã bàn vào ngữ cảnh lượt
   * hiện tại (`chat-history-pinning`): `_rank` chỉ nhìn câu hỏi của lượt này, nên tin vừa
   * được trích ở lượt trước rơi khỏi top-K **52%** số lần khi người dùng đổi chủ đề (đo
   * 29/07/2026) — và khi đó model đọc được cái *tên* trong history mà không có dòng dữ liệu
   * nào của nó.
   *
   * Optional để client cũ không vỡ: thiếu ⇒ server không ghim gì, hành vi như trước.
   */
  insight_id?: string;
}

export interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
  /**
   * Citations của CHÍNH lượt này. Server cần chúng để dịch marker `[n]` trong history
   * thành tên bài: bảng ánh xạ `n → insight` được dựng LẠI mỗi lượt, nên `[3]` của lượt
   * trước và `[3]` của lượt này là hai tin khác nhau. Không gửi ⇒ server bỏ marker đi.
   */
  citations?: TurnCitation[];
}

export interface Citation {
  /**
   * Số marker do SERVER cấp phát (số thứ tự trong index, 1..N) — KHÔNG phải vị trí trong
   * mảng `citations`. Hai hệ chỉ trùng khi model trích dẫn liền mạch từ [1], và nó thường
   * làm vậy chỉ vì prompt dặn "tin ở đầu danh sách đáng chọn hơn". Giải marker bằng
   * `citations.find(c => c.n === n)`, tuyệt đối không bằng `citations[n - 1]`.
   */
  n: number;
  insight_id: string;
  title: string;
  source_url: string;
}

export interface ChatRequest {
  question: string;
  history: ChatTurn[];
  insight_id?: string | null;
  /**
   * Working set — insight người dùng đang thao tác (mở trang chi tiết, bấm citation).
   * Tách khỏi `question` một cách CÓ CHỦ ĐÍCH: nhét URL/UUID vào text câu hỏi vừa phá bất
   * biến "prompt không chứa định danh", vừa làm nhiễu phép tính từ khoá của server.
   */
  referenced_insight_ids?: string[];
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  // "expanded" = server tự mở rộng từ scope bài sang toàn hệ thống khi câu hỏi vượt
  // phạm vi bài đang xem (change `chat-scope-routing`).
  // "focused" = có working set do người dùng chọn (change `chat-context-depth`).
  mode: 'insight' | 'global' | 'meta' | 'expanded' | 'focused';
}

// Backend cũng cắt còn 10 lượt gần nhất; giữ số ở đây để không gửi thừa qua mạng.
export const MAX_HISTORY_TURNS = 10;

export async function postChat(payload: ChatRequest): Promise<ChatResponse> {
  const { data } = await api.post<ChatResponse>('/chat', {
    ...payload,
    history: payload.history.slice(-MAX_HISTORY_TURNS),
  });
  return data;
}

/** Mã lỗi do server phát trong sự kiện `error` của luồng SSE. */
export type ChatErrorCode = 'quota' | 'not_found' | 'server';

export interface ChatStreamHandlers {
  /** Mốc tiến trình thật của pipeline — thay spinner đơn. */
  onStatus?: (text: string) => void;
  /** Một mẩu câu trả lời. Nội dung TẠM: `onCommit` mới là bản chốt. */
  onToken?: (text: string) => void;
  /**
   * Sự kiện chốt. `answer` là bản đã qua grounding/fail-closed nên có thể KHÁC hẳn phần
   * đã stream — luôn THAY, không bao giờ nối thêm.
   */
  onCommit?: (data: ChatResponse) => void;
  onError?: (code: ChatErrorCode, message: string) => void;
}

/**
 * Đọc `POST /api/v1/chat/stream` bằng fetch + ReadableStream.
 *
 * Không dùng `EventSource`: nó chỉ biết GET, mà payload chat có `history` — nhét vào query
 * string thì vỡ giới hạn URL ngay ở lượt hỏi thứ ba. Nên tự tách khung SSE, vốn cũng chỉ là
 * "các khối cách nhau bằng dòng trống".
 *
 * `signal` để huỷ khi người dùng đổi scope (design D6). Huỷ là đường ra BÌNH THƯỜNG, không
 * phải lỗi — hàm nuốt `AbortError` và không gọi `onError`.
 */
export async function streamChat(
  payload: ChatRequest,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  let response: Response;
  try {
    response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...payload,
        history: payload.history.slice(-MAX_HISTORY_TURNS),
      }),
      signal,
    });
  } catch (err) {
    if (signal?.aborted) return;
    throw err;
  }

  if (!response.ok || !response.body) {
    handlers.onError?.('server', 'Không kết nối được tới trợ lý.');
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Khung SSE kết thúc bằng dòng trống. Phần đuôi chưa đủ khung thì giữ lại chờ chunk
      // sau — chunk mạng cắt ở đâu là chuyện của TCP, không liên quan tới ranh giới khung.
      let sep = buffer.indexOf('\n\n');
      while (sep !== -1) {
        dispatchFrame(buffer.slice(0, sep), handlers);
        buffer = buffer.slice(sep + 2);
        sep = buffer.indexOf('\n\n');
      }
    }
  } catch (err) {
    if (signal?.aborted) return;
    throw err;
  }
}

function dispatchFrame(frame: string, handlers: ChatStreamHandlers): void {
  let event = 'message';
  let data = '';
  for (const line of frame.split('\n')) {
    if (line.startsWith('event: ')) event = line.slice(7);
    else if (line.startsWith('data: ')) data += line.slice(6);
  }
  if (!data) return;

  const parsed = JSON.parse(data);
  if (event === 'status') handlers.onStatus?.(parsed.text);
  else if (event === 'token') handlers.onToken?.(parsed.text);
  else if (event === 'commit') handlers.onCommit?.(parsed as ChatResponse);
  else if (event === 'error') handlers.onError?.(parsed.code, parsed.message);
}
