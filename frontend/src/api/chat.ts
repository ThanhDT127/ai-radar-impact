import { apiClient as api } from './client';

export interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface Citation {
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
  mode: 'insight' | 'global';
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
