import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import {
  clearSession,
  loadSession,
  saveSession,
  MAX_PERSISTED_MESSAGES,
  SESSION_VERSION,
  STORAGE_KEY,
  type Message,
} from '../chatSession';

// VÌ SAO TEST NÀY TỒN TẠI: tầng lưu trữ là thứ duy nhất đứng giữa "lỡ bấm F5" và "mất sạch
// cuộc hội thoại". Ba chế độ hỏng của nó đều IM LẶNG — blob rút gọn làm tắt cơ chế ghim, blob
// phiên bản cũ làm citation trỏ sai tin, storage bị chặn làm vỡ widget — nên không có test thì
// không có gì báo.

beforeEach(() => {
  window.sessionStorage.clear();
});

afterEach(() => {
  vi.restoreAllMocks();
});

/** Một lượt trả lời đầy đủ, đúng hình dạng mà widget nhập vào luồng sau khi `commit`. */
function botTurn(): Message {
  return {
    role: 'assistant',
    content: 'Theo tin [3] thì có bản vá khẩn.',
    citations: [
      {
        n: 3,
        kind: 'insight',
        insight_id: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
        title: 'CISA vá khẩn',
        source_url: 'https://example.test/cisa',
      },
    ],
  };
}

describe('round-trip', () => {
  it('giữ NGUYÊN VẸN insight_id của citation', () => {
    // Đây là lưới cho cơ chế ghim của `chat-history-pinning`: rút gọn blob còn {role, content}
    // cho "gọn" thì sau F5 mọi lượt cũ mất insight_id, ghim tắt trong im lặng, giao diện trông
    // y hệt, và người dùng chỉ thấy bot "quên" chuyện vừa bàn.
    saveSession({ messages: [botTurn()], workingSet: [], open: true });

    const loaded = loadSession();
    expect(loaded?.messages[0].citations?.[0]).toEqual({
      n: 3,
      kind: 'insight',
      insight_id: 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
      title: 'CISA vá khẩn',
      source_url: 'https://example.test/cisa',
    });
  });

  it('giữ working set và trạng thái mở panel', () => {
    saveSession({
      messages: [],
      workingSet: [{ id: 'id-1', title: 'Tin một' }],
      open: true,
    });

    const loaded = loadSession();
    expect(loaded?.workingSet).toEqual([{ id: 'id-1', title: 'Tin một' }]);
    expect(loaded?.open).toBe(true);
  });

  it('trả null khi chưa có gì được lưu', () => {
    expect(loadSession()).toBeNull();
  });

  it('clearSession xoá luồng của tab', () => {
    saveSession({ messages: [botTurn()], workingSet: [], open: true });
    clearSession();
    expect(loadSession()).toBeNull();
  });
});

describe('phiên bản và dữ liệu hỏng', () => {
  it('bỏ qua blob lệch phiên bản, KHÔNG migrate', () => {
    window.sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        v: SESSION_VERSION + 1,
        messages: [botTurn()],
        workingSet: [],
        open: true,
      }),
    );

    expect(loadSession()).toBeNull();
  });

  it('bỏ qua JSON hỏng', () => {
    window.sessionStorage.setItem(STORAGE_KEY, '{ đây không phải JSON');
    expect(loadSession()).toBeNull();
  });

  it('bỏ qua blob đúng phiên bản nhưng sai hình dạng', () => {
    window.sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ v: SESSION_VERSION, messages: 'không phải mảng', workingSet: [] }),
    );
    expect(loadSession()).toBeNull();
  });
});

describe('suy giảm êm khi storage không dùng được', () => {
  it('loadSession trả null khi getItem ném lỗi', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new Error('storage bị chặn');
    });
    expect(() => loadSession()).not.toThrow();
    expect(loadSession()).toBeNull();
  });

  it('saveSession không ném ra ngoài khi setItem ném lỗi', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new Error('quota đầy');
    });
    expect(() => saveSession({ messages: [botTurn()], workingSet: [], open: true })).not.toThrow();
  });

  it('clearSession không ném ra ngoài khi removeItem ném lỗi', () => {
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw new Error('storage bị chặn');
    });
    expect(() => clearSession()).not.toThrow();
  });
});

describe('lược bớt trước khi ghi', () => {
  it('KHÔNG ghi searchSuggestions', () => {
    saveSession({
      messages: [{ ...botTurn(), searchSuggestions: '<div id="google-suggestions"></div>' }],
      workingSet: [],
      open: true,
    });

    // Khẳng định trên chuỗi thô: trường này là HTML đi thẳng vào dangerouslySetInnerHTML, nên
    // điều cần bảo đảm là nó KHÔNG NẰM trong storage, không phải nó bị bỏ qua lúc đọc.
    const raw = window.sessionStorage.getItem(STORAGE_KEY) ?? '';
    expect(raw).not.toContain('google-suggestions');
    expect(raw).not.toContain('searchSuggestions');
    expect(loadSession()?.messages[0].citations).toHaveLength(1);
  });

  it('cắt còn MAX_PERSISTED_MESSAGES message gần nhất', () => {
    const many: Message[] = Array.from({ length: MAX_PERSISTED_MESSAGES + 10 }, (_, i) => ({
      role: 'user',
      content: `câu ${i}`,
    }));

    saveSession({ messages: many, workingSet: [], open: true });

    const loaded = loadSession();
    expect(loaded?.messages).toHaveLength(MAX_PERSISTED_MESSAGES);
    // Giữ phần MỚI NHẤT — phần cũ mới là phần bỏ được.
    expect(loaded?.messages[loaded.messages.length - 1].content).toBe(
      `câu ${MAX_PERSISTED_MESSAGES + 9}`,
    );
  });
});
