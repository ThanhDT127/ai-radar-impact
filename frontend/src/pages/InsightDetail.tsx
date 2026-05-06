import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchInsightById } from '../api/insights';
import ImpactBadge from '../components/ImpactBadge';
import styles from '../styles/insights.module.css';

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
        <h2>Insight not found</h2>
        <p>This insight may have been removed or the URL is incorrect.</p>
        <Link to="/">← Back to insights</Link>
      </div>
    );
  }

  const publishedDate = new Date(insight.created_at).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  });

  return (
    <div className={styles.detailPage}>
      <Link to="/" className={styles.backLink}>← All Insights</Link>

      <div className={styles.detailHeader}>
        <h1 className={styles.detailTitle}>{insight.title}</h1>
        <ImpactBadge label={insight.impact_label} />
      </div>

      <div className={styles.detailMeta}>
        <span>{publishedDate}</span>
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
        <span>Confidence {Math.round(insight.confidence * 100)}%</span>
      </div>

      <div className={styles.detailBody}>
        {insight.summary_short && (
          <>
            <p className={styles.detailSectionLabel}>Summary</p>
            <p className={styles.detailSummaryShort}>{insight.summary_short}</p>
          </>
        )}

        {insight.summary_medium && (
          <>
            <p className={styles.detailSectionLabel}>Analysis</p>
            <p className={styles.detailSummaryMedium}>{insight.summary_medium}</p>
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

      <a
        href={insight.source_url}
        target="_blank"
        rel="noopener noreferrer"
        className={styles.sourceLink}
      >
        🔗 View original source
      </a>
    </div>
  );
}
