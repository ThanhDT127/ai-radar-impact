import { useEffect, useRef, useState } from 'react';
import { Link, useMatch } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { streamChat, type ChatTurn, type Citation } from '../api/chat';
import { fetchInsightById } from '../api/insights';
import { parseAnswer } from './chatAnswer';
import styles from './ChatWidget.module.css';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  isError?: boolean;
  // Server tự mở rộng sang toàn hệ thống khi câu hỏi vượt phạm vi bài đang xem. Phải gắn
  // nhãn, vì người dùng đang ở scope "Bài đang xem" mà câu trả lời lại đến từ tin khác —
  // không nói ra thì trông như bot bịa từ bài đang mở.
  expanded?: boolean;
}

// Toàn cục (rời detail hoặc bỏ chip) là MỘT scope thật với luồng riêng, không phải "không có
// ngữ cảnh" gom chung với mọi lần hỏi toàn cục khác. Xem design D2.
const GLOBAL_SCOPE = '__global__';
const EMPTY_THREAD: Message[] = [];

const QUOTA_MESSAGE =
  'Đã hết lượt hỏi trong ngày hôm nay. Bạn quay lại vào ngày mai nhé, hoặc xem trực tiếp trên dashboard.';
const NETWORK_MESSAGE = 'Không gửi được câu hỏi. Kiểm tra kết nối rồi thử lại nhé.';

/**
 * Câu trả lời đang chảy về. Nằm NGOÀI `threads` có chủ đích: chỉ câu đã chốt mới được
 * nhập luồng. Nhờ vậy phần dở không bao giờ lọt vào `history` gửi lên ở lượt sau, và huỷ
 * giữa chừng (đổi scope) chỉ cần vứt object này đi.
 *
 * `scope` là scope ĐÃ HỎI, không phải scope đang xem — người dùng có thể đổi bài trong lúc
 * chờ, và bong bóng phải ở lại đúng luồng của nó.
 */
interface Pending {
  scope: string;
  text: string;
  status: string | null;
}

/** Marker `[n]` → link tới insight mang đúng `n` đó. Logic giải marker ở `chatAnswer.ts`. */
function renderAnswer(content: string, citations: Citation[]) {
  return parseAnswer(content, citations).map((segment, idx) =>
    segment.citation ? (
      <Link
        key={idx}
        to={`/insights/${segment.citation.insight_id}`}
        className={styles.marker}
        title={segment.citation.title}
      >
        {segment.text}
      </Link>
    ) : (
      <span key={idx}>{segment.text}</span>
    ),
  );
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  // Mỗi scope (một insight_id cụ thể, hoặc toàn cục) có luồng hội thoại RIÊNG. Không dùng một
  // mảng gộp cho cả phiên: gộp xuyên scope là context poisoning (Nguy hiểm #3) — history của bài
  // cũ bám theo khi người dùng đã đổi bài. Xem design D1/D2.
  const [threads, setThreads] = useState<Record<string, Message[]>>({});
  const [input, setInput] = useState('');
  const [contextDropped, setContextDropped] = useState(false);
  const [contextTitle, setContextTitle] = useState<string | null>(null);
  const [pending, setPending] = useState<Pending | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const queryClient = useQueryClient();

  // Insight đang mở lấy từ route — widget nằm trong Layout nên không nhận được props
  // từ trang. Rời trang chi tiết thì match về null → tự quay lại chế độ toàn cục.
  const detailMatch = useMatch('/insights/:id');
  const routeInsightId = detailMatch?.params.id ?? null;
  const activeInsightId = contextDropped ? null : routeInsightId;

  // Scope hội thoại hiện tại + luồng của nó. Đổi scope (đổi bài, bỏ chip, rời detail) đổi luôn
  // luồng hiển thị và luồng lấy history khi gửi. `messages` = luồng của scope hiện tại.
  const scopeKey = activeInsightId ?? GLOBAL_SCOPE;
  const messages = threads[scopeKey] ?? EMPTY_THREAD;

  // Chuyển sang insight khác thì context chip phải theo, kể cả khi người dùng đã bỏ
  // chip của insight trước đó.
  useEffect(() => {
    setContextDropped(false);
  }, [routeInsightId]);

  useEffect(() => {
    let cancelled = false;
    if (!activeInsightId) {
      setContextTitle(null);
      return;
    }
    queryClient
      .fetchQuery({
        queryKey: ['insight', activeInsightId],
        queryFn: () => fetchInsightById(activeInsightId),
        staleTime: 5 * 60 * 1000,
      })
      .then((insight) => {
        if (!cancelled) setContextTitle(insight?.title ?? null);
      })
      .catch(() => {
        if (!cancelled) setContextTitle(null);
      });
    return () => {
      cancelled = true;
    };
  }, [activeInsightId, queryClient]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pending, open]);

  // Đổi scope giữa luồng đang stream → HUỶ (design D6). Không huỷ thì phần dở vẫn chảy về
  // và người dùng thấy câu trả lời của bài cũ trong khung của bài mới — đúng loại nhầm lẫn
  // mà `chat-context-isolation` (①) sinh ra để chặn.
  useEffect(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setPending(null);
  }, [scopeKey]);

  // Ghi message vào luồng của scope chỉ định. Dùng `key` cố định thay vì scope hiện tại: câu
  // trả lời có thể về sau khi người dùng đã đổi bài, và phải rơi vào luồng đã hỏi, không phải
  // luồng đang xem.
  function appendToScope(key: string, message: Message) {
    setThreads((prev) => ({ ...prev, [key]: [...(prev[key] ?? []), message] }));
  }

  function send(question: string) {
    const trimmed = question.trim();
    // Chặn gửi trùng khi luồng chưa xong — thundering herd của Nguy hiểm #1 chính là người
    // dùng bấm Gửi nhiều lần vì tưởng treo.
    if (!trimmed || pending) return;

    const targetScope = scopeKey;
    const insightId = activeInsightId;

    // History gửi đi CHỈ gồm lượt của scope hiện tại (bỏ các bong bóng lỗi) — không bao giờ kéo
    // theo lượt của scope khác.
    const history: ChatTurn[] = (threads[targetScope] ?? [])
      .filter((m) => !m.isError)
      .map((m) => ({ role: m.role, content: m.content }));

    appendToScope(targetScope, { role: 'user', content: trimmed });
    setInput('');
    setPending({ scope: targetScope, text: '', status: null });

    const controller = new AbortController();
    abortRef.current = controller;

    /** Kết thúc luồng: nhập một message vào luồng đã hỏi rồi dọn trạng thái tạm. */
    function settle(message: Message) {
      if (controller.signal.aborted) return;
      appendToScope(targetScope, message);
      setPending(null);
      abortRef.current = null;
    }

    streamChat(
      { question: trimmed, history, insight_id: insightId },
      {
        onStatus: (text) =>
          setPending((p) => (p && !controller.signal.aborted ? { ...p, status: text } : p)),
        onToken: (text) =>
          setPending((p) =>
            p && !controller.signal.aborted ? { ...p, text: p.text + text } : p,
          ),
        // `answer` của sự kiện chốt THAY phần đã stream, không nối thêm: nó là bản đã qua
        // grounding, và ở ca fail-closed nó là một câu hoàn toàn khác (design D2).
        onCommit: (data) =>
          settle({
            role: 'assistant',
            content: data.answer,
            citations: data.citations,
            expanded: data.mode === 'expanded',
          }),
        onError: (code, message) =>
          settle({
            role: 'assistant',
            content: code === 'quota' ? QUOTA_MESSAGE : message,
            isError: true,
          }),
      },
      controller.signal,
    ).catch(() => settle({ role: 'assistant', content: NETWORK_MESSAGE, isError: true }));
  }

  function retryLast() {
    const scopeMessages = threads[scopeKey] ?? [];
    const lastUser = [...scopeMessages].reverse().find((m) => m.role === 'user');
    if (!lastUser) return;
    setThreads((prev) => ({
      ...prev,
      [scopeKey]: (prev[scopeKey] ?? []).filter((m) => !m.isError),
    }));
    send(lastUser.content);
  }

  if (!open) {
    return (
      <button
        type="button"
        className={styles.launcher}
        onClick={() => setOpen(true)}
        aria-label="Mở trợ lý hỏi đáp"
      >
        💬 Hỏi trợ lý
      </button>
    );
  }

  return (
    <div className={styles.panel} role="dialog" aria-label="Trợ lý hỏi đáp">
      <div className={styles.header}>
        <span className={styles.title}>Trợ lý AI Radar</span>
        <button
          type="button"
          className={styles.iconBtn}
          onClick={() => setOpen(false)}
          aria-label="Đóng"
        >
          ✕
        </button>
      </div>

      {/* Badge phạm vi — hiện khi đang ở trang chi tiết, kể cả sau khi đã chuyển sang
          toàn hệ thống. Chip cũ chỉ có một chiều (bài → toàn cục) nên muốn quay lại bài
          phải điều hướng; badge này chuyển HAI CHIỀU tại chỗ (design D7). */}
      {routeInsightId && (
        <div className={styles.scopeBar}>
          <span className={styles.scopeText} title={contextTitle ?? undefined}>
            Phạm vi: <strong>{activeInsightId ? 'Bài đang xem' : 'Toàn hệ thống'}</strong>
          </span>
          <button
            type="button"
            className={styles.scopeToggle}
            onClick={() => setContextDropped((dropped) => !dropped)}
            aria-label={
              activeInsightId
                ? 'Chuyển sang hỏi toàn hệ thống'
                : 'Chuyển sang hỏi trong bài đang xem'
            }
          >
            {activeInsightId ? 'Hỏi toàn hệ thống' : 'Hỏi trong bài này'}
          </button>
        </div>
      )}

      <div className={styles.messages}>
        {messages.length === 0 && (
          <p className={styles.empty}>
            {activeInsightId
              ? 'Hỏi bất cứ điều gì về tin đang mở — kể cả chi tiết trong bài gốc.'
              : 'Hỏi về các tin trong hệ thống, ví dụ: "tuần này có gì cho Security?"'}
          </p>
        )}

        {messages.map((message, idx) =>
          message.role === 'user' ? (
            <div key={idx} className={styles.bubbleUser}>
              {message.content}
            </div>
          ) : (
            <div key={idx} className={message.isError ? styles.bubbleError : styles.bubbleBot}>
              {message.expanded && (
                <span className={styles.expandedTag}>🔎 Tìm trên toàn hệ thống</span>
              )}
              {renderAnswer(message.content, message.citations ?? [])}
              {message.citations && message.citations.length > 0 && (
                <div className={styles.citations}>
                  {/* Số ở đây phải KHỚP marker trong câu (`citation.n`), không tự đánh lại
                      thành [1..N]: đánh lại tạo hệ quy chiếu thứ hai cho `n` — đúng thứ vừa
                      gây ra lỗi trỏ sai. Inline nói [12] thì list cũng phải nói [12]. */}
                  {message.citations.map((citation) => (
                    <Link
                      key={citation.insight_id}
                      to={`/insights/${citation.insight_id}`}
                      className={styles.citationLink}
                    >
                      [{citation.n}] {citation.title}
                    </Link>
                  ))}
                </div>
              )}
              {message.isError && (
                <button type="button" className={styles.retryBtn} onClick={retryLast}>
                  Thử lại
                </button>
              )}
            </div>
          ),
        )}

        {/* Bong bóng đang chảy. Có token thì hiện token; chưa có thì hiện MỐC TIẾN TRÌNH
            thật do server phát. Khoảng đầu (5–35s đo thật) là lúc model đang thinking, chưa
            sinh token nào — status lấp đúng khoảng đó, thay cho spinner một dòng cố định. */}
        {pending && pending.scope === scopeKey && (
          <div className={styles.bubbleBot}>
            {pending.text ? (
              renderAnswer(pending.text, [])
            ) : (
              <span className={styles.status}>{pending.status ?? 'Đang gửi câu hỏi…'}</span>
            )}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form
        className={styles.form}
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          className={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Nhập câu hỏi…"
          aria-label="Câu hỏi"
        />
        <button type="submit" className={styles.sendBtn} disabled={pending !== null}>
          Gửi
        </button>
      </form>
    </div>
  );
}
