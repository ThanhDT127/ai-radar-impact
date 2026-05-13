import styles from '../styles/dashboard.module.css';

export type InsightSort = 'created_at' | 'published_at' | 'urgency' | 'trust_score';

interface SortDropdownProps {
  value: InsightSort;
  onChange: (value: InsightSort) => void;
}

const OPTIONS: Array<{ value: InsightSort; label: string }> = [
  { value: 'created_at', label: 'Mới nhất' },
  { value: 'published_at', label: 'Theo ngày xuất bản' },
  { value: 'urgency', label: 'Ảnh hưởng cao nhất' },
  { value: 'trust_score', label: 'Tin cậy cao nhất' },
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
