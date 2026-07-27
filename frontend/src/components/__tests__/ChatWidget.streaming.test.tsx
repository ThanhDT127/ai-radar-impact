import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ChatStreamHandlers } from '../../api/chat';
import ChatWidget from '../ChatWidget';

// VÌ SAO TEST NÀY TỒN TẠI: streaming đưa vào widget một trạng thái chưa từng có — câu trả lời
// TẠM, hiện trên màn hình trước khi server kịp kiểm grounding. Ba thứ phải khoá:
//   1. text tạm KHÔNG BAO GIỜ được nhập luồng hội thoại (nó sẽ thành `history` của lượt sau);
//   2. sự kiện chốt THAY text tạm — ca fail-closed là ca text tạm hoàn toàn sai;
//   3. đổi scope giữa luồng → huỷ, và phần dở không rơi sang luồng scope mới (design D6).
// Đây đều là lỗi chỉ sống ở state frontend: backend trả đúng mà người dùng vẫn thấy sai.

const { streamChatMock } = vi.hoisted(() => ({ streamChatMock: vi.fn() }));

vi.mock('../../api/chat', () => ({ streamChat: streamChatMock }));
vi.mock('../../api/insights', () => ({
  fetchInsightById: vi.fn(async (id: string) => ({ id, title: `Tin ${id}` })),
}));

/** Điều khiển tay một luồng đang chảy — mô phỏng server phát từng sự kiện một. */
interface Live {
  handlers: ChatStreamHandlers;
  signal?: AbortSignal;
  payload: { question: string; history: unknown[]; insight_id?: string | null };
  resolve: () => void;
}

let live: Live[] = [];

beforeEach(() => {
  streamChatMock.mockReset();
  live = [];
  streamChatMock.mockImplementation(
    (payload, handlers, signal) =>
      new Promise<void>((resolve) => {
        live.push({ handlers, signal, payload, resolve });
      }),
  );
});

function last(): Live {
  return live[live.length - 1];
}

/** Phát một sự kiện từ "server" và để React xử lý xong. */
async function emit(fn: (l: Live) => void) {
  await act(async () => {
    fn(last());
  });
}

function Harness() {
  const navigate = useNavigate();
  return (
    <>
      <button onClick={() => navigate('/insights/A')}>go-A</button>
      <button onClick={() => navigate('/insights/B')}>go-B</button>
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

async function ask(user: ReturnType<typeof userEvent.setup>, text: string) {
  await user.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), text);
  await user.click(screen.getByRole('button', { name: 'Gửi' }));
  await waitFor(() => expect(streamChatMock).toHaveBeenCalled());
}

describe('ChatWidget — render tăng dần + trạng thái tiến trình', () => {
  it('hiện status của server trong lúc chờ, rồi token chảy vào bong bóng', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await ask(user, 'tuần này có gì');

    // Chưa có token nào: chỗ này trước đây là spinner "Đang tìm trong hệ thống…" cứng.
    await emit((l) => l.handlers.onStatus?.('Đang tìm trong hệ thống…'));
    expect(screen.getByText('Đang tìm trong hệ thống…')).toBeTruthy();

    await emit((l) => l.handlers.onStatus?.('Đang soạn câu trả lời…'));
    expect(screen.getByText('Đang soạn câu trả lời…')).toBeTruthy();

    // Token đầu tiên chiếm chỗ status.
    await emit((l) => l.handlers.onToken?.('Có ba tin '));
    expect(screen.getByText(/Có ba tin/)).toBeTruthy();
    expect(screen.queryByText('Đang soạn câu trả lời…')).toBeNull();

    // Marker `[n]` được tách ra thành đoạn riêng ngay khi đang stream, nên khẳng định trên
    // text đã ráp của bong bóng chứ không trên một node lá.
    await emit((l) => l.handlers.onToken?.('đáng chú ý [1].'));
    const bubble = screen.getByText(/Có ba tin/).closest('div');
    expect(bubble?.textContent).toBe('Có ba tin đáng chú ý [1].');
  });

  it('sự kiện chốt gắn citations với ĐÚNG số marker của nó', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await ask(user, 'tuần này có gì');

    await emit((l) => l.handlers.onToken?.('Tin quan trọng [7].'));
    await emit((l) =>
      l.handlers.onCommit?.({
        answer: 'Tin quan trọng [7].',
        citations: [
          { n: 7, insight_id: 'ins-7', title: 'Tin số bảy', source_url: 'https://e/7' },
        ],
        mode: 'global',
      }),
    );

    const link = screen.getByRole('link', { name: /\[7\] Tin số bảy/ });
    expect(link.getAttribute('href')).toBe('/insights/ins-7');
  });

  it('fail-closed: sự kiện chốt THAY text tạm, không để lại chữ ungrounded', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await ask(user, 'có tin gì về Gemini 4');

    await emit((l) => l.handlers.onToken?.('Có, Google vừa ra Gemini 4.'));
    expect(screen.getByText(/Google vừa ra Gemini 4/)).toBeTruthy();

    await emit((l) =>
      l.handlers.onCommit?.({
        answer: 'Tôi không đủ căn cứ trong hệ thống để trả lời câu hỏi này.',
        citations: [],
        mode: 'global',
      }),
    );

    expect(screen.getByText(/không đủ căn cứ/)).toBeTruthy();
    expect(screen.queryByText(/Google vừa ra Gemini 4/)).toBeNull();
  });

  it('nhãn mở rộng vẫn hiện khi câu trả lời đến qua stream', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu ngoài phạm vi bài');

    await emit((l) => l.handlers.onToken?.('Toàn hệ thống có [2].'));
    await emit((l) =>
      l.handlers.onCommit?.({
        answer: 'Toàn hệ thống có [2].',
        citations: [],
        mode: 'expanded',
      }),
    );

    expect(screen.getByText(/Tìm trên toàn hệ thống/)).toBeTruthy();
  });
});

describe('ChatWidget — chống gửi trùng khi đang stream', () => {
  it('nút Gửi bị vô hiệu hoá cho tới khi luồng chốt', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await ask(user, 'câu dài');

    const send = screen.getByRole('button', { name: 'Gửi' }) as HTMLButtonElement;
    expect(send.disabled).toBe(true);

    await emit((l) => l.handlers.onToken?.('đang trả lời…'));
    expect((screen.getByRole('button', { name: 'Gửi' }) as HTMLButtonElement).disabled).toBe(
      true,
    );

    await emit((l) =>
      l.handlers.onCommit?.({ answer: 'xong [1].', citations: [], mode: 'global' }),
    );
    expect((screen.getByRole('button', { name: 'Gửi' }) as HTMLButtonElement).disabled).toBe(
      false,
    );
  });

  it('gõ thêm và bấm Gửi khi đang stream KHÔNG sinh request thứ hai', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await ask(user, 'câu một');

    await user.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), 'câu hai');
    await user.click(screen.getByRole('button', { name: 'Gửi' }));

    expect(streamChatMock).toHaveBeenCalledTimes(1);
  });
});

describe('ChatWidget — huỷ khi đổi scope (design D6)', () => {
  it('đổi bài giữa luồng: request bị abort và phần dở không sang luồng mới', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi ở A');

    await emit((l) => l.handlers.onToken?.('phần trả lời dở của A'));
    expect(screen.getByText(/phần trả lời dở của A/)).toBeTruthy();
    const streamA = last();

    await user.click(screen.getByRole('button', { name: 'go-B' }));

    expect(streamA.signal?.aborted).toBe(true);
    expect(screen.queryByText(/phần trả lời dở của A/)).toBeNull();
  });

  it('phần dở KHÔNG nhập luồng cũ: quay lại A không thấy nó, và history sạch', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi ở A');
    await emit((l) => l.handlers.onToken?.('phần trả lời dở của A'));

    await user.click(screen.getByRole('button', { name: 'go-B' }));
    await user.click(screen.getByRole('button', { name: 'go-A' }));

    // Câu hỏi còn (người dùng đã hỏi thật), câu trả lời dở thì không.
    expect(screen.getByText('câu hỏi ở A')).toBeTruthy();
    expect(screen.queryByText(/phần trả lời dở của A/)).toBeNull();

    await ask(user, 'hỏi lại ở A');
    expect(last().payload.history).toEqual([{ role: 'user', content: 'câu hỏi ở A' }]);
  });

  it('sự kiện đến SAU khi đã huỷ bị bỏ qua, không nhiễm luồng nào', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi ở A');
    const streamA = last();

    await user.click(screen.getByRole('button', { name: 'go-B' }));

    // Server chậm chân: commit về sau khi client đã bỏ đi.
    await emit(() =>
      streamA.handlers.onCommit?.({
        answer: 'câu trả lời muộn của A',
        citations: [],
        mode: 'insight',
      }),
    );

    expect(screen.queryByText(/câu trả lời muộn của A/)).toBeNull();
    await user.click(screen.getByRole('button', { name: 'go-A' }));
    expect(screen.queryByText(/câu trả lời muộn của A/)).toBeNull();
  });

  it('đổi phạm vi bằng badge cũng huỷ luồng đang chảy', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi trong bài');
    await emit((l) => l.handlers.onToken?.('đang trả lời trong bài'));
    const streamA = last();

    await user.click(screen.getByRole('button', { name: 'Chuyển sang hỏi toàn hệ thống' }));

    expect(streamA.signal?.aborted).toBe(true);
    expect(screen.queryByText(/đang trả lời trong bài/)).toBeNull();
  });
});

describe('ChatWidget — lỗi qua sự kiện', () => {
  it('mã quota hiện thông báo hết lượt kèm nút Thử lại', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await ask(user, 'tuần này có gì');

    await emit((l) => l.handlers.onError?.('quota', 'từ server'));

    expect(screen.getByText(/hết lượt hỏi trong ngày/)).toBeTruthy();
    expect(screen.getByRole('button', { name: 'Thử lại' })).toBeTruthy();
  });
});
