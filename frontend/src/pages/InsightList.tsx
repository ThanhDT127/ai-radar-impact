import { startTransition, useEffect, useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchInsights } from '../api/insights';
import { fetchSources } from '../api/sources';
import { fetchInsightStats } from '../api/stats';
import InsightCard from '../components/InsightCard';
import KPISummary from '../components/KPISummary';
import Pagination from '../components/Pagination';
import type { InsightSort } from '../components/SortDropdown';
import SortDropdown from '../components/SortDropdown';
import TabBar from '../components/TabBar';
import type { InsightTab } from '../components/TabBar';
import styles from '../styles/insights.module.css';
import dashboardStyles from '../styles/dashboard.module.css';

const PAGE_SIZE = 12;
const SOURCE_PREVIEW_LIMIT = 12;

const ROLE_OPTIONS = [
  'Executive', 'Engineering', 'Data/AI', 'Product',
  'Content/Marketing', 'Legal/Compliance', 'HR/L&D', 'Toàn công ty',
];

const URGENCY_ITEMS = [
  { id: 'critical', label: 'Khẩn cấp' },
  { id: 'high', label: 'Cao' },
  { id: 'medium', label: 'Trung bình' },
  { id: 'low', label: 'Thấp' },
];

const MOMENTUM_ITEMS = [
  { id: 'new', label: 'Mới' },
  { id: 'rising', label: 'Đang nổi' },
  { id: 'mature', label: 'Ổn định' },
];

const VIETNAM_ITEMS = [
  { id: 'high', label: 'Liên quan cao' },
  { id: 'medium', label: 'Liên quan vừa' },
  { id: 'low', label: 'Thấp' },
];

const PRESET_URGENT = ['critical', 'high'];
const PRESET_MOMENTUM = ['rising', 'new'];

function SkeletonCard() {
  return (
    <div className={styles.skeleton}>
      <div className={styles.cardHeader}>
        <div className={`${styles.skeletonLine} ${styles.skeletonLineTitle}`} />
        <div className={`${styles.skeletonLine} ${styles.skeletonLineBadge}`} />
      </div>
      <div className={`${styles.skeletonLine} ${styles.skeletonLineBody}`} />
      <div className={`${styles.skeletonLine} ${styles.skeletonLineBodySmall}`} />
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
  const [page, setPage] = useState(1);
  const [activeTab, setActiveTab] = useState<InsightTab>('overview');
  const [sortBy, setSortBy] = useState<InsightSort>('created_at');
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([]);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const [selectedUrgency, setSelectedUrgency] = useState<string[]>([]);
  const [selectedMomentum, setSelectedMomentum] = useState<string[]>([]);
  const [selectedVietnam, setSelectedVietnam] = useState<string[]>([]);

  const [showFilters, setShowFilters] = useState(false);
  const [sourceQuery, setSourceQuery] = useState('');
  const [showAllSources, setShowAllSources] = useState(false);

  useEffect(() => {
    setPage(1);
  }, [activeTab, sortBy, selectedRoles, selectedSourceIds, selectedUrgency, selectedMomentum, selectedVietnam]);

  useEffect(() => {
    setSelectedUrgency([]);
    setSelectedMomentum([]);
    setSelectedVietnam([]);
    setSourceQuery('');
    setShowAllSources(false);
  }, [activeTab]);

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
      'insights', activeTab, page, sortBy,
      selectedSourceIds, selectedRoles,
      selectedUrgency, selectedMomentum, selectedVietnam,
    ],
    queryFn: () =>
      fetchInsights({
        page,
        size: PAGE_SIZE,
        sort_by: sortBy,
        source_id: activeTab === 'sources' ? selectedSourceIds : null,
        role: activeTab === 'roles' ? selectedRoles : null,
        urgency: selectedUrgency.length > 0 ? selectedUrgency : null,
        momentum: selectedMomentum.length > 0 ? selectedMomentum : null,
        vietnam_relevance: selectedVietnam.length > 0 ? selectedVietnam : null,
      }),
  });

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

  const togglePresetUrgent = () =>
    setSelectedUrgency(presetUrgentActive ? [] : PRESET_URGENT);
  const togglePresetVietnam = () =>
    setSelectedVietnam(presetVietnamActive ? [] : ['high']);
  const togglePresetMomentum = () =>
    setSelectedMomentum(presetMomentumActive ? [] : PRESET_MOMENTUM);

  const advancedCount =
    selectedUrgency.length + selectedMomentum.length + selectedVietnam.length +
    (activeTab === 'sources' ? selectedSourceIds.length : 0) +
    (activeTab === 'roles' ? selectedRoles.length : 0);

  const clearAll = () => {
    setSelectedUrgency([]);
    setSelectedMomentum([]);
    setSelectedVietnam([]);
    setSelectedSourceIds([]);
    setSelectedRoles([]);
    setSourceQuery('');
  };

  const hasItems = (overviewQuery.data?.items.length ?? 0) > 0;

  const renderChipRow = (
    label: string,
    items: { id: string; label: string }[],
    selected: string[],
    setSelected: (next: string[]) => void,
  ) => (
    <div className={dashboardStyles.filterRow}>
      <span className={dashboardStyles.filterRowLabel}>{label}</span>
      {items.map((item) => (
        <button
          key={item.id}
          className={selected.includes(item.id) ? dashboardStyles.filterChipActive : dashboardStyles.filterChip}
          onClick={() => setSelected(toggle(item.id, selected))}
        >
          {item.label}
        </button>
      ))}
    </div>
  );

  return (
    <div className={styles.listPage}>
      <section className={styles.hero}>
        <p className={styles.eyebrow}>AI Impact Radar</p>
        <h1 className={styles.pageTitle}>Tổng hợp tín hiệu AI theo nguồn và vai trò tác động</h1>
        <p className={styles.pageSubtitle}>
          Theo dõi thay đổi từ vendor, research, tech press và nguồn tiếng Việt trong một luồng
          phân tích thống nhất.
        </p>
      </section>

      <section className={styles.panel}>
        <TabBar
          activeTab={activeTab}
          onChange={(tab) => startTransition(() => setActiveTab(tab))}
        />
      </section>

      <section className={styles.panel}>
        <KPISummary stats={stats} isLoading={statsLoading} />
      </section>

      <section className={styles.panel}>
        <div className={dashboardStyles.toolbar}>
          <div className={dashboardStyles.toolbarLeft}>
            <SortDropdown value={sortBy} onChange={setSortBy} />
            <button
              className={presetUrgentActive ? dashboardStyles.presetActive : dashboardStyles.preset}
              onClick={togglePresetUrgent}
            >
              <span aria-hidden>🔥</span> Khẩn cấp
            </button>
            <button
              className={presetVietnamActive ? dashboardStyles.presetActive : dashboardStyles.preset}
              onClick={togglePresetVietnam}
            >
              <span aria-hidden>🇻🇳</span> Việt Nam
            </button>
            <button
              className={presetMomentumActive ? dashboardStyles.presetActive : dashboardStyles.preset}
              onClick={togglePresetMomentum}
            >
              <span aria-hidden>📈</span> Đang nổi
            </button>
          </div>
          <button
            className={dashboardStyles.filterToggle}
            onClick={() => setShowFilters((v) => !v)}
          >
            <span>⚙</span>
            <span>Bộ lọc</span>
            {advancedCount > 0 && (
              <span className={dashboardStyles.filterBadge}>{advancedCount}</span>
            )}
            <span className={dashboardStyles.filterCaret}>{showFilters ? '▴' : '▾'}</span>
          </button>
        </div>
      </section>

      {showFilters && (
        <section className={styles.panel}>
          <div className={dashboardStyles.filterPanel}>
            {activeTab === 'overview' && (
              <>
                {renderChipRow('Mức độ', URGENCY_ITEMS, selectedUrgency, setSelectedUrgency)}
                {renderChipRow('Xu hướng', MOMENTUM_ITEMS, selectedMomentum, setSelectedMomentum)}
                {renderChipRow('Việt Nam', VIETNAM_ITEMS, selectedVietnam, setSelectedVietnam)}
              </>
            )}

            {activeTab === 'roles' && (
              <>
                {renderChipRow('Mức độ', URGENCY_ITEMS, selectedUrgency, setSelectedUrgency)}
                {renderChipRow('Xu hướng', MOMENTUM_ITEMS, selectedMomentum, setSelectedMomentum)}
                {renderChipRow('Việt Nam', VIETNAM_ITEMS, selectedVietnam, setSelectedVietnam)}
                {renderChipRow(
                  'Vai trò',
                  ROLE_OPTIONS.map((r) => ({ id: r, label: r })),
                  selectedRoles,
                  setSelectedRoles,
                )}
              </>
            )}

            {activeTab === 'sources' && (
              <>
                {renderChipRow('Mức độ', URGENCY_ITEMS, selectedUrgency, setSelectedUrgency)}
                {renderChipRow('Xu hướng', MOMENTUM_ITEMS, selectedMomentum, setSelectedMomentum)}
                {renderChipRow('Việt Nam', VIETNAM_ITEMS, selectedVietnam, setSelectedVietnam)}
                <div className={dashboardStyles.sourceRow}>
                  <span className={dashboardStyles.sourceLabel}>Nguồn</span>
                  <div className={dashboardStyles.sourceContent}>
                    <input
                      type="search"
                      placeholder="Tìm nguồn..."
                      value={sourceQuery}
                      onChange={(e) => setSourceQuery(e.target.value)}
                      className={dashboardStyles.sourceSearch}
                    />
                    <div className={dashboardStyles.sourceChipWrap}>
                      {visibleSources.map((s) => (
                        <button
                          key={s.id}
                          className={selectedSourceIds.includes(s.id) ? dashboardStyles.filterChipActive : dashboardStyles.filterChip}
                          onClick={() => setSelectedSourceIds((cur) => toggle(s.id, cur))}
                        >
                          {s.name} <span className={dashboardStyles.sourceCount}>{s.insight_count}</span>
                        </button>
                      ))}
                    </div>
                    {!sourceQuery.trim() && filteredSources.length > SOURCE_PREVIEW_LIMIT && (
                      <button
                        className={dashboardStyles.moreButton}
                        onClick={() => setShowAllSources((v) => !v)}
                      >
                        {showAllSources ? `Thu gọn` : `Xem tất cả ${filteredSources.length} nguồn`}
                      </button>
                    )}
                    {emptySources.length > 0 && (
                      <p className={dashboardStyles.filterFootnote}>
                        {emptySources.length} nguồn chưa có insight: {emptySources.map((s) => s.name).join(', ')}.
                      </p>
                    )}
                  </div>
                </div>
              </>
            )}

            {advancedCount > 0 && (
              <div className={dashboardStyles.filterFooter}>
                <button className={dashboardStyles.clearAll} onClick={clearAll}>
                  Xóa tất cả bộ lọc
                </button>
              </div>
            )}
          </div>
        </section>
      )}

      {overviewQuery.isLoading && (
        <div className={styles.cardGrid}>
          {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      )}

      {overviewQuery.isError && (
        <div className={styles.errorState}>
          <p>Không thể tải dữ liệu bản tin.</p>
          <p className={styles.errorDetail}>{overviewQuery.error.message}</p>
        </div>
      )}

      {!overviewQuery.isLoading && !hasItems && (
        <div className={styles.emptyState}>
          <h3>Chưa có bản tin phù hợp</h3>
          <p>Điều chỉnh bộ lọc hoặc chạy pipeline ingestion để nạp dữ liệu mới.</p>
        </div>
      )}

      {hasItems && overviewQuery.data && (
        <>
          <div className={styles.cardGrid}>
            {overviewQuery.data.items.map((insight) => (
              <InsightCard key={insight.id} insight={insight} />
            ))}
          </div>
          <Pagination
            page={page}
            total={overviewQuery.data.total}
            size={PAGE_SIZE}
            onPageChange={(nextPage) => startTransition(() => setPage(nextPage))}
          />
        </>
      )}
    </div>
  );
}
