import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import {
  createSubscriber,
  deleteSubscriber,
  fetchSubscribers,
  updateSubscriber,
  type Subscriber,
} from '../api/subscribers';
import { ROLE_DISPLAY_LABEL } from '../components/RoleBadge';
import styles from '../styles/subscribers.module.css';

/** 9 vai trò của `ALLOWED_ROLES` — lấy thứ tự từ ROLE_DISPLAY_LABEL để không lệch taxonomy. */
const ALL_ROLES = Object.keys(ROLE_DISPLAY_LABEL);

/**
 * Hai vai trò này hiện chưa có insight nào gắn vào `affected_roles`, nên người chỉ đăng ký
 * chúng sẽ không nhận được bản tin nào. Cảnh báo tại chỗ để không phải đi tìm nguyên nhân.
 */
const ROLES_WITHOUT_INSIGHTS = ['Data Analyst', 'Người dùng phổ thông'];

function errorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  }
  return 'Có lỗi xảy ra, thử lại sau.';
}

export default function Subscribers() {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [roles, setRoles] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);

  const { data: subscribers, isLoading } = useQuery({
    queryKey: ['subscribers'],
    queryFn: fetchSubscribers,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['subscribers'] });

  const createMutation = useMutation({
    mutationFn: createSubscriber,
    onSuccess: () => {
      setEmail('');
      setDisplayName('');
      setRoles([]);
      setError(null);
      invalidate();
    },
    onError: (err) => setError(errorMessage(err)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, ...payload }: { id: string; roles?: string[]; active?: boolean }) =>
      updateSubscriber(id, payload),
    onSuccess: invalidate,
    onError: (err) => setError(errorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteSubscriber,
    onSuccess: invalidate,
    onError: (err) => setError(errorMessage(err)),
  });

  const toggleRole = (role: string) =>
    setRoles((prev) => (prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    createMutation.mutate({ email, roles, display_name: displayName || null });
  };

  const selectedEmptyRoles = roles.filter((r) => ROLES_WITHOUT_INSIGHTS.includes(r));
  const showEmptyRoleHint = selectedEmptyRoles.length > 0 && selectedEmptyRoles.length === roles.length;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1 className={styles.title}>Người nhận bản tin</h1>
        <p className={styles.subtitle}>
          Bản tin gửi Thứ Hai và Thứ Năm, mỗi người tối đa 3 tin chọn theo vai trò đã đăng ký.
        </p>
      </header>

      <form className={styles.card} onSubmit={handleSubmit}>
        <div className={styles.formRow}>
          <input
            className={styles.input}
            type="email"
            required
            placeholder="email@congty.vn"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            className={styles.input}
            type="text"
            placeholder="Tên hiển thị (tuỳ chọn)"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        </div>

        <span className={styles.fieldLabel}>Vai trò nhận tin</span>
        <div className={styles.roleGrid}>
          {ALL_ROLES.map((role) => {
            const selected = roles.includes(role);
            const empty = ROLES_WITHOUT_INSIGHTS.includes(role);
            return (
              <button
                key={role}
                type="button"
                onClick={() => toggleRole(role)}
                className={[
                  styles.roleChip,
                  selected ? styles.roleChipActive : '',
                  empty && !selected ? styles.roleChipEmpty : '',
                ]
                  .filter(Boolean)
                  .join(' ')}
              >
                {ROLE_DISPLAY_LABEL[role] ?? role}
              </button>
            );
          })}
        </div>

        {showEmptyRoleHint && (
          <p className={styles.hint}>
            {selectedEmptyRoles.join(', ')} hiện chưa có insight nào gắn vai trò này — người nhận
            sẽ không nhận được bản tin. Chọn thêm vai trò khác hoặc &ldquo;Toàn công ty&rdquo;.
          </p>
        )}

        <div className={styles.actions}>
          <button
            className={styles.button}
            type="submit"
            disabled={!email || roles.length === 0 || createMutation.isPending}
          >
            {createMutation.isPending ? 'Đang thêm…' : 'Thêm người nhận'}
          </button>
          {roles.length === 0 && (
            <span className={styles.subtitle}>Chọn ít nhất 1 vai trò</span>
          )}
        </div>

        {error && <p className={styles.error}>{error}</p>}
      </form>

      <div className={styles.card}>
        {isLoading ? (
          <p className={styles.empty}>Đang tải…</p>
        ) : !subscribers || subscribers.length === 0 ? (
          <p className={styles.empty}>Chưa có người nhận nào.</p>
        ) : (
          <div className={styles.tableWrap}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Email</th>
                  <th>Tên</th>
                  <th>Vai trò</th>
                  <th>Trạng thái</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {subscribers.map((sub: Subscriber) => (
                  <tr key={sub.id} className={sub.active ? undefined : styles.rowInactive}>
                    <td>{sub.email}</td>
                    <td>{sub.display_name ?? '—'}</td>
                    <td>
                      <div className={styles.roleTags}>
                        {sub.roles.map((role) => (
                          <span key={role} className={styles.roleTag}>
                            {ROLE_DISPLAY_LABEL[role] ?? role}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <span className={sub.active ? styles.statusOn : styles.statusOff}>
                        {sub.active ? 'Đang nhận' : 'Đã tắt'}
                      </span>
                    </td>
                    <td>
                      <div className={styles.actions}>
                        <button
                          type="button"
                          className={styles.linkButton}
                          onClick={() =>
                            updateMutation.mutate({ id: sub.id, active: !sub.active })
                          }
                        >
                          {sub.active ? 'Tắt nhận' : 'Bật lại'}
                        </button>
                        <button
                          type="button"
                          className={`${styles.linkButton} ${styles.linkButtonDanger}`}
                          onClick={() => deleteMutation.mutate(sub.id)}
                        >
                          Xoá
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
