import styles from '../styles/dashboard.module.css';

export type InsightSort = 'created_at' | 'published_at' | 'urgency' | 'trust_score' | 'actionability_score';

interface SortDropdownProps {
  value: InsightSort;
  onChange: (value: InsightSort) => void;
}

const OPTIONS: Array<{ value: InsightSort; label: string }> = [
  { value: 'published_at', label: 'Mới nhất' },
  { value: 'created_at', label: 'Theo ngày cào' },
  { value: 'urgency', label: 'Ảnh hưởng cao nhất' },
];

export default function SortDropdown({ value, onChange }: SortDropdownProps) {
  return (
    <label className={styles.sortBox}>
      <span className={styles.sortLabel}>Sắp xếp</span>
      <select
        className={styles.sortSelect}
        value={value}
        onChange={(event) => onChange(event.target.value as InsightSort)}
      >
        {OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}
