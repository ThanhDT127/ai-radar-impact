import styles from '../styles/insights.module.css';

interface PaginationProps {
  page: number;
  total: number;
  size: number;
  onPageChange: (newPage: number) => void;
}

export default function Pagination({ page, total, size, onPageChange }: PaginationProps) {
  const totalPages = Math.ceil(total / size);
  if (totalPages <= 1) return null;

  return (
    <div className={styles.pagination}>
      <button
        className={styles.paginationBtn}
        disabled={page <= 1}
        onClick={() => onPageChange(page - 1)}
        aria-label="Previous page"
      >
        ← Previous
      </button>
      <span className={styles.paginationInfo}>
        {page} / {totalPages}
      </span>
      <button
        className={styles.paginationBtn}
        disabled={page >= totalPages}
        onClick={() => onPageChange(page + 1)}
        aria-label="Next page"
      >
        Next →
      </button>
    </div>
  );
}
