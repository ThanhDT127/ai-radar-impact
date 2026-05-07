import { Link } from 'react-router-dom';
import type { InsightListItem } from '../types/insight';
import ImpactBadge from './ImpactBadge';
import RelativeTime from './RelativeTime';
import RoleBadge from './RoleBadge';
import styles from '../styles/insights.module.css';

interface InsightCardProps {
  insight: InsightListItem;
}

function hasVietnamese(text: string): boolean {
  return /[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]/i.test(text);
}

function makeDisplayTitle(insight: InsightListItem): string {
  if (insight.summary_short && !hasVietnamese(insight.title)) {
    return insight.summary_short;
  }
  return insight.title;
}

function makeWhatChanged(insight: InsightListItem): string {
  return insight.summary_short ?? insight.title;
}

function makeWhyItMatters(insight: InsightListItem): string {
  if (insight.summary_medium) {
    return insight.summary_medium;
  }

  const roles = insight.affected_roles.slice(0, 2).join(', ');
  if (roles && insight.event_type) {
    return `Đáng chú ý cho ${roles} vì đây là ${insight.event_type.toLowerCase()} từ ${insight.source_name}.`;
  }

  if (insight.event_type) {
    return `Đây là ${insight.event_type.toLowerCase()} từ ${insight.source_name}, phù hợp để theo dõi tác động tiếp theo.`;
  }

  return `Tín hiệu này đến từ ${insight.source_name} và cần được theo dõi trong bối cảnh công việc liên quan.`;
}

export default function InsightCard({ insight }: InsightCardProps) {
  const timeValue = insight.published_at ?? insight.created_at;
  const displayTitle = makeDisplayTitle(insight);
  const showOriginalTitle = displayTitle !== insight.title;
  const whatChanged = makeWhatChanged(insight);
  const whyItMatters = makeWhyItMatters(insight);

  return (
    <Link to={`/insights/${insight.id}`} className={styles.card}>
      <div className={styles.cardHeader}>
        <div className={styles.cardHeading}>
          <span className={styles.sourcePill}>{insight.source_name}</span>
          <h3 className={styles.cardTitle}>{displayTitle}</h3>
          {showOriginalTitle && <p className={styles.cardOriginalTitle}>{insight.title}</p>}
        </div>
        <ImpactBadge label={insight.impact_label} />
      </div>

      <div className={styles.cardInsightBlock}>
        <span className={styles.cardLabel}>Điểm chính</span>
        <p className={styles.cardSummary}>{whatChanged}</p>
      </div>

      <div className={styles.cardInsightBlock}>
        <span className={styles.cardLabel}>Đáng chú ý</span>
        <p className={styles.cardWhy}>{whyItMatters}</p>
      </div>

      <div className={styles.topicList}>
        {insight.topics.slice(0, 3).map((topic) => (
          <span key={topic} className={styles.topicTag}>{topic}</span>
        ))}
        {insight.event_type && <span className={styles.eventTag}>{insight.event_type}</span>}
      </div>

      {insight.affected_roles.length > 0 && (
        <div className={styles.cardInsightBlock}>
          <span className={styles.cardLabel}>Ai bị ảnh hưởng</span>
          <div className={styles.roleList}>
            {insight.affected_roles.slice(0, 3).map((role) => (
              <RoleBadge key={role} role={role} />
            ))}
          </div>
        </div>
      )}

      <div className={styles.cardMeta}>
        <span className={styles.cardTime}>
          <RelativeTime value={timeValue} />
        </span>
        <span className={styles.metaDot}>•</span>
        <span className={styles.cardConfidence}>
          Uy tín nguồn {Math.round(insight.trust_score * 100)}%
        </span>
      </div>
    </Link>
  );
}
