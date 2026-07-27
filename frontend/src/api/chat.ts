import { apiClient as api } from './client';

export interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
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
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  // "expanded" = server tự mở rộng từ scope bài sang toàn hệ thống khi câu hỏi vượt
  // phạm vi bài đang xem (change `chat-scope-routing`).
  mode: 'insight' | 'global' | 'meta' | 'expanded';
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
