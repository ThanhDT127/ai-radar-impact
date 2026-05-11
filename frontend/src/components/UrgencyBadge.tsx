import type { Urgency } from '../types/insight';
import styles from '../styles/insights.module.css';

interface UrgencyBadgeProps {
  urgency: Urgency | null;
}

const URGENCY_LABEL: Record<Urgency, string> = {
  critical: 'Khẩn cấp',
  high: 'Cao',
  medium: 'Trung bình',
  low: 'Thấp',
};

const URGENCY_CLASS: Record<Urgency, string> = {
  critical: 'badgeCritical',
  high: 'badgeHigh',
  medium: 'badgeMedium',
  low: 'badgeWatch',
};

export default function UrgencyBadge({ urgency }: UrgencyBadgeProps) {
  if (!urgency) return null;
  const className = `${styles.badge} ${styles[URGENCY_CLASS[urgency]]}`.trim();
  return (
    <span className={className} title={`Mức độ cấp thiết: ${URGENCY_LABEL[urgency]}`}>
      <span className={styles.badgeDot} aria-hidden="true">●</span>
      <span>{URGENCY_LABEL[urgency]}</span>
    </span>
  );
}
