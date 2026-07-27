import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { streamChat, type ChatStreamHandlers } from '../chat';

// VÌ SAO TEST NÀY TỒN TẠI: ranh giới khung SSE và ranh giới chunk mạng là HAI thứ khác nhau.
// TCP cắt ở đâu là chuyện của TCP — một khung có thể đến làm ba mảnh, và ba khung có thể đến
// trong một mảnh. Bộ đọc nào ngầm giả định "một chunk = một khung" sẽ chạy đúng suốt lúc dev
// (câu trả lời ngắn, mạng localhost) rồi hỏng trên mạng thật, im lặng, dưới dạng mất token.

const enc = new TextEncoder();

function bodyOf(chunks: string[]): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(controller) {
      for (const c of chunks) controller.enqueue(enc.encode(c));
      controller.close();
    },
  });
}

function mockFetch(chunks: string[], init: Partial<Response> = {}) {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    body: bodyOf(chunks),
    ...init,
  }));
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

function collector() {
  const events: string[] = [];
  const handlers: ChatStreamHandlers = {
    onStatus: (t) => events.push(`status:${t}`),
    onToken: (t) => events.push(`token:${t}`),
    onCommit: (d) => events.push(`commit:${d.answer}|${d.mode}|${d.citations.length}`),
    onError: (c, m) => events.push(`error:${c}:${m}`),
  };
  return { events, handlers };
}

const FRAMES = [
  'event: status\ndata: {"text":"Đang tìm trong hệ thống…"}\n\n',
  'event: token\ndata: {"text":"Có lỗ hổng "}\n\n',
  'event: token\ndata: {"text":"OpenSSL [1]."}\n\n',
  'event: commit\ndata: {"answer":"Có lỗ hổng OpenSSL [1].","citations":[{"n":1,"insight_id":"x","title":"t","source_url":"u"}],"mode":"global"}\n\n',
];

beforeEach(() => {
  vi.unstubAllGlobals();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('streamChat — tách khung SSE', () => {
  it('đọc đủ status/token/commit khi mỗi khung là một chunk', async () => {
    mockFetch(FRAMES);
    const { events, handlers } = collector();

    await streamChat({ question: 'q', history: [] }, handlers);

    expect(events).toEqual([
      'status:Đang tìm trong hệ thống…',
      'token:Có lỗ hổng ',
      'token:OpenSSL [1].',
      'commit:Có lỗ hổng OpenSSL [1].|global|1',
    ]);
  });

  it('một khung đến làm nhiều mảnh vẫn ráp lại đúng', async () => {
    const whole = FRAMES.join('');
    const pieces: string[] = [];
    for (let i = 0; i < whole.length; i += 7) pieces.push(whole.slice(i, i + 7));
    mockFetch(pieces);
    const { events, handlers } = collector();

    await streamChat({ question: 'q', history: [] }, handlers);

    expect(events).toEqual([
      'status:Đang tìm trong hệ thống…',
      'token:Có lỗ hổng ',
      'token:OpenSSL [1].',
      'commit:Có lỗ hổng OpenSSL [1].|global|1',
    ]);
  });

  it('nhiều khung trong một chunk cũng ra đủ sự kiện', async () => {
    mockFetch([FRAMES.join('')]);
    const { events, handlers } = collector();

    await streamChat({ question: 'q', history: [] }, handlers);

    expect(events).toHaveLength(4);
  });

  it('token có xuống dòng đi qua nguyên vẹn', async () => {
    mockFetch(['event: token\ndata: {"text":"dòng một\\ndòng hai"}\n\n']);
    const { events, handlers } = collector();

    await streamChat({ question: 'q', history: [] }, handlers);

    expect(events).toEqual(['token:dòng một\ndòng hai']);
  });

  it('sự kiện error được chuyển tiếp kèm mã', async () => {
    mockFetch(['event: error\ndata: {"code":"quota","message":"Hết lượt rồi"}\n\n']);
    const { events, handlers } = collector();

    await streamChat({ question: 'q', history: [] }, handlers);

    expect(events).toEqual(['error:quota:Hết lượt rồi']);
  });
});

describe('streamChat — huỷ và lỗi mạng', () => {
  it('huỷ là đường ra bình thường: không ném, không gọi onError', async () => {
    const controller = new AbortController();
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        controller.abort();
        const err = new Error('aborted');
        err.name = 'AbortError';
        throw err;
      }),
    );
    const { events, handlers } = collector();

    await expect(
      streamChat({ question: 'q', history: [] }, handlers, controller.signal),
    ).resolves.toBeUndefined();
    expect(events).toEqual([]);
  });

  it('lỗi mạng thật (không huỷ) vẫn ném ra cho caller xử lý', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new Error('mạng hỏng');
      }),
    );
    const { handlers } = collector();

    await expect(streamChat({ question: 'q', history: [] }, handlers)).rejects.toThrow(
      'mạng hỏng',
    );
  });

  it('HTTP lỗi → onError, không treo im lặng', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => ({ ok: false, body: null })));
    const { events, handlers } = collector();

    await streamChat({ question: 'q', history: [] }, handlers);

    expect(events[0]).toMatch(/^error:server:/);
  });
});

describe('streamChat — payload', () => {
  it('cắt history còn 10 lượt gần nhất trước khi gửi', async () => {
    const fetchMock = mockFetch(FRAMES);
    const history = Array.from({ length: 14 }, (_, i) => ({
      role: 'user' as const,
      content: `lượt ${i}`,
    }));

    await streamChat({ question: 'q', history }, {});

    const sent = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(sent.history).toHaveLength(10);
    expect(sent.history[0].content).toBe('lượt 4');
  });
});
