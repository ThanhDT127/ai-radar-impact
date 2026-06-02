import type { Urgency } from '../types/insight';
import Tooltip from './Tooltip';
import { TOOLTIP } from './TooltipContent';
import styles from '../styles/badges.module.css';

interface UrgencyBadgeProps {
  urgency: Urgency | null;
}

const URGENCY_LABEL: Record<Urgency, string> = {
  critical: 'Khẩn cấp',
  high: 'Cấp thiết: Cao',
  medium: 'Cấp thiết: Trung bình',
  low: 'Cấp thiết: Thấp',
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
  const tip = TOOLTIP.urgency[urgency] ?? '';
  return (
    <Tooltip content={tip}>
      <span className={className}>
        <span className={styles.badgeDot} aria-hidden="true">●</span>
        <span>{URGENCY_LABEL[urgency]}</span>
      </span>
    </Tooltip>
  );
}
