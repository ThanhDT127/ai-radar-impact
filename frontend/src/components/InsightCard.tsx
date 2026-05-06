import { Link } from 'react-router-dom';
import type { InsightListItem } from '../types/insight';
import ImpactBadge from './ImpactBadge';
import styles from '../styles/insights.module.css';

interface InsightCardProps {
  insight: InsightListItem;
}

function relativeTime(isoDate: string): string {
  const now = Date.now();
  const then = new Date(isoDate).getTime();
  const diffMs = now - then;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 60) return `${diffMin} phút trước`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr} giờ trước`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay === 1) return 'Hôm qua';
  if (diffDay < 30) return `${diffDay} ngày trước`;
  return new Date(isoDate).toLocaleDateString('vi-VN');
}

export default function InsightCard({ insight }: InsightCardProps) {
  const timeDisplay = insight.published_at
    ? relativeTime(insight.published_at)
    : relativeTime(insight.created_at);

  return (
    <Link to={`/insights/${insight.id}`} className={styles.card}>
      <div className={styles.cardHeader}>
        <h3 className={styles.cardTitle}>{insight.title}</h3>
        <ImpactBadge label={insight.impact_label} />
      </div>

      {insight.summary_short && (
        <p className={styles.cardSummary}>{insight.summary_short}</p>
      )}

      <div className={styles.cardFooter}>
        <div className={styles.topicList}>
          {insight.topics.slice(0, 2).map((topic) => (
            <span key={topic} className={styles.topicTag}>{topic}</span>
          ))}
          {insight.event_type && (
            <span className={styles.eventTag}>{insight.event_type}</span>
          )}
        </div>
        {insight.affected_roles.length > 0 && (
          <div className={styles.roleList}>
            {insight.affected_roles.slice(0, 2).map((role) => (
              <span key={role} className={styles.roleTag}>👤 {role}</span>
            ))}
          </div>
        )}
        <span className={styles.cardTime}>📅 {timeDisplay}</span>
      </div>
    </Link>
  );
}
