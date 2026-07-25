import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ChatRequest } from '../../api/chat';
import ChatWidget from '../ChatWidget';

// VÌ SAO TEST NÀY TỒN TẠI: history gộp xuyên scope là Nguy hiểm #3 của báo cáo To-Be
// (Context Drift / History Poisoning). Widget từng giữ MỘT mảng `messages` cho cả phiên và
// gửi toàn bộ nó làm `history` kèm `insight_id` của scope hiện tại → câu nối tiếp mập mờ ("nó",
// "rủi ro thì sao") mang ngữ cảnh bài cũ trong khi server đọc bài mới. Bất biến các test này
// khoá: `history` gửi lên CHỈ được chứa lượt của scope hiện tại (insight_id cụ thể hoặc toàn cục),
// không bao giờ kéo theo lượt của scope khác. Test khẳng định trên PAYLOAD gửi đi, không trên DOM.

const { postChatMock } = vi.hoisted(() => ({ postChatMock: vi.fn() }));

vi.mock('../../api/chat', () => ({ postChat: postChatMock }));
vi.mock('../../api/insights', () => ({
  fetchInsightById: vi.fn(async (id: string) => ({ id, title: `Tin ${id}` })),
}));

let answerCount = 0;

beforeEach(() => {
  postChatMock.mockReset();
  answerCount = 0;
  postChatMock.mockImplementation(async () => ({
    answer: `trả lời ${++answerCount}`,
    citations: [],
    mode: 'global',
  }));
});

/** Payload của lần gọi postChat thứ i (1-indexed). */
function payload(i: number): ChatRequest {
  return postChatMock.mock.calls[i - 1][0] as ChatRequest;
}

/** Nav buttons + widget: điều khiển route để mô phỏng đổi scope trong cùng phiên. */
function Harness() {
  const navigate = useNavigate();
  return (
    <>
      <button onClick={() => navigate('/insights/A')}>go-A</button>
      <button onClick={() => navigate('/insights/B')}>go-B</button>
      <button onClick={() => navigate('/')}>go-home</button>
      <ChatWidget />
    </>
  );
}

function renderWidget() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={['/']}>
        <Harness />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

async function openWidget(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: 'Mở trợ lý hỏi đáp' }));
}

/** Gõ câu hỏi, gửi, chờ postChat được gọi lần thứ `expectCall` rồi chờ câu trả lời render. */
async function ask(
  user: ReturnType<typeof userEvent.setup>,
  text: string,
  expectCall: number,
) {
  await user.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), text);
  await user.click(screen.getByRole('button', { name: 'Gửi' }));
  await waitFor(() => expect(postChatMock).toHaveBeenCalledTimes(expectCall));
  await screen.findByText(`trả lời ${expectCall}`);
}

describe('ChatWidget — cô lập history theo scope (chống drift)', () => {
  // Task 3.1
  it('A→B→A: history ở B không chứa lượt của A; quay lại A thấy lại luồng A', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    // Scope A: hỏi câu đầu — history rỗng, insight_id = A.
    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi A', 1);
    expect(payload(1).insight_id).toBe('A');
    expect(payload(1).history).toEqual([]);

    // Đổi sang scope B, hỏi câu nối tiếp mập mờ.
    await user.click(screen.getByRole('button', { name: 'go-B' }));
    await ask(user, 'rủi ro của nó', 2);
    expect(payload(2).insight_id).toBe('B');
    // BẤT BIẾN: history của B tuyệt đối không mang lượt của A.
    expect(payload(2).history).toEqual([]);
    expect(payload(2).history.some((t) => t.content.includes('câu hỏi A'))).toBe(false);
    // Luồng B không hiển thị lượt của A.
    expect(screen.queryByText('câu hỏi A')).toBeNull();

    // Quay lại A: luồng A còn nguyên, câu tiếp theo mang history của A.
    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await screen.findByText('câu hỏi A');
    expect(screen.queryByText('rủi ro của nó')).toBeNull();
    await ask(user, 'thêm câu A', 3);
    expect(payload(3).insight_id).toBe('A');
    expect(payload(3).history).toEqual([
      { role: 'user', content: 'câu hỏi A' },
      { role: 'assistant', content: 'trả lời 1' },
    ]);
  });

  // Task 3.2 — "Xung đột Mức 2" của Scope Paradox.
  // (`chat-scope-routing` thay chip một chiều bằng badge phạm vi hai chiều; bất biến
  // "history theo scope" không đổi, chỉ đổi control để bấm.)
  it('chuyển scope sang toàn hệ thống: insight_id vắng VÀ history không chứa lượt về bài', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi A', 1);

    await user.click(
      screen.getByRole('button', { name: 'Chuyển sang hỏi toàn hệ thống' }),
    );
    await ask(user, 'tuần này có gì', 2);

    expect(payload(2).insight_id).toBeFalsy();
    expect(payload(2).history).toEqual([]);
    expect(payload(2).history.some((t) => t.content.includes('câu hỏi A'))).toBe(false);
  });

  // Task 3.3 — rời detail về danh sách; khẳng định trên payload, không trên DOM.
  it('rời detail về danh sách: history là luồng toàn cục, không phải luồng bài', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi A', 1);

    // Điều hướng về '/', hỏi toàn cục.
    await user.click(screen.getByRole('button', { name: 'go-home' }));
    await ask(user, 'tổng quan hệ thống', 2);

    expect(payload(2).insight_id).toBeFalsy();
    expect(payload(2).history).toEqual([]);
    expect(payload(2).history.some((t) => t.content.includes('câu hỏi A'))).toBe(false);
  });

  // Task 2.4 — đóng/mở panel không được mất luồng nào.
  it('đóng rồi mở lại panel: luồng của scope A còn nguyên', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi A', 1);

    // Đóng panel (nút ✕ có aria-label "Đóng") rồi mở lại.
    await user.click(screen.getByRole('button', { name: 'Đóng' }));
    await openWidget(user);

    // Luồng A còn nguyên.
    await screen.findByText('câu hỏi A');
    await screen.findByText('trả lời 1');
    // Câu tiếp theo vẫn mang history của A.
    await ask(user, 'thêm câu A', 2);
    expect(payload(2).insight_id).toBe('A');
    expect(payload(2).history).toEqual([
      { role: 'user', content: 'câu hỏi A' },
      { role: 'assistant', content: 'trả lời 1' },
    ]);
  });
});
