import type { ActionType, RecommendationItem } from '../types/insight';
import { ROLE_DISPLAY_LABEL } from './RoleBadge';
import styles from '../styles/badges.module.css';

interface RecommendationsByRoleProps {
  recommendations: Record<string, RecommendationItem> | null;
}

const ACTION_LABEL: Record<ActionType, string> = {
  watch: 'Theo dõi',
  read: 'Đọc kỹ',
  test: 'Thử nghiệm',
  PoC: 'Đề xuất PoC',
  roadmap: 'Vào roadmap',
};

const ACTION_CLASS: Record<ActionType, string> = {
  watch: 'actionWatch',
  read: 'actionRead',
  test: 'actionTest',
  PoC: 'actionPoc',
  roadmap: 'actionRoadmap',
};

export default function RecommendationsByRole({ recommendations }: RecommendationsByRoleProps) {
  if (!recommendations || Object.keys(recommendations).length === 0) return null;

  return (
    <div className={styles.recommendationsBlock}>
      {Object.entries(recommendations).map(([role, item]) => (
        <div key={role} className={styles.recommendationRow}>
          <div className={styles.recommendationHead}>
            <span className={styles.recommendationRole}>{ROLE_DISPLAY_LABEL[role] ?? role}</span>
            <span className={`${styles.actionBadge} ${styles[ACTION_CLASS[item.action_type]] ?? ''}`}>
              {ACTION_LABEL[item.action_type] ?? item.action_type}
            </span>
          </div>
          <p className={styles.recommendationNote}>{item.note}</p>
        </div>
      ))}
    </div>
  );
}
