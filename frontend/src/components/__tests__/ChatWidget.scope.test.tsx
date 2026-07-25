import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ChatRequest } from '../../api/chat';
import ChatWidget from '../ChatWidget';

// VÌ SAO TEST NÀY TỒN TẠI: `chat-context-isolation` (①) chỉ có chip bỏ-ngữ-cảnh MỘT
// CHIỀU — bỏ rồi thì muốn hỏi lại trong bài phải điều hướng đi rồi quay lại. Change
// `chat-scope-routing` thay nó bằng badge phạm vi HAI CHIỀU. Test khoá hai thứ: badge
// phản ánh đúng scope đang gửi lên server, và câu trả lời `mode="expanded"` được gắn
// nhãn — người dùng đang ở scope "Bài đang xem" mà câu trả lời đến từ tin khác, không
// nói ra thì trông như bot bịa từ bài đang mở.

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
    mode: 'insight',
  }));
});

function payload(i: number): ChatRequest {
  return postChatMock.mock.calls[i - 1][0] as ChatRequest;
}

function Harness() {
  const navigate = useNavigate();
  return (
    <>
      <button onClick={() => navigate('/insights/A')}>go-A</button>
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

describe('ChatWidget — badge phạm vi hai chiều', () => {
  it('ở trang chi tiết hiện scope "Bài đang xem"; ngoài danh sách không có badge', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    expect(screen.queryByText(/Phạm vi:/)).toBeNull();

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    expect(await screen.findByText('Bài đang xem')).toBeTruthy();
  });

  it('chuyển được CẢ HAI CHIỀU tại chỗ, không điều hướng', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole('button', { name: 'go-A' }));

    // Bài → toàn hệ thống
    await user.click(screen.getByRole('button', { name: 'Chuyển sang hỏi toàn hệ thống' }));
    expect(await screen.findByText('Toàn hệ thống')).toBeTruthy();
    await ask(user, 'câu toàn cục', 1);
    expect(payload(1).insight_id).toBeFalsy();

    // Toàn hệ thống → quay lại bài. Đây là chiều mà ① KHÔNG có.
    await user.click(
      screen.getByRole('button', { name: 'Chuyển sang hỏi trong bài đang xem' }),
    );
    expect(await screen.findByText('Bài đang xem')).toBeTruthy();
    await ask(user, 'câu trong bài', 2);
    expect(payload(2).insight_id).toBe('A');
  });

  it('mỗi chiều chuyển scope giữ luồng hội thoại riêng (cô lập của ①)', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole('button', { name: 'go-A' }));

    await ask(user, 'hỏi trong bài', 1);
    await user.click(screen.getByRole('button', { name: 'Chuyển sang hỏi toàn hệ thống' }));
    await ask(user, 'hỏi toàn cục', 2);

    expect(payload(2).history).toEqual([]);

    // Quay lại bài: history của luồng bài còn nguyên, không dính lượt toàn cục.
    await user.click(
      screen.getByRole('button', { name: 'Chuyển sang hỏi trong bài đang xem' }),
    );
    await ask(user, 'hỏi tiếp trong bài', 3);

    expect(payload(3).insight_id).toBe('A');
    expect(payload(3).history).toEqual([
      { role: 'user', content: 'hỏi trong bài' },
      { role: 'assistant', content: 'trả lời 1' },
    ]);
    expect(payload(3).history.some((t) => t.content.includes('toàn cục'))).toBe(false);
  });
});

describe('ChatWidget — nhãn câu trả lời mở rộng', () => {
  it('mode="expanded" được gắn nhãn tìm toàn hệ thống', async () => {
    postChatMock.mockImplementation(async () => ({
      answer: `trả lời ${++answerCount}`,
      citations: [],
      mode: 'expanded',
    }));
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole('button', { name: 'go-A' }));

    await ask(user, 'câu ngoài phạm vi bài', 1);

    expect(screen.getByText(/Tìm trên toàn hệ thống/)).toBeTruthy();
  });

  it('mode="insight" KHÔNG gắn nhãn — nhãn phải phân biệt được hai loại', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole('button', { name: 'go-A' }));

    await ask(user, 'câu trong bài', 1);

    expect(screen.queryByText(/Tìm trên toàn hệ thống/)).toBeNull();
  });
});
