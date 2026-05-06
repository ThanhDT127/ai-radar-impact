import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchInsightById } from '../api/insights';
import ImpactBadge from '../components/ImpactBadge';
import styles from '../styles/insights.module.css';

function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString('vi-VN', {
    year: 'numeric', month: 'long', day: 'numeric',
  });
}

export default function InsightDetail() {
  const { id } = useParams<{ id: string }>();

  const { data: insight, isLoading, isError } = useQuery({
    queryKey: ['insight', id],
    queryFn: () => fetchInsightById(id!),
    enabled: !!id,
    retry: false,
  });

  if (isLoading) {
    return (
      <div className={styles.detailPage}>
        <div className={styles.skeleton} style={{ height: 300 }}>
          <div className={`${styles.skeletonLine} ${styles['skeletonLine-title']}`} style={{ height: 28, width: '60%' }} />
          <div className={`${styles.skeletonLine} ${styles['skeletonLine-body']}`} />
          <div className={`${styles.skeletonLine} ${styles['skeletonLine-body2']}`} />
        </div>
      </div>
    );
  }

  if (isError || !insight) {
    return (
      <div className={`${styles.detailPage} ${styles.notFound}`}>
        <h2>Không tìm thấy bản tin</h2>
        <p>Bản tin này có thể đã bị xóa hoặc đường dẫn không đúng.</p>
        <Link to="/">← Về danh sách bản tin</Link>
      </div>
    );
  }

  const publishedDate = insight.published_at
    ? formatDate(insight.published_at)
    : formatDate(insight.created_at);

  const analyzedDate = formatDate(insight.created_at);

  return (
    <div className={styles.detailPage}>
      <Link to="/" className={styles.backLink}>← Tất cả bản tin</Link>

      <div className={styles.detailHeader}>
        <h1 className={styles.detailTitle}>{insight.title}</h1>
        <ImpactBadge label={insight.impact_label} />
      </div>

      <div className={styles.detailMeta}>
        <span>📅 {publishedDate}</span>
        {insight.event_type && (
          <>
            <span className={styles.detailMetaDot}>·</span>
            <span>{insight.event_type}</span>
          </>
        )}
        {insight.nature && (
          <>
            <span className={styles.detailMetaDot}>·</span>
            <span>{insight.nature}</span>
          </>
        )}
        <span className={styles.detailMetaDot}>·</span>
        <span>Độ tin cậy {Math.round(insight.confidence * 100)}%</span>
      </div>

      <div className={styles.detailBody}>
        {insight.summary_short && (
          <>
            <p className={styles.detailSectionLabel}>Tóm tắt</p>
            <p className={styles.detailSummaryShort}>{insight.summary_short}</p>
          </>
        )}

        {insight.summary_medium && (
          <>
            <p className={styles.detailSectionLabel}>Phân tích chi tiết</p>
            <p className={styles.detailSummaryMedium}>{insight.summary_medium}</p>
          </>
        )}

        {insight.affected_roles.length > 0 && (
          <>
            <p className={styles.detailSectionLabel}>Vai trò ảnh hưởng</p>
            <div className={styles.roleList}>
              {insight.affected_roles.map((role) => (
                <span key={role} className={styles.roleTag}>👤 {role}</span>
              ))}
            </div>
          </>
        )}

        {insight.topics.length > 0 && (
          <div className={styles.detailTopics}>
            {insight.topics.map((topic) => (
              <span key={topic} className={styles.topicTag}>{topic}</span>
            ))}
          </div>
        )}
      </div>

      <div className={styles.detailFooter}>
        <span className={styles.analyzedDate}>🤖 Phân tích lúc: {analyzedDate}</span>
        <a
          href={insight.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.sourceLink}
        >
          🔗 Xem nguồn gốc
        </a>
      </div>
    </div>
  );
}
