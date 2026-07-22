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
}

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
  const [messages, setMessages] = useState<Message[]>([]);
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

  const mutation = useMutation({
    mutationFn: postChat,
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.answer, citations: data.citations },
      ]);
    },
    onError: (error) => {
      const status = axios.isAxiosError(error) ? error.response?.status : undefined;
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: status === 429 ? QUOTA_MESSAGE : NETWORK_MESSAGE,
          isError: true,
        },
      ]);
    },
  });

  function send(question: string) {
    const trimmed = question.trim();
    if (!trimmed || mutation.isPending) return;

    // History gửi đi là hội thoại TRƯỚC câu hỏi này, bỏ các bong bóng lỗi.
    const history: ChatTurn[] = messages
      .filter((m) => !m.isError)
      .map((m) => ({ role: m.role, content: m.content }));

    setMessages((prev) => [...prev, { role: 'user', content: trimmed }]);
    setInput('');
    mutation.mutate({ question: trimmed, history, insight_id: activeInsightId });
  }

  function retryLast() {
    const lastUser = [...messages].reverse().find((m) => m.role === 'user');
    if (!lastUser) return;
    setMessages((prev) => prev.filter((m) => !m.isError));
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

      {activeInsightId && (
        <div className={styles.chip}>
          <span className={styles.chipText}>
            Đang hỏi về: {contextTitle ?? 'tin đang mở'}
          </span>
          <button
            type="button"
            className={styles.chipClose}
            onClick={() => setContextDropped(true)}
            aria-label="Bỏ ngữ cảnh, hỏi toàn bộ hệ thống"
          >
            ✕
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
