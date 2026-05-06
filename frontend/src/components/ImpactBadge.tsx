import styles from '../styles/insights.module.css';

interface ImpactBadgeProps {
  label: string | null;
}

const LABEL_ICONS: Record<string, string> = {
  // Tiếng Việt (v2)
  'Nghiêm trọng': '🔴',
  'Cao': '🟠',
  'Trung bình': '🟡',
  'Thấp': '🟢',
  'Theo dõi': '⚪',
  // English fallback (data cũ)
  Critical: '🔴',
  High: '🟠',
  Medium: '🟡',
  Low: '🟢',
  Watch: '⚪',
};

const LABEL_CLASS: Record<string, string> = {
  'Nghiêm trọng': 'badge-Critical',
  'Cao': 'badge-High',
  'Trung bình': 'badge-Medium',
  'Thấp': 'badge-Low',
  'Theo dõi': 'badge-Watch',
  Critical: 'badge-Critical',
  High: 'badge-High',
  Medium: 'badge-Medium',
  Low: 'badge-Low',
  Watch: 'badge-Watch',
};

export default function ImpactBadge({ label }: ImpactBadgeProps) {
  if (!label) return null;

  const badgeClass = LABEL_CLASS[label] ?? '';
  const className = `${styles.badge} ${styles[badgeClass] ?? ''}`;
  const icon = LABEL_ICONS[label] ?? '';

  return (
    <span className={className}>
      {icon} {label}
    </span>
  );
}
