import { startTransition, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchInsights } from '../api/insights';
import { fetchSources } from '../api/sources';
import { fetchInsightStats } from '../api/stats';
import FilterChips from '../components/FilterChips';
import type { FilterChipItem } from '../components/FilterChips';
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
const ROLE_OPTIONS = [
  'Executive',
  'Engineering',
  'Data/AI',
  'Product',
  'Content/Marketing',
  'Legal/Compliance',
  'HR/L&D',
  'Toàn công ty',
];

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

function toggleSelection(value: string, selected: string[]): string[] {
  return selected.includes(value)
    ? selected.filter((item) => item !== value)
    : [...selected, value];
}

export default function InsightList() {
  const [page, setPage] = useState(1);
  const [activeTab, setActiveTab] = useState<InsightTab>('overview');
  const [sortBy, setSortBy] = useState<InsightSort>('created_at');
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>([]);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);

  useEffect(() => {
    setPage(1);
  }, [activeTab, sortBy, selectedRoles, selectedSourceIds]);

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['insight-stats'],
    queryFn: fetchInsightStats,
  });

  const { data: sources = [] } = useQuery({
    queryKey: ['sources'],
    queryFn: fetchSources,
  });

  const overviewQuery = useQuery({
    queryKey: ['insights', activeTab, page, sortBy, selectedSourceIds, selectedRoles],
    queryFn: () =>
      fetchInsights({
        page,
        size: PAGE_SIZE,
        sort_by: sortBy,
        source_id: activeTab === 'sources' ? selectedSourceIds : null,
        role: activeTab === 'roles' ? selectedRoles : null,
      }),
  });

  const sortedSources = [...sources].sort((left, right) => {
    if (right.insight_count !== left.insight_count) {
      return right.insight_count - left.insight_count;
    }
    return left.name.localeCompare(right.name);
  });

  const activeSources = sortedSources.filter((source) => source.insight_count > 0);
  const emptySources = sortedSources.filter((source) => source.insight_count === 0);

  const sourceItems: FilterChipItem[] = activeSources.map((source) => ({
    id: source.id,
    label: source.name,
    count: source.insight_count,
  }));

  const roleItems: FilterChipItem[] = ROLE_OPTIONS.map((role) => ({
    id: role,
    label: role,
    count: overviewQuery.data?.items.filter((item) => item.affected_roles.includes(role)).length,
  }));

  const hasItems = (overviewQuery.data?.items.length ?? 0) > 0;

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
          onChange={(tab) => {
            startTransition(() => setActiveTab(tab));
          }}
        />
      </section>

      <section className={styles.panel}>
        <KPISummary stats={stats} isLoading={statsLoading} />
      </section>

      <section className={styles.panel}>
        <div className={dashboardStyles.toolbar}>
          <SortDropdown value={sortBy} onChange={setSortBy} />
          {activeTab === 'sources' && (
            <span className={dashboardStyles.emptyFilterHint}>
              Chọn một hoặc nhiều nguồn để xem publisher nào đang phát tín hiệu gì.
            </span>
          )}
          {activeTab === 'roles' && (
            <span className={dashboardStyles.emptyFilterHint}>
              Chọn một hoặc nhiều vai trò để ưu tiên nhóm bị ảnh hưởng.
            </span>
          )}
        </div>
      </section>

      {activeTab === 'sources' && (
        <section className={styles.panel}>
          <FilterChips
            items={sourceItems}
            selected={selectedSourceIds}
            onToggle={(id) => setSelectedSourceIds((current) => toggleSelection(id, current))}
          />
          {emptySources.length > 0 && (
            <p className={dashboardStyles.filterFootnote}>
              {emptySources.length} nguồn đang chưa có insight hiển thị:
              {' '}
              {emptySources.map((source) => source.name).join(', ')}.
            </p>
          )}
        </section>
      )}

      {activeTab === 'roles' && (
        <section className={styles.panel}>
          <FilterChips
            items={roleItems}
            selected={selectedRoles}
            onToggle={(id) => setSelectedRoles((current) => toggleSelection(id, current))}
          />
        </section>
      )}

      {overviewQuery.isLoading && (
        <div className={styles.cardGrid}>
          {Array.from({ length: 6 }).map((_, index) => <SkeletonCard key={index} />)}
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
            onPageChange={(nextPage) => {
              startTransition(() => setPage(nextPage));
            }}
          />
        </>
      )}
    </div>
  );
}
