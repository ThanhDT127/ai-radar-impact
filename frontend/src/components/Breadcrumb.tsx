import { Link } from 'react-router-dom';
import styles from './Breadcrumb.module.css';

interface BreadcrumbProps {
  tier?: string | null;
  title?: string;
}

const TIER_LABELS: Record<string, string> = {
  Tactical: 'Hành động ngay',
  Operational: 'Vận hành',
  Strategic: 'Chiến lược',
  Informational: 'Tham khảo',
};

export default function Breadcrumb({ tier, title }: BreadcrumbProps) {
  const truncated = title && title.length > 40 ? `${title.slice(0, 40)}…` : title;

  return (
    <nav className={styles.breadcrumb} aria-label="Điều hướng">
      <Link to="/" className={styles.crumb}>
        ← Tất cả bản tin
      </Link>
      {tier && (
        <>
          <span className={styles.sep} aria-hidden="true">/</span>
          <span className={styles.crumb}>{TIER_LABELS[tier] ?? tier}</span>
        </>
      )}
      {truncated && (
        <>
          <span className={styles.sep} aria-hidden="true">/</span>
          <span className={`${styles.crumb} ${styles.current}`} aria-current="page">
            {truncated}
          </span>
        </>
      )}
    </nav>
  );
}
