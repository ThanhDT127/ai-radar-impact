import styles from '../styles/insights.module.css';

interface ImpactBadgeProps {
  label: string | null;
}

const LABEL_ICONS: Record<string, string> = {
  'Nghiêm trọng': '●',
  Cao: '●',
  'Trung bình': '●',
  Thấp: '●',
  'Theo dõi': '●',
  Critical: '●',
  High: '●',
  Medium: '●',
  Low: '●',
  Watch: '●',
};

const LABEL_CLASS: Record<string, string> = {
  'Nghiêm trọng': 'badgeCritical',
  Cao: 'badgeHigh',
  'Trung bình': 'badgeMedium',
  Thấp: 'badgeLow',
  'Theo dõi': 'badgeWatch',
  Critical: 'badgeCritical',
  High: 'badgeHigh',
  Medium: 'badgeMedium',
  Low: 'badgeLow',
  Watch: 'badgeWatch',
};

export default function ImpactBadge({ label }: ImpactBadgeProps) {
  if (!label) return null;

  const className = `${styles.badge} ${styles[LABEL_CLASS[label] ?? '']}`.trim();
  const icon = LABEL_ICONS[label] ?? '●';

  return (
    <span className={className}>
      <span className={styles.badgeDot} aria-hidden="true">{icon}</span>
      <span>{label}</span>
    </span>
  );
}
