import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ChatRequest } from '../../api/chat';
import ChatWidget from '../ChatWidget';

// VÌ SAO TEST NÀY TỒN TẠI: Nguy hiểm #3 của báo cáo To-Be (Context Drift / History
// Poisoning) — câu nối tiếp mập mờ ("nó", "rủi ro thì sao") mang ngữ cảnh bài cũ trong khi
// server đọc bài mới.
//
// ⚠️ BẤT BIẾN ĐÃ ĐỔI (change `chat-context-depth`, 28/07/2026). Bản cũ chặn bằng cách CÔ LẬP
// history theo scope: mỗi bài một luồng riêng. Cách đó chữa được drift nhưng sinh ra một
// chế độ hỏng khác, đo được: đọc riêng bài A rồi bài B thì KHÔNG luồng nào chứa cả hai, nên
// "so sánh hai cái này" không thể trả lời (recall@5 = 0/4).
//
// Bản mới gộp về MỘT luồng và chặn drift bằng ngữ cảnh thay vì bằng sự cô lập:
//
//   BẤT BIẾN: mọi tin được nhắc trong history đều còn mặt trong ngữ cảnh của lượt hiện tại
//             — hoặc trong `referenced_insight_ids`, hoặc trong index toàn hệ thống.
//
// Drift cũ là một MÂU THUẪN giữa hai nguồn (history nói A, context là B). Khi cả A lẫn B
// cùng nằm trong payload thì mâu thuẫn đó không tồn tại để mà phải chặn.
//
// Test vẫn khẳng định trên PAYLOAD gửi đi, không trên DOM.

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
      mode: 'global',
    });
  });
});

/** Payload của lần gọi postChat thứ i (1-indexed). */
function payload(i: number): ChatRequest {
  return streamChatMock.mock.calls[i - 1][0] as ChatRequest;
}

/** Nav buttons + widget: điều khiển route để mô phỏng đổi scope trong cùng phiên. */
function Harness() {
  const navigate = useNavigate();
  return (
    <>
      <button onClick={() => navigate('/insights/A')}>go-A</button>
      <button onClick={() => navigate('/insights/B')}>go-B</button>
      <button onClick={() => navigate('/insights/C')}>go-C</button>
      <button onClick={() => navigate('/insights/D')}>go-D</button>
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

/** Gõ câu hỏi, gửi, chờ streamChat được gọi lần thứ `expectCall` rồi chờ câu trả lời render. */
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

describe('ChatWidget — một luồng + working set (chống drift bằng ngữ cảnh)', () => {
  it('A→B: một luồng giữ cả hai lượt, VÀ cả hai bài cùng nằm trong ngữ cảnh', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi A', 1);
    expect(payload(1).referenced_insight_ids).toEqual(['A']);
    expect(payload(1).history).toEqual([]);

    // Đổi sang bài B rồi hỏi câu nối tiếp mập mờ — ca kinh điển của drift.
    await user.click(screen.getByRole('button', { name: 'go-B' }));
    await ask(user, 'rủi ro của nó', 2);

    // BẤT BIẾN MỚI: history CÓ mang lượt của A, nhưng A cũng có mặt trong ngữ cảnh, nên
    // "nó" giải được. Đây chính là chỗ bản cũ phải cắt history đi vì A không có trong context.
    expect(payload(2).referenced_insight_ids).toEqual(['A', 'B']);
    expect(payload(2).history.map((t) => t.content)).toEqual([
      'câu hỏi A',
      'trả lời 1',
    ]);

    // Một luồng ⇒ cả hai lượt cùng hiển thị, không còn chuyện "quay lại mới thấy".
    expect(screen.getByText('câu hỏi A')).toBeTruthy();
    expect(screen.getByText('rủi ro của nó')).toBeTruthy();
  });

  it('bài nào bị bỏ khỏi ngữ cảnh thì KHÔNG còn trong payload lượt sau', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi A', 1);
    await user.click(screen.getByRole('button', { name: 'go-B' }));

    await user.click(screen.getByRole('button', { name: 'Bỏ Tin A khỏi ngữ cảnh' }));
    await ask(user, 'câu tiếp', 2);

    expect(payload(2).referenced_insight_ids).toEqual(['B']);
  });

  it('working set không vượt trần ô sâu — giữ các mục MỚI NHẤT', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    for (const id of ['A', 'B', 'C', 'D']) {
      await user.click(screen.getByRole('button', { name: `go-${id}` }));
      await waitFor(() =>
        expect(screen.queryByRole('button', { name: `Bỏ Tin ${id} khỏi ngữ cảnh` })).toBeTruthy(),
      );
    }
    await ask(user, 'câu hỏi', 1);

    expect(payload(1).referenced_insight_ids).toEqual(['B', 'C', 'D']);
  });

  it('rời detail về danh sách: ngữ cảnh GIỮ nguyên các bài đã đọc', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi A', 1);

    // Rời trang chi tiết KHÔNG còn xoá ngữ cảnh: bài vừa đọc vẫn là thứ người dùng đang
    // nói tới. Bản cũ nhảy sang một luồng toàn cục rỗng ở đây.
    await user.click(screen.getByRole('button', { name: 'go-home' }));
    await ask(user, 'so sánh với các tin khác', 2);

    expect(payload(2).referenced_insight_ids).toEqual(['A']);
    expect(payload(2).history.map((t) => t.content)).toEqual(['câu hỏi A', 'trả lời 1']);
  });

  it('không có bài nào trong ngữ cảnh ⇒ câu hỏi toàn cục thuần', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);
    await ask(user, 'tuần này có gì', 1);

    expect(payload(1).referenced_insight_ids).toEqual([]);
    expect(payload(1).insight_id).toBeFalsy();
  });

  it('đóng rồi mở lại panel: luồng và ngữ cảnh còn nguyên', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    await user.click(screen.getByRole('button', { name: 'go-A' }));
    await ask(user, 'câu hỏi A', 1);

    await user.click(screen.getByRole('button', { name: 'Đóng' }));
    await openWidget(user);

    await screen.findByText('câu hỏi A');
    await screen.findByText('trả lời 1');
    await ask(user, 'thêm câu A', 2);
    expect(payload(2).referenced_insight_ids).toEqual(['A']);
    expect(payload(2).history.map((t) => t.content)).toEqual(['câu hỏi A', 'trả lời 1']);
  });

  it('history mang theo citations của từng lượt (để server giải marker thành tên bài)', async () => {
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    streamChatMock.mockImplementationOnce(async (_p, handlers) => {
      answerCount += 1;  // giữ đồng bộ với bộ đếm của mock mặc định
      handlers.onCommit?.({
        answer: 'trả lời 1 [7]',
        citations: [
          { n: 7, insight_id: 'X', title: 'Kubernetes CVE', source_url: 'https://x' },
        ],
        mode: 'global',
      });
    });
    await ask(user, 'câu đầu', 1);
    await ask(user, 'câu sau', 2);

    expect(payload(2).history[1].citations).toEqual([
      { n: 7, title: 'Kubernetes CVE', insight_id: 'X' },
    ]);
  });

  it('citations trong history mang ĐỊNH DANH insight, không chỉ tiêu đề', async () => {
    // Server cần id để GHIM tin đã bàn vào ngữ cảnh lượt sau (`chat-history-pinning`).
    // Chỉ có tiêu đề thì server phải khớp ngược theo chuỗi — phép mờ, và một lần tra nhầm
    // sẽ ghim SAI tin trong im lặng. Test này khoá ranh giới đó ở phía client.
    const user = userEvent.setup();
    renderWidget();
    await openWidget(user);

    streamChatMock.mockImplementationOnce(async (_p, handlers) => {
      answerCount += 1;
      handlers.onCommit?.({
        // Marker phải đứng NGAY sau "trả lời 1": `renderAnswer` cắt câu thành từng span
        // theo marker, nên helper `ask()` chỉ khớp được khi span đầu đúng bằng chuỗi đó.
        answer: 'trả lời 1 [3] và [9]',
        citations: [
          { n: 3, insight_id: 'id-cisa', title: 'CISA vá khẩn', source_url: 'https://a' },
          { n: 9, insight_id: 'id-npm', title: 'npm supply chain', source_url: 'https://b' },
        ],
        mode: 'global',
      });
    });
    await ask(user, 'tin bảo mật tuần này?', 1);
    // Đổi hẳn chủ đề — đúng ca mà `_rank` đánh rơi tin cũ khỏi top-K.
    await ask(user, 'còn Kubernetes thì sao?', 2);

    const sent = payload(2).history[1].citations;
    expect(sent?.map((c) => c.insight_id)).toEqual(['id-cisa', 'id-npm']);
    // Số marker vẫn giữ nguyên: server KHÔNG đánh số lại giữa các lượt.
    expect(sent?.map((c) => c.n)).toEqual([3, 9]);
  });
});
