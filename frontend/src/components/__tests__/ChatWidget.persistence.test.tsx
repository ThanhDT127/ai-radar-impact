import { describe, it, expect, vi, beforeEach } from 'vitest';
import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ChatRequest, ChatStreamHandlers } from '../../api/chat';
import { STORAGE_KEY } from '../chatSession';
import ChatWidget from '../ChatWidget';

// VÌ SAO TEST NÀY TỒN TẠI: cuộc hội thoại chỉ sống trong `useState`, mà `history` lại do
// client dựng lại và gửi lên mỗi lượt — nên một lần F5 lỡ tay xoá sạch cả những lượt đã trả
// tiền cho model.
//
// BẤT BIẾN được khoá ở đây:
//
//   A — Luồng hội thoại thuộc về TAB, KHÔNG thuộc về ngữ cảnh. Bỏ hết working set KHÔNG
//       được đụng tới câu chữ đã trao đổi. Phiên bản đầu của widget
//       (`chat-context-isolation`) đánh khoá luồng theo scope và hỏng đúng kiểu này; lưu bền
//       mở lại đúng cám dỗ đó dưới dạng "đánh khoá blob cho gọn".
//   C — Chỉ nội dung ĐÃ CHỐT mới chạm storage. Text đang stream là tạm — ở ca fail-closed nó
//       là một câu hoàn toàn khác câu cuối.

const { streamChatMock } = vi.hoisted(() => ({ streamChatMock: vi.fn() }));

vi.mock('../../api/chat', () => ({ streamChat: streamChatMock }));
vi.mock('../../api/insights', () => ({
  fetchInsightById: vi.fn(async (id: string) => ({ id, title: `Tin ${id}` })),
}));

let answerCount = 0;

beforeEach(() => {
  window.sessionStorage.clear();
  streamChatMock.mockReset();
  answerCount = 0;
  streamChatMock.mockImplementation(async (_payload, handlers: ChatStreamHandlers) => {
    handlers.onCommit?.({
      answer: `trả lời ${++answerCount}`,
      citations: [],
      mode: 'global',
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

/** Mount widget mới — mô phỏng một lần tải tài liệu (F5) khi gọi lại sau `unmount()`. */
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

describe('ChatWidget — hội thoại bền vững theo tab', () => {
  it('khôi phục hội thoại, working set và trạng thái mở sau khi tải lại trang', async () => {
    const user = userEvent.setup();
    const first = renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await screen.findByRole('button', { name: 'Bỏ Tin A khỏi ngữ cảnh' });
    await ask(user, 'bài này nói gì', 1);

    first.unmount();
    renderWidget();

    // Panel mở lại ngay — người dùng đã để nó mở, khôi phục trạng thái đó KHÔNG phải "tự
    // động mở" (widget vẫn không tự bật khi chưa ai đụng tới nó).
    expect(await screen.findByText('trả lời 1')).toBeInTheDocument();
    expect(screen.getByText('bài này nói gì')).toBeInTheDocument();
    // Chip đến từ STORAGE chứ không từ effect route: mount lại ở '/' nên không có bài nào
    // trên route để mà dựng lại.
    expect(screen.getByRole('button', { name: 'Bỏ Tin A khỏi ngữ cảnh' })).toBeInTheDocument();

    // Khẳng định trên PAYLOAD, không chỉ trên DOM: hội thoại khôi phục phải thật sự chảy
    // vào lượt kế tiếp.
    await ask(user, 'còn gì nữa', 2);
    expect(payload(2).history).toHaveLength(2);
    expect(payload(2).history[0].content).toBe('bài này nói gì');
    expect(payload(2).referenced_insight_ids).toEqual(['A']);
  });

  it('citations sống sót qua tải lại — insight_id vẫn đi kèm history', async () => {
    // Lưới cho cơ chế ghim của `chat-history-pinning`: mất `insight_id` thì server không ghim
    // gì, giao diện trông y hệt, và bot chỉ "quên" chuyện vừa bàn.
    const user = userEvent.setup();
    const first = renderWidget();
    await openWidget(user);

    streamChatMock.mockImplementationOnce(async (_p, handlers: ChatStreamHandlers) => {
      answerCount += 1;
      handlers.onCommit?.({
        answer: 'theo [4] thì có bản vá',
        citations: [{ n: 4, insight_id: 'Z', title: 'Tin Z', source_url: 'https://z' }],
        mode: 'global',
      });
    });
    await user.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), 'tuần này có gì');
    await user.click(screen.getByRole('button', { name: 'Gửi' }));
    await screen.findByRole('link', { name: '[4] Tin Z' });

    first.unmount();
    renderWidget();
    await screen.findByRole('link', { name: '[4] Tin Z' });

    await ask(user, 'nói kỹ hơn', 2);
    const botTurn = payload(2).history[1];
    expect(botTurn.citations).toEqual([{ n: 4, title: 'Tin Z', insight_id: 'Z' }]);
  });

  it('xoa_het_working_set_khong_dung_toi_hoi_thoai', async () => {
    // BẤT BIẾN A. Đỏ ngay nếu ai đó đánh khoá storage theo working set/scope "cho gọn".
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await user.click(screen.getByRole('button', { name: 'go-B' }));
    await screen.findByRole('button', { name: 'Bỏ Tin B khỏi ngữ cảnh' });
    await ask(user, 'so sánh hai bài', 1);

    await user.click(screen.getByRole('button', { name: 'Bỏ Tin A khỏi ngữ cảnh' }));
    await user.click(screen.getByRole('button', { name: 'Bỏ Tin B khỏi ngữ cảnh' }));
    await waitFor(() => expect(screen.queryByLabelText('Tin đang trong ngữ cảnh')).toBeNull());

    // Hội thoại còn nguyên trên màn hình…
    expect(screen.getByText('so sánh hai bài')).toBeInTheDocument();
    expect(screen.getByText('trả lời 1')).toBeInTheDocument();

    // …và còn nguyên trong dữ liệu lưu, nên nó sống sót qua cả tải lại lẫn việc ngữ cảnh rỗng.
    await ask(user, 'câu tiếp', 2);
    expect(payload(2).history).toHaveLength(2);
    expect(payload(2).referenced_insight_ids).toEqual([]);
  });

  it('lượt bị gián đoạn: text tạm KHÔNG vào storage, câu hỏi được giữ kèm nút Thử lại', async () => {
    // BẤT BIẾN C.
    const user = userEvent.setup();
    const first = renderWidget();
    await openWidget(user);
    await ask(user, 'câu đầu tiên', 1);

    let hung: ChatStreamHandlers | null = null;
    streamChatMock.mockImplementationOnce(
      (_p: ChatRequest, handlers: ChatStreamHandlers) =>
        new Promise<void>(() => {
          hung = handlers;
        }),
    );
    await user.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), 'câu bị cắt ngang');
    await user.click(screen.getByRole('button', { name: 'Gửi' }));
    await waitFor(() => expect(hung).not.toBeNull());
    act(() => hung!.onToken?.('PHẦN DỞ DANG'));
    await screen.findByText(/PHẦN DỞ DANG/);

    // Storage không được chứa text tạm — khẳng định trên chuỗi thô của blob.
    expect(window.sessionStorage.getItem(STORAGE_KEY) ?? '').not.toContain('PHẦN DỞ DANG');

    first.unmount();
    renderWidget();

    expect(await screen.findByText('câu bị cắt ngang')).toBeInTheDocument();
    expect(screen.queryByText(/PHẦN DỞ DANG/)).toBeNull();
    expect(screen.getByText(/Câu trả lời bị gián đoạn/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Thử lại' })).toBeInTheDocument();
  });

  it('Thử lại gửi lại đúng một lượt — không nhân đôi bong bóng câu hỏi', async () => {
    const user = userEvent.setup();
    const first = renderWidget();
    await openWidget(user);
    await ask(user, 'câu đầu tiên', 1);

    streamChatMock.mockImplementationOnce(() => new Promise<void>(() => {}));
    await user.type(screen.getByRole('textbox', { name: 'Câu hỏi' }), 'câu bị cắt ngang');
    await user.click(screen.getByRole('button', { name: 'Gửi' }));
    await waitFor(() => expect(streamChatMock).toHaveBeenCalledTimes(2));

    first.unmount();
    renderWidget();
    await screen.findByRole('button', { name: 'Thử lại' });

    await user.click(screen.getByRole('button', { name: 'Thử lại' }));
    await waitFor(() => expect(streamChatMock).toHaveBeenCalledTimes(3));

    // Đúng MỘT bong bóng cho câu hỏi đó. Bản cũ của `retryLast()` để lại hai.
    expect(screen.getAllByText('câu bị cắt ngang')).toHaveLength(1);
    // …và `history` gửi lên cũng không có lượt trùng: nó dừng ở lượt đã hoàn tất trước đó.
    expect(payload(3).question).toBe('câu bị cắt ngang');
    expect(payload(3).history).toHaveLength(2);
    expect(payload(3).history.map((t) => t.content)).toEqual(['câu đầu tiên', 'trả lời 1']);
  });

  it('Cuộc trò chuyện mới xoá sạch, giữ panel mở, và không quay lại sau khi tải lại', async () => {
    const user = userEvent.setup();
    const first = renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await screen.findByRole('button', { name: 'Bỏ Tin A khỏi ngữ cảnh' });
    await ask(user, 'câu cũ', 1);

    await user.click(screen.getByRole('button', { name: 'Bắt đầu cuộc trò chuyện mới' }));

    expect(screen.queryByText('câu cũ')).toBeNull();
    expect(screen.queryByLabelText('Tin đang trong ngữ cảnh')).toBeNull();
    // Panel vẫn mở: ô nhập còn đó, và trạng thái trống hiện như lần mở đầu tiên.
    expect(screen.getByRole('textbox', { name: 'Câu hỏi' })).toBeInTheDocument();
    expect(screen.getByText(/Hỏi về các tin trong hệ thống/)).toBeInTheDocument();

    first.unmount();
    renderWidget();
    await screen.findByRole('textbox', { name: 'Câu hỏi' });
    expect(screen.queryByText('câu cũ')).toBeNull();
  });

  it('hai lần mount độc lập khi storage trống — không rò luồng của lần trước', async () => {
    const user = userEvent.setup();
    const first = renderWidget();
    await openWidget(user);
    await ask(user, 'câu của tab một', 1);

    first.unmount();
    window.sessionStorage.clear(); // mô phỏng một TAB KHÁC: storage riêng, không thấy gì
    renderWidget();

    expect(screen.queryByText('câu của tab một')).toBeNull();
    expect(screen.getByRole('button', { name: 'Mở trợ lý hỏi đáp' })).toBeInTheDocument();
  });
});
