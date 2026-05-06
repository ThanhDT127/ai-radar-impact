import styles from '../styles/insights.module.css';

interface ImpactBadgeProps {
  label: string | null;
}

const LABEL_ICONS: Record<string, string> = {
  Critical: '🔴',
  High: '🟠',
  Medium: '🟡',
  Low: '🟢',
  Watch: '⚪',
};

export default function ImpactBadge({ label }: ImpactBadgeProps) {
  if (!label) return null;

  const className = `${styles.badge} ${styles[`badge-${label}`] ?? ''}`;
  const icon = LABEL_ICONS[label] ?? '';

  return (
    <span className={className}>
      {icon} {label}
    </span>
  );
}
