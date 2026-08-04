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
    await emit((l) => l.handlers.onStatus?.('searching', 'Đang tìm trong hệ thống…'));
    expect(screen.getByText(/Đang tìm trong hệ thống…/)).toBeTruthy();

    await emit((l) => l.handlers.onStatus?.('composing', 'Đang soạn câu trả lời…'));
    expect(screen.getByText(/Đang soạn câu trả lời…/)).toBeTruthy();
    // XẾP CHỒNG: mốc trước KHÔNG biến mất khi mốc sau tới (`chat-status-milestones`).
    expect(screen.getByText(/Đang tìm trong hệ thống…/)).toBeTruthy();

    // Token đầu tiên chiếm chỗ status.
    await emit((l) => l.handlers.onToken?.('Có ba tin '));
    expect(screen.getByText(/Có ba tin/)).toBeTruthy();
    expect(screen.queryByText(/Đang soạn câu trả lời…/)).toBeNull();

    // Marker `[n]` được tách ra thành đoạn riêng ngay khi đang stream, nên khẳng định trên
    // text đã ráp của bong bóng chứ không trên một node lá.
    await emit((l) => l.handlers.onToken?.('đáng chú ý [1].'));
    const bubble = screen.getByText(/Có ba tin/).closest('div');
    expect(bubble?.textContent).toBe('Có ba tin đáng chú ý [1].');
  });

  // --- Mốc tiến trình xếp chồng (change `chat-status-milestones`, task 4.5/4.6) ----------
  //
  // VÌ SAO CẦN: bản trước ghi đè MỘT dòng, nên chuỗi việc server làm là vô hình và người
  // dùng chỉ thấy một dòng nhấp nháy. Bất biến mới là *mốc phân biệt bằng `key`, không bằng
  // `text`* — `text` mang số liệu của lượt nên hai lần phát cùng một mốc luôn khác chuỗi.

  it('mốc cùng `key` CẬP NHẬT TẠI CHỖ, không đẻ dòng trùng', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await ask(user, 'tuần này có gì');

    await emit((l) => l.handlers.onStatus?.('reading', 'Đang đọc bài đang xem…'));
    await emit((l) => l.handlers.onStatus?.('reading', 'Đang đọc kỹ 3 tin: «Tin A»…'));

    expect(screen.queryByText(/Đang đọc bài đang xem…/)).toBeNull();
    expect(screen.getAllByText(/Đang đọc kỹ 3 tin/)).toHaveLength(1);
  });

  it('`key` lạ (server mới hơn client) vẫn hiện, không bị nuốt', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await ask(user, 'tuần này có gì');

    await emit((l) => l.handlers.onStatus?.('mot_moc_chua_biet', 'Đang làm việc gì đó mới…'));

    expect(screen.getByText(/Đang làm việc gì đó mới…/)).toBeTruthy();
  });

  it('vượt trần 4 dòng thì bỏ dòng CŨ NHẤT', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await ask(user, 'tuần này có gì');

    for (const k of ['searching', 'ranked', 'pinned', 'reading', 'composing']) {
      await emit((l) => l.handlers.onStatus?.(k, `mốc ${k}`));
    }

    expect(screen.queryByText(/mốc searching/)).toBeNull();
    for (const k of ['ranked', 'pinned', 'reading', 'composing']) {
      expect(screen.getByText(new RegExp(`mốc ${k}`))).toBeTruthy();
    }
  });

  it('khối mốc biến mất hẳn khi câu trả lời được chốt', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await ask(user, 'tuần này có gì');

    await emit((l) => l.handlers.onStatus?.('searching', 'Đang tìm trong hệ thống…'));
    await emit((l) =>
      l.handlers.onCommit?.({ answer: 'Xong rồi.', citations: [], mode: 'global' }),
    );

    expect(screen.queryByText(/Đang tìm trong hệ thống…/)).toBeNull();
    expect(screen.getByText(/Xong rồi./)).toBeTruthy();
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

describe('ChatWidget — điều hướng giữa luồng (bất biến đổi ở chat-context-depth)', () => {
  it('phần dở KHÔNG BAO GIỜ nhập luồng: chỉ câu đã chốt mới vào history', async () => {
    // Bất biến này KHÔNG đổi — `pending` vẫn nằm ngoài `messages`. Đổi là ở chỗ nó không
    // còn bị vứt khi điều hướng: text tạm sống tới khi `commit` thay nó bằng bản đã qua
    // grounding, và chỉ bản đó vào history của lượt sau.
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi ở A');

    await emit((l) => l.handlers.onToken?.('phần trả lời dở của A'));
    expect(screen.getByText(/phần trả lời dở của A/)).toBeTruthy();

    await emit((l) =>
      l.handlers.onCommit?.({ answer: 'bản đã chốt', citations: [], mode: 'focused' }),
    );
    expect(screen.queryByText(/phần trả lời dở của A/)).toBeNull();

    await ask(user, 'hỏi tiếp');
    expect(last().payload.history).toEqual([
      { role: 'user', content: 'câu hỏi ở A', citations: undefined },
      { role: 'assistant', content: 'bản đã chốt', citations: [] },
    ]);
  });

  it('đổi bài giữa luồng KHÔNG còn huỷ — một luồng nghĩa là câu trả lời vẫn đúng chỗ', async () => {
    // Đảo bất biến của `chat-streaming-sse` D6 một cách có chủ đích: hồi đó đổi scope là
    // đổi luồng, nên phần dở phải bị vứt kẻo hiện trong khung của bài mới. Nay chỉ có MỘT
    // luồng, nên câu trả lời đang chảy vẫn thuộc đúng cuộc hội thoại này — huỷ nó đi mới là
    // mất dữ liệu người dùng đã trả tiền để sinh ra.
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi trong bài');
    await emit((l) => l.handlers.onToken?.('đang trả lời trong bài'));
    const streamA = last();

    await user.click(screen.getByRole('button', { name: 'go-B' }));

    expect(streamA.signal?.aborted).toBe(false);
    expect(screen.getByText(/đang trả lời trong bài/)).toBeTruthy();

    await emit(() =>
      streamA.handlers.onCommit?.({ answer: 'chốt', citations: [], mode: 'focused' }),
    );
    expect(screen.getByText('chốt')).toBeTruthy();
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
