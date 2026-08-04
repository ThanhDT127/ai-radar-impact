import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ChatRequest } from '../../api/chat';
import ChatWidget from '../ChatWidget';

// VÌ SAO TEST NÀY TỒN TẠI (thay `ChatWidget.scope.test.tsx`): phạm vi hội thoại không còn
// là một CHẾ ĐỘ để bật/tắt mà là một TẬP tin sửa được — working set (`chat-context-depth`).
// Badge hai chiều của `chat-scope-routing` biến mất cùng lý do: nó chỉ diễn tả được "một
// bài" hoặc "toàn hệ thống", trong khi ca hỏng phải chữa là "hai bài cùng lúc".
//
// Test khoá: tin vào ngữ cảnh khi mở trang chi tiết và khi bấm citation; bỏ được từng
// mục; và những gì hiển thị đúng bằng những gì gửi lên server (`referenced_insight_ids`).
// Nhãn `mode="expanded"` vẫn giữ — đường `insight_id` cũ còn sống cho client cũ.

// Widget nay tiêu thụ `streamChat` (SSE) chứ không `postChat` — bất biến các test này khoá
// thì không đổi, chỉ đổi đường ống. Mock trả thẳng một `commit`: hình dạng luồng là việc của
// `ChatWidget.streaming.test.tsx`.
const { streamChatMock } = vi.hoisted(() => ({ streamChatMock: vi.fn() }));

vi.mock('../../api/chat', () => ({ streamChat: streamChatMock }));
vi.mock('../../api/insights', () => ({
  fetchInsightById: vi.fn(async (id: string) => ({ id, title: `Tin ${id}` })),
}));

let answerCount = 0;

beforeEach(() => {
  streamChatMock.mockReset();
  answerCount = 0;
  streamChatMock.mockImplementation(async (_payload, handlers) => {
    handlers.onCommit?.({
      answer: `trả lời ${++answerCount}`,
      citations: [],
      mode: 'insight',
    });
  });
});

function payload(i: number): ChatRequest {
  return streamChatMock.mock.calls[i - 1][0] as ChatRequest;
}

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

async function ask(
  user: ReturnType<typeof userEvent.setup>,
  text: string,
  expectCall: number,
) {
  await user.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), text);
  await user.click(screen.getByRole('button', { name: 'Gửi' }));
  await waitFor(() => expect(streamChatMock).toHaveBeenCalledTimes(expectCall));
  await screen.findByText(`trả lời ${expectCall}`);
}

describe('ChatWidget — working set', () => {
  it('mở trang chi tiết đưa bài vào ngữ cảnh, và chip hiện đúng tin đó', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    // Ở danh sách: chưa có gì trong ngữ cảnh.
    expect(screen.queryByLabelText('Tin đang trong ngữ cảnh')).toBeNull();

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await screen.findByRole('button', { name: 'Bỏ Tin A khỏi ngữ cảnh' });

    await ask(user, 'bài này nói gì', 1);
    expect(payload(1).referenced_insight_ids).toEqual(['A']);
  });

  it('bấm citation đưa tin được trích vào ngữ cảnh', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    streamChatMock.mockImplementationOnce(async (_p, handlers) => {
      answerCount += 1;
      handlers.onCommit?.({
        answer: 'xem thêm [4]',
        citations: [
          { n: 4, insight_id: 'Z', title: 'Tin Z', source_url: 'https://z' },
        ],
        mode: 'global',
      });
    });
    await user.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), 'tuần này có gì');
    await user.click(screen.getByRole('button', { name: 'Gửi' }));
    await screen.findByText('Tin Z', { exact: false });

    // Link nguồn dưới bong bóng — bấm vào là đưa tin đó vào ngữ cảnh.
    await user.click(screen.getByRole('link', { name: '[4] Tin Z' }));
    await screen.findByRole('button', { name: 'Bỏ Tin Z khỏi ngữ cảnh' });

    await ask(user, 'nói kỹ hơn về nó', 2);
    expect(payload(2).referenced_insight_ids).toContain('Z');
  });

  it('bỏ chip thì tin đó không còn được gửi lên', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await user.click(screen.getByRole('button', { name: 'go-B' }));
    await screen.findByRole('button', { name: 'Bỏ Tin B khỏi ngữ cảnh' });

    await user.click(screen.getByRole('button', { name: 'Bỏ Tin A khỏi ngữ cảnh' }));
    expect(screen.queryByRole('button', { name: 'Bỏ Tin A khỏi ngữ cảnh' })).toBeNull();

    await ask(user, 'câu hỏi', 1);
    expect(payload(1).referenced_insight_ids).toEqual(['B']);
  });

  it('mở lại đúng bài đang có trong ngữ cảnh không tạo chip trùng', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await screen.findByRole('button', { name: 'Bỏ Tin A khỏi ngữ cảnh' });
    await user.click(screen.getByRole('button', { name: 'go-home' }));
    await user.click(screen.getByRole('button', { name: 'go-A' }));

    await ask(user, 'câu hỏi', 1);
    expect(payload(1).referenced_insight_ids).toEqual(['A']);
  });

  it('có working set thì KHÔNG gửi kèm insight_id (đường cũ mode B nhường chỗ)', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await screen.findByRole('button', { name: 'Bỏ Tin A khỏi ngữ cảnh' });
    await ask(user, 'bài này nói gì', 1);

    expect(payload(1).insight_id).toBeFalsy();
    expect(payload(1).referenced_insight_ids).toEqual(['A']);
  });

  it('câu trả lời mode="expanded" vẫn được gắn nhãn', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    streamChatMock.mockImplementationOnce(async (_p, handlers) => {
      answerCount += 1;
      handlers.onCommit?.({ answer: 'tìm toàn hệ thống', citations: [], mode: 'expanded' });
    });
    await user.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), 'có tin sa thải không');
    await user.click(screen.getByRole('button', { name: 'Gửi' }));

    await screen.findByText(/Tìm trên toàn hệ thống/);
  });
});
