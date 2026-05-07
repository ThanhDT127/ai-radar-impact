import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchInsightById } from '../api/insights';
import ImpactBadge from '../components/ImpactBadge';
import RelativeTime from '../components/RelativeTime';
import RoleBadge from '../components/RoleBadge';
import styles from '../styles/insights.module.css';

function formatDateTime(isoDate: string): string {
  return new Date(isoDate).toLocaleString('vi-VN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
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
        <div className={styles.skeleton} style={{ minHeight: 320 }} />
      </div>
    );
  }

  if (isError || !insight) {
    return (
      <div className={`${styles.detailPage} ${styles.notFound}`}>
        <h2>Không tìm thấy bản tin</h2>
        <p>Bản tin này có thể đã bị xóa hoặc đường dẫn không còn hợp lệ.</p>
        <Link to="/">Về danh sách bản tin</Link>
      </div>
    );
  }

  const publishedValue = insight.published_at ?? insight.created_at;

  return (
    <div className={styles.detailPage}>
      <Link to="/" className={styles.backLink}>← Tất cả bản tin</Link>

      <div className={styles.detailHeader}>
        <div className={styles.detailHero}>
          <span className={styles.sourcePill}>{insight.source_name}</span>
          <h1 className={styles.detailTitle}>{insight.title}</h1>
        </div>
        <ImpactBadge label={insight.impact_label} />
      </div>

      <div className={styles.detailMeta}>
        <span><RelativeTime value={publishedValue} /></span>
        <span className={styles.metaDot}>•</span>
        <span>{insight.event_type ?? 'Bản tin tổng hợp'}</span>
        <span className={styles.metaDot}>•</span>
        <span>{insight.nature ?? 'Thông tin chung'}</span>
        <span className={styles.metaDot}>•</span>
        <span>Tin cậy {Math.round(insight.trust_score * 100)}%</span>
      </div>

      <div className={styles.detailBody}>
        {insight.summary_short && (
          <section className={styles.detailSection}>
            <p className={styles.detailSectionLabel}>Tóm tắt</p>
            <p className={styles.detailSummaryShort}>{insight.summary_short}</p>
          </section>
        )}

        {insight.summary_medium && (
          <section className={styles.detailSection}>
            <p className={styles.detailSectionLabel}>Phân tích chi tiết</p>
            <p className={styles.detailSummaryMedium}>{insight.summary_medium}</p>
          </section>
        )}

        {insight.affected_roles.length > 0 && (
          <section className={styles.detailSection}>
            <p className={styles.detailSectionLabel}>Vai trò ảnh hưởng</p>
            <div className={styles.roleList}>
              {insight.affected_roles.map((role) => (
                <RoleBadge key={role} role={role} />
              ))}
            </div>
          </section>
        )}

        {insight.topics.length > 0 && (
          <section className={styles.detailSection}>
            <p className={styles.detailSectionLabel}>Chủ đề</p>
            <div className={styles.topicList}>
              {insight.topics.map((topic) => (
                <span key={topic} className={styles.topicTag}>{topic}</span>
              ))}
            </div>
          </section>
        )}

        <section className={styles.detailTimeline}>
          <div className={styles.timelineCard}>
            <p className={styles.detailSectionLabel}>Xuất bản</p>
            <strong>{formatDateTime(publishedValue)}</strong>
          </div>
          <div className={styles.timelineCard}>
            <p className={styles.detailSectionLabel}>Phân tích</p>
            <strong>{formatDateTime(insight.created_at)}</strong>
          </div>
        </section>
      </div>

      <div className={styles.detailFooter}>
        <div className={styles.sourceMeta}>
          <p className={styles.detailSectionLabel}>Nguồn</p>
          <strong>{insight.source_name}</strong>
          <span>{insight.source_type.toUpperCase()}</span>
        </div>
        <a
          href={insight.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.sourceLink}
        >
          Xem bài gốc
        </a>
      </div>
    </div>
  );
}
