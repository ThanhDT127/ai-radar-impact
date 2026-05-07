import type { InsightStats } from '../types/source';
import styles from '../styles/dashboard.module.css';

interface KPISummaryProps {
  stats: InsightStats | undefined;
  isLoading?: boolean;
}

const KPI_ITEMS = [
  { key: 'total', label: 'Tổng bản tin' },
  { key: 'critical_high', label: 'Mức ảnh hưởng cao' },
  { key: 'opportunities', label: 'Cơ hội' },
  { key: 'active_sources', label: 'Nguồn hoạt động' },
] as const;

export default function KPISummary({ stats, isLoading = false }: KPISummaryProps) {
  return (
    <div className={styles.kpiGrid}>
      {KPI_ITEMS.map((item) => (
        <div key={item.key} className={styles.kpiCard}>
          <span className={styles.kpiLabel}>{item.label}</span>
          <strong className={styles.kpiValue}>
            {isLoading || !stats ? '...' : stats[item.key].toLocaleString('vi-VN')}
          </strong>
        </div>
      ))}
    </div>
  );
}
