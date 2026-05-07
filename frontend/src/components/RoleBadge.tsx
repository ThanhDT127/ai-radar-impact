import styles from '../styles/insights.module.css';

interface RoleBadgeProps {
  role: string;
}

export default function RoleBadge({ role }: RoleBadgeProps) {
  return <span className={styles.roleBadge}>{role}</span>;
}
