import Tooltip from './Tooltip';
import { TOOLTIP } from './TooltipContent';
import styles from '../styles/badges.module.css';

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

export const ROLE_DISPLAY_LABEL: Record<string, string> = {
  Executive: 'Leader',
  Engineering: 'Lập trình & Kỹ sư',
  'Data/AI': 'Dữ liệu & AI',
  Product: 'Quản lý sản phẩm',
  'Content/Marketing': 'Marketing & Nội dung',
  'Legal/Compliance': 'Pháp lý & Tuân thủ',
  'HR/L&D': 'Nhân sự & Đào tạo',
  'Toàn công ty': 'Toàn công ty',
  DevOps: 'DevOps',
  Infrastructure: 'Hạ tầng mạng/Cloud',
  Security: 'An toàn thông tin',
  'BA/QA': 'BA/QA',
  'Designer/UX': 'Thiết kế/UX',
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
