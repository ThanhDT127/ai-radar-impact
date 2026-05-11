import type { Momentum } from '../types/insight';
import styles from '../styles/insights.module.css';

interface MomentumIndicatorProps {
  momentum: Momentum | null;
}

export default function MomentumIndicator({ momentum }: MomentumIndicatorProps) {
  // Only render `rising` — `new` is redundant with RelativeTime, `mature` has no signal value
  if (momentum !== 'rising') return null;
  return (
    <span className={styles.momentumPill} title="Đà tin: Đang nổi lên">
      <span aria-hidden="true">🔥</span>
      <span>Đang nổi lên</span>
    </span>
  );
}
