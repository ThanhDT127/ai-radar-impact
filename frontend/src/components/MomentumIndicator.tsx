import type { Momentum } from '../types/insight';
import Tooltip from './Tooltip';
import { TOOLTIP } from './TooltipContent';
import styles from '../styles/badges.module.css';

interface MomentumIndicatorProps {
  momentum: Momentum | null;
}

const MOMENTUM_CONFIG: Record<string, { icon: string; label: string; className: string }> = {
  rising: { icon: '🔥', label: 'Đang nổi lên', className: 'momentumRising' },
  new: { icon: '✨', label: 'Mới xuất hiện', className: 'momentumNew' },
  mature: { icon: '📊', label: 'Đã ổn định', className: 'momentumMature' },
};

export default function MomentumIndicator({ momentum }: MomentumIndicatorProps) {
  if (!momentum) return null;
  const config = MOMENTUM_CONFIG[momentum];
  if (!config) return null;
  const tip = TOOLTIP.momentum[momentum as keyof typeof TOOLTIP.momentum] ?? '';
  const className = `${styles.momentumPill} ${styles[config.className] ?? ''}`.trim();
  return (
    <Tooltip content={tip}>
      <span className={className}>
        <span aria-hidden="true">{config.icon}</span>
        <span>{config.label}</span>
      </span>
    </Tooltip>
  );
}
