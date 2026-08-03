import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useMatch } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { streamChat, type ChatStatusKey, type ChatTurn, type Citation } from '../api/chat';
import { fetchInsightById } from '../api/insights';
import { parseAnswer } from './chatAnswer';
import {
  clearSession,
  loadSession,
  saveSession,
  type Message,
  type Ref,
} from './chatSession';
import styles from './ChatWidget.module.css';

/**
 * Số Ô SÂU của server (`settings.chat_deep_slots`). Giữ đồng bộ bằng tay: server vẫn cắt
 * lại theo cấu hình thật của nó, nên lệch số chỉ làm UI hiện thừa vài chip chứ không sinh
 * ra hành vi sai.
 */
const MAX_REFS = 3;

const QUOTA_MESSAGE =
  'Đã hết lượt hỏi trong ngày hôm nay. Bạn quay lại vào ngày mai nhé, hoặc xem trực tiếp trên dashboard.';
const NETWORK_MESSAGE = 'Không gửi được câu hỏi. Kiểm tra kết nối rồi thử lại nhé.';

/**
 * Câu trả lời đang chảy về. Nằm NGOÀI `messages` có chủ đích: chỉ câu đã chốt mới được
 * nhập luồng. Nhờ vậy phần dở không bao giờ lọt vào `history` gửi lên ở lượt sau, và huỷ
 * giữa chừng chỉ cần vứt object này đi.
 */
interface Pending {
  text: string;
  /** Các mốc tiến trình đã nhận, theo thứ tự đến. Mốc CUỐI là mốc đang chạy. */
  steps: Step[];
}

/** Một mốc tiến trình đã hiện trên khối chờ. */
interface Step {
  key: ChatStatusKey;
  text: string;
}

/**
 * Trần số dòng mốc hiện cùng lúc. Vượt thì bỏ dòng CŨ NHẤT — panel chat hẹp, và mốc cũ nhất
 * là mốc ít liên quan nhất tới việc người dùng đang chờ.
 */
const MAX_STEPS = 4;

/** Tên miền của một URL, để nhãn nguồn web nói rõ nó đến từ đâu. URL hỏng thì trả rỗng. */
function hostOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '');
  } catch {
    return '';
  }
}

/**
 * Gộp một mốc mới vào danh sách: cùng `key` thì CẬP NHẬT TẠI CHỖ, khác thì thêm dòng.
 *
 * Phân biệt bằng `key` chứ không bằng `text` vì `text` mang số liệu của lượt — mốc `reading`
 * phát lần đầu là câu chung chung, phát lần hai là tên tin thật, và đó vẫn là MỘT mốc.
 * `key` lạ (server mới hơn client) vẫn được thêm như dòng mới, không bao giờ bị nuốt.
 */
function mergeStep(steps: Step[], key: ChatStatusKey, text: string): Step[] {
  const at = steps.findIndex((s) => s.key === key);
  if (at !== -1) {
    const next = [...steps];
    next[at] = { key, text };
    return next;
  }
  return [...steps, { key, text }].slice(-MAX_STEPS);
}

export default function ChatWidget() {
  /**
   * Luồng đã lưu của TAB này, đọc đúng MỘT lần lúc mount.
   *
   * Đọc trong initializer của `useState` chứ không trong `useEffect` là có chủ đích: nó chạy
   * TRƯỚC mọi effect, nên effect route ở dưới thấy working set đã khôi phục và hành xử như
   * một lần điều hướng bình thường (bài đang mở đã có ⇒ giữ nguyên; chưa có ⇒ thêm vào và
   * đẩy mục cũ nhất ra). Đọc trong effect thì working set sẽ nhấp nháy qua trạng thái rỗng.
   */
  const [restored] = useState(() => loadSession());
  const [open, setOpen] = useState(() => restored?.open ?? false);
  /**
   * MỘT luồng hội thoại cho cả phiên (change `chat-context-depth`).
   *
   * Trước đây mỗi scope một luồng (`chat-context-isolation`), để chặn context poisoning:
   * đổi bài A→B rồi hỏi "nó" thì history nói A còn context là B — một MÂU THUẪN giữa hai
   * nguồn. Nay cả A lẫn B đều nằm trong `workingSet` và cùng được gửi lên, nên không còn
   * mâu thuẫn để mà phải chặn; nó thành bài toán khử nhập nhằng bình thường mà model làm
   * được. Bất biến thay thế: **mọi tin được nhắc trong history đều còn mặt trong ngữ cảnh
   * của lượt hiện tại** — hoặc trong working set, hoặc trong index toàn hệ thống.
   *
   * Chính việc tách đôi mới là thứ làm người dùng không so sánh được hai bài đã đọc riêng
   * (đo 28/07/2026: recall@5 = 0/4 cho câu so sánh hồi chỉ).
   */
  const [messages, setMessages] = useState<Message[]>(() => restored?.messages ?? []);
  const [workingSet, setWorkingSet] = useState<Ref[]>(() => restored?.workingSet ?? []);
  const [input, setInput] = useState('');
  const [pending, setPending] = useState<Pending | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const queryClient = useQueryClient();

  // Insight đang mở lấy từ route — widget nằm trong Layout nên không nhận được props
  // từ trang.
  const detailMatch = useMatch('/insights/:id');
  const routeInsightId = detailMatch?.params.id ?? null;

  /** Thêm một tin vào working set. Đã có thì giữ nguyên vị trí; tràn thì bỏ mục cũ nhất. */
  const addRef = useCallback((ref: Ref) => {
    setWorkingSet((prev) =>
      prev.some((r) => r.id === ref.id) ? prev : [...prev, ref].slice(-MAX_REFS),
    );
  }, []);

  function removeRef(id: string) {
    setWorkingSet((prev) => prev.filter((r) => r.id !== id));
  }

  // Mở trang chi tiết = đưa bài đó vào ngữ cảnh. Đây là thao tác "vừa phân tích bài này"
  // mà người dùng nhắc tới sau đó bằng "hai bài vừa rồi".
  useEffect(() => {
    if (!routeInsightId) return;
    let cancelled = false;
    queryClient
      .fetchQuery({
        queryKey: ['insight', routeInsightId],
        queryFn: () => fetchInsightById(routeInsightId),
        staleTime: 5 * 60 * 1000,
      })
      .then((insight) => {
        if (!cancelled && insight?.title) addRef({ id: routeInsightId, title: insight.title });
      })
      .catch(() => {
        /* không lấy được tiêu đề thì thôi — ngữ cảnh thiếu một chip còn hơn chip vô danh */
      });
    return () => {
      cancelled = true;
    };
  }, [routeInsightId, queryClient, addRef]);

  /**
   * Ghi luồng xuống bộ nhớ của tab sau mỗi thay đổi đã chốt.
   *
   * ⚠️ `pending` KHÔNG có trong deps, và đó là một BẤT BIẾN chứ không phải tối ưu: text đang
   * stream là nội dung TẠM — ở ca fail-closed nó là một câu hoàn toàn khác câu cuối. Cho nó
   * vào đây vừa ghi storage mỗi token, vừa dựng lại đúng cái bẫy mà `chat-streaming-sse` đã
   * chặn ở phía `history`.
   */
  useEffect(() => {
    saveSession({ messages, workingSet, open });
  }, [messages, workingSet, open]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pending, open]);

  // Rời trang / unmount giữa luồng thì huỷ. KHÔNG còn huỷ khi đổi bài như trước: một luồng
  // duy nhất nghĩa là câu trả lời đang chảy vẫn thuộc đúng cuộc hội thoại này.
  useEffect(() => () => abortRef.current?.abort(), []);

  /** Marker `[n]` → link tới insight mang đúng `n` đó, và bấm vào thì tin vào ngữ cảnh. */
  function renderAnswer(content: string, citations: Citation[]) {
    return parseAnswer(content, citations).map((segment, idx) => {
      const cite = segment.citation;
      if (!cite) return <span key={idx}>{segment.text}</span>;
      // Marker trỏ nguồn WEB mở ra ngoài: nó không có trang chi tiết, và nó KHÔNG vào
      // working set (working set là tập insight để rót vào ô sâu — một URL không rót được).
      if (cite.kind === 'web' || !cite.insight_id) {
        return (
          <a
            key={idx}
            href={cite.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.marker}
            title={cite.title}
          >
            {segment.text}
          </a>
        );
      }
      return (
        <Link
          key={idx}
          to={`/insights/${cite.insight_id}`}
          className={styles.marker}
          title={cite.title}
          onClick={() => addRef({ id: cite.insight_id!, title: cite.title })}
        >
          {segment.text}
        </Link>
      );
    });
  }

  /**
   * Gửi một câu hỏi.
   *
   * `base` = luồng mà câu hỏi này nối tiếp; mặc định là luồng hiện tại. Tham số này tồn tại
   * cho đường HỎI LẠI: ở đó luồng phải bị cắt về trước lượt hỏi cũ, mà `messages` trong
   * closure thì vẫn là bản chưa cắt — dùng nó sẽ vừa đẻ bong bóng câu hỏi thứ hai trên màn
   * hình, vừa nhét một lượt trùng vào `history` gửi lên.
   */
  function send(question: string, base?: Message[]) {
    const trimmed = question.trim();
    // Chặn gửi trùng khi luồng chưa xong — thundering herd của Nguy hiểm #1 chính là người
    // dùng bấm Gửi nhiều lần vì tưởng treo.
    if (!trimmed || pending) return;

    const baseMessages = base ?? messages;

    // History mang theo citations của TỪNG lượt: server cần chúng để dịch `[n]` thành tên
    // bài, vì bảng ánh xạ được dựng lại mỗi lượt nên con số cũ trỏ tin khác.
    //
    // `insight_id` đi kèm để server GHIM tin đã bàn vào ngữ cảnh lượt sau
    // (`chat-history-pinning`). Dữ liệu vốn đã có sẵn trong `Citation`, trước đây bị lược
    // đi ở đúng chỗ này.
    const history: ChatTurn[] = baseMessages
      .filter((m) => !m.isError)
      .map((m) => ({
        role: m.role,
        content: m.content,
        // Chỉ gửi lại nguồn INSIGHT: `insight_id` ở đây tồn tại để server ghim tin đã bàn vào
        // ngữ cảnh lượt sau, mà nguồn web thì không ghim được (ô sâu nhận insight, không nhận
        // URL) và nó cũng đã hết vòng đời cùng lượt hỏi sinh ra nó.
        citations: m.citations
          ?.filter((c) => c.kind !== 'web' && c.insight_id)
          .map((c) => ({
            n: c.n,
            title: c.title,
            insight_id: c.insight_id as string,
          })),
      }));
    const refs = workingSet.map((r) => r.id);

    setMessages([...baseMessages, { role: 'user', content: trimmed }]);
    setInput('');
    setPending({ text: '', steps: [] });

    const controller = new AbortController();
    abortRef.current = controller;

    /** Kết thúc luồng: nhập một message vào luồng rồi dọn trạng thái tạm. */
    function settle(message: Message) {
      if (controller.signal.aborted) return;
      setMessages((prev) => [...prev, message]);
      setPending(null);
      abortRef.current = null;
    }

    streamChat(
      {
        question: trimmed,
        history,
        // `insight_id` chỉ dùng khi KHÔNG có working set — giữ đường cũ (mode B + sentinel)
        // sống cho client cũ và eval harness. Có refs thì server đi đường một-lượt-gọi.
        insight_id: refs.length ? null : routeInsightId,
        referenced_insight_ids: refs,
      },
      {
        onStatus: (key, text) =>
          setPending((p) =>
            p && !controller.signal.aborted
              ? { ...p, steps: mergeStep(p.steps, key, text) }
              : p,
          ),
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
            searchSuggestions: data.search_suggestions,
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

  /**
   * Hỏi lại lượt gần nhất — dùng cho cả bong bóng lỗi lẫn lượt bị gián đoạn vì tải lại trang.
   *
   * Cắt luồng về TRƯỚC lượt hỏi đó rồi để `send()` tự đặt lại bong bóng câu hỏi, thay vì giữ
   * bong bóng cũ. Bản trước chỉ lọc bỏ bong bóng lỗi rồi gọi `send()`, mà `send()` lại nối
   * thêm một lượt user nữa ⇒ **câu hỏi hiện hai lần**. Lỗi đó ẩn được vì đường lỗi hiếm;
   * lượt gián đoạn biến nó thành đường đi thường xuyên.
   */
  function retryLast() {
    let at = -1;
    for (let i = messages.length - 1; i >= 0; i -= 1) {
      if (messages[i].role === 'user') {
        at = i;
        break;
      }
    }
    if (at === -1) return;
    send(messages[at].content, messages.slice(0, at));
  }

  /**
   * Bắt đầu cuộc trò chuyện mới: xoá luồng, xoá working set, xoá dữ liệu đã lưu của tab.
   *
   * Vì sao cần: trước change này F5 chính là nút reset duy nhất. Khi luồng đã sống sót qua
   * F5, một cuộc hội thoại dài/lạc đề không còn đường thoát — mà `history` vẫn được gửi lên
   * mỗi lượt (tốn token, và cơ chế ghim của `chat-history-pinning` cứ bám vào chủ đề cũ).
   *
   * Huỷ luồng đang chảy trước khi xoá: `settle()` của luồng đó kiểm tra `signal.aborted`, nên
   * không huỷ thì câu trả lời của cuộc hội thoại CŨ sẽ rơi vào cuộc hội thoại MỚI.
   */
  function startNewConversation() {
    abortRef.current?.abort();
    abortRef.current = null;
    setPending(null);
    setMessages([]);
    setWorkingSet([]);
    clearSession();
  }

  /**
   * Lượt hỏi bị GIÁN ĐOẠN: luồng kết thúc bằng một câu hỏi chưa có câu trả lời, và không có
   * luồng nào đang chạy — tức là trang đã được tải lại giữa lúc câu trả lời đang sinh.
   *
   * Suy ra từ CẤU TRÚC của luồng, không từ một cờ lưu kèm. Một cờ được ghi ở chỗ này và đọc
   * ở chỗ khác là một cơ hội để hai nguồn sự thật lệch nhau; còn "lượt cuối là của người
   * dùng" thì tự nó đã là định nghĩa.
   *
   * Lúc gửi bình thường thì `setMessages` và `setPending` nằm cùng một batch nên `pending`
   * đã khác `null` ngay ở render đầu tiên có lượt hỏi ⇒ không có nhấp nháy giả.
   */
  const interrupted =
    !pending && messages.length > 0 && messages[messages.length - 1].role === 'user';

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
        <div className={styles.headerActions}>
          {/* Đặt ở header, cạnh nút đóng — CỐ Ý xa ô nhập câu hỏi: đây là thao tác hiếm và
              huỷ dữ liệu, để cạnh chỗ gõ là mời bấm nhầm. */}
          <button
            type="button"
            className={styles.iconBtn}
            onClick={startNewConversation}
            aria-label="Bắt đầu cuộc trò chuyện mới"
            title="Cuộc trò chuyện mới"
          >
            ✚
          </button>
          <button
            type="button"
            className={styles.iconBtn}
            onClick={() => setOpen(false)}
            aria-label="Đóng"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Working set — các tin đang được đọc kỹ. Thay badge phạm vi một-lựa-chọn của
          `chat-scope-routing`: ngữ cảnh nay là một TẬP sửa được, không phải một chế độ. */}
      {workingSet.length > 0 && (
        <div className={styles.refBar} aria-label="Tin đang trong ngữ cảnh">
          <span className={styles.refLabel}>Đang đọc kỹ:</span>
          {workingSet.map((ref) => (
            <span key={ref.id} className={styles.refChip}>
              <span className={styles.refTitle} title={ref.title}>
                {ref.title}
              </span>
              <button
                type="button"
                className={styles.refRemove}
                onClick={() => removeRef(ref.id)}
                aria-label={`Bỏ ${ref.title} khỏi ngữ cảnh`}
              >
                ✕
              </button>
            </span>
          ))}
        </div>
      )}

      <div className={styles.messages}>
        {messages.length === 0 && (
          <p className={styles.empty}>
            {workingSet.length > 0
              ? 'Hỏi về những tin đang đọc kỹ — kể cả chi tiết trong bài gốc, hoặc so sánh chúng với nhau.'
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
                  {message.citations.map((citation) =>
                    /* Nguồn WEB hiển thị khác hẳn nguồn hệ thống: tin trong hệ thống đã qua
                       phân tích và chấm tin cậy, trang web thì chưa. Trộn chung một kiểu là
                       để người dùng gán nhầm mức tin cậy. Nó cũng không có trang chi tiết để
                       điều hướng tới, và KHÔNG vào working set — working set là tập insight. */
                    citation.kind === 'web' ? (
                      <a
                        key={`web-${citation.n}`}
                        href={citation.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.citationWeb}
                      >
                        [{citation.n}] 🌐 {citation.title}
                        <span className={styles.citationDomain}>
                          {hostOf(citation.source_url)}
                        </span>
                      </a>
                    ) : (
                      <Link
                        key={citation.insight_id ?? `n-${citation.n}`}
                        to={`/insights/${citation.insight_id}`}
                        className={styles.citationLink}
                        onClick={() =>
                          citation.insight_id &&
                          addRef({ id: citation.insight_id, title: citation.title })
                        }
                      >
                        [{citation.n}] {citation.title}
                      </Link>
                    ),
                  )}
                </div>
              )}
              {/* Bắt buộc theo điều khoản Google khi câu trả lời dùng Grounding with
                  Google Search. HTML do Google cấp, render nguyên trạng. */}
              {message.searchSuggestions && (
                <div
                  className={styles.searchSuggestions}
                  dangerouslySetInnerHTML={{ __html: message.searchSuggestions }}
                />
              )}
              {message.isError && (
                <button type="button" className={styles.retryBtn} onClick={retryLast}>
                  Thử lại
                </button>
              )}
            </div>
          ),
        )}

        {/* Lượt hỏi bị gián đoạn vì tải lại trang. Giữ câu hỏi lại thay vì lặng lẽ vứt: người
            dùng đã gõ nó, và server đã tính tiền lượt đó rồi (`chat-streaming-sse` D5). */}
        {interrupted && (
          <div className={styles.bubbleError}>
            Câu trả lời bị gián đoạn vì trang được tải lại.
            <button type="button" className={styles.retryBtn} onClick={retryLast}>
              Thử lại
            </button>
          </div>
        )}

        {/* Bong bóng đang chảy. Có token thì hiện token; chưa có thì hiện MỐC TIẾN TRÌNH
            thật do server phát. Khoảng đầu (5–35s đo thật) là lúc model đang thinking, chưa
            sinh token nào — status lấp đúng khoảng đó, thay cho spinner một dòng cố định. */}
        {pending && (
          <div className={styles.bubbleBot}>
            {pending.text ? (
              renderAnswer(pending.text, [])
            ) : pending.steps.length === 0 ? (
              <span className={styles.status}>Đang gửi câu hỏi…</span>
            ) : (
              /* XẾP CHỒNG, không ghi đè: mốc đã qua ở lại (mờ + ✓) để người dùng thấy CHUỖI
                 việc server đã làm, thay vì một dòng nhấp nháy rồi biến mất. Không có thanh
                 tiến trình % — ta không biết còn bao lâu (85% thời gian nằm ở lượt gọi
                 model), mà một thanh chạy sai là một lời hứa sai. */
              <ul className={styles.statusList}>
                {pending.steps.map((step, i) => {
                  const current = i === pending.steps.length - 1;
                  return (
                    <li
                      key={step.key}
                      className={current ? styles.statusCurrent : styles.statusDone}
                    >
                      <span aria-hidden="true">{current ? '⟳' : '✓'}</span> {step.text}
                    </li>
                  );
                })}
              </ul>
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
