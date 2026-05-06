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
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 30) return `${diffDay}d ago`;
  return new Date(isoDate).toLocaleDateString();
}

export default function InsightCard({ insight }: InsightCardProps) {
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
          {insight.topics.slice(0, 3).map((topic) => (
            <span key={topic} className={styles.topicTag}>{topic}</span>
          ))}
        </div>
        <span className={styles.cardTime}>{relativeTime(insight.created_at)}</span>
      </div>
    </Link>
  );
}
