import { useEffect, useRef, useState } from 'react';
import { Link, useMatch } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { postChat, type ChatTurn, type Citation } from '../api/chat';
import { fetchInsightById } from '../api/insights';
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

/** Marker [n] trong câu trả lời → link tới insight thứ n trong citations. */
function renderAnswer(content: string, citations: Citation[]) {
  const parts = content.split(/(\[\d+\])/g);
  return parts.map((part, idx) => {
    const match = /^\[(\d+)\]$/.exec(part);
    if (!match) return <span key={idx}>{part}</span>;
    const citation = citations[Number(match[1]) - 1];
    if (!citation) return <span key={idx}>{part}</span>;
    return (
      <Link
        key={idx}
        to={`/insights/${citation.insight_id}`}
        className={styles.marker}
        title={citation.title}
      >
        {part}
      </Link>
    );
  });
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
  const messagesEndRef = useRef<HTMLDivElement>(null);
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
  }, [messages, open]);

  // Ghi message vào luồng của scope chỉ định. Dùng `key` cố định thay vì scope hiện tại: câu
  // trả lời có thể về sau khi người dùng đã đổi bài, và phải rơi vào luồng đã hỏi, không phải
  // luồng đang xem.
  function appendToScope(key: string, message: Message) {
    setThreads((prev) => ({ ...prev, [key]: [...(prev[key] ?? []), message] }));
  }

  const mutation = useMutation({ mutationFn: postChat });

  function send(question: string) {
    const trimmed = question.trim();
    if (!trimmed || mutation.isPending) return;

    const targetScope = scopeKey;
    const insightId = activeInsightId;

    // History gửi đi CHỈ gồm lượt của scope hiện tại (bỏ các bong bóng lỗi) — không bao giờ kéo
    // theo lượt của scope khác.
    const history: ChatTurn[] = (threads[targetScope] ?? [])
      .filter((m) => !m.isError)
      .map((m) => ({ role: m.role, content: m.content }));

    appendToScope(targetScope, { role: 'user', content: trimmed });
    setInput('');
    mutation.mutate(
      { question: trimmed, history, insight_id: insightId },
      {
        onSuccess: (data) =>
          appendToScope(targetScope, {
            role: 'assistant',
            content: data.answer,
            citations: data.citations,
            expanded: data.mode === 'expanded',
          }),
        onError: (error) => {
          const status = axios.isAxiosError(error) ? error.response?.status : undefined;
          appendToScope(targetScope, {
            role: 'assistant',
            content: status === 429 ? QUOTA_MESSAGE : NETWORK_MESSAGE,
            isError: true,
          });
        },
      },
    );
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
                  {message.citations.map((citation, n) => (
                    <Link
                      key={citation.insight_id}
                      to={`/insights/${citation.insight_id}`}
                      className={styles.citationLink}
                    >
                      [{n + 1}] {citation.title}
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

        {mutation.isPending && (
          <div className={styles.bubbleBot}>Đang tìm trong hệ thống…</div>
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
        <button type="submit" className={styles.sendBtn} disabled={mutation.isPending}>
          Gửi
        </button>
      </form>
    </div>
  );
}
