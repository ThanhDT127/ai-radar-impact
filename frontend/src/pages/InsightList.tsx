import { startTransition, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchInsights } from '../api/insights';
import { fetchSources } from '../api/sources';
import { fetchInsightStats } from '../api/stats';
import InsightCard from '../components/InsightCard';
import KPISummary from '../components/KPISummary';
import Pagination from '../components/Pagination';
import Tooltip from '../components/Tooltip';
import { TOOLTIP } from '../components/TooltipContent';
import type { InsightSort } from '../components/SortDropdown';
import SortDropdown from '../components/SortDropdown';
import styles from '../styles/list.module.css';
import dashStyles from '../styles/dashboard.module.css';

function getFilterTooltip(rowLabel: string, itemId: string): string {
  if (rowLabel === 'Phân tầng') {
    return TOOLTIP.tier[itemId as keyof typeof TOOLTIP.tier] ?? '';
  }
  if (rowLabel === 'Độ cấp thiết') {
    return TOOLTIP.urgency[itemId as keyof typeof TOOLTIP.urgency] ?? '';
  }
  if (rowLabel === 'Xu hướng') {
    return TOOLTIP.momentum[itemId as keyof typeof TOOLTIP.momentum] ?? '';
  }
  if (rowLabel === 'Việt Nam') {
    return TOOLTIP.vietnam[itemId as keyof typeof TOOLTIP.vietnam] ?? '';
  }
  if (rowLabel === 'Vai trò') {
    return TOOLTIP.role[itemId as keyof typeof TOOLTIP.role] ?? '';
  }
  return '';
}

const PAGE_SIZE = 12;
const SOURCE_PREVIEW_LIMIT = 12;

const ROLE_OPTIONS = [
  'Executive', 'Engineering', 'Data/AI', 'Product',
  'Content/Marketing', 'Legal/Compliance', 'HR/L&D', 'Toàn công ty',
];

const URGENCY_ITEMS = [
  { id: 'critical', label: 'Khẩn cấp' },
  { id: 'high', label: 'Cấp thiết: Cao' },
  { id: 'medium', label: 'Cấp thiết: Trung bình' },
  { id: 'low', label: 'Cấp thiết: Thấp' },
];

const MOMENTUM_ITEMS = [
  { id: 'new', label: 'Mới phát hành 🕒' },
  { id: 'rising', label: 'Đang nổi lên 🔥' },
  { id: 'mature', label: 'Đã ổn định 🛡️' },
];

const VIETNAM_ITEMS = [
  { id: 'high', label: 'Liên quan cao 🇻🇳' },
  { id: 'medium', label: 'Liên quan vừa' },
  { id: 'low', label: 'Ít liên quan' },
];

const TIER_ITEMS = [
  { id: 'Tactical', label: '🎯 Hành động ngay (Tactical)' },
  { id: 'Operational', label: '⚙️ Vận hành (Operational)' },
  { id: 'Strategic', label: '🔭 Chiến lược (Strategic)' },
  { id: 'Informational', label: 'ℹ️ Tham khảo (Informational)' },
];

const ROLE_LABELS: Record<string, string> = {
  Executive: 'Leader 👔',
  Engineering: 'Lập trình & Kỹ sư 💻',
  'Data/AI': 'Dữ liệu & AI 📊',
  Product: 'Quản lý sản phẩm 🚀',
  'Content/Marketing': 'Marketing & Nội dung 📝',
  'Legal/Compliance': 'Pháp lý & Tuân thủ 🛡️',
  'HR/L&D': 'Nhân sự & Đào tạo 👥',
  'Toàn công ty': 'Toàn công ty 🏢',
};

const PRESET_URGENT = ['critical', 'high'];
const PRESET_MOMENTUM = ['rising', 'new'];

function SkeletonCard() {
  return (
    <div className={styles.skeleton}>
      <div className={styles.skeletonImage} />
      <div className={styles.skeletonBody}>
        <div className={`${styles.skeletonLine} ${styles.skeletonLineBadge}`} />
        <div className={`${styles.skeletonLine} ${styles.skeletonLineTitle}`} />
        <div className={`${styles.skeletonLine} ${styles.skeletonLineBody}`} />
        <div className={`${styles.skeletonLine} ${styles.skeletonLineBodySmall}`} />
      </div>
    </div>
  );
}

function toggle(value: string, selected: string[]): string[] {
  return selected.includes(value)
    ? selected.filter((item) => item !== value)
    : [...selected, value];
}

function arraysEqual(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false;
  const set = new Set(a);
  return b.every((v) => set.has(v));
}

export default function InsightList() {
  const [searchParams, setSearchParams] = useSearchParams();

  const page = parseInt(searchParams.get('page') ?? '1', 10);
  const sortBy = (searchParams.get('sort_by') as InsightSort) ?? 'created_at';
  const selectedSourceIds = useMemo(() => searchParams.get('source_id')?.split(',').filter(Boolean) ?? [], [searchParams]);
  const selectedRoles = useMemo(() => searchParams.get('role')?.split(',').filter(Boolean) ?? [], [searchParams]);
  const selectedUrgency = useMemo(() => searchParams.get('urgency')?.split(',').filter(Boolean) ?? [], [searchParams]);
  const selectedMomentum = useMemo(() => searchParams.get('momentum')?.split(',').filter(Boolean) ?? [], [searchParams]);
  const selectedVietnam = useMemo(() => searchParams.get('vietnam_relevance')?.split(',').filter(Boolean) ?? [], [searchParams]);
  const selectedTier = useMemo(() => searchParams.get('intelligence_tier')?.split(',').filter(Boolean) ?? [], [searchParams]);
  const searchQuery = searchParams.get('search') ?? '';

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [sourceQuery, setSourceQuery] = useState('');
  const [showAllSources, setShowAllSources] = useState(false);

  const updateFilterParams = (key: string, values: string[] | string | number | null) => {
    const newParams = new URLSearchParams(searchParams);
    
    if (values === null || values === undefined || (Array.isArray(values) && values.length === 0) || values === '') {
      newParams.delete(key);
    } else if (Array.isArray(values)) {
      newParams.set(key, values.join(','));
    } else {
      newParams.set(key, String(values));
    }
    
    if (key !== 'page') {
      newParams.delete('page');
    }
    
    setSearchParams(newParams);
  };

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['insight-stats'],
    queryFn: fetchInsightStats,
  });

  const { data: sources = [] } = useQuery({
    queryKey: ['sources'],
    queryFn: fetchSources,
  });

  const overviewQuery = useQuery({
    queryKey: [
      'insights', page, sortBy,
      selectedSourceIds, selectedRoles,
      selectedUrgency, selectedMomentum, selectedVietnam, selectedTier,
    ],
    queryFn: () =>
      fetchInsights({
        page,
        size: PAGE_SIZE,
        sort_by: sortBy,
        source_id: selectedSourceIds.length > 0 ? selectedSourceIds : null,
        role: selectedRoles.length > 0 ? selectedRoles : null,
        urgency: selectedUrgency.length > 0 ? selectedUrgency : null,
        momentum: selectedMomentum.length > 0 ? selectedMomentum : null,
        vietnam_relevance: selectedVietnam.length > 0 ? selectedVietnam : null,
        intelligence_tier: selectedTier.length > 0 ? selectedTier : null,
      }),
  });

  // Client-side search filter applied on top of server-filtered results
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim() || !overviewQuery.data?.items) {
      return overviewQuery.data?.items ?? [];
    }
    const q = searchQuery.toLowerCase();
    return overviewQuery.data.items.filter(item =>
      item.title.toLowerCase().includes(q) ||
      (item.summary_short?.toLowerCase().includes(q)) ||
      (item.so_what?.toLowerCase().includes(q)) ||
      item.topics.some(t => t.toLowerCase().includes(q)) ||
      item.affected_roles.some(r => r.toLowerCase().includes(q))
    );
  }, [searchQuery, overviewQuery.data?.items]);

  const sortedSources = useMemo(
    () => [...sources].sort((l, r) => r.insight_count - l.insight_count || l.name.localeCompare(r.name)),
    [sources],
  );
  const activeSources = sortedSources.filter((s) => s.insight_count > 0);
  const emptySources = sortedSources.filter((s) => s.insight_count === 0);

  const filteredSources = sourceQuery.trim()
    ? activeSources.filter((s) => s.name.toLowerCase().includes(sourceQuery.trim().toLowerCase()))
    : activeSources;
  const visibleSources = showAllSources || sourceQuery.trim()
    ? filteredSources
    : filteredSources.slice(0, SOURCE_PREVIEW_LIMIT);

  const presetUrgentActive = arraysEqual(selectedUrgency, PRESET_URGENT);
  const presetVietnamActive = selectedVietnam.length === 1 && selectedVietnam[0] === 'high';
  const presetMomentumActive = arraysEqual(selectedMomentum, PRESET_MOMENTUM);

  const togglePresetUrgent = () => {
    updateFilterParams('urgency', presetUrgentActive ? [] : PRESET_URGENT);
  };
  const togglePresetVietnam = () => {
    updateFilterParams('vietnam_relevance', presetVietnamActive ? [] : ['high']);
  };
  const togglePresetMomentum = () => {
    updateFilterParams('momentum', presetMomentumActive ? [] : PRESET_MOMENTUM);
  };

  const advancedCount =
    selectedUrgency.length + selectedMomentum.length + selectedVietnam.length + selectedTier.length +
    selectedSourceIds.length + selectedRoles.length;

  const clearAllFilters = () => {
    const newParams = new URLSearchParams();
    if (searchParams.has('sort_by')) {
      newParams.set('sort_by', searchParams.get('sort_by')!);
    }
    setSourceQuery('');
    setSearchParams(newParams);
  };

  const hasAnyFilter = advancedCount > 0 || searchQuery.trim() !== '';
  const hasItems = (filteredItems.length) > 0;

  const renderChipRow = (
    label: string,
    items: { id: string; label: string }[],
    selected: string[],
    setSelected: (next: string[]) => void,
  ) => (
    <div className={dashStyles.filterRow}>
      <span className={dashStyles.filterRowLabel}>{label}</span>
      <div className={dashStyles.filterChips}>
        {items.map((item) => {
          const tooltipContent = getFilterTooltip(label, item.id);
          return (
            <Tooltip key={item.id} content={tooltipContent}>
              <button
                className={selected.includes(item.id) ? dashStyles.filterChipActive : dashStyles.filterChip}
                onClick={() => setSelected(toggle(item.id, selected))}
              >
                {item.label}
              </button>
            </Tooltip>
          );
        })}
      </div>
    </div>
  );

  // Build label maps for active filter chips display
  const urgencyLabelMap = Object.fromEntries(URGENCY_ITEMS.map(i => [i.id, i.label]));
  const momentumLabelMap = Object.fromEntries(MOMENTUM_ITEMS.map(i => [i.id, i.label]));
  const vietnamLabelMap = Object.fromEntries(VIETNAM_ITEMS.map(i => [i.id, i.label]));
  const tierLabelMap = Object.fromEntries(TIER_ITEMS.map(i => [i.id, i.label]));
  const sourceLabelMap = Object.fromEntries(sources.map((s) => [s.id, s.name]));

  return (
    <div className={styles.listPage}>
      {/* Filter Drawer Backdrop */}
      {drawerOpen && (
        <div
          className={dashStyles.filterDrawerBackdrop}
          onClick={() => setDrawerOpen(false)}
        />
      )}

      {/* Filter Drawer */}
      <div className={`${dashStyles.filterDrawer} ${drawerOpen ? dashStyles.filterDrawerOpen : ''}`}>
        <div className={dashStyles.filterDrawerHeader}>
          <h2>Bộ lọc nâng cao</h2>
          <button onClick={() => setDrawerOpen(false)} aria-label="Đóng bộ lọc">✕</button>
        </div>

        <div className={dashStyles.filterDrawerBody}>
          {renderChipRow('Phân tầng', TIER_ITEMS, selectedTier, (next) => updateFilterParams('intelligence_tier', next))}
          {renderChipRow('Độ cấp thiết', URGENCY_ITEMS, selectedUrgency, (next) => updateFilterParams('urgency', next))}
          {renderChipRow('Xu hướng', MOMENTUM_ITEMS, selectedMomentum, (next) => updateFilterParams('momentum', next))}
          {renderChipRow('Việt Nam', VIETNAM_ITEMS, selectedVietnam, (next) => updateFilterParams('vietnam_relevance', next))}
          {renderChipRow(
            'Vai trò',
            ROLE_OPTIONS.map((r) => ({ id: r, label: ROLE_LABELS[r] ?? r })),
            selectedRoles,
            (next) => updateFilterParams('role', next),
          )}

          <div className={dashStyles.sourceRow}>
            <span className={dashStyles.sourceLabel}>Nguồn</span>
            <div className={dashStyles.sourceContent}>
              <input
                type="search"
                placeholder="Tìm nguồn..."
                value={sourceQuery}
                onChange={(e) => setSourceQuery(e.target.value)}
                className={dashStyles.sourceSearch}
              />
              <div className={dashStyles.sourceChipWrap}>
                {visibleSources.map((s) => (
                  <button
                    key={s.id}
                    className={selectedSourceIds.includes(s.id) ? dashStyles.filterChipActive : dashStyles.filterChip}
                    onClick={() => updateFilterParams('source_id', toggle(s.id, selectedSourceIds))}
                  >
                    {s.name} <span className={dashStyles.sourceCount}>{s.insight_count}</span>
                  </button>
                ))}
              </div>
              {!sourceQuery.trim() && filteredSources.length > SOURCE_PREVIEW_LIMIT && (
                <button
                  className={dashStyles.moreButton}
                  onClick={() => setShowAllSources((v) => !v)}
                >
                  {showAllSources ? `Thu gọn` : `Xem tất cả ${filteredSources.length} nguồn`}
                </button>
              )}
              {emptySources.length > 0 && (
                <p className={dashStyles.filterFootnote}>
                  {emptySources.length} nguồn chưa có insight: {emptySources.map((s) => s.name).join(', ')}.
                </p>
              )}
            </div>
          </div>
        </div>

        <div className={dashStyles.filterDrawerFooter}>
          <button onClick={clearAllFilters}>Xóa tất cả</button>
        </div>
      </div>

      {/* Hero section */}
      <section className={styles.hero}>
        <p className={styles.eyebrow}>AI Impact Radar</p>
        <h1 className={styles.pageTitle}>Tổng hợp tín hiệu AI theo nguồn và vai trò tác động</h1>
        <p className={styles.pageSubtitle}>
          Theo dõi thay đổi từ vendor, research, tech press và nguồn tiếng Việt trong một luồng
          phân tích thống nhất.
        </p>
      </section>

      <section className={styles.panel}>
        <KPISummary stats={stats} isLoading={statsLoading} />
      </section>

      {/* Toolbar */}
      <section className={styles.panel}>
        <div className={dashStyles.toolbar}>
          <div className={dashStyles.toolbarLeft}>
            <SortDropdown value={sortBy} onChange={(newSort) => updateFilterParams('sort_by', newSort)} />
            <button
              className={presetUrgentActive ? dashStyles.presetActive : dashStyles.preset}
              onClick={togglePresetUrgent}
            >
              <span aria-hidden>🔥</span> Khẩn cấp
            </button>
            <button
              className={presetVietnamActive ? dashStyles.presetActive : dashStyles.preset}
              onClick={togglePresetVietnam}
            >
              <span aria-hidden>🇻🇳</span> Việt Nam
            </button>
            <button
              className={presetMomentumActive ? dashStyles.presetActive : dashStyles.preset}
              onClick={togglePresetMomentum}
            >
              <span aria-hidden>📈</span> Đang nổi
            </button>
          </div>
          <div className={dashStyles.toolbarRight}>
            {overviewQuery.data && Math.ceil(overviewQuery.data.total / PAGE_SIZE) > 1 && (
              <Pagination
                page={page}
                total={overviewQuery.data.total}
                size={PAGE_SIZE}
                onPageChange={(nextPage) => {
                  startTransition(() => updateFilterParams('page', nextPage));
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
                variant="compact"
              />
            )}
            <button
              className={dashStyles.filterToggle}
              onClick={() => setDrawerOpen((v) => !v)}
            >
              <span>⚙️</span>
              <span>Bộ lọc</span>
              {advancedCount > 0 && (
                <span className={dashStyles.filterBadge}>{advancedCount}</span>
              )}
            </button>
          </div>
        </div>
      </section>

      {/* Active Filter Chips Row */}
      {hasAnyFilter && (
        <section className={styles.panel}>
          <div className={dashStyles.activeFilterChips}>
            {selectedTier.map((id) => (
              <button
                key={`tier-${id}`}
                className={dashStyles.activeFilterChip}
                onClick={() => updateFilterParams('intelligence_tier', selectedTier.filter((v) => v !== id))}
              >
                {tierLabelMap[id] ?? id} ×
              </button>
            ))}
            {selectedUrgency.map((id) => (
              <button
                key={`urgency-${id}`}
                className={dashStyles.activeFilterChip}
                onClick={() => updateFilterParams('urgency', selectedUrgency.filter((v) => v !== id))}
              >
                {urgencyLabelMap[id] ?? id} ×
              </button>
            ))}
            {selectedMomentum.map((id) => (
              <button
                key={`momentum-${id}`}
                className={dashStyles.activeFilterChip}
                onClick={() => updateFilterParams('momentum', selectedMomentum.filter((v) => v !== id))}
              >
                {momentumLabelMap[id] ?? id} ×
              </button>
            ))}
            {selectedVietnam.map((id) => (
              <button
                key={`vietnam-${id}`}
                className={dashStyles.activeFilterChip}
                onClick={() => updateFilterParams('vietnam_relevance', selectedVietnam.filter((v) => v !== id))}
              >
                {vietnamLabelMap[id] ?? id} ×
              </button>
            ))}
            {selectedRoles.map((id) => (
              <button
                key={`role-${id}`}
                className={dashStyles.activeFilterChip}
                onClick={() => updateFilterParams('role', selectedRoles.filter((v) => v !== id))}
              >
                {ROLE_LABELS[id] ?? id} ×
              </button>
            ))}
            {selectedSourceIds.map((id) => (
              <button
                key={`source-${id}`}
                className={dashStyles.activeFilterChip}
                onClick={() => updateFilterParams('source_id', selectedSourceIds.filter((v) => v !== id))}
              >
                {sourceLabelMap[id] ?? id} ×
              </button>
            ))}
            {searchQuery.trim() && (
              <button
                className={dashStyles.activeFilterChip}
                onClick={() => updateFilterParams('search', null)}
              >
                🔍 {searchQuery} ×
              </button>
            )}
          </div>
        </section>
      )}

      {/* Loading state */}
      {overviewQuery.isLoading && (
        <div className={styles.cardGrid}>
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {/* Error state */}
      {overviewQuery.isError && (
        <div className={styles.errorState}>
          <p>Không thể tải dữ liệu bản tin.</p>
          <p className={styles.errorDetail}>{overviewQuery.error.message}</p>
        </div>
      )}

      {/* Empty state */}
      {!overviewQuery.isLoading && !hasItems && (
        <div className={styles.emptyState}>
          <h3>Chưa có bản tin phù hợp</h3>
          <p>Điều chỉnh bộ lọc hoặc chạy pipeline ingestion để nạp dữ liệu mới.</p>
        </div>
      )}

      {/* Card grid */}
      {hasItems && overviewQuery.data && (
        <>
          {/* Result count — shown only when any filter / search is active */}
          {hasAnyFilter && (
            <p className={dashStyles.resultCount}>
              Đang hiển thị {filteredItems.length} / {overviewQuery.data.total} bản tin
            </p>
          )}

          <div className={styles.cardGrid}>
            {filteredItems.map((item, idx) => (
              <InsightCard key={item.id} insight={item} index={idx} />
            ))}
          </div>
          <Pagination
            page={page}
            total={overviewQuery.data.total}
            size={PAGE_SIZE}
            onPageChange={(nextPage) => {
              startTransition(() => updateFilterParams('page', nextPage));
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
          />
        </>
      )}
    </div>
  );
}
