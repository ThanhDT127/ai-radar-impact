import Tooltip from './Tooltip';
import { TOOLTIP } from './TooltipContent';
import styles from '../styles/badges.module.css';

interface RoleBadgeProps {
  role: string;
}

const ROLE_CLASS: Record<string, string> = {
  'Data Analyst': 'roleDataAI',
  'Data Scientist': 'roleDataAI',
  'AI Engineer': 'roleDataAI',
  'Data Engineer': 'roleDataAI',
  Security: 'roleSecurity',
  Dev: 'roleEngineering',
  'Tech Lead': 'roleExecutive',
  'Người dùng phổ thông': 'roleAll',
  'Toàn công ty': 'roleAll',
};

export const ROLE_DISPLAY_LABEL: Record<string, string> = {
  'Data Analyst': 'Data Analyst',
  'Data Scientist': 'Data Scientist',
  'AI Engineer': 'AI Engineer',
  'Data Engineer': 'Data Engineer',
  Security: 'Bảo mật',
  Dev: 'Lập trình viên',
  'Tech Lead': 'Tech Lead',
  'Người dùng phổ thông': 'Người dùng',
  'Toàn công ty': 'Toàn công ty',
};

export default function RoleBadge({ role }: RoleBadgeProps) {
  const variant = ROLE_CLASS[role];
  const className = variant
    ? `${styles.roleBadge} ${styles[variant]}`
    : styles.roleBadge;
  const tip = TOOLTIP.role[role as keyof typeof TOOLTIP.role] ?? '';
  return (
    <Tooltip content={tip}>
      <span className={className}>{ROLE_DISPLAY_LABEL[role] ?? role}</span>
    </Tooltip>
  );
}
