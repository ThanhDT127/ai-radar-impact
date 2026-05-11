import styles from '../styles/insights.module.css';

interface RoleBadgeProps {
  role: string;
}

const ROLE_CLASS: Record<string, string> = {
  Executive: 'roleExecutive',
  Engineering: 'roleEngineering',
  'Data/AI': 'roleDataAI',
  Product: 'roleProduct',
  'Content/Marketing': 'roleContent',
  'Legal/Compliance': 'roleLegal',
  'HR/L&D': 'roleHr',
  'Toàn công ty': 'roleAll',
  DevOps: 'roleDevops',
  Infrastructure: 'roleInfrastructure',
  Security: 'roleSecurity',
  'BA/QA': 'roleBaqa',
  'Designer/UX': 'roleDesigner',
};

export default function RoleBadge({ role }: RoleBadgeProps) {
  const variant = ROLE_CLASS[role];
  const className = variant
    ? `${styles.roleBadge} ${styles[variant]}`
    : styles.roleBadge;
  return <span className={className}>{role}</span>;
}
