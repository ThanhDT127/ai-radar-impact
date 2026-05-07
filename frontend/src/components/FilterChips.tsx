import styles from '../styles/dashboard.module.css';

export interface FilterChipItem {
  id: string;
  label: string;
  count?: number;
}

interface FilterChipsProps {
  items: FilterChipItem[];
  selected: string[];
  onToggle: (id: string) => void;
}

export default function FilterChips({ items, selected, onToggle }: FilterChipsProps) {
  return (
    <div className={styles.chipsWrap}>
      {items.map((item) => {
        const active = selected.includes(item.id);
        return (
          <button
            key={item.id}
            type="button"
            className={active ? styles.chipActive : styles.chip}
            onClick={() => onToggle(item.id)}
            aria-pressed={active}
          >
            <span className={styles.chipLabel}>{item.label}</span>
            {typeof item.count === 'number' && (
              <span className={active ? styles.chipCountActive : styles.chipCount}>
                {item.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
