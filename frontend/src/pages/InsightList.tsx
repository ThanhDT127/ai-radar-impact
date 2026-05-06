import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchInsights } from '../api/insights';
import InsightCard from '../components/InsightCard';
import Pagination from '../components/Pagination';
import styles from '../styles/insights.module.css';

const PAGE_SIZE = 12;

function SkeletonCard() {
  return (
    <div className={styles.skeleton}>
      <div className={styles.cardHeader}>
        <div className={`${styles.skeletonLine} ${styles['skeletonLine-title']}`} />
        <div className={`${styles.skeletonLine} ${styles['skeletonLine-badge']}`} />
      </div>
      <div className={`${styles.skeletonLine} ${styles['skeletonLine-body']}`} />
      <div className={`${styles.skeletonLine} ${styles['skeletonLine-body2']}`} />
    </div>
  );
}

export default function InsightList() {
  const [page, setPage] = useState(1);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['insights', page],
    queryFn: () => fetchInsights({ page, size: PAGE_SIZE }),
  });

  return (
    <div className={styles.listPage}>
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Bản tin Radar AI</h1>
        <p className={styles.pageSubtitle}>
          Tín hiệu công nghệ và AI được phân tích tự động từ các nguồn uy tín
        </p>
      </div>

      {isLoading && (
        <div className={styles.cardGrid}>
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {isError && (
        <div className={styles.errorState}>
          <p>⚠️ Không thể tải dữ liệu bản tin</p>
          <p style={{ fontSize: '0.8rem', marginTop: 8, opacity: 0.6 }}>
            {(error as Error)?.message}
          </p>
        </div>
      )}

      {data && data.items.length === 0 && (
        <div className={styles.emptyState}>
          <h3>Chưa có bản tin nào</h3>
          <p>Chạy pipeline ingestion để thu thập và phân tích bản tin đầu tiên.</p>
        </div>
      )}

      {data && data.items.length > 0 && (
        <>
          <div className={styles.cardGrid}>
            {data.items.map((insight) => (
              <InsightCard key={insight.id} insight={insight} />
            ))}
          </div>
          <Pagination
            page={page}
            total={data.total}
            size={PAGE_SIZE}
            onPageChange={setPage}
          />
        </>
      )}
    </div>
  );
}
