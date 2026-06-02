import { useEffect, useRef, useState } from 'react';
import type { InsightStats } from '../types/source';
import Tooltip from './Tooltip';
import { TOOLTIP } from './TooltipContent';
import styles from '../styles/dashboard.module.css';

interface KPISummaryProps {
  stats: InsightStats | undefined;
  isLoading?: boolean;
}

type TrendDirection = 'up' | 'down' | 'flat';

interface KPIConfig {
  key: keyof InsightStats;
  label: string;
  subtitle: string;
  tooltipKey: keyof typeof TOOLTIP.kpi;
  color: 'neutral' | 'danger' | 'success' | 'info';
  icon: string;
  trendPositive: TrendDirection;
}

const KPI_ITEMS: KPIConfig[] = [
  {
    key: 'total',
    label: 'Tổng bản tin',
    subtitle: '7 ngày gần nhất',
    tooltipKey: 'total',
    color: 'neutral',
    icon: '📊',
    trendPositive: 'up',
  },
  {
    key: 'critical_high',
    label: 'Ảnh hưởng cao',
    subtitle: 'Cần chú ý ngay',
    tooltipKey: 'critical',
    color: 'danger',
    icon: '🔴',
    trendPositive: 'down',
  },
  {
    key: 'opportunities',
    label: 'Cơ hội hành động',
    subtitle: 'Có thể áp dụng',
    tooltipKey: 'opportunity',
    color: 'success',
    icon: '✅',
    trendPositive: 'up',
  },
  {
    key: 'active_sources',
    label: 'Nguồn hoạt động',
    subtitle: 'Đang cập nhật',
    tooltipKey: 'sources',
    color: 'info',
    icon: '📡',
    trendPositive: 'up',
  },
];

const COLOR_CLASS: Record<string, string> = {
  danger: 'kpiDanger',
  success: 'kpiSuccess',
  info: 'kpiInfo',
  neutral: '',
};

// Easing function for count-up animation
function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

function useCountUp(target: number, duration = 800): number {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef<number>(0);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    if (target === 0) { setDisplay(0); return; }
    // Respect prefers-reduced-motion
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setDisplay(target);
      return;
    }
    startRef.current = null;
    const animate = (now: number) => {
      if (startRef.current === null) startRef.current = now;
      const elapsed = now - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      setDisplay(Math.round(easeOutCubic(progress) * target));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate);
      }
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return display;
}

interface KPIValueProps {
  value: number;
  isLoading: boolean;
  hasData: boolean;
}

function KPIValue({ value, isLoading, hasData }: KPIValueProps) {
  const displayed = useCountUp(hasData && !isLoading ? value : 0);
  if (isLoading || !hasData) return <span>—</span>;
  return <span>{displayed.toLocaleString('vi-VN')}</span>;
}

export default function KPISummary({ stats, isLoading = false }: KPISummaryProps) {
  return (
    <div className={styles.kpiGrid}>
      {KPI_ITEMS.map((item) => {
        const colorClass = COLOR_CLASS[item.color];
        const cardClass = colorClass
          ? `${styles.kpiCard} ${styles[colorClass]}`
          : styles.kpiCard;
        const value = stats ? (stats[item.key] as number) : 0;
        const tooltip = TOOLTIP.kpi[item.tooltipKey] ?? '';

        return (
          <div key={item.key} className={cardClass}>
            <div className={styles.kpiHeader}>
              <span className={styles.kpiIcon} aria-hidden="true">{item.icon}</span>
              <span className={styles.kpiLabel}>
                {item.label}
                <Tooltip content={tooltip}>
                  <span className={styles.kpiInfoIcon} aria-label="Thông tin">ⓘ</span>
                </Tooltip>
              </span>
            </div>
            <strong className={styles.kpiValue}>
              <KPIValue value={value} isLoading={isLoading} hasData={!!stats} />
            </strong>
            <span className={styles.kpiSubtitle}>{item.subtitle}</span>
          </div>
        );
      })}
    </div>
  );
}
