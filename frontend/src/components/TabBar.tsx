import styles from '../styles/dashboard.module.css';

export type InsightTab = 'overview' | 'sources' | 'roles';

interface TabBarProps {
  activeTab: InsightTab;
  onChange: (tab: InsightTab) => void;
}

const TABS: Array<{ id: InsightTab; label: string }> = [
  { id: 'overview', label: 'Tổng quan' },
  { id: 'sources', label: 'Theo nguồn' },
  { id: 'roles', label: 'Theo vai trò' },
];

export default function TabBar({ activeTab, onChange }: TabBarProps) {
  return (
    <div className={styles.tabBar} role="tablist" aria-label="Insight views">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          aria-selected={activeTab === tab.id}
          className={activeTab === tab.id ? styles.tabActive : styles.tab}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
